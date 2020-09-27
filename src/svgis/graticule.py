#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Draw regular-interval graticules for a coordinate system'''

# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, 2020, Neil Freeman <contact@fakeisthenewreal.org>
import json
from functools import partial

from pyproj.transformer import Transformer

from . import bounding, errors, projection, utils


def graticule(bounds, step, crs_or_method=None):
    """
    Draw graticules.

    Args:
        bounds (tuple): In WGS84 coordinates.
        step (int): Distance between graticule lines, in the output projection.
        crs_or_method (str): A projection specification.

    Returns:
        A generator that yields GeoJSON-like dicts of graticule features.
    """
    if crs_or_method == 'file':
        raise errors.SvgisError("'file' is not a valid option for projecting graticules.")

    if crs_or_method:
        out_crs = projection.pick(crs_or_method, bounds=bounds, file_crs=utils.DEFAULT_GEOID)
        unproject = Transformer.from_crs(utils.DEFAULT_GEOID, out_crs, skip_equivalent=True, always_xy=True)
        bounds = bounding.transform(bounds, transformer=unproject)

    else:
        unproject = Transformer.from_crs(4269, 4269, always_xy=True, skip_equivalent=True)

    minx, miny, maxx, maxy = bounds

    minx, miny = utils.modfloor(minx, step), utils.modfloor(miny, step)
    maxx, maxy = utils.modceil(maxx, step), utils.modceil(maxy, step)

    frange = partial(utils.frange, cover=True)

    i = 0
    for i, X in enumerate(frange(minx, maxx + step, step), 1):
        coords = unproject.itransform([(X, y) for y in frange(miny, maxy + step, step / 2.0)])
        yield _feature(i, coords, axis='x', coord=X)

    for i, Y in enumerate(frange(miny, maxy + step, step), i + 1):
        coords = unproject.itransform([(x, Y) for x in frange(minx, maxx + step, step / 2.0)])
        yield _feature(i, coords, axis='y', coord=Y)


def _feature(i, coords, axis=None, coord=None):
    return {
        'geometry': {'type': 'LineString', 'coordinates': list(coords)},
        'properties': {'axis': axis, 'coord': coord},
        'type': 'Feature',
        'id': i,
    }


def layer(bounds, step, crs=None):
    """
    Returns a graticule FeatureCollection object over the given bounds.

    Args:
        bounds (tuple): minx, miny, maxx, maxy
        step (numeric): distance between graticule lines
        crs: a CRS object or SRID.
    Returns:
        dict
    """
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": tuple(graticule(bounds, step, crs)),
    }


def geojson(bounds, step, crs=None):
    """
    Create a geojson with graticules of the given bounds.

    Returns:
        str
    """
    return json.dumps(layer(bounds, step, crs))
