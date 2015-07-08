from __future__ import division
import math


def rect(length, angle):
    '''polar to cartesian coordinates'''
    return length * math.cos(angle), length * math.sin(angle)


def replacebounds(bounds1, bounds2):
    '''Replace any missing min/max points in bounds1 with from bounds2'''

    if any(not v for v in bounds1):
        bounds1 = tuple((a or b) for a, b in zip(bounds1, bounds2))

    return bounds1

def _frange(a, b, count=None):
    """Yield <count> points between two floats"""
    count = count or 10
    jump = (b - a) / 10

    while a < b:
        yield a
        a += jump


def mbr_to_bounds(minx, miny, maxx, maxy):
    """Convert min, max points to a boundary ring"""

    xs, ys = list(_frange(minx, maxx)), list(_frange(miny, maxy))

    left_top = [(minx, y) for y in ys] + [(x, maxy) for x in xs][1:]

    ys.reverse()
    xs.reverse()

    return left_top + [(maxx, y) for y in ys] + [(x, miny) for x in xs]
