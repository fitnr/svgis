#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>

from functools import partial

try:
    import visvalingamwyatt as vw
except ImportError:
    pass
from . import utils


def updatebounds(old, new):
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


def extend_bbox(bbox, ext=100):
    '''
    Widen the bounding box just a little bit. Assumes the bbox is in feet or meters or something.
    '''
    return bbox[0] - ext, bbox[1] - ext, bbox[2] + ext, bbox[3] + ext


def bounds_to_ring(minx, miny, maxx, maxy):
    """Convert min, max points to a boundary ring."""

    xs, ys = list(utils.between(minx, maxx)), list(utils.between(miny, maxy))

    left_top = [(minx, y) for y in ys] + [(x, maxy) for x in xs][1:]

    ys.reverse()
    xs.reverse()

    return left_top + [(maxx, y) for y in ys] + [(x, miny) for x in xs]


def simplifier(ratio):
    '''
    Create a simplification function, if visvalingamwyatt is available.
    Otherwise, return a noop function.

    Args:
        ratio (int): Between 1 and 99
    '''
    try:
        # put this first to get NameError out of the way
        simplify = vw.simplify_geometry

        if ratio is None or ratio >= 100 or ratio < 1:
            raise ValueError

        return partial(simplify, ratio=ratio / 100.)

    except (TypeError, ValueError, NameError):
        return None


def bbox_covers(b1, b2):
    '''
    Return True if b1 covers b2.

    Args:
        b1 (tuple): A bounding box (minx, miny, maxx, maxy)
        b2 (tuple): A bounding box
    '''
    return b1[0] <= b2[0] and b1[1] <= b2[1] and b1[2] >= b2[2] and b1[3] >= b2[3]
