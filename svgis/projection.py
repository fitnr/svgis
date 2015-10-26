'''Helpers for dealing with projections'''
# -*- coding: utf-8 -*-
import pyproj
import utm
from fiona import transform
import fiona.crs
from pyproj import Proj
from fionautil import scale


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


def generatecrs(minx, miny, maxx, maxy, use_proj=None):
    '''Choose a projection, either the local UTM zone or
    create a custom transverse mercator.
    Returns a proj4 string
    '''
    if use_proj == 'utm':
        midx = (minx + maxx) / 2
        midy = (miny + maxy) / 2

        return utm_proj4(midx, midy)

    else:
        # Create a custom TM projection
        x0 = (float(minx) + float(maxx)) // 2

        return tm_proj4(x0, miny, maxy)


def choosecrs(in_crs, bounds, use_proj=None):
    '''Choose a projection. If the layer is projected, use that.
    Otherwise, create use a passed projection or create a custom transverse mercator.
    :in_crs dict A fiona-type proj4 dictionary
    :bounds tuple (minx, miny, maxx, maxy)
    :use_proj string wither 'utm' or 'local'
    :returns dict fiona-type proj4 dictionary
    '''
    if use_proj is None and not Proj(**in_crs).is_latlong():
        # it's projected already, so noop.
        return in_crs

    else:
        return fiona.crs.from_string(generatecrs(*bounds, use_proj=use_proj))


def project_scale(in_crs, out_crs, ring, scalar=None):
    '''Project and apply a scale to a ring'''
    xs, ys = transform.transform(in_crs, out_crs, *zip(*ring))

    projected = zip(xs, ys)

    # then scale
    if scalar:
        return scale.scale(projected, scalar)
    else:
        return projected


def project_mbr(in_crs, out_crs, minx, miny, maxx, maxy):
    minpt, maxpt = zip(*transform.transform(in_crs, out_crs, (minx, maxx), (miny, maxy)))
    return minpt + maxpt
