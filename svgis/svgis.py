"""Draw geodata layers into svg"""
# -*- coding: utf-8 -*-
from collections import Iterable
import fiona
import fiona.transform
import svgwrite
import fionautil.coords
from . import projection
from . import draw
from . import svg
from fionautil import scale
from . import convert

STYLE = ('polyline, line, rect, path, polygon, .polygon {'
         ' fill: none;'
         ' stroke: #000;'
         ' stroke-width: 1px;'
         ' stroke-linejoin: round;'
         '}')


def _draw_feature(geom, properties=None, **kwargs):
    '''Draw a single feature given a geometry object and properties object'''
    properties = properties or {}

    if kwargs.get('classes'):
        if not isinstance(kwargs['classes'], Iterable):
            kwargs['classes'] = [kwargs['classes']]

        try:
            kwargs['class_'] = ' '.join(svg.sanitize(properties.get(c, '')) for c in kwargs.pop('classes'))

        except TypeError:
            pass

    if kwargs.get('id_field'):
        try:
            kwargs['id'] = svg.sanitize(properties.get(kwargs.pop('id_field')))
        except AttributeError:
            pass

    result = draw.geometry(geom, **kwargs)
    return result


class SVGIS(object):

    """Draw geodata files to SVG"""

    # pylint: disable=too-many-instance-attributes

    # bounds is the bounding box in input coordinates
    bounds = tuple()
    # MBR is the bounding box in output coordinates, to be determined as we draw.
    mbr = (None, None, None, None)

    def __init__(self, files, bounds=None, out_crs=None, **kwargs):
        '''
        Create an SVGIS object, which will stand ready to generate some maps
        :files list/str A list of files to map
        :bounds list/tuple An iterable with four float coordinates in (minx, miny, maxx, maxy) format
        :out_crs dict A proj-4 like mapping
        :use_proj string A keyword for picking a projection (either utm or local)
        :style string CSS to add to output file
        :scalar int Map scale to use (output coordinate are divided by this)
        :padding number Buffer each edge by this many map units
        '''
        if isinstance(files, basestring):
            self.files = [files]
        elif isinstance(files, Iterable):
            self.files = files
        else:
            raise ValueError("'files' must be a file name or list of file names")

        if bounds and len(bounds) == 4:
            self.bounds = bounds

        self.out_crs = out_crs

        self.use_proj = kwargs.pop('use_proj', None)

        self.scalar = kwargs.pop('scalar', None) or 1

        self.style = STYLE + (kwargs.pop('style', '') or '')

        self.padding = kwargs.pop('padding', None) or 0

    def __repr__(self):
        return ('SVGIS(files={0.files}, out_crs={0.out_crs}, '
                'bounds={0.bounds}, padding={0.padding}, '
                'scalar={0.scalar})').format(self)

    def compose_file(self, filename, scalar, bounds=None, **kwargs):
        '''
        Draw fiona file to svgwrite Group object.
        :filename string path to a fiona-readable file
        :scalar int map scale
        :bounds tuple (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK
        '''
        with fiona.open(filename, "r") as layer:
            group = svgwrite.container.Group(id=layer.name)

            bounds = bounds or self.bounds or layer.bounds

            if not self.out_crs:
                # Determine projection transformation:
                # either use something passed in, a non latlong layer projection,
                # the local UTM, or customize local TM
                self.out_crs = projection.choosecrs(layer.crs, bounds, use_proj=self.use_proj)

            self.mbr = convert.updatebounds(self.mbr, projection.project_mbr(layer.crs, self.out_crs, *bounds))

            if 'classes' in kwargs:
                kwargs['classes'] = [c for c in kwargs['classes'] if c in layer.schema['properties']]

            if 'id_field' in kwargs:
                if kwargs['id_field'] not in layer.schema['properties'].keys():
                    del kwargs['id_field']

            if self.out_crs != layer.crs:
                reproject = lambda geom: fiona.transform.transform_geom(layer.crs, self.out_crs, geom)
            else:
                reproject = lambda f: f

            for _, f in layer.items(**{'bbox': bounds}):
                geom = scale.geometry(reproject(f['geometry']), scalar)

                target = _draw_feature(geom, f['properties'], **kwargs)

                group.add(target)

        return group

    def compose(self, style=None, scalar=None, bounds=None, **kwargs):
        '''
        Draw files to svg.
        :scalar int factor by which to scale the data.
        :style string CSS to append to parent object CSS
        :bounds list/tuple Bounding box to draw within. Defaults to map data bounds.
        :viewbox bool If True, draw SVG with a viewbox. If False, translate coordinates to the frame. Defaults to True.
        '''
        scalar = scalar or self.scalar
        style = self.style + (style or '')

        viewbox = kwargs.pop('viewbox', True)

        container = svgwrite.container.Group(transform='scale(1, -1)', fill_rule='evenodd')
        container.translate(self.padding, -self.padding)

        with fiona.drivers():
            for filename in self.files:
                container.add(self.compose_file(filename, scalar, bounds=bounds, **kwargs))

        w, h, x0, y1 = self.dims(scalar, bounds=bounds)

        if viewbox:
            drawing = svg.create((w, h), [container], style=style)
            drawing.viewbox(x0, -y1, w, h)

        else:
            container.translate(-x0, -y1)
            drawing = svg.create((w, h), [container], style=style)

        return drawing

    def dims(self, scalar, bounds=None):
        '''
        Calculate the width, height, origin X and max Y of the document
        :scalar int map scale
        :bounds list/tuple input bounds to calculate with instead
        '''
        if bounds and len(bounds) == 4:
            mbr_ring = convert.mbr_to_bounds(*bounds)
        else:
            mbr_ring = convert.mbr_to_bounds(*self.mbr)

        boundary = scale.scale(mbr_ring, scalar)
        try:
            x0, y0, x1, y1 = fionautil.coords.bounds(list(boundary))
        except ValueError:
            raise ValueError('Problem calculating bounds. Check that coordinates are in x, y order.')

        w = x1 - x0 + (self.padding * 2)
        h = y1 - y0 + (self.padding * 2)

        return w, h, x0, y1
