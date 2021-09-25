#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Do the work of picking, generating and transforming coordinate reference systems."""
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, 2020, Neil Freeman <contact@fakeisthenewreal.org>
import logging
import os.path

import utm
from pyproj.crs import CRS
from pyproj.exceptions import CRSError

from . import bounding, errors
from .utils import DEFAULT_GEOID

LOG = logging.getLogger('svgis')
METHODS = 'default', 'file', 'local', 'utm'


def tm_proj4(x0, y0, y1):
    """
    Generate the proj4 string for a local Transverse Mercator projection
    centered at a given longitude and between two latitudes.

    Args:
        x0 (float): longitude
        y0 (float): latitude 0
        y1 (float): latitude 1

    Returns:
        (str) proj4 string
    """
    proj = f'+proj=lcc +lon_0={x0} +lat_1={y1} +lat_2={y0} +lat_0={y1}'
    return proj + ' +x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'


def utm_proj4(lon, lat):
    """
    Generate the proj4 string for the UTM projection at a given (lon, lat) coordinate.

    Args:
        lon (float): longitude
        lat (float): latitude

    Returns:
        (str) proj4 string
    """
    try:
        _, _, zonenumber, zoneletter = utm.from_latlon(lat, lon)

        if zoneletter in 'ZYXWVUTSRQPN':
            hemisphere = 'north'

        elif zoneletter in 'MLKJHGFEDCBA':
            hemisphere = 'south'

        return f'+proj=utm +zone={zonenumber} +{hemisphere} +datum=WGS84 +units=m +no_defs'

    except utm.error.OutOfRangeError as err:
        raise errors.SvgisError(err) from err


def generateproj4(method, bounds, file_crs):
    """
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
    """
    LOG.debug('generating proj4')
    if bounds is None or file_crs is None:
        raise errors.SvgisError('generatecrs missing bounds and file crs')

    is_longlat = _is_longlat(file_crs)
    if method == 'default':
        # Check if file_crs _is_longlat, if not use that.
        # Option to continue returning default if we didn't get a file_crs
        if is_longlat:
            method = 'local'
        else:
            return CRS(file_crs)

    if is_longlat:
        longlat_bounds = bounds
    else:
        longlat_bounds = bounding.transform(bounds, in_crs=file_crs, out_crs=DEFAULT_GEOID)

    minx, miny, maxx, maxy = longlat_bounds

    if method == 'utm':
        midx = (minx + maxx) / 2
        midy = (miny + maxy) / 2
        return utm_proj4(midx, midy)

    if method == 'local':
        # Create a custom TM projection
        x0 = (float(minx) + float(maxx)) // 2

        return tm_proj4(x0, miny, maxy)

    raise errors.SvgisError(f"Unexpected method. Valid methods are default, local or utm. Got: {method}")


def _is_longlat(crs):
    '''Test if CRS is in lat/long coordinates'''
    try:
        return crs['proj'] == 'longlat'
    except (KeyError, TypeError, AttributeError):
        pass

    projection = CRS(crs)

    try:
        return projection.is_geographic
    except AttributeError:
        return crs.to_dict().get('proj') == 'longlat'


def pick(project, bounds=None, file_crs=None):
    """
    Pick a projection or projection method to use.

    Returns:
        (mixed) one of: None, 'local', 'utm' or a dict
    """
    LOG.debug('projection.pick("%s")', project)
    project = project or 'default'
    if isinstance(project, CRS):
        return project

    try:
        return CRS(project)
    except CRSError:
        pass

    if isinstance(project, str):
        LOG.debug('projection is a str')
        if project.lower() == 'file':
            LOG.debug('"project" == file')
            return file_crs if file_crs is not None else 'file'

        if project.lower() in METHODS:
            LOG.debug('"project" is in METHODS')
            return CRS(generateproj4(project, bounds, file_crs))

        if os.path.exists(project):
            with open(project) as f:
                return CRS(f.read())

    raise errors.SvgisError(f'Unable to convert to projection: {project}')


def fake_to_string(crs):
    """
    Fake to_string for debugging in places where fiona.crs.to_string
    isn't available
    """
    return ' '.join(f'+{i[0]}={i[1]}' for i in crs.items())
