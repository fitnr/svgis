#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Utilities for working with bounding boxes'''

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
from fiona.transform import transform as fionatransform
from . import utils


def check(bounds):
    '''Check if bounds are valid.'''
    # Refuse to set these more than once
    try:
        if bounds is None or len(bounds) != 4 or not all(bounds):
            raise ValueError

    except (TypeError, AttributeError, ValueError):
        return False

    if bounds[0] > bounds[2]:
        bounds = bounds[2], bounds[1], bounds[0], bounds[3]

    if bounds[1] > bounds[3]:
        bounds = bounds[0], bounds[3], bounds[2], bounds[1]

    return bounds


def update(old, new):
    '''
    Extend old with any more distant values from newpoints.
    Also replace any missing min/max points in old with values from new.
    '''
    bounds = []
    inf = float('inf')
    neginf = inf * -1

    # python3 gives TypeError when using None in min/max
    # This contraption avoids that problem.
    # List comp below replaces Nones in bounds with real values in new or old
    for n, m in zip(new[:2], old[:2]):
        try:
            if neginf in (m, n):
                bounds.append(max(n, m))
                continue

            bounds.append(min(n, m))
        except TypeError:
            bounds.append(None)

    for n, m in zip(new[2:], old[2:]):
        try:
            if inf in (m, n):
                bounds.append(min(n, m))
                continue

            bounds.append(max(n, m))
        except TypeError:
            bounds.append(None)

    if any(not v for v in bounds):
        bounds = list((a or b or c) for a, b, c in zip(bounds, new, old))

    return bounds


def pad(bounds, ext=100):
    '''
    Pad a bounding box. Works best when input is in feet or meters or something.
    '''
    try:
        return bounds[0] - ext, bounds[1] - ext, bounds[2] + ext, bounds[3] + ext
    except TypeError:
        return bounds


def ring(bounds):
    '''Convert min, max points to a boundary ring.'''
    minx, miny, maxx, maxy = bounds
    xs, ys = list(utils.between(minx, maxx)), list(utils.between(miny, maxy))

    left_top = [(minx, y) for y in ys] + [(x, maxy) for x in xs][1:]

    ys.reverse()
    xs.reverse()

    return left_top + [(maxx, y) for y in ys] + [(x, miny) for x in xs]


def covers(b1, b2):
    '''
    Return True if b1 covers b2.

    Args:
        b1 (tuple): A bounding box (minx, miny, maxx, maxy)
        b2 (tuple): A bounding box
    '''
    return b1[0] <= b2[0] and b1[1] <= b2[1] and b1[2] >= b2[2] and b1[3] >= b2[3]


def transform(in_crs, out_crs, bounds):
    '''
    Project a bounding box, taking care to not slice off the sides.

    Args:
        in_crs (dict): Fiona-type proj4 mapping representing input projection.
        out_crs (dict): Fiona-type proj4 mapping representing output projection.
        bounds (tuple): bounding box to transform.

    Returns:
        tuple
    '''
    if in_crs is None:
        raise TypeError('Need input CRS, not None')

    if out_crs is None:
        raise TypeError('Need output CRS, not None')

    if in_crs == out_crs:
        return bounds

    try:
        xs, ys = list(zip(*ring(bounds)))
    except ValueError:
        # file is likely empty
        return float('-inf'), float('-inf'), float('inf'), float('inf')

    xbounds, ybounds = fionatransform(in_crs, out_crs, xs, ys)

    return min(xbounds), min(ybounds), max(xbounds), max(ybounds)
