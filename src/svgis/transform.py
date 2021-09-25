# -*- coding: utf-8 -*-
'''Clip and simplify geometries'''
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, 2020, Neil Freeman <contact@fakeisthenewreal.org>
from functools import partial

try:
    from shapely.geometry import mapping, shape
    from shapely.geos import TopologicalError
except ImportError:
    pass
try:
    import numpy as np
except ImportError:
    pass
try:
    import visvalingamwyatt as vw
except ImportError:
    pass


def clipper(bbox):
    """
    Create a clipping function for a given bounding box.

    Args:
        bbox (tuple): bounding box

    Returns:
        function that will given geometries to input bounding box
    """
    minx, miny, maxx, maxy = bbox
    bounds = {
        "type": "Polygon",
        "coordinates": [[(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)]],
    }
    try:
        bbox_shape = shape(bounds)

        def func(geometry):
            # This is technically only needed in Py3, but whatever.
            try:
                clipped = bbox_shape.intersection(shape(geometry))
            except (ValueError, TopologicalError):
                return geometry

            return mapping(clipped)

    except NameError:

        def func(geometry):
            return geometry

    return func


def clip(geometry, bounds):
    """
    Clip a geometry to a bounding box. Equivalent to calling clipper(bounds)(geometry).

    Args:
        geometry (dict): geometry object
        bounds (tuple): bounding box

    Returns:
        (dict) geometry
    """
    try:
        return clipper(bounds)(geometry)

    except NameError:
        return geometry


def simplifier(ratio):
    """
    Create a simplification function, if visvalingamwyatt is available.
    Otherwise, return a noop function.

    Args:
        ratio (int): Between 1 and 99

    Returns:
        simplification function
    """
    try:
        # put this first to get NameError out of the way
        simplify = vw.simplify_geometry

        if ratio is None or ratio >= 100 or ratio < 1:
            raise SvgisError("Invalid ratio")

        return partial(simplify, ratio=ratio / 100.0)

    except (TypeError, ValueError, NameError):
        return None


def scale(coordinates, scalar=1):
    '''Scale a list of coordinates by a scalar. Only use with projected coordinates'''
    try:
        try:
            arr = np.array(coordinates, dtype=float)

        except TypeError:
            arr = np.array(list(coordinates), dtype=float)

        return arr * scalar

    except NameError:
        if isinstance(coordinates, tuple):
            return [coordinates[0] * scalar, coordinates[1] * scalar]

        return [(c[0] * scalar, c[1] * scalar) for c in coordinates]


def scale_rings(rings, factor=1):
    """Apply scale() to a list of rings."""
    return [scale(ring, factor) for ring in rings]


def scale_geom(geom, factor=1):
    """
    Scale a geometry by a given factor

    Args:
        geom (dict): geojson-like dict
        factor (numeric): scale factor, default: 1
    """
    if geom['type'] == 'MultiPolygon':
        geom['coordinates'] = [scale_rings(rings, factor) for rings in geom['coordinates']]

    elif geom['type'] in ('Polygon', 'MultiLineString'):
        geom['coordinates'] = scale_rings(geom['coordinates'], factor)

    elif geom['type'] in ('MultiPoint', 'LineString'):
        geom['coordinates'] = scale(geom['coordinates'], factor)

    elif geom['type'] == 'Point':
        geom['coordinates'] = scale(geom['coordinates'], factor)

    elif geom['type'] == 'GeometryCollection':
        geom['geometries'] = [scale_geom(i) for i in geom['geometries']]

    else:
        raise NotImplementedError(f"Unsupported geometry type: {geom['type']}")

    return geom
