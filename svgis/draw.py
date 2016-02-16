#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

from __future__ import division
import fionautil.measure
from . import clip, svg
from .errors import SvgisError

"""
Draw a geometries elements as SVG
"""


def _applyid(multifunc):
    '''
    This decorator applies the ID attribute to the group that
    contains multi-part geometries, rather than the elements of the group.
    '''

    def func(coordinates, **kwargs):
        ID = kwargs.pop('id', None)
        result = svg.group(multifunc(coordinates, **kwargs), fill_rule="evenodd", id=ID)
        return result

    return func


def linestring(coordinates, **kwargs):
    return svg.polyline(coordinates, **kwargs)


@_applyid
def multilinestring(coordinates, **kwargs):
    return [linestring(coords, **kwargs) for coords in coordinates]


def lines(geom, **kwargs):
    '''
    Draw a LineString or MultiLineString geometry.

    Args:
        geom (object): A GeoJSON-like LineString or MultiLineString geometry object.

    Returns:
        unicode representation of the SVG group or polyline element(s).
    '''
    if geom['type'] == 'LineString':
        return linestring(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiLineString':
        return multilinestring(geom['coordinates'], **kwargs)


def polygons(geom, **kwargs):
    '''
    Draw polygon(s) in a feature. transform is a function to operate on coords.
    Draws first ring clockwise, and subsequent ones counter-clockwise.

    Args:
        geom (object): A GeoJSON-like Polygon or MultiPolygon geometry object.

    Returns:
        unicode representation of the SVG group, path or polygon element.
    '''
    if geom['type'] == 'Polygon':
        return polygon(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiPolygon':
        return multipolygon(geom['coordinates'], **kwargs)


def polygon(coordinates, **kwargs):
    if len(coordinates) == 1:
        return svg.polygon(coordinates[0], **kwargs)

    # This is trickier because drawing holes in SVG.
    # We go clockwise on the first ring, then counterclockwise
    if fionautil.measure.counterclockwise(coordinates[0]):
        coordinates[0] = coordinates[0][::-1]

    kwargs['class'] = ('polygon ' + kwargs.pop('class', '')).strip()

    instructions = ['M'] + list(coordinates[0]) + ['z']

    for ring in coordinates[1:]:
        # make all interior run the counter-clockwise
        if fionautil.measure.clockwise(ring):
            ring = ring[::-1]

        instructions.extend(['M'] + list(ring) + ['z'])

    pth = svg.path(instructions, fill_rule='evenodd', **kwargs)

    return pth


@_applyid
def multipolygon(coordinates, **kwargs):
    return [polygon(coords, **kwargs) for coords in coordinates]


def points(geom, **kwargs):
    '''
    Draw a Point or MultiPoint geometry

    Args:
        geom (object): A GeoJSON-like Point or MultiPoint geometry object.

    Returns:
        unicode representation of the SVG group, or circle element
    '''
    kwargs['r'] = kwargs.get('r', 1)

    if geom['type'] == 'Point':
        return svg.circle(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiPoint':
        return multipoint(geom['coordinates'], **kwargs)


@_applyid
def multipoint(coordinates, **kwargs):
    return [svg.circle((pt[0], pt[1]), **kwargs) for pt in coordinates]


def geometrycollection(collection, bbox, precision, **kwargs):
    ID = kwargs.pop('id', None)
    geoms = [geometry(g, bbox=bbox, precision=precision, **kwargs) for g in collection['geometries']]
    return svg.group(geoms, fill_rule="evenodd", id=ID)


def geometry(geom, bbox=None, precision=None, **kwargs):
    '''
    Draw a geometry. Will return either a single geometry or a group.

    Args:
        geom (object): A GeoJSON-like geometry object. Coordinates must be 2-dimensional.
        bbox (tuple): An optional bounding minimum bounding box
        precision (int): Rounding precision, must be 0 or greater (default: no rounding).
        kwargs (object): keyword args to be passed onto the created elements (e.g. class, id, style).

    Returns:
        unicode representation of SVG element(s) of the given geometry.
    '''
    if bbox:
        geom = clip.clip(geom, bbox)

    if geom['type'] in ('Point', 'MultiPoint'):
        return points(geom, precision=precision, **kwargs)

    elif geom['type'] in ('LineString', 'MultiLineString'):
        return lines(geom, precision=precision, **kwargs)

    elif geom['type'] in ('Polygon', 'MultiPolygon'):
        return polygons(geom, precision=precision, **kwargs)

    elif geom['type'] == 'GeometryCollection':
        return geometrycollection(geom, bbox, precision, **kwargs)

    else:
        raise SvgisError("Can't draw features of type: {}".format(geom['type']))


def group(geometries, **kwargs):
    '''
    Add a list of geometries to a group.

    Args:
        geometries (Sequence): GeoJSON-like geometry dicts.

    Returns:
        unicode representation of the SVG group
    '''
    return svg.group([geometries(g, fill_rule="evenodd", **kwargs) for g in geometries])
