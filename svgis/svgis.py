"""Draw geodata layers into svg"""
# -*- coding: utf-8 -*-
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
from . import svg
from . import scale

STYLE = '''
polyline, line, rect, path, polygon, .polygon {
 fill: none;
 stroke: #000;
 stroke-width: 1px;
 stroke-linejoin: round;
}'''


def _collate_bounds(geometry, bounds):
    minx, miny, maxx, maxy = bounds

    geometry['coordinates'] = list(list(x) for x in geometry['coordinates'])
    x0, y0, x1, y1 = fionautil.geometry.bbox(geometry)

    return min(minx, x0), min(miny, y0), max(maxx, x1), max(maxy, y1)


def _choosecrs(in_crs, bounds=None, use_utm=None):
    '''Choose a projection. If the layer is projected, use that.
    Otherwise, create use a passed projection or create a custom transverse mercator.
    Returns a function that operates on features
    '''
    if use_utm:
        midx = (bounds[0] + bounds[2]) / 2
        midy = (bounds[1] + bounds[3]) / 2

        try:
            out_crs = fiona.crs.from_string(projection.utm_proj4(midx, midy))
        except ValueError:
            return _choosecrs(in_crs, bounds, use_utm=None)

    elif Proj(**in_crs).is_latlong():

        minpt, maxpt = (bounds[0], bounds[1]), (bounds[2], bounds[3])
        # Create a custom TM projection
        x0 = (float(minpt[0]) + float(maxpt[0])) / 2

        out_proj4 = projection.tm_proj4(x0, minpt[1], maxpt[1])
        out_crs = fiona.crs.from_string(out_proj4)

    else:
        # it's projected already, so noop.
        out_crs = in_crs

    return out_crs


class SVGIS(object):

    """Draw geodata files to SVG"""

    bounds = dict()
    in_crs = None

    def __init__(self, files, mbr, out_crs=None, **kwargs):
        self.files = files

        self.mbr = mbr or None

        self.out_crs = out_crs

        self.use_utm = kwargs.pop('use_utm', False)

        self.scalar = kwargs.pop('scalar', 1)

        self.style = kwargs.pop('style', STYLE)

        self.padding = kwargs.pop('padding', 0)

    def _project_mbr(self, scalar):
        '''Project and apply a scale to the MBR'''
        mx, my, MX, MY = self.mbr

        x0, x1, y0, y1 = fiona.transform.transform(self.in_crs, self.out_crs, (mx, MX), (my, MY))

        # then scale the min and max
        x0, y0 = scale.scale((x0, y0), scalar)
        x1, y1 = scale.scale((x1, y1), scalar)

        return (x0, y0, x1, y1)

    def _dims(self, x0, y0, x1, y1):
        w = x1 - x0 + (self.padding * 2)
        h = y1 - y0 + (self.padding * 2)

        return w, h

    def compose_file(self, filename, scalar, **kwargs):
        '''Draw file to svg
        filename -- a fiona-readable file
        mbr -- a tuple containing (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK
        '''
        with fiona.open(filename, "r") as layer:
            group = svgwrite.container.SVG(fill_rule="evenodd", id=layer.name)

            if self.in_crs is None:
                self.in_crs = layer.crs

            if not self.out_crs:
                # Determine projection transformation:
                # either use something passed in, a non latlong layer projection,
                # the local UTM, or customize local TM
                self.out_crs = _choosecrs(layer.crs, self.mbr or layer.bounds, use_utm=self.use_utm)

            if self.out_crs != layer.crs:
                reproject = lambda geom: fiona.transform.transform_geom(layer.crs, self.out_crs, geom)
            else:
                reproject = lambda f: f

            if not self.mbr:
                self.bounds[filename] = 1e28, 1e28, -1e28, -1e28

            for _, f in layer.items(bbox=self.mbr):
                geom = scale.geometry(reproject(f['geometry']), scalar)

                if not self.mbr:
                    self.bounds[filename] = _collate_bounds(geom, self.bounds[filename])

                for p in draw.geometry(geom, **kwargs):
                    group.add(p)

        return group

    def compose(self, style=None, scalar=None, **kwargs):
        '''Draw files to svg.
        scalar -- factor by which to scale the data.
        style -- CSS
        '''
        scalar = scalar or self.scalar
        style = style or self.style

        container = svgwrite.container.SVG()

        with fiona.drivers():
            for filename in self.files:
                group = self.compose_file(filename, scalar, **kwargs)
                container.add(group)

        # Either project the bounds, or don't
        if self.mbr:
            bounds = self._project_mbr(scalar)
        else:
            bounds = [(min(x), min(y), max(X), max(Y)) for x, y, X, Y in [zip(*self.bounds.values())]]

        dims = self._dims(*bounds)
        drawing = svg.create(dims, [container], style=style)

        return svg.frame(drawing, bounds[:2], bounds[2:], self.padding)
