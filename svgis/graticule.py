#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import json
from functools import partial
from . import projection, utils


"""
Draw regular-interval graticules for a coordinate system
"""


def graticule(bounds, step, crs=None):
    '''
    Draw graticules.

    Args:
        bounds (tuple): In WGS84 coordinates.
        step (int): Distance between graticule lines, in the output projection.
        crs (str): A projection specification.

    Returns:
        A generator that yields GeoJSON-like dicts of graticule features.
    '''
    if crs == 'file':
        raise ValueError("'file' is not a valid option for projecting graticules.")

    if crs:
        method, out_crs = projection.pick(crs)
        if method in ('local', 'utm'):
            out_crs = projection.generatecrs(*bounds, proj_method=method)

        bounds = projection.transform_bounds({'init': u'epsg:4326'}, out_crs, bounds)

    minx, miny, maxx, maxy = bounds

    minx, miny = utils.modfloor(minx, step), utils.modfloor(miny, step)
    maxx, maxy = utils.modceil(maxx, step), utils.modceil(maxy, step)

    frange = partial(utils.frange, step=step, cover=True)

    for i, X in enumerate(frange(minx, maxx + step), 1):
        yield _feature(i, [(X, y) for y in frange(miny, maxy + step)])

    for i, Y in enumerate(frange(miny, maxy + step), i+1):
        yield _feature(i, [(x, Y) for x in frange(minx, maxx + step)])


def _feature(i, coords):
    return {
        'geometry': {
            'type': 'LineString',
            'coordinates': coords
        },
        'type': 'Feature',
        'id': i
    }


def layer(bounds, step, crs=None):
    return {
        "type": "FeatureCollection",
        "features": list(graticule(bounds, step, crs))
    }


def geojson(bounds, step, crs=None):
    '''
    Create a geojson with graticules of the given bounds.

    Returns:
        str
    '''
    return json.dumps(layer(bounds, step, crs))
