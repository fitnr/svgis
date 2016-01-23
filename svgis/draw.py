"""Draw a geometries elements as SVG"""
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import fionautil.measure
import fionautil.round
from . import clip, svg
from .errors import SvgisError


def applyid(multifunc):
    '''
    This decorator applies the ID attribute to the group that
    contains multi-part geometries, rather than the elements of the group.
    '''

    def func(coordinates, **kwargs):
        ID = kwargs.pop('id', None)
        result = _group(multifunc(coordinates, **kwargs), id=ID)
        return result

    return func


def linestring(coordinates, **kwargs):
    return svg.element('polyline', coordinates, **kwargs)


@applyid
def multilinestring(coordinates, **kwargs):
    return [linestring(coords, **kwargs) for coords in coordinates]


def lines(geom, **kwargs):
    if geom['type'] == 'LineString':
        return linestring(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiLineString':
        return multilinestring(geom['coordinates'], **kwargs)


def polygons(geom, **kwargs):
    '''
    Draw polygon(s) in a feature. transform is a function to operate on coords.
    Draws first ring clockwise, and subsequent ones counter-clockwise.
    '''
    if geom['type'] == 'Polygon':
        return polygon(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiPolygon':
        return multipolygon(geom['coordinates'], **kwargs)


def polygon(coordinates, **kwargs):
    '''Draw an svg polygon based on coordinates.'''
    if len(coordinates) == 1:
        return svg.element('polygon', coordinates[0], **kwargs)

    # This is trickier because drawing holes in SVG.
    # We go clockwise on the first ring, then counterclockwise
    if fionautil.measure.counterclockwise(coordinates[0]):
        coordinates[0] = coordinates[0][::-1]

    if 'class' in kwargs:
        kwargs['class'] = 'polygon ' + kwargs.pop('class')
    else:
        kwargs['class'] = 'polygon'

    instructions = list(coordinates[0]) + ['z']

    for ring in coordinates[1:]:
        # make all interior run the counter-clockwise
        if fionautil.measure.clockwise(ring):
            ring = ring[::-1]

        instructions.extend(['M'] + list(ring) + ['z'])

    pth = svg.path(instructions, fill_rule='evenodd', **kwargs)

    return pth


@applyid
def multipolygon(coordinates, **kwargs):
    return [polygon(coords, **kwargs) for coords in coordinates]


def points(geom, **kwargs):
    kwargs['r'] = kwargs.get('r', 1)

    if geom['type'] == 'Point':
        return svg.circle(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiPoint':
        return multipoint(geom['coordinates'], **kwargs)


@applyid
def multipoint(coordinates, **kwargs):
    return [svg.circle((pt[0], pt[1]), **kwargs) for pt in coordinates]


def geometrycollection(collection, bbox, precision, **kwargs):
    ID = kwargs.pop('id', None)
    geoms = [geometry(g, bbox=bbox, precision=precision, **kwargs) for g in collection['geometries']]
    return _group(geoms, id=ID)


def geometry(geom, bbox=None, precision=3, **kwargs):
    '''
    Draw a geometry. Will return either a single geometry or a group.
    :geom object A GeoJSON-like geometry object. Coordinates must be 2-dimensional.
    :bbox tuple An optional bounding minimum bounding box
    :precision int Rounding precision. precision=None disables rounding.
    :kwargs object keyword args to be passed onto the created elements. (Things like class, id, style, etc).
    '''
    if bbox:
        geom = clip.clip(geom, bbox)

    if precision is not None:
        geom = fionautil.round.geometry(geom, precision)

    if geom['type'] in ('Point', 'MultiPoint'):
        return points(geom, **kwargs)

    elif geom['type'] in ('LineString', 'MultiLineString'):
        return lines(geom, **kwargs)

    elif geom['type'] in ('Polygon', 'MultiPolygon'):
        return polygons(geom, **kwargs)

    elif geom['type'] == 'GeometryCollection':
        return geometrycollection(geom, bbox, precision, **kwargs)

    else:
        raise SvgisError("Can't draw features of type: {}".format(geom['type']))


def _group(elements, **kwargs):
    '''Group a list of elements. Won't group one element.'''
    if len(elements) == 1:
        return elements[0]

    g = svg.group(elements, fill_rule="evenodd", **kwargs)

    return g


def group(geometries, **kwargs):
    '''
    Return a group with geometries drawn into it.
    :geometries Sequence GeoJSON-like geometry dicts.
    '''
    return _group([geometries(g, **kwargs) for g in geometries])
