"""Draw geodata layers into svg"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import Iterable
import logging
import fiona
import fiona.transform
import svgwrite
from fionautil import scale, coords
from . import convert, clip, css, draw, errors, projection, svg


STYLE = ('polyline, line, rect, path, polygon, .polygon {'
         ' fill: none;'
         ' stroke: #000;'
         ' stroke-width: 1px;'
         ' stroke-linejoin: round;'
         '}')


def _property(prop, properties):
    if prop in properties:
        return prop + '_' + str(properties[prop])
    else:
        return prop


def _construct_classes(classes, properties):
    if isinstance(classes, basestring):
        classes = [classes]

    classes = [svg.sanitize(_property(x, properties)) for x in classes]
    return (' '.join(classes)).strip()


def _get_classes(classlist, properties, name=None):
    '''Create a list of classes that also appear in the properties'''
    classes = [c for c in classlist if c in properties]
    if name:
        classes.insert(0, name)
    return classes


def _draw_feature(geom, properties=None, classes=None, id_field=None, **kwargs):
    '''Draw a single feature given a geometry object and properties object'''
    properties = properties or {}
    classes = classes or []

    try:
        kwargs['class_'] = _construct_classes(classes, properties)
    except TypeError:
        pass

    if id_field:
        try:
            kwargs['id'] = svg.sanitize(properties.get(id_field))
        except AttributeError:
            pass

    return draw.geometry(geom, **kwargs)


class SVGIS(object):

    """Draw geodata files to SVG"""

    # pylint: disable=too-many-instance-attributes

    # bounds is the bounding box in input coordinates
    bounds = tuple()
    # MBR is the bounding box in output coordinates, to be determined as we draw.
    mbr = (None, None, None, None)

    def __init__(self, files, bounds=None, out_crs=None, **kwargs):
        '''
        An SVGIS object, which will stand ready to generate some maps.
        :files list/str A list of files to map
        :bounds list/tuple An iterable with four float coordinates in (minx, miny, maxx, maxy) format
        :out_crs dict A proj-4 like mapping
        :use_proj string A keyword for picking a projection (file, utm or local)
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

        self.clip = kwargs.get('clip', True)

        self.log = logging.getLogger('svgis')

        self.simplifier = convert.simplifier(kwargs.pop('simplify', 0.95))

    def __repr__(self):
        return ('SVGIS(files={0.files}, out_crs={0.out_crs}, '
                'bounds={0.bounds}, padding={0.padding}, '
                'scalar={0.scalar})').format(self)

    def get_clipper(self, in_crs, in_bounds, out_bounds, scalar=None):
        '''
        Get a clipping function for the given input crs and bounds.
        Returns None if in_bounds == out_bounds or clipping is off.
        '''
        scalar = scalar or self.scalar
        projected_mbr = projection.project_mbr(in_crs, self.out_crs, *out_bounds)
        self.mbr = convert.updatebounds(self.mbr, projected_mbr)

        if self.clip and out_bounds != in_bounds:
            clipper = clip.prepare([c * scalar for c in convert.extend_bbox(projected_mbr)])
        else:
            clipper = lambda g: g

        return clipper

    def reprojector(self, in_crs):
        '''Return a reprojection transform from in_crs to self.out_crs.'''
        if self.out_crs != in_crs:
            reproject = lambda geom: fiona.transform.transform_geom(in_crs, self.out_crs, geom)
        else:
            reproject = lambda f: f

        return reproject

    def set_out_crs(self, layer_crs, bounds):
        '''Set the out CRS, if not yet set.'''
        if not self.out_crs:
            # Determine projection transformation:
            # either use something passed in, a non latlong layer projection,
            # the local UTM, or customize local TM
            self.out_crs = projection.choosecrs(layer_crs, bounds, use_proj=self.use_proj)

    def compose_file(self, filename, scalar, bounds=None, **kwargs):
        '''
        Draw fiona file to svgwrite Group object.
        :filename string path to a fiona-readable file
        :scalar int map scale
        :bounds tuple (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK
        '''
        with fiona.open(filename, "r") as layer:
            bounds = bounds or self.bounds or layer.bounds

            simplifier = kwargs.pop('simplifier', lambda x: x)

            # Set the output CRS, if not yet set.
            self.set_out_crs(layer.crs, bounds)

            # Get clipping function based on a slightly extended version of projected_mbr.
            clipper = self.get_clipper(layer.crs, layer.bounds, bounds, scalar=scalar)

            # feature reprojection function (could be no op).
            reproject = self.reprojector(layer.crs)

            # A list of class names to get from layer properties.
            kwargs['classes'] = _get_classes(kwargs.get('classes', []), layer.schema['properties'], layer.name)

            # Remove the id field if it doesn't appear in the properties.
            if 'id_field' in kwargs:
                if kwargs['id_field'] not in layer.schema['properties'].keys():
                    del kwargs['id_field']

            group = svgwrite.container.Group(id=layer.name)

            for _, f in layer.items(bbox=bounds):
                geom = scale.geometry(reproject(f['geometry']), scalar)
                geom = clipper(geom)
                geom = simplifier(geom)

                try:
                    target = _draw_feature(geom, f['properties'], **kwargs)
                    group.add(target)

                except errors.SvgisError as e:
                    self.log.error("Error drawing %s: %s", filename, e.message)

        return group

    def compose(self, style=None, scalar=None, bounds=None, **kwargs):
        '''
        Draw files to svg. Returns unicode.
        :scalar int factor by which to scale the data.
        :style string CSS to append to parent object CSS
        :bounds list/tuple Map bounding box in input units. Defaults to map data bounds.
        :viewbox bool If True, draw SVG with a viewbox. If False, translate coordinates to the frame. Defaults to True.
        '''
        scalar = scalar or self.scalar
        style = self.style + (style or '')

        viewbox = kwargs.pop('viewbox', True)
        inline_css = kwargs.pop('inline_css', False)

        if 'simplify' in kwargs:
            kwargs['simplifier'] = convert.simplifier(kwargs.pop('simplify'))
        else:
            kwargs['simplifier'] = self.simplifier

        container = svgwrite.container.Group(transform='scale(1, -1)', fill_rule='evenodd')
        container.translate(self.padding, -self.padding)

        with fiona.drivers():
            for filename in self.files:
                container.add(self.compose_file(filename, scalar, bounds=bounds, **kwargs))

        w, h, x0, y1 = self.dims(scalar, bounds=bounds)

        if not viewbox:
            container.translate(-x0, -y1)

        drawing = svg.create((w, h), [container], style=style)

        if viewbox:
            drawing.viewbox(x0, -y1, w, h)

        result = drawing.tostring()

        if inline_css:
            return css.inline(result, style)

        else:
            return result

    def dims(self, scalar, bounds=None):
        '''
        Calculate the width, height, origin X and max Y of the document
        :scalar int map scale
        :bounds list/tuple input bounds to calculate with instead
        '''
        if bounds and len(bounds) == 4:
            mbr_ring = convert.mbr_to_bounds(*bounds)
        else:
            mbr_ring = convert.mbr_to_bounds(self.mbr[0], self.mbr[1], self.mbr[2], self.mbr[3])

        boundary = scale.scale(mbr_ring, scalar)
        try:
            x0, y0, x1, y1 = coords.bounds(list(boundary))
        except ValueError:
            raise ValueError('Problem calculating bounds. Check that coordinates are in x, y order.')

        w = x1 - x0 + (self.padding * 2)
        h = y1 - y0 + (self.padding * 2)

        return w, h, x0, y1
