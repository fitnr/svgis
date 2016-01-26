#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import os.path
import pyproj
import utm
from fiona import transform
import fiona.crs

'''
Helpers for dealing with projections
'''


def tm_proj4(x0, y0, y1):
    return ('+proj=lcc +lon_0={x0} +lat_1={y1} +lat_2={y0} +lat_0={y1}'
            '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0'
            '+units=m +no_defs').format(x0=x0, y0=y0, y1=y1)


def utm_proj4(x, y):
    '''Generate the proj4 string for a given (lon, lat) coordinate.'''
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
    if (use_proj is None or use_proj == 'file') and not pyproj.Proj(**in_crs).is_latlong():
        # it's projected already, so noop.
        return in_crs

    else:
        return fiona.crs.from_string(generatecrs(*bounds, use_proj=use_proj))


def project_mbr(in_crs, out_crs, minx, miny, maxx, maxy):
    minpt, maxpt = zip(*transform.transform(in_crs, out_crs, (minx, maxx), (miny, maxy)))
    return minpt + maxpt


def reproject_bounds(in_crs, out_crs, boundaryring):
    xs, ys = zip(*boundaryring)

    if in_crs is None:
        raise TypeError('Need input CRS, not None')

    if out_crs is None:
        raise TypeError('Need output CRS, not None')

    xbounds, ybounds = transform.transform(in_crs, out_crs, xs, ys)

    return min(xbounds), min(ybounds), max(xbounds), max(ybounds)


def pick(project):
    use_proj, out_crs = None, None

    if project.lower() in ('local', 'utm'):
        use_proj = project.lower()

    elif os.path.exists(project):
        # Is a file
        with open(project) as f:
            out_crs = fiona.crs.from_string(f.read())

    elif project[:5].lower() == 'epsg:':
        # Is an epsg code
        _, epsg = project.split(':')
        out_crs = fiona.crs.from_epsg(int(epsg))

    else:
        # Assume it's a proj4 string.
        # fiona.crs.from_string returns {} if it isn't.
        out_crs = fiona.crs.from_string(project)

    return use_proj, out_crs

