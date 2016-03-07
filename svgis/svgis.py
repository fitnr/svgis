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
from .utils import isinf

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
    _unprojected_bounds = None

    # The crs of these bounds
    _unprojected_bounds_crs = None

    # The bounding box in output coordinates, to be determined as we draw.
    _projected_bounds = (None, None, None, None)

    in_crs = None

    simplifier = None

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
        self.log.info('starting SVGIS, files: %s', ', '.join(self.files))

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
            self.log.info('set up reprojection')
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

    def _project_bounds(self, in_crs, passed_bounds):
        '''Set projected bounds, but only once.'''
        if passed_bounds and not any(self._projected_bounds):
            self._projected_bounds = projection.transform_bounds(in_crs, self.out_crs, passed_bounds)
            self._unprojected_bounds_crs = in_crs

    def _extend_bounds(self, in_crs, layer_bounds):
        '''Extend projected bounds, used when calculating bounds as we go.'''
        projected = projection.transform_bounds(in_crs, self.out_crs, layer_bounds)
        self._projected_bounds = convert.updatebounds(self._projected_bounds, projected)

    def _get_local_projected_bounds(self, layer_crs):
        '''Get the projected bounds in local terms.'''
        if layer_crs != self._unprojected_bounds_crs:
            return projection.transform_bounds(self.out_crs, layer_crs, self._projected_bounds)

    def _prepare_layer(self, layer, filename, bounds, scalar, **kwargs):
        '''
        Prepare the keyword args for draing a layer
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
            result['layer'] = os.path.splitext(os.path.basename(filename))[0]
        else:
            result['layer'] = layer.name

        # A list of class names to get from layer properties.
        class_fields = kwargs.pop('class_fields', None) or self.class_fields
        result['classes'] = [x for x in class_fields if x in layer.schema['properties']]

        # Add the layer name to the class list.
        result['classes'].insert(0, result['layer'])

        # Remove the id field if it doesn't appear in the properties.
        id_field = kwargs.pop('id_field', self.id_field)

        result['id_field'] = id_field if id_field in layer.schema['properties'].keys() else None

        result.update(kwargs)

        return result

    def _compose_file(self, filename, unprojected_bounds=None, **kwargs):
        '''
        Draw fiona file to an SVG group.

        Args:
            filename (string): path to a fiona-readable file
            unprojected_bounds (tuple): (minx, maxx, miny, maxy) in the layer's coordinate system.
                                        'None' values are OK. "Unprojected" here refers to
                                        the fact that we haven't transformed these bounds yet.
                                        They may well, in fact, be in a projection.
            scalar (int): map scale
            simplifier (function): Simplification function. Defaults to self.simplify.
            class_fields (sequence): Fields to turn in the element classes (default: self.class_fields).
            id_field (string): Field to use as element ID (default: self.id_field).

        Returns:
            unicode
        '''
        self.log.info('starting %s', filename)
        with fiona.open(filename, "r") as layer:

            bounds = unprojected_bounds or self._unprojected_bounds or layer.bounds

            # Set the output CRS, if not yet set.
            self.set_crs(layer.crs, bounds)

            if unprojected_bounds or self._unprojected_bounds:
                # Use the passed bounds, if they exist.
                # This sets self._projected_bounds, and prevents it from being altered
                self._project_bounds(layer.crs, unprojected_bounds)
                # Get the bounds to use here from the projected bounds.
                # If None, the unprojected bounds are our best bet.
                bounds = (
                            self._get_local_projected_bounds(layer.crs) or
                            unprojected_bounds or
                            self._unprojected_bounds
                         )

            else:
                # Using bounds from all the input layers.
                # self._projected_bounds will continue to be updated.
                self._extend_bounds(layer.crs, bounds)

            kwargs = self._prepare_layer(layer, filename, bounds, **kwargs)
            group = tuple(self._feature(f, **kwargs) for _, f in layer.items(bbox=bounds))

        return {
            'members': group,
            'id': kwargs['layer'],
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

        Returns:
            unicode
        '''
        layer = kwargs.pop('layer', '?')

        # Set up the element's properties.
        kwargs['class'] = _style.construct_classes(classes, feature['properties'])

        if id_field:
            kwargs['id'] = _style.sanitize(feature['properties'].get(id_field))

        try:
            geom = feature['geometry']

            # Apply transformations to the geometry.
            for t in transforms:
                if t is not None:
                    geom = t(geom)

            return draw.geometry(geom, **kwargs)

        except KeyError as e:
            self.log.warning("no geometry found for feature %s of %s: %s",
                             kwargs.get('id', feature.get('id', '?')), layer, e)
            return u''

        except ValueError as e:
            self.log.warning("error transforming feature %s of %s: %s",
                             kwargs.get('id', feature.get('id', '?')), layer, e)
            return u''

        except errors.SvgisError as e:
            self.log.warning("error drawing feature  %s of %s: %s",
                             kwargs.get('id', feature.get('id', '?')), layer, e)
            return u''

    def compose(self, scalar=None, bounds=None, **kwargs):
        '''
        Draw files to svg.

        Args:
            scalar (int): factor by which to scale the data, generally a small number (1/map scale).
            bounds (Sequence): Map bounding box in input units. Defaults to map data bounds.
            style (str): CSS to append to parent object CSS.
            viewbox (bool): If True, draw SVG with a viewbox. If False, translate coordinates to the frame.
                            Defaults to True.
            precision (float): Round coordinates to this precision [default: 0].
            simplify (float): Must be between 0 and 1. Fraction of removable coordinates to keep.
            inline (bool): If False, do not add CSS style attributes to each element.

        Returns:
            String (unicode in Python 2) containing an entire SVG document.
        '''
        # Set up arguments
        scalar = scalar or self.scalar

        drgs = {
            'style': kwargs.pop('style', ''),
            'viewbox': kwargs.pop('viewbox', True),
            'inline': kwargs.pop('inline', True),
        }

        if bounds:
            reset_bounds = True
        else:
            reset_bounds = False
            bounds = self._unprojected_bounds

        if 'simplify' in kwargs:
            self.log.info('setting up simplifier with factor: %s', kwargs['simplify'])
            kwargs['simplifier'] = convert.simplifier(kwargs.pop('simplify'))
        else:
            kwargs['simplifier'] = self.simplifier

        kwargs['precision'] = drgs['precision'] = kwargs.get('precision', 0)

        # Draw files
        with fiona.drivers():
            members = [svg.group(**self._compose_file(f, bounds, scalar=scalar, **kwargs))
                       for f in self.files]

        self.log.info('composing drawing')
        drawing = self._draw(members, bounds, scalar, **drgs)

        # Reset bounds so that self can be used again fresh. This is hacky.
        if reset_bounds:
            self._projected_bounds = (None, None, None, None)

        return drawing

    def _draw(self, members, bounds, scalar, **kwargs):
        '''
        Combine drawn layers into an SVG drawing.

        Args:
            members (list): unicode representations of SVG groups.
            bounds (Sequence): Map bounding box in input units. If None, uses map data bounds.
            scalar (int): factor by which to scale the data, generally a small number (1/map scale).
            style (str): CSS to append to parent object CSS.
            viewbox (bool): If True, draw SVG with a viewbox. If False, translate coordinates to
                            the frame. Defaults to True.
            inline (bool): If True, try to run CSS into each element.

        Returns:
            String (unicode in Python 2) containing an entire SVG document.
        '''
        groupargs = {
            'transform': 'scale(1, -1) translate({},{})'.format(self.padding, -self.padding),
            'fill_rule': 'evenodd'
        }

        svgargs = {
            'precision': kwargs.pop('precision', 0),
            'style': self.style + (kwargs.pop('style', '') or '')
        }

        x0, y0, x1, y1 = self._corners(scalar, unprojected_bounds=bounds)

        # width and height
        size = [
            x1 - x0 + (self.padding * 2),
            y1 - y0 + (self.padding * 2)
        ]

        if kwargs.pop('viewbox', True):
            svgargs['viewbox'] = [x0, -y1] + size
        else:
            groupargs['transform'] += ' translate({}, {})'.format(-x0, -y1)

        # Create container and then SVG
        container = svg.group(members, **groupargs)
        drawing = svg.drawing(size, [container], **svgargs)

        if kwargs.pop('inline', False):
            self.log.info('inlining styles')
            drawing = _style.inline(drawing, svgargs['style'])

        return drawing

    def _corners(self, scalar, unprojected_bounds=None):
        '''
        Calculate the bounds in svg coordinates.
        By default, uses self's minimum bounding rectangle.

        Args:
            scalar (int): Map scale
            bounds (Sequence): Optional bounds to calculate with (in output coordinates)

        Returns:
            tuple representing minx, miny, maxx, maxy in output coordinates
        '''
        if unprojected_bounds is None:
            bounds = self._projected_bounds
        else:
            bounds = projection.transform_bounds(self.in_crs, self.out_crs, unprojected_bounds)

        if any([isinf(b) for b in bounds]):
            self.log.warning('Drawing has infinite bounds, consider changing projection or bounding box.')

        bounds = tuple(b or 0.0 for b in bounds)

        try:
            return [i * float(scalar) for i in bounds]

        except ValueError:
            raise ValueError('Problem calculating drawing dimensions. '
                             'Are bounds are in minx, miny, maxx, maxy order?')
