from __future__ import division
from functools import partial
from itertools import izip as zip
try:
    import visvalingamwyatt as vw
except ImportError:
    pass


def updatebounds(old, new):
    '''
    Extend old with any more distant values from newpoints.
    Also replace any missing min/max points in old with values from new.
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
        bounds = list((a or b or c) for a, b, c in zip(bounds, new, old))

    return bounds


def extend_bbox(bbox, ext=100):
    '''
    Widen the bounding box just a little bit. Assumes the bbox is in feet or meters or something.
    '''
    return bbox[0] - ext, bbox[1] - ext, bbox[2] + ext, bbox[3] + ext


def simplifier(ratio):
    try:
        if ratio == 1. or ratio is None:
            raise ValueError

        return partial(vw.simplify_geometry, ratio=ratio)

    except (ValueError, NameError):
        return lambda g: g
