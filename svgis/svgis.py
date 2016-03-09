# -*- coding: utf-8 -*-

"""Draw SVG maps"""

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
from . import bounding, draw, errors, projection, svg, transform
from . import style as _style
from .utils import isinf


STYLE = ('polyline,line,rect,path,polygon,.polygon{'
         'fill:none;'
         'stroke:#000;'
         'stroke-width:1px;'
         'stroke-linejoin:round;'
         '}')

# WGS 84
DEFAULT_PROJECTION = {'init': 'epsg:4269', 'no_defs': True, 'proj': 'longlat'}


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
        style (Sequence): Path to a css file or a css string.
        class_fields (Sequence): A comma-separated string or list of class names to
                                 use the SVG drawing.
        id_field (string): Field to use to determine id of each element in the drawing.
        inline (bool): If False, do not move CSS declarations into each element.

    Returns:
        String (unicode in Python 2) containing an entire SVG document.
    '''
    scale = (1 / scale) if scale else 1
    bounds = bounds if bounds and len(bounds) == 4 else None

    # Try to read style file(s)
    styles = u''.join(_style.pick(s) for s in kwargs.pop('style', []))

    proj_method, out_crs = projection.pick(kwargs.pop('crs', None))

    class_fields = set(a for c in kwargs.pop('class_fields', []) for a in c.split(','))

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
        class_fields=class_fields,
        simplify=kwargs.pop('simplify', None)
    ).compose(**kwargs)

    return drawing


class SVGIS(object):

    """
    Draw geodata files to SVG.

    Args:
        files (list): A list of files to draw.
        bounds (Sequence): An iterable with four float coordinates in (minx, miny, maxx, maxy) format
        out_crs (dict): A proj-4 like mapping. Overrides proj_method.
        proj_method (string): A keyword for picking a projection (file, utm or local).
        style (string): CSS to add to output file
        scalar (int): Map scale to use (output coordinate are divided by this)
        padding (number): Buffer each edge by this many map units

    """

    # The bounding box in input coordinates.
    _unprojected_bounds = (None,) * 4

    # The bounding box in output coordinates, to be determined as we draw.
    _projected_bounds = (None,) * 4

    _in_crs, _out_crs = None, None

    clipper = None
    simplifier = None

    def __init__(self, files, bounds=None, out_crs=None, **kwargs):
        self.log = logging.getLogger('svgis')

        if isinstance(files, basestring):
            self.files = [files]
        elif isinstance(files, Iterable):
            self.files = files
        else:
            raise ValueError("'files' must be a file name or list of file names")

        self.log.info('starting SVGIS, files: %s', ', '.join(self.files))

        if bounding.check(bounds):
            self._unprojected_bounds = bounds
        elif bounds:
            self.log.warn("ignoring invalid bounds: %s", bounds)

        self._out_crs = out_crs

        self.proj_method = kwargs.pop('proj_method', None)

        self.scalar = kwargs.pop('scalar', 1) or 1

        self.style = STYLE + (kwargs.pop('style', '') or '')

        self.padding = kwargs.pop('padding', 0) or 0

        self.precision = kwargs.pop('precision', None)

        self.clip = kwargs.pop('clip', True)

        self.simplifier = transform.simplifier(kwargs.pop('simplify', None))

        self.id_field = kwargs.pop('id_field', None)

        self.class_fields = kwargs.pop('class_fields', [])

    def __repr__(self):
        return ('SVGIS(files={0.files}, out_crs={0.out_crs})').format(self)

    @property
    def in_crs(self):
        return self._in_crs

    def set_in_crs(self, crs):
        if not self.in_crs and crs:
            self._in_crs = crs

        if not crs:
            # Assume input CRS is WGS 84
            self._in_crs = DEFAULT_PROJECTION
            self.log.warn('Found no input coordinate system, '
                          'assuming WGS84 (long/lat) coordinates.')

    @property
    def out_crs(self):
        return self._out_crs

    def set_out_crs(self, bounds, method):
        '''Set the output CRS, if not yet set.'''
        if self.out_crs:
            return

        # Determine projection transformation:
        # either use something passed in, a non latlong layer projection,
        # the local UTM, or customize local TM
        self._out_crs = projection.choosecrs(self.in_crs, bounds, proj_method=method)

    @property
    def unprojected_bounds(self):
        '''Returns None if projected bounds aren't set'''
        if not all(self._unprojected_bounds):
            return None
        return self._unprojected_bounds

    @property
    def projected_bounds(self):
        '''Returns None if projected bounds aren't (yet) set'''
        if not all(self._projected_bounds):
            return None
        return self._projected_bounds

    def update_projected_bounds(self, in_crs, out_crs, bounds, padding=None):
        '''
        Extend projected_bounds bbox with self.padding.

        Args:
            in_crs (dict): CRS of bounds.
            out_crs (dict) desired output CRS.
            bounds (tuple): bounding box.

        Returns:
            (tuple) bounding box in out_crs coordinates.
        '''
        # This may happen many times if we were passed bounds, but it's a cheap operation.
        projected = bounding.transform(in_crs, out_crs, bounds)
        self._projected_bounds = bounding.pad(projected, padding or 0)
        return self._projected_bounds

    def _get_clipper(self, layer_bounds, out_bounds, scalar=None):
        '''
        Get a clipping function for the given input crs and bounds.

        Args:
            layer_bounds (tuple): The bounds of the layer.
            out_bounds (tuple): The desired output bounds (in layer coordinates).
            scalar (float): Map scale.

        Returns:
            None if layer_bounds are inside out_bounds or clipping is off.
        '''
        if not self.clip or bounding.covers(out_bounds, layer_bounds):
            return None

        scalar = scalar or self.scalar

        if not self.clipper:
            padded_bounds = bounding.pad(self.projected_bounds, 1000)
            self.clipper = transform.clipper([c * scalar for c in padded_bounds])

        return self.clipper

    def _reprojector(self, in_crs):
        '''Return a reprojection transform from in_crs to self.out_crs.'''
        if self.out_crs != in_crs:
            self.log.info('set up reprojection')
            self.log.debug('projecting from: %s', in_crs)
            self.log.debug('projecting to: %s', self.out_crs)
            return partial(fiona.transform.transform_geom, in_crs, self.out_crs)

        else:
            return None

    def _prepare_layer(self, layer, filename, bounds, scalar, **kwargs):
        '''
        Prepare the keyword args for drawing a layer.

        Args:
            layer (fiona.layer): input layer
            filename (str): Name of file, used for group id attribute.
            bounds (tuple): Bounding box (in layer.crs).
            scalar (int): Map scale
            simplifier (function): simplication function
            id_field (str): Field to use for element id attribute.
            class_fields (list): Fields to use for element class attribute.

        Returns:
            (dict) Arguments for self._feature
        '''
        result = {
            'transforms': [
                self._reprojector(layer.crs),
                partial(fionautil.scale.geometry, factor=scalar),
                # Get clipping function based on a slightly extended version of _projected_bounds.
                self._get_clipper(layer.bounds, bounds, scalar=scalar),
                kwargs.pop('simplifier', None)
            ]
        }

        # Correct for OGR's lack of creativity for GeoJSONs.
        if layer.name == 'OGRGeoJSON':
            result['name'] = os.path.splitext(os.path.basename(filename))[0]
        else:
            result['name'] = layer.name

        # A list of class names to get from layer properties.
        class_fields = kwargs.pop('class_fields', None) or self.class_fields
        result['classes'] = [x for x in class_fields if x in layer.schema['properties']]

        # Remove the id field if it doesn't appear in the properties.
        id_field = kwargs.pop('id_field', self.id_field)

        result['id_field'] = id_field if id_field in layer.schema['properties'].keys() else None

        result.update(kwargs)

        return result

    def _compose_file(self, filename, unprojected_bounds=None, padding=None, **kwargs):
        '''
        Draw fiona file to an SVG group.

        Args:
            filename (string): path to a fiona-readable file
            unprojected_bounds (tuple): (minx, maxx, miny, maxy) in the layer's coordinate system.
                                        'None' values are OK. "Unprojected" here refers to
                                        the fact that we haven't transformed these bounds yet.
                                        They may well, in fact, be in a projection.
            padding (int): Number of map units by which to pad output bounds.
            scalar (int): map scale
            simplifier (function): Simplification function. Defaults to self.simplify.
            class_fields (sequence): Fields to turn in the element classes (default: self.class_fields).
            id_field (string): Field to use as element ID (default: self.id_field).

        Returns:
            unicode
        '''
        self.log.info('starting %s', filename)

        padding = padding or self.padding

        with fiona.open(filename, "r") as layer:
            # Set the input CRS, if not yet set.
            self.set_in_crs(layer.crs)

            # When we have passed bounds:
            if unprojected_bounds:
                # Set the output CRS, if not yet set, using unprojected bounds.
                self.set_out_crs(unprojected_bounds, method=self.proj_method)

                # If we haven't set the projected bounds yet, do that.
                if not self.projected_bounds:
                    self.update_projected_bounds(self.in_crs, self.out_crs, unprojected_bounds, padding)

                # Convert global bounds to layer.crs.
                bounds = bounding.transform(self.out_crs, layer.crs, self.projected_bounds)

            # When we have no passed bounds:
            else:
                # Set the output CRS, if not yet set, using this layer's bounds.
                self.set_out_crs(layer.bounds, method=self.proj_method)

                # Extend projection_bounds
                self.update_projected_bounds(layer.crs, self.out_crs, layer.bounds, padding)
                bounds = layer.bounds

            kwargs = self._prepare_layer(layer, filename, bounds, **kwargs)
            group = tuple(self._feature(f, **kwargs) for _, f in layer.items(bbox=bounds))

        return {
            'members': group,
            'id': kwargs['name'],
            'class': u' '.join(_style.sanitize(c) for c in layer.schema['properties'].keys())
        }

    def _feature(self, feature, transforms, classes, id_field=None, **kwargs):
        '''
        Draw a single feature.

        Args:
            feature (dict): A GeoJSON like feature dict produced by Fiona.
            transforms (list): Functions to apply to the geometry.
            classes (list): Names (unsanitized) of fields to apply as classes in the output element.
            id_field (str): Field to use as id of the output element.
            kwargs: Additional properties to apply to the element.
            name (str): layer name (usually basename of the input file).

        Returns:
            unicode
        '''
        name = kwargs.pop('name', '?')

        # Set up the element's properties.
        classes = _style.construct_classes(classes, feature['properties'])
        # Add the layer name to the class list.
        if name != '?':
            classes.insert(0, _style.sanitize(name))
        kwargs['class'] = ' '.join(classes)

        if id_field:
            kwargs['id'] = _style.sanitize(feature['properties'].get(id_field))

        try:
            geom = feature['geometry']

            # Check if geometry exists (a bit unpythonic, but cleaner errs this way).
            if geom is None:
                raise KeyError('NULL geometry')

            # Apply transformations to the geometry.
            for t in transforms:
                if t is not None:
                    geom = t(geom)

        except KeyError as e:
            self.log.warning('no geometry found for feature %s of %s: %s',
                             kwargs.get('id', feature.get('id', '?')), name, e)
            return u''

        except ValueError as e:
            self.log.warning('error transforming feature %s of %s: %s',
                             kwargs.get('id', feature.get('id', '?')), name, e)
            return u''

        try:
            # Draw the geometry.
            return draw.geometry(geom, **kwargs)

        except (TypeError, errors.SvgisError) as e:
            self.log.warning('unable to draw feature %s of %s: %s',
                             kwargs.get('id', feature.get('id', '?')), name, e)
            return u''

    def compose(self, scalar=None, bounds=None, **kwargs):
        '''
        Draw files to svg.

        Args:
            scalar (int): factor by which to scale the data, generally a small number (1/map scale).
            bounds (Sequence): Map bounding box in WGS84 (longlat) coordinates.
                               Defaults to map data bounds.
            style (str): CSS to append to parent object CSS.
            padding (int): Number of (projected) units to pad bounds by.
            viewbox (bool): If True, draw SVG with a viewbox. If False, translate coordinates
                            to the frame. Defaults to True.
            precision (float): Round coordinates to this precision [default: 0].
            simplify (float): Must be between 0 and 1. Fraction of removable coordinates to keep.
            inline (bool): If False, do not add CSS style attributes to each element.

        Returns:
            String (unicode in Python 2) containing an entire SVG document.
        '''
        # Set up arguments
        scalar = scalar or self.scalar
        unprojected_bounds = bounding.check(bounds) or self.unprojected_bounds

        drgs = {
            'style': kwargs.pop('style', ''),
            'viewbox': kwargs.pop('viewbox', True),
            'inline': kwargs.pop('inline', True),
        }

        if 'simplify' in kwargs:
            self.log.info('setting up simplifier with factor: %s', kwargs['simplify'])
            kwargs['simplifier'] = transform.simplifier(kwargs.pop('simplify'))
        else:
            kwargs['simplifier'] = self.simplifier

        kwargs['precision'] = drgs['precision'] = kwargs.get('precision', self.precision)

        # Draw files
        with fiona.drivers():
            members = [svg.group(**self._compose_file(f, unprojected_bounds, scalar=scalar, **kwargs))
                       for f in self.files]

        self.log.info('composing drawing')
        drawing = self._draw(members, scalar, **drgs)

        # Always reset projected bounds
        self._projected_bounds = (None,) * 4

        return drawing

    def _draw(self, members, scalar, **kwargs):
        '''
        Combine drawn layers into an SVG drawing.

        Args:
            members (list): unicode representations of SVG groups.
            scalar (int): factor by which to scale the data, generally a small number (1/map scale).
            style (str): CSS to append to parent object CSS.
            viewbox (bool): If True, draw SVG with a viewbox. If False, translate coordinates to
                            the frame. Defaults to True.
            inline (bool): If True, try to run CSS into each element.

        Returns:
            String (unicode in Python 2) containing an entire SVG document.
        '''
        transform_attrib = 'scale(1,-1)'

        svgargs = {
            'precision': kwargs.pop('precision', 0),
            'style': self.style + (kwargs.pop('style', '') or '')
        }

        if any([isinf(b) for b in self._projected_bounds]):
            self.log.warning('Drawing has infinite bounds, consider changing projection or bounding box.')

        x0, y0, x1, y1 = [float(b or 0.) * scalar for b in self.projected_bounds]

        # width and height
        size = [x1 - x0, y1 - y0]

        if kwargs.pop('viewbox', True):
            svgargs['viewbox'] = [x0, -y1] + size
            self.log.debug('drawing with viewbox')
        else:
            transform_attrib += ' translate({},{})'.format(-x0, -y1)
            self.log.debug('translating contents to fit')

        # Create container and then SVG
        container = svg.group(members, fill_rule='evenodd', transform=transform_attrib)
        drawing = svg.drawing(size, [container], **svgargs)

        if kwargs.pop('inline', False):
            self.log.info('inlining styles')
            drawing = _style.inline(drawing, svgargs['style'])

        return drawing
