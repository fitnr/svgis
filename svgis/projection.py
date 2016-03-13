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
from six import string_types
from .utils import DEFAULT_GEOID
from . import bounding


METHODS = 'default', 'file', 'local', 'utm'


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


def generateproj4(method, bounds, file_crs):
    '''
    Generate a Proj4 projection definition: either the local UTM zone
    or a custom transverse mercator.

    Args:
        method (str): If default, local or utm.
            * If 'utm': generate a UTM. Otherwise, a local projection,
            * If 'local': generate a custom local transverse mercator projection,
            * If 'default': if file_crs is longlat, act like local. otherwise use file_crs
        bounds (tuple): bounding box
        file_crs (dict): Fiona-generated CRS of the input file

    Returns:
        (str) proj4 string
    '''
    if bounds is None or file_crs is None:
        raise ValueError('generatecrs missing bounds and file crs')

    is_longlat = _is_longlat(file_crs)

    if method == 'default':
        # Check if file_crs _is_longlat, if not use that.
        # Option to continue returning default if we didn't get a file_crs
        if is_longlat:
            method = 'local'
        else:
            return fiona.crs.to_string(file_crs)

    if is_longlat:
        longlat_bounds = bounds
    else:
        longlat_bounds = bounding.transform(file_crs, DEFAULT_GEOID, bounds)

    minx, miny, maxx, maxy = longlat_bounds

    if method == 'utm':
        midx = (minx + maxx) / 2
        midy = (miny + maxy) / 2

        return utm_proj4(midx, midy)

    elif method == 'local':
        # Create a custom TM projection
        x0 = (float(minx) + float(maxx)) // 2

        return tm_proj4(x0, miny, maxy)


def _is_longlat(crs):
    '''Test if CRS is in lat/long coordinates'''
    try:
        if crs.get('proj') == 'longlat' or pyproj.Proj(**crs).is_latlong():
            return True
    except RuntimeError:
        pass

    return False


def pick(project, bounds=None, file_crs=None):
    '''
    Pick a projection or projection method to use.

    Returns:
        (mixed) one of: None, 'local', 'utm' or a dict
    '''
    out_crs = None
    project = project or 'default'

    if isinstance(project, dict):
        return project

    elif isinstance(project, string_types):
        if project.lower() == 'file':
            out_crs = file_crs if file_crs is not None else 'file'

        # Is an epsg code
        elif project.lower()[:5] == 'epsg:':
            out_crs = fiona.crs.from_epsg(int(project.split(':')[1]))

        elif project.lower() in METHODS:
            try:
                out_crs = fiona.crs.from_string(generateproj4(project, bounds, file_crs))

            except ValueError:
                return project

        # Is a file
        elif os.path.exists(project):
            with open(project) as f:
                out_crs = fiona.crs.from_string(f.read())

        else:
            # Assume it's a proj4 string.
            # fiona.crs.from_string returns {} if it isn't.
            out_crs = fiona.crs.from_string(project)

    return out_crs


def fake_to_string(crs):
    '''
    Fake to_string for debugging in places where fiona.crs.to_string
    isn't available
    '''
    return ' '.join('+{0[0]}={0[1]}'.format(i) for i in crs.items())
