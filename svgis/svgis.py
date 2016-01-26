# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>

import os.path
from collections import Iterable
from functools import partial
import logging
import fiona
import fiona.transform
import fionautil.scale
from . import convert, clip, css, draw, errors, projection, svg

"""
Draw geodata layers into svg
"""


STYLE = ('polyline, line, rect, path, polygon, .polygon {'
         ' fill: none;'
         ' stroke: #000;'
         ' stroke-width: 1px;'
         ' stroke-linejoin: round;'
         '}')


def map(layers, bounds=None, scale=1, padding=0, **kwargs):
    '''
    Draw a geodata layer to a simple SVG.
    :layers sequence Input geodata files.
    :output path Output file name
    :bounds sequence (minx, miny, maxx, maxy)
    :scale int Map scale. Larger numbers -> smaller maps
    :padding int Pad around bounds by this much. In projection units.
    :project string EPSG code, PROJ.4 string, or file containing a PROJ.4 string
    '''
    scale = (1 / scale) if scale else 1
    bounds = bounds if bounds and len(bounds) == 4 else None

    # Try to read style file
    styles = css.pick(kwargs.pop('style', None))

    use_proj, out_crs = projection.pick(kwargs.pop('project'))

    if kwargs.get('class_fields'):
        kwargs['classes'] = kwargs.pop('class_fields').split(',')

    kwargs.pop('class_fields', None)

    drawing = SVGIS(
        layers,
        bounds=bounds,
        scalar=scale,
        use_proj=use_proj,
        out_crs=out_crs,
        padding=padding,
        style=styles,
        clip=kwargs.pop('clip', True)
    ).compose(**kwargs)

    return drawing


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

    kwargs['class'] = _construct_classes(classes, properties)

    if id_field:
        kwargs['id'] = svg.sanitize(properties.get(id_field))

    return draw.geometry(geom, **kwargs)


class SVGIS(object):

    """Draw geodata files to SVG"""

    # pylint: disable=too-many-instance-attributes

    # bounds is the bounding box in input coordinates
    bounds = None

    # MBR is the bounding box in output coordinates, to be determined as we draw.
    mbr = (None, None, None, None)

    in_crs = None

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

        self.scalar = kwargs.pop('scalar', 1) or 1

        self.style = STYLE + (kwargs.pop('style', '') or '')

        self.padding = kwargs.pop('padding', 0) or 0

        self.clip = kwargs.pop('clip', True)

        self.log = logging.getLogger('svgis')

        self.simplifier = convert.simplifier(kwargs.pop('simplify', None))

    def __repr__(self):
        return ('SVGIS(files={0.files}, out_crs={0.out_crs})').format(self)

    def _get_clipper(self, in_crs, in_bounds, out_bounds, scalar=None):
        '''
        Get a clipping function for the given input crs and bounds.
        Returns None if in_bounds == out_bounds or clipping is off.
        '''
        scalar = scalar or self.scalar
        projected_mbr = projection.project_mbr(in_crs, self.out_crs, *out_bounds)
        self.mbr = convert.updatebounds(self.mbr, projected_mbr)

        if self.clip and out_bounds != in_bounds:
            return clip.prepare([c * scalar for c in convert.extend_bbox(projected_mbr)])

        else:
            return lambda x: x

    def _reprojector(self, in_crs):
        '''Return a reprojection transform from in_crs to self.out_crs.'''
        if self.out_crs != in_crs:
            return partial(fiona.transform.transform_geom, in_crs, self.out_crs)

        else:
            return lambda geom: geom

    def set_crs(self, crs, bounds):
        '''Set the output CRS, if not yet set.'''
        if not self.in_crs:
            self.in_crs = crs

        if not self.out_crs:
            # Determine projection transformation:
            # either use something passed in, a non latlong layer projection,
            # the local UTM, or customize local TM
            self.out_crs = projection.choosecrs(crs, bounds, use_proj=self.use_proj)

    def _compose_file(self, filename, scalar, bounds=None, **kwargs):
        '''
        Draw fiona file to string.
        :filename string path to a fiona-readable file
        :scalar int map scale
        :bounds tuple (minx, maxx, miny, maxy) in the layer's coordinate system. 'None' values are OK
        :simplifier function Simplification function. Defaults to self.simplify.
        :classes list Fields to turn in the element classes
        :id_field string Field to use as element ID
        '''
        with fiona.open(filename, "r") as layer:
            bounds = bounds or self.bounds or layer.bounds

            simplifier = kwargs.pop('simplifier', lambda x: x)

            # Set the output CRS, if not yet set.
            self.set_crs(layer.crs, bounds)

            # Get clipping function based on a slightly extended version of projected_mbr.
            clipper = self._get_clipper(layer.crs, layer.bounds, bounds, scalar=scalar)

            # feature reprojection function (could be no op).
            reproject = self._reprojector(layer.crs)

            # Correct for OGR's lack of creativity for GeoJSONs
            if layer.name == 'OGRGeoJSON':
                layer.name, _ = os.path.splitext(os.path.basename(filename))

            # A list of class names to get from layer properties.
            kwargs['classes'] = _get_classes(kwargs.get('classes', []), layer.schema['properties'], layer.name)

            # Remove the id field if it doesn't appear in the properties.
            if 'id_field' in kwargs:
                if kwargs['id_field'] not in list(layer.schema['properties'].keys()):
                    del kwargs['id_field']

            group = []
            for _, f in layer.items(bbox=bounds):
                # Project and scale
                try:
                    geom = fionautil.scale.geometry(reproject(f['geometry']), scalar)
                except ValueError as e:
                    self.log.error("Error drawing feature %s of %s: %s", filename, f.get('id'), e.message)
                    continue

                # clip to bounds
                geom = clipper(geom)

                # Simplify
                geom = simplifier(geom)

                try:
                    target = _draw_feature(geom, f['properties'], **kwargs)
                    group.append(target)

                except errors.SvgisError as e:
                    self.log.error("Error drawing %s: %s", filename, e.message)

        return svg.group(group, id=layer.name)

    def compose(self, style=None, scalar=None, bounds=None, **kwargs):
        '''
        Draw files to svg. Returns unicode.
        :scalar int factor by which to scale the data, generally a small number (1/map scale).
        :style string CSS to append to parent object CSS
        :bounds list/tuple Map bounding box in input units. Defaults to map data bounds.
        :viewbox bool If True, draw SVG with a viewbox. If False, translate coordinates to the frame. Defaults to True.
        :precision float Round coordinates to this precision [default: 0].
        :simplify float Must be between 0 and 1. Fraction of removable coordinates to keep.
        :inline_css bool If True, try to run CSS into each element.
        '''
        # Set up arguments
        scalar = scalar or self.scalar
        style = self.style + (style or '')
        bounds = bounds or self.bounds

        viewbox = kwargs.pop('viewbox', True)
        inline_css = kwargs.pop('inline_css', False)

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
            members = [self._compose_file(f, scalar, bounds=bounds, **kwargs) for f in self.files]

        w, h, x0, y1 = self._dims(scalar, bounds=bounds)

        if viewbox:
            svgargs['viewbox'] = (x0, -y1, w, h)
        else:
            groupargs['transform'] += ' translate({}, {})'.format(-x0, -y1)

        # Create container and then SVG
        container = svg.group(members, **groupargs)
        drawing = svg.drawing((w, h), [container], **svgargs)

        if inline_css:
            return css.inline(drawing, style)

        else:
            return drawing

    def _dims(self, scalar, bounds=None):
        '''
        Calculate the width, height, origin X and max Y of the document.
        By default, uses self's minimum bounding rectangle.
        :scalar int Map scale
        :bounds Sequence Optional bounds to calculate with (in output coordinates)
        '''
        if bounds is not None:
            bounds = projection.reproject_bounds(self.in_crs, self.out_crs, convert.bounds_to_ring(*bounds))
        else:
            bounds = self.mbr

        scalar = float(scalar)

        try:
            x0, y0, x1, y1 = [i * scalar for i in bounds]
            w = x1 - x0 + (self.padding * 2)
            h = y1 - y0 + (self.padding * 2)

            return w, h, x0, y1

        except ValueError:
            raise ValueError('Problem calculating bounds. Check that bounds are in minx, miny, maxx, maxy order.')
