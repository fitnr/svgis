#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

from __future__ import division
import sys
import os.path
import logging
import fiona.crs
from .. import css, projection
from ..svgis import SVGIS


def scale(layer, factor, **_):
    '''Rescale an SVG by a factor'''
    return css.rescale(layer, factor)


def add_style(layer, style, replace=None, **_):
    '''Add a CSS string to an SVG's style attribute.
    :layer string Input svg file location
    :output mixed Either a file handle or filename
    :style string The input CSS, css file or '-'. Strings ending in ".css" are treated as files, "-" reads from stdin.
    '''
    if style == '-':
        style = '/dev/stdin'

    root, ext = os.path.splitext(style)

    if ext == '.css' or root == '/dev/stdin':
        with open(style) as f:
            style = f.read()

    return css.add_style(layer, style, replace=replace)


def pick_projection(project):
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


def pick_style(style):
    try:
        _, ext = os.path.splitext(style)
        if ext == '.css':
            with open(style) as f:
                return f.read()

    except AttributeError:
        # Probably style is None.
        return None

    except IOError:
        logging.getLogger('svg').warn("Couldn't read %s, proceeding with default style", style)

    return style


def draw(layers, bounds=None, scale=1, padding=0, **kwargs):
    '''
    Draw a geodata layer to a simple SVG.
    :layers sequence Input geodata files.
    :output path Output file name
    :bounds sequence (minx, miny, maxx, maxy)
    :scale int Map scale. Larger numbers -> smaller maps
    :padding int Pad around bounds by this much. In projection units.
    :project string EPSG code, PROJ.4 string, or file containing a PROJ.4 string
    '''
    scale = (1 / scale) if scale else 1

    # Try to read style file
    styles = pick_style(kwargs.pop('style', None))

    use_proj, out_crs = pick_projection(kwargs.pop('project'))

    if kwargs.get('class_fields'):
        kwargs['classes'] = kwargs.pop('class_fields').split(',')

    kwargs.pop('class_fields', None)

    drawing = SVGIS(
        layers,
        bounds=bounds,
        scalar=scale,
        use_proj=use_proj,
        out_crs=out_crs,
        padding=padding,
        style=styles,
        clip=kwargs.pop('clip', True)
    ).compose(**kwargs)

    return drawing


def proj(_, minx, miny, maxx, maxy, project=None):
    '''Return a transverse mercator projection for the given bounds'''
    prj = projection.generatecrs(minx, miny, maxx, maxy, project)
    return prj + '\n'
