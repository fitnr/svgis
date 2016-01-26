#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>

try:
    from shapely.geometry import shape, mapping
    import numpy as np
except ImportError:
    pass


def d2_geom(geom):
    if geom['type'] == 'Point':
        geom['coordinates'] = geom['coordinates'][:2]

    elif geom['type'] in ('MultiPoint', 'LineString'):
        geom['coordinates'] = [p[:2] for p in geom['coordinates']]

    elif geom['type'] in ('MultiLineString', 'Polygon'):
        geom['coordinates'] = [[p[:2] for p in ring] for ring in geom['coordinates']]

    elif geom['type'] == 'MultiPolygon':
        geom['coordinates'] = [[[p[:2] for p in ring] for ring in poly] for poly in geom['coordinates']]

    elif geom['type'] == 'GeometryCollection':
        geom['geometries'] = [d2_geom(g) for g in geom['geometries']]

    return geom


def _expand_np(coordinates):
    return np.array(_expand_py(coordinates))


def _expand_py(coordinates):
    return list(coordinates)


def expand(ring):
    try:
        return _expand_np(ring)
    except NameError:
        return _expand_py(ring)


def expand_rings(rings):
    try:
        return [_expand_np(ring) for ring in rings]
    except NameError:
        return [_expand_py(ring) for ring in rings]


def expand_geom(geom):
    '''Expand generators in a geometry's coordinates.'''

    if geom['type'] == 'MultiPolygon':
        geom['coordinates'] = [expand_rings(rings) for rings in geom['coordinates']]

    elif geom['type'] in ('Polygon', 'MultiLineString'):
        geom['coordinates'] = expand_rings(geom['coordinates'])

    elif geom['type'] in ('MultiPoint', 'LineString'):
        geom['coordinates'] = expand(geom['coordinates'])

    elif geom['type'] == 'Point':
        geom['coordinates'] = expand(geom['coordinates'])

    elif geom['type'] == 'GeometryCollection':
        geom['geometries'] = [expand_geom(g) for g in geom['geometries']]

    else:
        raise NotImplementedError("Unsupported geometry type " + geom['type'])

    return geom


def prepare(bbox):
    minx, miny, maxx, maxy = bbox
    bounds = {
        "type": "Polygon",
        "coordinates": [[(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)]]
    }
    try:
        bbox = shape(bounds)

        def func(geometry):
            geom = expand_geom(geometry)
            clipped = bbox.intersection(shape(geom))
            return mapping(clipped)

    except NameError:
        def func(geometry):
            return geometry

    return func


def clip(geometry, bbox):
    '''Clip a geometry to a bounding box. BBOX may be a tuple or a shapely geometry object'''
    try:
        return prepare(bbox)(geometry)

    except NameError:
        return geometry
