'''Helpers for dealing with projections'''
# -*- coding: utf-8 -*-
import pyproj
import utm
from fiona import transform
from . import scale


def tm_proj4(x0, y0, y1):
    return ('+proj=lcc +lon_0={x0} +lat_1={y1} +lat_2={y0} +lat_0={y1}'
            '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0'
            '+units=m +no_defs').format(x0=x0, y0=y0, y1=y1)


def tm(x0, y0, y1):
    '''Generate a local transverse mercator projection'''
    proj4 = tm_proj4(x0, y0, y1)
    return pyproj.Proj(proj4)


def utm_proj4(x, y):
    '''Generate the proj4 string for a given (lon, lat) coordinate'''

    try:
        _, _, zonenumber, zoneletter = utm.from_latlon(y, x)
        return zonetoproj4(zonenumber, zoneletter)

    except utm.error.OutOfRangeError as e:
        raise ValueError(e)


def zonetoproj4(zonenumber, zoneletter):
    if zoneletter in 'ZYXWVUTSRQPN':
        hemisphere = 'north'

    elif zoneletter in 'MLKJHGFEDCBA':
        hemisphere = 'south'

    return '+proj=utm +zone={} +{} +datum=WGS84 +units=m +no_defs'.format(zonenumber, hemisphere)

def project_scale(in_crs, out_crs, ring, scalar=None):
    '''Project and apply a scale to a ring'''
    xs, ys = transform.transform(in_crs, out_crs, *zip(*ring))

    projected = zip(xs, ys)

    # then scale
    if scalar:
        return scale.scale(projected, scalar)
    else:
        return projected
