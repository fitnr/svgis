import fiona
import fiona.crs
import fiona.transform
import svgwrite
import fionautil.layer
import fionautil.feature
import fionautil.geometry
from pyproj import Proj
from . import projection
from . import draw
from . import convert
from . import svg

STYLE = '''
polyline, line, rect, path, polygon, .polygon {
    fill: none;
    stroke: #000;
    stroke-width: 1px;
    stroke-linejoin: round
}'''


def _minmaxpts(bounds, mbr):
    '''Replace any missing min/max points with those from the layer's bounds'''
    if any(v is None for v in mbr):
        minx, maxx, miny, maxy = [(a or b) for a, b in zip(mbr, bounds)]

    minpt = (minx, miny)
    maxpt = (maxx, maxy)

    return minpt, maxpt


def _choosecrs(in_crs, bounds=None, use_utm=None):
    '''Choose a projection. If the layer is projected, use that.
    Otherwise, create use a passed projection or create a custom transverse mercator.
    Returns a function that operates on features
    '''
    in_proj = Proj(**in_crs)

    if in_proj.is_latlong():
        if use_utm:
            midx = (bounds[0] + bounds[2]) / 2
            midy = (bounds[1] + bounds[3]) / 2

            try:
                out_proj4 = projection.utmproj4(midx, midy)
            except ValueError:
                return _choosecrs(in_crs, bounds, use_utm=None)

        else:
            minpt, maxpt = (bounds[0], bounds[1]), (bounds[2], bounds[3])
            # Create a custom TM projection
            x0 = (float(minpt[0]) + float(maxpt[0])) / 2
            out_proj4 = projection.tm_proj4(x0, minpt[1], maxpt[1])

        out_crs = fiona.crs.from_string(out_proj4)

    else:
        # it's projected already, so noop.
        out_crs = None

    return out_crs


def _minmax(transform, bounds, scalar=None):
    '''Use a minpt and maxpt to translate a group to be visible'''
    # Project the minpt and maxpt if necessary
    minpt, maxpt = zip(*transform((bounds[0], bounds[2]), (bounds[1], bounds[3])))

    scalar = scalar or 1

    # then scale the min and max
    x0, y0 = convert.scale(minpt, scalar)
    x1, y1 = convert.scale(maxpt, scalar)

    return (x0, y0), (x1, y1)


def _framedrawing(groups, minpt, maxpt, style=None, padding=0):
    '''Translate the group to the correct spot and save the drawing'''
    x0, y0 = minpt
    x1, y1 = maxpt

    style = style or STYLE

    padding = padding or 0

    # set window
    for group in groups:
        group.translate(-x0 + padding, y1 + padding)

        group.scale(1, -1)

    return svg.create((x1 - x0 + padding + padding, y1 - y0 + padding + padding), groups, profile='full', style=style)


def compose(filename, mbr=None, out_crs=None, scalar=None, style=None, padding=0, **kwargs):
    '''Draw file to svg
    filename: a fiona-readable file
    mbr: a tuple containing (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK
    '''
    scalar = scalar or 1

    bbox = {'bbox': mbr} if mbr else {}

    with fiona.drivers():
        with fiona.open(filename, "r") as layer:
            group = svgwrite.container.Group(fill_rule="evenodd", id=layer.name)

            if not out_crs:
                # Determine projection transformation:
                # either use something passed in, a non latlong layer projection,
                # the local UTM, or customize local TM
                out_crs = _choosecrs(layer.crs, mbr or layer.bounds, use_utm=kwargs.pop('use_utm'))

            if out_crs:
                reproject = lambda geom: fiona.transform.transform_geom(layer.crs, out_crs, geom)
                transform = lambda xs, ys: fiona.transform.transform(layer.crs, out_crs, xs, ys)

            else:
                reproject = lambda f: f
                transform = lambda x, y: (x, y)

            # FYI, we can't use the layer bounds
            # because of obvious things about map projections
            minx, miny, maxx, maxy = 1e28, 1e28, -1e28, -1e28

            for _, f in layer.items(**bbox):
                geom = convert.scale_geometry(reproject(f['geometry']), scalar)
                if not mbr:
                    # Can't have a generator
                    geom['coordinates'] = list(list(x) for x in geom['coordinates'])
                    x0, y0, x1, y1 = fionautil.geometry.bbox(geom)
                    minx, miny = min(minx, x0), min(miny, y0)
                    maxx, maxy = max(maxx, x1), max(maxy, y1)

                for p in draw.geometry(geom, **kwargs):
                    group.add(p)

    # Either project the bounds, or don't
    if mbr:
        lowerleft, topright = _minmax(transform, mbr, scalar)
    else:
        lowerleft, topright = (minx, miny), (maxx, maxy)

    return _framedrawing([group], lowerleft, topright, style, padding)
