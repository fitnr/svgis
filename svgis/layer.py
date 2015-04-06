import fiona
import svgwrite
import fionautil.layer
import fionautil.geometry
import pyproj
from . import feature
from . import projection
from . import draw as svgdraw
from . import convert
from . import svg

STYLE = '''polyline, path {
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


def _chooseprojection(crs, out_proj=None, minpt=None, maxpt=None):
    '''Choose a projection. If the layer is projected, use that.
    Otherwise, create use a passed projection or create a custom transverse mercator.
    Returns a function that operates on features
    '''
    if out_proj:
        return out_proj

    in_proj = pyproj.Proj(*crs)

    if in_proj.is_latlong():
        # Create a custom TM projection
        x0 = (float(minpt[0]) + float(maxpt[0])) / 2
        out_proj = projection.tm(x0, minpt[1], maxpt[1])

    else:
        # it's projected already, so noop.
        out_proj = None

    return out_proj


def _project_minmax(proj, minpt, maxpt, scalar=None):
    '''Use a minpt and maxpt to translate a group to be visible
    If proj is None, assume points are already projected
    '''
    # Project them minpt and maxpt if necessary
    if proj:
        minpt = proj(*minpt)
        maxpt = proj(*maxpt)

    scalar = scalar or 1

    # then scale the min and max
    x0, y0 = convert.scale(minpt, scalar)
    x1, y1 = convert.scale(maxpt, scalar)

    return (x0, y0), (x1, y1)


def _drawing(group, minpt, maxpt, style=None):
    '''Translate the group to the correct spot and save the drawing'''
    x0, y0 = minpt
    x1, y1 = maxpt

    style = style or STYLE

    # set window
    group.translate(-x0, y0)
    group.scale(1, -1)
    group.translate(0, -(y1 - y0))

    return svg.create((x1 - x0, y1 - y0), [group], profile='full', style=style)


def compose(filename, mbr=None, scalar=None, style=None, **kwargs):
    '''Draw file to svg
    filename: a fiona-readable file
    mbr: a tuple containing (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK
    '''
    scalar = scalar or 1

    mbr = mbr or (None, None, None, None)

    group = svgwrite.container.Group(fill_rule="evenodd")

    with fiona.drivers():
        with fiona.open(filename, "r") as layer:
            # determine bounds if not given
            minpt, maxpt = _minmaxpts(layer.bounds, mbr)

            # minpt, maxpt are either numbers passed in (in the layer's coordinate system)
            # or the extent of the layer (in the native coordinate system)

            # Determine projection transformation:
            # either use something passed in, a non latlong layer projection, or custom TM
            out_proj = _chooseprojection(layer.crs, kwargs.get('proj'), minpt, maxpt)

            if out_proj:
                in_proj = pyproj.Proj(*layer.crs)
                reproject = lambda feature: fionautil.feature.reproject(in_proj, out_proj, feature)
            else:
                reproject = lambda x: x

            for f in layer.items(bbox=minpt + maxpt):
                f = feature.scale(reproject(f), scalar)

                for p in svgdraw.feature(f, **kwargs):
                    group.add(p)

    lowerleft, topright = _project_minmax(out_proj, minpt, maxpt, scalar)

    # debugging
    group.add(svgwrite.shapes.Line((lowerleft), (topright)))

    drawing = _drawing(group, lowerleft, topright, style)

    return drawing.tostring()
