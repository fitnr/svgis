from __future__ import division
import math


def rect(length, angle):
    '''polar to cartesian coordinates'''
    return length * math.cos(angle), length * math.sin(angle)


def updatebounds(old, new):
    '''
    Extend old with any more distant values from newpoints.
    Also replace any missing min/max points in old with values from new
    '''
    bounds = []

    # python3 gives TypeError when using None in min/max
    # This contraption avoids that problem.
    # List comp below replaces Nones in bounds with real values in new or old
    for n, m in zip(new[:2], old[:2]):
        try:
            bounds.append(min(n, m))
        except TypeError:
            bounds.append(None)

    for n, m in zip(new[2:], old[2:]):
        try:
            bounds.append(max(n, m))
        except TypeError:
            bounds.append(None)

    if any(not v for v in bounds):
        bounds = tuple((a or b or c) for a, b, c in zip(bounds, new, old))

    return bounds


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
