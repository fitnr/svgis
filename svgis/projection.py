#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Deal with projections'''

# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import os.path
import fiona.transform
import fiona.crs
import pyproj
import utm


def tm_proj4(x0, y0, y1):
    '''
    Generate the proj4 string for a local Transverse Mercator projection
    centered at a given longitude and between two latitudes.

    Args:
        x0 (float): longitude
        y0 (float): latitude 0
        y1 (float): latitude 1

    Returns:
        (str) proj4 string
    '''
    return ('+proj=lcc +lon_0={x0} +lat_1={y1} +lat_2={y0} +lat_0={y1}'
            '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0'
            '+units=m +no_defs').format(x0=x0, y0=y0, y1=y1)


def utm_proj4(lon, lat):
    '''
    Generate the proj4 string for the UTM projection at a given (lon, lat) coordinate.

    Args:
        lon (float): longitude
        lat (float): latitude

    Returns:
        (str) proj4 string
    '''
    try:
        _, _, zonenumber, zoneletter = utm.from_latlon(lat, lon)

        if zoneletter in 'ZYXWVUTSRQPN':
            hemisphere = 'north'

        elif zoneletter in 'MLKJHGFEDCBA':
            hemisphere = 'south'

        return '+proj=utm +zone={} +{} +datum=WGS84 +units=m +no_defs'.format(zonenumber, hemisphere)

    except utm.error.OutOfRangeError as e:
        raise ValueError(e)


def generatecrs(minx, miny, maxx, maxy, proj_method=None):
    '''Choose a projection, either the local UTM zone or
    create a custom transverse mercator.

    Returns:
        (str) proj4 string
    '''
    if proj_method == 'utm':
        midx = (minx + maxx) / 2
        midy = (miny + maxy) / 2

        return utm_proj4(midx, midy)

    else:
        # Create a custom TM projection
        x0 = (float(minx) + float(maxx)) // 2

        return tm_proj4(x0, miny, maxy)


def _is_latlong(crs):
    '''Test if CRS is in lat/long coordinates'''
    try:
        if crs.get('proj') == 'longlat' or pyproj.Proj(**crs).is_latlong():
            return True
    except RuntimeError:
        pass

    return False


def choosecrs(in_crs, bounds, proj_method=None):
    '''Choose a projection. If the layer is projected, use that.
    Otherwise, create use a passed projection or create a custom transverse mercator.

    Args:
        in_crs (dict): A fiona-type proj4 dictionary
        bounds (tuple): (minx, miny, maxx, maxy)
        proj_method (string): either 'utm' or 'local'

    Returns:
        fiona-type proj4 dict.
    '''
    if proj_method == 'file' or (proj_method is None and not _is_latlong(in_crs)):
        # it's projected already, so noop.
        return in_crs

    else:
        return fiona.crs.from_string(generatecrs(*bounds, proj_method=proj_method))


def pick(project):
    '''
    Pick a projection or projection method to use.

    Returns:
        (tuple) method, crs
        method will be one of: None, 'local', 'utm'
        crs will be None or a dict
    '''
    proj_method, out_crs = None, None

    if project is None:
        # Protect future option of using file or picking
        return None, None

    if project.lower() in ('local', 'utm'):
        proj_method = project.lower()

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

    return proj_method, out_crs
