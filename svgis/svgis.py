"""Draw geodata layers into svg"""
# -*- coding: utf-8 -*-
import fiona
import fiona.crs
import fiona.transform
import svgwrite
from pyproj import Proj
import fionautil.coords
from . import projection
from . import draw
from . import svg
from . import scale
from . import convert

STYLE = ('polyline, line, rect, path, polygon, .polygon {'
         ' fill: none;'
         ' stroke: #000;'
         ' stroke-width: 1px;'
         ' stroke-linejoin: round;'
         '}')

def _choosecrs(in_crs, bounds=None, use_proj=None):
    '''Choose a projection. If the layer is projected, use that.
    Otherwise, create use a passed projection or create a custom transverse mercator.
    Returns a function that operates on features
    '''
    if use_proj == 'utm':
        midx = (bounds[0] + bounds[2]) / 2
        midy = (bounds[1] + bounds[3]) / 2

        try:
            out_crs = fiona.crs.from_string(projection.utm_proj4(midx, midy))
        except ValueError:
            return _choosecrs(in_crs, bounds, use_proj=None)

    elif use_proj == 'local_tm' or Proj(**in_crs).is_latlong():
        # Create a custom TM projection
        x0 = (float(bounds[0]) + float(bounds[2])) // 2

        out_proj4 = projection.tm_proj4(x0, bounds[1], bounds[3])
        out_crs = fiona.crs.from_string(out_proj4)

    else:
        # it's projected already, so noop.
        out_crs = in_crs

    return out_crs

class SVGIS(object):

    """Draw geodata files to SVG"""

    bounds = dict()
    in_crs = None

    def __init__(self, files, bounds=None, out_crs=None, **kwargs):
        self.files = files

        bounds = bounds or (None,) * 4

        self.mbr = convert.replacebounds(bounds, (None, None, None, None))

        self.out_crs = out_crs

        self.use_proj = kwargs.pop('use_proj')

        self.scalar = kwargs.pop('scalar', 1)

        self.style = kwargs.pop('style', STYLE)

        self.padding = kwargs.pop('padding', 0)

    @property
    def _incomplete_mbr(self):
        return any([x is None for x in self.mbr])

    def compose_file(self, filename, scalar, **kwargs):
        '''Draw file to svg
        filename -- a fiona-readable file
        mbr -- a tuple containing (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK
        '''
        with fiona.open(filename, "r") as layer:
            group = svgwrite.container.Group(id=layer.name)

            if self.in_crs is None:
                self.in_crs = layer.crs

            self.bounds[layer.name] = convert.replacebounds(self.mbr, layer.bounds)

            if 'classes' in kwargs:
                classes = [c for c in kwargs['classes'] if c in layer.schema['properties']]
                kwargs.pop('classes')
            else:
                classes = None

            id_field = kwargs.pop('id_field', None)

            if id_field not in layer.schema['properties'].keys():
                id_field = None

            if not self.out_crs:
                # Determine projection transformation:
                # either use something passed in, a non latlong layer projection,
                # the local UTM, or customize local TM
                self.out_crs = _choosecrs(layer.crs, self.bounds[layer.name], use_proj=self.use_proj)

            if self.out_crs != layer.crs:
                reproject = lambda geom: fiona.transform.transform_geom(layer.crs, self.out_crs, geom)
            else:
                reproject = lambda f: f

            for _, f in layer.items(bbox=self.bounds[layer.name]):
                attribs = {}
                geom = scale.geometry(reproject(f['geometry']), scalar)

                if classes:
                    attribs['class'] = ' '.join([str(f['properties'][c]).replace(' ', '_') for c in classes])

                if id_field:
                    attribs['id'] = str(f['properties'][id_field]).replace(' ', '_')

                ps = draw.geometry(geom, **kwargs)

                if len(ps) > 1:
                    target = svgwrite.container.Group()
                    for p in ps:
                        target.add(p)
                else:
                    target = ps[0]

                target.attribs.update(attribs)
                group.add(target)

        return group

    def compose(self, style=None, scalar=None, **kwargs):
        '''Draw files to svg.
        scalar -- factor by which to scale the data.
        style -- CSS
        '''
        scalar = scalar or self.scalar
        style = style or self.style

        viewbox = kwargs.pop('viewbox', None)

        container = svgwrite.container.Group(transform='scale(1, -1)', fill_rule='evenodd')
        container.translate(self.padding, -self.padding)

        with fiona.drivers():
            for filename in self.files:
                container.add(self.compose_file(filename, scalar, **kwargs))

        w, h, x0, y1 = self._bounds(scalar)

        if viewbox:
            drawing = svg.create((w, h), [container], style=style)
            drawing.viewbox(x0, -y1, w, h)

        else:
            container.translate(-x0, -y1)
            drawing = svg.create((w, h), [container], style=style)

        return drawing

    def _bounds(self, scalar):
        if self._incomplete_mbr:
            self.mbr = [(min(x), min(y), max(X), max(Y)) for x, y, X, Y in [zip(*self.bounds.values())]][0]

        mbr_ring = convert.mbr_to_bounds(*self.mbr)
        boundary = projection.project_scale(self.in_crs, self.out_crs, mbr_ring, scalar)

        x0, y0, x1, y1 = fionautil.coords.bounds(list(boundary))

        w = x1 - x0 + (self.padding * 2)
        h = y1 - y0 + (self.padding * 2)

        return w, h, x0, y1
