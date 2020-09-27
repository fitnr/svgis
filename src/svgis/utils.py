#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Utilities for svgis'''

# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
from itertools import groupby
from math import ceil, floor

from .errors import SvgisError

# WGS 84
DEFAULT_GEOID = 4326


def posint(i):
    '''Fake class for positive integers only'''
    val = int(i)
    if val < 0:
        raise SvgisError('Must be a positive integer')
    return val


def isinf(x):
    """Check if input is infinite."""
    inf = float('inf')
    return x in (inf, inf * -1)


def between(a, b, count=None):
    """Yield <count> points between two floats"""
    jump = (b - a) / float(count or 10.0)

    while a < b:
        yield a
        a += jump


def frange(a, b, step, cover=None):
    """like range, but for floats."""
    while a < b:
        yield a
        a += step

    if cover:
        yield a


def modfloor(inp, mod):
    """A floor function that snaps to steps of size mod."""
    i = inp - (inp % mod)
    return int(floor(i))


def modceil(inp, mod):
    """A ceil function that snaps to steps of size mod."""
    i = inp + mod - (inp % mod)
    return int(ceil(i))


def rnd(i, precision=None):
    """Optionally round to a given precision."""
    if precision is None:
        return i

    return round(i, precision)


def dedupe(array):
    """Use itertools.groupby to remove duplicates in a list."""
    try:
        array = array.tolist()
    except AttributeError:
        pass

    for g in groupby(array):
        yield g[0]


def signed_area(coords):
    """Return the signed area enclosed by a ring using the linear time
    algorithm at http://www.cgafaq.info/wiki/Polygon_Area. A value >= 0
    indicates a counter-clockwise oriented ring."""
    try:
        xs, ys = tuple(map(list, zip(*coords)))
    except ValueError:
        # Attempt to handle a z-dimension
        xs, ys, _ = tuple(map(list, zip(*coords)))

    xs.append(xs[1])
    ys.append(ys[1])
    return sum(xs[i] * (ys[i + 1] - ys[i - 1]) for i in range(1, len(coords))) / 2.0


def clockwise(coords):
    """Check if coordinates move in a clockwise direction."""
    return signed_area(coords) < 0


def counterclockwise(coords):
    """Check if coordinates move in a counterclockwise direction."""
    return signed_area(coords) >= 0
