# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
from __future__ import division
import os.path
from collections import Iterable
from functools import partial
import logging
import fiona
import fiona.transform
import fionautil.scale
from . import convert, clip, draw, errors, projection, svg
from . import style as _style

"""
Draw geodata layers into SVGs.
"""


STYLE = ('polyline, line, rect, path, polygon, .polygon {'
         ' fill: none;'
         ' stroke: #000;'
         ' stroke-width: 1px;'
         ' stroke-linejoin: round;'
         '}')


def map(layers, bounds=None, scale=None, padding=0, **kwargs):
    '''
    Draw a geodata layer to SVG. This is shorthand for creating a :class:`SVGIS` instance
    and immediately runnning :class:`SVGIS.compose`.

    Args:
        layers (sequence): Input geodata files.
        output (path): Output file name
        bounds (sequence): (minx, miny, maxx, maxy)
        scale (int): Map scale. Larger numbers -> smaller maps
        padding (int): Pad around bounds by this much. In projection units.
        crs (string): EPSG code, PROJ.4 string, or file containing a PROJ.4 string
        clip (bool): If true, clip features output to bounds.
        style (string): Path to a css file or a css string.
        class_fields (Sequence): A comma-separated string or list of class names to
                                 use the SVG drawing.
        id_field (string): Field to use to determine id of each element in the drawing.
        inline (bool): If True, try to move CSS declarations into each element.

    Returns:
        String (unicode in Python 2) containing an entire SVG document.
    '''
    scale = (1 / scale) if scale else 1
    bounds = bounds if bounds and len(bounds) == 4 else None

    # Try to read style file
    styles = _style.pick(kwargs.pop('style', None))

    proj_method, out_crs = projection.pick(kwargs.pop('crs', None))

    class_fields = (kwargs.pop('class_fields', None) or '').split(',')

    drawing = SVGIS(
        layers,
        bounds=bounds,
        scalar=scale,
        proj_method=proj_method,
        out_crs=out_crs,
        padding=padding,
        style=styles,
        clip=kwargs.pop('clip', True),
        id_field=kwargs.pop('id_field', None),
        class_fields=class_fields
    ).compose(**kwargs)

    return drawing


def _property(prop, properties):
    '''
    Map a prop name to either prop_value or prop.

    Args:
        prop (unicode): Unicode property name
        properties (dict): Contains only unicode
    '''
    if prop in properties:
        try:
            return u'' + prop + u'_' + properties[prop]
        except TypeError:
            return unicode(prop) + u'_' + unicode(properties[prop])

    return prop


def _construct_classes(classes, properties):
    if isinstance(classes, basestring):
        classes = [classes]

    props = {unicode(k): unicode(v) for k, v in properties.items()}

    classes = [_style.sanitize(_property(unicode(x), props)) for x in classes]
    return (u' '.join(classes)).strip()


def _get_classes(classlist, properties, name=None):
    '''Create a list of classes that also appear in the properties'''
    classes = [c for c in classlist if c in properties]
    if name:
        classes.insert(0, name)
    return classes


class SVGIS(object):

    """
    Draw geodata files to SVG.

    Args:
        files (list): A list of files to draw.
        bounds (Sequence): An iterable with four float coordinates in (minx, miny, maxx, maxy) format
        out_crs (dict): A proj-4 like mapping. Overrides proj.
        project (string): A keyword for picking a projection (file, utm or local).
        style (string): CSS to add to output file
        scalar (int): Map scale to use (output coordinate are divided by this)
        padding (number): Buffer each edge by this many map units

    """

    # pylint: disable=too-many-instance-attributes

    # The bounding box in input coordinates.
    _unprojected_bounds = None

    # The bounding box in output coordinates, to be determined as we draw.
    _projected_bounds = (None, None, None, None)

    in_crs = None

    def __init__(self, files, bounds=None, out_crs=None, **kwargs):
        if isinstance(files, basestring):
            self.files = [files]
        elif isinstance(files, Iterable):
            self.files = files
        else:
            raise ValueError("'files' must be a file name or list of file names")

        if bounds and len(bounds) == 4:
            self._unprojected_bounds = bounds

        self.out_crs = out_crs

        self.proj_method = kwargs.pop('proj_method', None)

        self.scalar = kwargs.pop('scalar', 1) or 1

        self.style = STYLE + (kwargs.pop('style', '') or '')

        self.padding = kwargs.pop('padding', 0) or 0

        self.clip = kwargs.pop('clip', True)

        self.log = logging.getLogger('svgis')
        self.log.info('Starting SVGIS with %s', self.files)

        self.simplifier = convert.simplifier(kwargs.pop('simplify', None))

        self.id_field = kwargs.pop('id_field', None)

        self.class_fields = kwargs.pop('class_fields', [])


    def __repr__(self):
        return ('SVGIS(files={0.files}, out_crs={0.out_crs})').format(self)

    def _get_clipper(self, layer_bounds, out_bounds, scalar=None):
        '''
        Get a clipping function for the given input crs and bounds.

        Args:
            layer_bounds (tuple): The bounds of the layer.
            out_bounds (tuple): The desired output bounds (in layer coordinates).
            scalar (float): Map scale.

        Returns:
            None if in_bounds == out_bounds or clipping is off.
        '''
        scalar = scalar or self.scalar
        if self.clip and not convert.bbox_covers(out_bounds, layer_bounds):
            return clip.prepare([c * scalar for c in convert.extend_bbox(self._projected_bounds)])

        else:
            return None

    def _reprojector(self, in_crs):
        '''Return a reprojection transform from in_crs to self.out_crs.'''
        if self.out_crs != in_crs:
            return partial(fiona.transform.transform_geom, in_crs, self.out_crs)

        else:
            return None

    def set_crs(self, layer_crs, bounds):
        '''Set the output CRS, if not yet set. Also update internal mbr.'''
        if not self.in_crs:
            self.in_crs = layer_crs

        if not self.out_crs:
            # Determine projection transformation:
            # either use something passed in, a non latlong layer projection,
            # the local UTM, or customize local TM
            self.out_crs = projection.choosecrs(layer_crs, bounds, proj_method=self.proj_method)

        projected = projection.transform_bounds(layer_crs, self.out_crs, bounds)
        self._projected_bounds = convert.updatebounds(self._projected_bounds, projected)

    def _compose_file(self, filename, scalar, unprojected_bounds=None, **kwargs):
        '''
        Draw fiona file to an SVG group.

        Args:
            filename (string): path to a fiona-readable file
            scalar (int): map scale
            unprojected_bounds (tuple): (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK.
                                        "Unprojected" here refers to the fact that we haven't transformed these bounds yet.
                                        They may well, in fact, be in a projection.
            simplifier (function): Simplification function. Defaults to self.simplify.
            class_fields (list): Fields to turn in the element classes (default: self.class_fields).
            id_field (string): Field to use as element ID (default: self.id_field).

        Returns:
            unicode
        '''
        self.log.info('Starting %s', filename)
        with fiona.open(filename, "r") as layer:
            bounds = unprojected_bounds or self._unprojected_bounds or layer.bounds

            # Set the output CRS, if not yet set. Also extend _projected_bounds.
            self.set_crs(layer.crs, bounds)

            transforms = [
                self._reprojector(layer.crs),
                partial(fionautil.scale.geometry, factor=scalar),
                # Get clipping function based on a slightly extended version of _projected_bounds.
                self._get_clipper(layer.bounds, bounds, scalar=scalar),
                kwargs.pop('simplifier', None)
            ]

            # Correct for OGR's lack of creativity for GeoJSONs.
            if layer.name == 'OGRGeoJSON':
                kwargs['_file_name'], _ = os.path.splitext(os.path.basename(filename))
            else:
                kwargs['_file_name'] = layer.name

            # A list of class names to get from layer properties.
            cf = kwargs.pop('class_fields', self.class_fields)
            classes = _get_classes(cf, layer.schema['properties'], kwargs['_file_name'])

            # Remove the id field if it doesn't appear in the properties.
            id_field = kwargs.pop('id_field', self.id_field)

            layer_classes = list(layer.schema['properties'].keys())
            kwargs['id_field'] = id_field if id_field in layer_classes else None

            group = [self._feature(f, transforms, classes, **kwargs) for _, f in layer.items(bbox=bounds)]

        gargs = {
            'id': kwargs['_file_name'],
            'class': ' '.join(_style.sanitize(c) for c in layer_classes)
        }
        self.log.info('Finishing %s', filename)
        return svg.group(group, **gargs)

    def _feature(self, feature, transforms, classes, id_field, **kwargs):
        '''
        Draw a single feature.

        Args:
            feature (dict): A GeoJSON like feature dict produced by Fiona.
            transforms (list): Functions to apply to the geometry.
            classes (list): Names of fields to apply as classes in the output element.
            id_field (string): Field to use as id of the output element.
            kwargs: Additional properties to apply to the element.
        '''
        # Produce the geometry.
        file_name = kwargs.pop('_file_name', '?')

        try:
            geom = feature.get('geometry')

            for t in [x for x in transforms if x is not None]:
                geom = t(geom)

        except ValueError as e:
            self.log.warn("Error drawing feature %s of %s: %s", file_name, feature.get('id', '?'), e)
            return u''

        # Set up the element's properties.
        kwargs['class'] = _construct_classes(classes, feature['properties'])

        if id_field:
            kwargs['id'] = _style.sanitize(feature['properties'].get(id_field))

        try:
            return draw.geometry(geom, **kwargs)

        except errors.SvgisError as e:
            self.log.warn("Error drawing %s: %s", file_name, e)
            return u''

    def compose(self, style=None, scalar=None, bounds=None, **kwargs):
        '''
        Draw files to svg.

        Args:
            scalar (int): factor by which to scale the data, generally a small number (1/map scale).
            style (string): CSS to append to parent object CSS
            bounds (list):/tuple Map bounding box in input units. Defaults to map data bounds.
            viewbox (bool): If True, draw SVG with a viewbox. If False, translate coordinates to the frame. Defaults to True.
            precision (float): Round coordinates to this precision [default: 0].
            simplify (float): Must be between 0 and 1. Fraction of removable coordinates to keep.
            inline (bool): If True, try to run CSS into each element.

        Returns:
            String (unicode in Python 2) containing an entire SVG document.
        '''
        # Set up arguments
        scalar = scalar or self.scalar
        style = self.style + (style or '')
        bounds = bounds or self._unprojected_bounds

        viewbox = kwargs.pop('viewbox', True)
        inline = kwargs.pop('inline', False)

        if 'simplify' in kwargs:
            kwargs['simplifier'] = convert.simplifier(kwargs.pop('simplify'))
        else:
            kwargs['simplifier'] = self.simplifier

        kwargs['precision'] = kwargs.get('precision', 0)

        groupargs = {
            'transform': 'scale(1, -1) translate({},{})'.format(self.padding, -self.padding),
            'fill_rule': 'evenodd'
        }
        svgargs = {
            'style': style
        }

        # Draw files
        with fiona.drivers():
            members = [self._compose_file(f, scalar, unprojected_bounds=bounds, **kwargs) for f in self.files]

        w, h, x0, y1 = self._dims(scalar, unprojected_bounds=bounds)

        if viewbox:
            svgargs['viewbox'] = (x0, -y1, w, h)
        else:
            groupargs['transform'] += ' translate({}, {})'.format(-x0, -y1)

        # Create container and then SVG
        container = svg.group(members, **groupargs)
        drawing = svg.drawing((w, h), [container], **svgargs)

        if inline:
            self.log.info('Inlining styles')
            return _style.inline(drawing, style)

        else:
            return drawing

    def _dims(self, scalar, unprojected_bounds=None):
        '''
        Calculate the width, height, origin X and max Y of the document.
        By default, uses self's minimum bounding rectangle.

        Args:
            scalar (int): Map scale
            bounds (Sequence): Optional bounds to calculate with (in output coordinates)
        '''
        if unprojected_bounds is None:
            bounds = self._projected_bounds
        else:
            bounds = projection.transform_bounds(self.in_crs, self.out_crs, unprojected_bounds)

        if any([convert.isinf(b) for b in bounds]):
            self.log.warn('Drawing has infinite bounds, consider changing projection or bounding box.')

        scalar = float(scalar)

        try:
            x0, y0, x1, y1 = [i * scalar for i in bounds]
            w = x1 - x0 + (self.padding * 2)
            h = y1 - y0 + (self.padding * 2)

            return w, h, x0, y1

        except ValueError:
            raise ValueError('Problem calculating bounds. Check that bounds are in minx, miny, maxx, maxy order.')
