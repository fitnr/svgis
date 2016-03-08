#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>

from __future__ import division
from math import ceil, floor
from itertools import groupby


def posint(i):
    '''Fake class for positive integers only'''
    I = int(i)
    if I < 0:
        raise ValueError('Must be a positive integer')
    return I


def isinf(x):
    inf = float('inf')
    return x == inf or x == inf * -1


def between(a, b, count=None):
    """Yield <count> points between two floats"""
    jump = (b - a) / (count or 10)

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
    i = inp - (inp % mod)
    return int(floor(i))


def modceil(inp, mod):
    i = inp + mod - (inp % mod)
    return int(ceil(i))


def rnd(i, precision):
    if precision is None:
        return i
    else:
        return round(i, precision)


def isstr(x):
    return isinstance(x, basestring)


def dedupe(array):
    '''
    Use itertools.groupby to remove duplicates in a list.
    '''
    try:
        array = array.tolist()
    except AttributeError:
        pass

    for g in groupby(array):
        yield g[0]
