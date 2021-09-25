# -*- coding: utf-8 -*-
"""Draw SVG maps"""
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, 2020, Neil Freeman <contact@fakeisthenewreal.org>
import logging
import os.path
import warnings
from collections.abc import Iterable
from functools import partial

import fiona
import fiona.transform
from pyproj.crs import CRS
from six import string_types

from . import bounding, draw, projection
from . import style as _style
from . import svg, transform, utils
from .errors import SvgisError

STYLE = (
    'polyline,line,rect,path,polygon,.polygon{'
    'fill:none;'
    'stroke:#000;'
    'stroke-width:1px;'
    'stroke-linejoin:round;'
    '}'
)


warnings.filterwarnings("ignore")


def map(layers, bounds=None, scale=None, **kwargs):
    """
    Draw a geodata layer to SVG. This is shorthand for creating a :class:`SVGIS` instance
    and immediately runnning :class:`SVGIS.compose`.

    Args:
        layers (sequence): Input geodata files.
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
        precision (int): Precision for rounding output coordinates.
        simplify (int): Integer between 1 and 99 describing simplification level.
                99: not very much. 1: a lot.

    Returns:
        ``str`` containing an entire SVG document.
    """
    # pylint: disable=redefined-builtin
    scale = (1.0 / scale) if scale else 1.0
    bounds = bounding.check(bounds)

    # Try to read style file(s)
    styles = ''.join(_style.pick(s) for s in kwargs.pop('style', []))

    class_fields = set(a for c in kwargs.pop('class_fields', []) for a in c.split(','))
    data_fields = set(a for c in kwargs.pop('data_fields', []) for a in c.split(','))

    drawing = SVGIS(
        layers,
        bounds=bounds,
        scalar=scale,
        crs=kwargs.pop('crs', None),
        style=styles,
        clip=kwargs.pop('clip', True),
        id_field=kwargs.pop('id_field', None),
        class_fields=class_fields,
        data_fields=data_fields,
        simplify=kwargs.pop('simplify', None),
    ).compose(**kwargs)

    return drawing


class SVGIS:

    """
    Draw geodata files to SVG.

    Args:
        files (list): A list of files to draw.
        bounds (Sequence): An iterable with four float coordinates in (minx, miny, maxx, maxy) format
        crs (dict): A proj-4 like mapping, or a projection method keyword (file, local, utm).
        style (string): CSS to add to output file
        scalar (int): Map scaling factor (output coordinate are multiplied by this)
        style (str): CSS styles
        padding (number): Buffer each edge by this many map units.
        precision (int): Precision for rounding output coordinates.
        simplify (int): Simplification factor (between 1 and 100).
        id_field (str): Field in data to use for ID'ing elements.
        class_fields (Sequence): Fields in data for added classes to elements.
    """

    # The bounding box in input coordinates.
    _unprojected_bounds = None

    # The bounding box in output coordinates, to be determined as we draw.
    _projected_bounds = None

    _in_crs, _out_crs = None, None

    clipper = None
    simplifier = None

    def __init__(self, files, bounds=None, crs=None, **kwargs):
        self.log = logging.getLogger('svgis')

        if isinstance(files, string_types):
            self.files = [files]
        elif isinstance(files, Iterable):
            self.files = files
        else:
            raise SvgisError("'files' must be a file name or list of file names")

        self.log.info('starting SVGIS, files: %s', ', '.join(self.files))

        if bounding.check(bounds):
            self._unprojected_bounds = bounds
        elif bounds:
            self.log.warning("ignoring invalid bounds: %s", bounds)

        # This may return a keyword, which will require more updating.
        # If so, will update when files are open.
        self._out_crs = kwargs.get('out_crs', crs)
        self.log.debug('picked tentative output projection or method: %s', self._out_crs)

        self.scalar = kwargs.pop('scalar', 1) or 1

        self.style = STYLE + (kwargs.pop('style', '') or '')

        self.padding = kwargs.pop('padding', 0) or 0

        self.precision = kwargs.pop('precision', None)

        self.clip = kwargs.pop('clip', True)

        simple = kwargs.pop('simplify', None)

        if simple:
            self.simplifier = transform.simplifier(simple)
            self.log.debug('Simplifying with a factor of %d', simple)

        self.id_field = kwargs.pop('id_field', None)

        self.class_fields = kwargs.pop('class_fields', [])
        self.data_fields = kwargs.pop('data_fields', [])

    def __repr__(self):
        return f'SVGIS(files={self.files}, out_crs={self.out_crs})'

    @property
    def in_crs(self):
        """Return the CRS being used for input geodata."""
        return self._in_crs

    def set_in_crs(self, crs):
        """
        Set the CRS to use for input geodata, falling back on the default (WGS84).
        """
        if not self.in_crs:
            if crs:
                self.log.debug('setting input crs to %s', crs)
                self._in_crs = projection.pick(crs)
                return

            # Assume input CRS is WGS 84
            self._in_crs = projection.pick(utils.DEFAULT_GEOID)
            self.log.debug('set_in_crs: setting input crs to default %s', self._in_crs)
            self.log.warning('set_in_crs: Found no input coordinate system, ' 'assuming WGS84 (long/lat) coordinates.')

    @property
    def out_crs(self):
        """The output CRS of this drawing"""
        if isinstance(self._out_crs, CRS):
            return self._out_crs
        return None

    def set_out_crs(self, bounds):
        '''Set the output CRS, if not yet set.'''
        if self.out_crs:
            return

        # Determine projection transformation:
        # either use something passed in, a non latlong layer projection,
        # the local UTM, or customize local TM
        self.log.debug('set_out_crs:  out crs: %s', self._out_crs)
        self.log.debug('set_out_crs:  in crs: %s', self.in_crs)
        self.log.debug('set_out_crs:  bounds: %s', bounds)
        self._out_crs = projection.pick(self._out_crs, bounds, self.in_crs)
        self.log.debug('set_out_crs: Set output crs to %s', self.out_crs)

    @property
    def unprojected_bounds(self):
        '''Returns None if projected bounds aren't set'''
        if self._unprojected_bounds:
            return self._unprojected_bounds
        return None

    @property
    def projected_bounds(self):
        '''Returns None if projected bounds aren't (yet) set'''
        if self._projected_bounds:
            return self._projected_bounds
        return None

    def update_projected_bounds(self, in_crs, out_crs, bounds, padding=None):
        """
        Extend projected_bounds bbox with self.padding.

        Args:
            in_crs (dict): CRS of bounds.
            out_crs (dict) desired output CRS.
            bounds (tuple): bounding box.

        Returns:
            ``tuple`` bounding box in out_crs coordinates.
        """
        # This may happen many times if we were passed bounds, but it's a cheap operation.
        self.log.debug('update_projected_bounds:  in_crs: %s', in_crs)
        self.log.debug('update_projected_bounds:  out_crs: %s', out_crs)
        projected = bounding.transform(bounds, in_crs=in_crs, out_crs=out_crs)
        self._projected_bounds = bounding.pad(projected, padding or 0)
        self.log.debug('update_projected_bounds:  new bounds: %s', self._projected_bounds)
        return self._projected_bounds

    def _get_clipper(self, layer_bounds, out_bounds, scalar=None):
        """
        Get a clipping function for the given input crs and bounds.

        Args:
            layer_bounds (tuple): The bounds of the layer.
            out_bounds (tuple): The desired output bounds (in layer coordinates).
            scalar (float): Map scale.

        Returns:
            ``None`` if layer_bounds are inside out_bounds or clipping is off.
        """
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
            self.log.debug('  input crs: %s', in_crs)
            self.log.debug('  output crs: %s', self.out_crs)
            return partial(fiona.transform.transform_geom, in_crs, self.out_crs.to_dict())

        return None

    def _prepare_layer(self, layer, filename, bounds, scalar, **kwargs):
        """
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
            ``dict`` Arguments for ``self._feature``
        """
        result = {
            'transforms': [
                self._reprojector(layer.crs),
                partial(transform.scale_geom, factor=scalar),
                # Get clipping function based on a slightly extended version of _projected_bounds.
                self._get_clipper(layer.bounds, bounds, scalar=scalar),
                self.simplifier,
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
        data_fields = kwargs.pop('data_fields', None) or self.data_fields
        result['datas'] = [x for x in data_fields if x in layer.schema['properties']]

        # Remove the id field if it doesn't appear in the properties.
        id_field = kwargs.pop('id_field', self.id_field)

        result['id_field'] = id_field if id_field in layer.schema['properties'].keys() else None

        result.update(kwargs)

        return result

    def compose_file(self, path, unprojected_bounds=None, **kwargs):
        """
        Draw fiona file to an SVG group.

        Args:
            path (string): path to a fiona-readable file, or an Apache Commons VFS spec for a zip
                           or tar archive, e.g. ``zip://path/to/archive.zip/file.shp``.
            unprojected_bounds (tuple): (minx, maxx, miny, maxy) in the layer's coordinate system.
                                        'None' values are OK. "Unprojected" here refers to
                                        the fact that we haven't transformed these bounds yet.
                                        They may well, in fact, be in a projection.
            padding (int): Number of map units by which to pad output bounds.
            scalar (int): map scale
            class_fields (sequence): Fields to turn in the element classes (default: self.class_fields).
            id_field (string): Field to use as element ID (default: self.id_field).

        Returns:
            A ``dict`` with the keys: ``members``, ``id``, ``class``.
            This is ready to be passed to ``svgis.svg.group``.
        """
        padding = kwargs.pop('padding', self.padding)
        kwargs['scalar'] = kwargs.get('scalar', self.scalar)
        unprojected_bounds = unprojected_bounds or self.unprojected_bounds
        with fiona.Env():
            self.log.debug('opening %s', path)
            with fiona.open(path) as layer:
                self.log.info('reading %s', layer.name)

                # Set the input CRS, if not yet set.
                self.set_in_crs(layer.crs)

                # When we have passed bounds:
                if unprojected_bounds:
                    self.log.debug("Set the output CRS, if not yet set, using unprojected bounds: %s", unprojected_bounds)
                    self.set_out_crs(unprojected_bounds)

                    # If we haven't set the projected bounds yet, do that.
                    if not self.projected_bounds:
                        self.update_projected_bounds(self.in_crs, self.out_crs, unprojected_bounds, padding)

                    self.log.debug(
                        'Getting projected bounds %s (%s) in layer crs (%s)',
                        self.projected_bounds,
                        self.out_crs,
                        layer.crs,
                    )
                    bounds = bounding.transform(self.projected_bounds, in_crs=self.out_crs, out_crs=layer.crs)

                # When we have no passed bounds:
                else:
                    self.log.debug("Set the output CRS, if not yet set, using this layer's bounds.")
                    self.set_out_crs(layer.bounds)

                    # Extend projection_bounds
                    self.update_projected_bounds(layer.crs, self.out_crs, layer.bounds, padding)
                    bounds = layer.bounds

                kwargs = self._prepare_layer(layer, path, bounds, **kwargs)
                group = tuple(self.feature(f, **kwargs) for _, f in layer.items(bbox=bounds))

        return {
            'members': group,
            'id': kwargs['name'],
            'class': ' '.join(_style.sanitize(c) for c in layer.schema['properties'].keys()),
        }

    def feature(self, feature, transforms, classes, datas=None, **kwargs):
        """
        Draw a single feature.

        Args:
            feature (dict): A GeoJSON like feature dict produced by Fiona.
            transforms (list): Functions to apply to the geometry.
            classes (list): Names (unsanitized) of fields to apply as classes in the output element.
            datas (dict): key-value pairs to add as data-KEY="value" elements in the output element.
            precision (int): rounding precision for coordinates.
            id_field (str): Field to use as id of the output element.
            name (str): layer name (usually basename of the input file).

        Returns:
            ``str``
        """
        name = kwargs.pop('name', None)
        geom = feature.get('geometry')
        precision = kwargs.pop('precision', self.precision)
        datas = datas or {}
        fid = feature['properties'].get(kwargs.get('id_field'), feature.get('id', '?'))

        try:
            # Check if geometry exists (a bit unpythonic, but cleaner errs this way).
            if geom is None:
                raise SvgisError('NULL geometry')

            # Apply transformations to the geometry.
            for t in transforms:
                geom = t(geom) if t is not None else geom

            if geom['coordinates'] is None or len(geom['coordinates']) == 0:
                self.log.debug(
                    'Skipping feature with empty geometry after transformation: "%s" in layer "%s"', fid, name or '?'
                )
                return ''

        except SvgisError as e:
            self.log.warning(
                'error transforming feature %s of %s: %s', kwargs.get('id', feature.get('id', '?')), name, e
            )
            return ''

        # Set up the element's properties.
        drawargs = _style.construct_datas(datas, feature['properties'])

        classes = _style.construct_classes(classes, feature['properties'])

        # Add the layer name to the class list.
        if name:
            classes.insert(0, _style.sanitize(name))

        drawargs['class'] = ' '.join(classes)

        if 'id_field' in kwargs and kwargs['id_field'] in feature['properties']:
            drawargs['id'] = _style.sanitize(fid)

        try:
            # Draw the geometry.
            return draw.geometry(geom, precision=precision, **drawargs)

        except SvgisError as e:
            self.log.warning('unable to draw feature %s of %s: %s', fid, name or '?', e)
            return ''

    def compose(self, bounds=None, style=None, viewbox=True, inline=True, **kwargs):
        """
        Draw files to svg.

        Args:
            bounds (Sequence): Map bounding box in WGS84 (longlat) coordinates.
                               Defaults to map data bounds.
            scalar (int): factor by which to scale the data, generally a small number (1/map scale).
            style (str): CSS to append to parent object CSS.
            viewbox (bool): If True, draw SVG with a viewbox. If False, translate coordinates
                            to the frame. Defaults to True.
            inline (bool): If False, do not add CSS style attributes to each element.
            padding (int): Number of (projected) units to pad bounds by.
            precision (int): Precision for rounding output coordinates.

        Returns:
            ``str`` containing an entire SVG document.
        """
        # Set up arguments
        scalar = kwargs.pop('scalar', self.scalar)
        bounds = bounding.check(bounds) or self.unprojected_bounds

        # Draw files
        members = [svg.group(**self.compose_file(f, bounds, scalar=scalar, **kwargs)) for f in self.files]

        self.log.info('compose(): bounds  = %s', bounds)
        self.log.info('compose(): style   = %s', (style or '')[:25])
        self.log.info('compose(): viewbox = %s', viewbox)
        drawing = self.draw(members, scalar, kwargs.get('precision'), style=style, viewbox=viewbox, inline=inline)

        # Always reset projected bounds.
        self._projected_bounds = None

        return drawing

    def draw(self, members, scalar=None, precision=None, style=None, **kwargs):
        """
        Combine drawn layers into an SVG drawing.

        Args:
            members (list): unicode representations of SVG groups.
            scalar (int): factor by which to scale the data, generally a small number (1/map scale).
            style (str): CSS to append to parent object CSS.
            viewbox (bool): If True, draw SVG with a viewbox. If False, translate coordinates to
                            the frame. Defaults to True.
            inline (bool): If True, try to run CSS into each element.

        Returns:
            ``str`` containing an entire SVG document.
        """
        scalar = scalar or self.scalar
        precision = precision or self.precision
        style = style or self.style
        transform_attrib = 'scale(1,-1)'

        try:
            if any((utils.isinf(b) for b in self._projected_bounds)):
                self.log.warning('Drawing has infinite bounds, consider changing projection or bounding box.')

            dims = [float(b or 0.0) * scalar for b in self.projected_bounds]
        except TypeError:
            self.log.warning(r'Unable to find bounds, map is probably empty ¯\_(ツ)_/¯')
            dims = 0, 0, 0, 0

        # width and height
        size = [dims[2] - dims[0], dims[3] - dims[1]]

        self.log.debug('Size: %f x %f', *size)

        if kwargs.pop('viewbox', True):
            viewbox = [dims[0], -dims[3]] + size
            self.log.debug('drawing with viewbox')
        else:
            viewbox = None
            transform_attrib += f' translate({-dims[0]},{-dims[3]})'
            self.log.debug('translating contents to fit')

        # Create container and then SVG
        container = svg.group(members, fill_rule='evenodd', transform=transform_attrib)
        drawing = svg.drawing(size, [container], style=style, precision=precision, viewbox=viewbox)

        if kwargs.pop('inline', False):
            self.log.info('inlining styles')
            drawing = _style.inline(drawing)

        return drawing
