#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Clip and simplify geometries'''

# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
from types import GeneratorType
from functools import partial
try:
    from shapely.geometry import shape, mapping
    from shapely.geos import TopologicalError
    import numpy as np
except ImportError:
    pass
try:
    import visvalingamwyatt as vw
except ImportError:
    pass


def _expand_np(coordinates):
    return np.array(_expand_py(coordinates))


def _expand_py(coordinates):
    return tuple(coordinates)


def expand(ring):
    if isinstance(ring, GeneratorType):
        try:
            return _expand_np(ring)
        except NameError:
            return _expand_py(ring)
    else:
        return ring


def expand_rings(rings):
    try:
        return tuple(_expand_np(ring) for ring in rings)
    except NameError:
        return tuple(_expand_py(ring) for ring in rings)


def expand_geom(geom):
    '''Expand generators in a geometry's coordinates.'''

    if geom['type'] == 'MultiPolygon':
        geom['coordinates'] = tuple(expand_rings(rings) for rings in geom['coordinates'])

    elif geom['type'] in ('Polygon', 'MultiLineString'):
        geom['coordinates'] = expand_rings(geom['coordinates'])

    elif geom['type'] in ('Point', 'MultiPoint', 'LineString'):
        geom['coordinates'] = expand(geom['coordinates'])

    elif geom['type'] == 'GeometryCollection':
        geom['geometries'] = tuple(expand_geom(g) for g in geom['geometries'])

    else:
        raise NotImplementedError("Unsupported geometry type " + geom['type'])

    return geom


def clipper(bbox):
    '''
    Create a clipping function for a given bounding box.

    Args:
        bbox (tuple): bounding box

    Returns:
        function that will given geometries to input bounding box
    '''
    minx, miny, maxx, maxy = bbox
    bounds = {
        "type": "Polygon",
        "coordinates": [[(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)]]
    }
    try:
        bbox_shape = shape(bounds)

        def func(geometry):
            # This is technically only needed in Py3, but whatever.
            geom = expand_geom(geometry)

            try:
                clipped = bbox_shape.intersection(shape(geom))
            except (ValueError, TopologicalError):
                return geometry

            return mapping(clipped)

    except NameError:
        def func(geometry):
            return geometry

    return func


def clip(geometry, bounds):
    '''
    Clip a geometry to a bounding box. Equivalent to calling clipper(bounds)(geometry).

    Args:
        geometry (dict): geometry object
        bounds (tuple): bounding box

    Returns:
        (dict) geometry
    '''
    try:
        return clipper(bounds)(geometry)

    except NameError:
        return geometry


def simplifier(ratio):
    '''
    Create a simplification function, if visvalingamwyatt is available.
    Otherwise, return a noop function.

    Args:
        ratio (int): Between 1 and 99

    Returns:
        simplification function
    '''
    try:
        # put this first to get NameError out of the way
        simplify = vw.simplify_geometry

        if ratio is None or ratio >= 100 or ratio < 1:
            raise ValueError

        return partial(simplify, ratio=ratio / 100.)

    except (TypeError, ValueError, NameError):
        return None
