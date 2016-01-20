"""Draw a geometries elements as SVG"""
# -*- coding: utf-8 -*-
from __future__ import division, print_function
try:
    import numpy as np
except ImportError:
    pass
import svgwrite
import fionautil.measure
from .clip import clip
from .errors import SvgisError

def applyid(multifunc):
    '''
    This decorator applies the ID attribute to the group that
    contains multi-part geometries, rather than the elements of the group.
    '''

    def func(coordinates, **kwargs):
        ID = kwargs.pop('id', None)

        result = _group(multifunc(coordinates, **kwargs))

        if ID:
            result.attribs['id'] = ID

        return result

    return func


def _round_pt(pt, precision):
    return round(pt[0], precision), round(pt[1], precision)


def _round_ring(ring, precision):
    try:
        np.round(coordinates, precision)
    except NameError:
        return [_round_pt(pt, precision) for pt in ring]


def linestring(coordinates, precision=3, **kwargs):
    coordinates = _round_ring(coordinates, precision)
    return svgwrite.shapes.Polyline(coordinates, **kwargs)


@applyid
def multilinestring(coordinates, **kwargs):
    return [linestring(coords, **kwargs) for coords in coordinates]


def lines(geom, **kwargs):
    if geom['type'] == 'LineString':
        return linestring(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiLineString':
        return multilinestring(geom['coordinates'], **kwargs)


def path(coordinates, **kwargs):
    return svgwrite.path.Path(['M'] + coordinates, **kwargs)


def polygons(geom, **kwargs):
    '''Draw polygon(s) in a feature. transform is a function to operate on coords.
    Draws first ring clockwise, and subsequent ones counter-clockwise.
    '''
    if geom['type'] == 'Polygon':
        return polygon(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiPolygon':
        return multipolygon(geom['coordinates'], **kwargs)


def _round_polygon_coordinates(coordinates, precision):
    # Drop possible Z coordinates and round. Two tracks here: numpy style and without-numpy style.
    try:
        return [np.round(np.array(ring)[:, 0:2], precision) for ring in coordinates]

    except NameError:
        return [_round_ring(coordinates, precision) for ring in coordinates]


def polygon(coordinates, precision=3, **kwargs):
    '''Draw an svg polygon based on coordinates.'''
    coordinates = _round_polygon_coordinates(coordinates, precision)

    if len(coordinates) == 1:
        return svgwrite.shapes.Polygon(coordinates[0], **kwargs)

    # This is trickier because drawing holes in SVG.
    # We go clockwise on the first ring, then counterclockwise
    if fionautil.measure.counterclockwise(coordinates[0]):
        coordinates[0] = coordinates[0][::-1]

    if 'class_' in kwargs:
        class_ = 'polygon ' + kwargs.pop('class_')
    else:
        class_ = 'polygon'

    pth = path(list(coordinates[0]) + ['z'], fill_rule='evenodd', class_=class_, **kwargs)

    for ring in coordinates[1:]:
        # make all interior run the counter-clockwise
        if fionautil.measure.clockwise(ring):
            ring = ring[::-1]

        pth.push(['M'] + list(ring) + ['z'])

    return pth


@applyid
def multipolygon(coordinates, **kwargs):
    return [polygon(coords, **kwargs) for coords in coordinates]


def points(geom, **kwargs):
    kwargs['r'] = kwargs.get('r', 1)

    if geom['type'] == 'Point':
        return point(geom['coordinates'], **kwargs)

    elif geom['type'] == 'MultiPoint':
        return multipoint(geom['coordinates'], **kwargs)


def point(coordinates, precision=3, **kwargs):
    try:
        pt = coordinates.pop()
    except (AttributeError, TypeError):
        pt = coordinates

    return svgwrite.shapes.Circle(center=_round_pt(pt, precision), **kwargs)


@applyid
def multipoint(coordinates, **kwargs):
    return [point((pt[0], pt[1]), **kwargs) for pt in coordinates]


def geometry(geom, bbox=None, **kwargs):
    '''
    Draw a geometry. Will return either a single geometry or a group.
    :geom object A GeoJSON-like geometry object
    :bbox tuple An optional bounding minimum bounding box
    :kwargs object keyword args to be passed onto svgwrite. Things like class_, id, style, etc.
    '''
    if bbox:
        geom = clip(geom, bbox)

    if geom['type'] in ('Point', 'MultiPoint'):
        return points(geom, **kwargs)

    elif geom['type'] in ('LineString', 'MultiLineString'):
        return lines(geom, **kwargs)

    elif geom['type'] in ('Polygon', 'MultiPolygon'):
        return polygons(geom, **kwargs)

    else:
        raise SvgisError("Can't draw features like this: {}".format(geom['type']))


def feature(feat, **kwargs):
    '''Draw a feature.'''
    return geometry(feat['geometry'], **kwargs)


def _group(elements, **kwargs):
    '''Group a list of svgwrite elements. Won't group one element.'''
    if len(elements) == 1:
        return elements[0]

    g = svgwrite.container.Group(fill_rule="evenodd", **kwargs)

    for e in elements:
        g.add(e)

    return g


def group(features, **kwargs):
    '''Return a group with features drawn into it.'''
    return _group([feature(f, **kwargs) for f in features])
