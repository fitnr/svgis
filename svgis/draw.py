"""Draw a geometries elements as SVG"""
# -*- coding: utf-8 -*-
from __future__ import division, print_function
from itertools import chain
try:
    import numpy as np
except ImportError:
    pass
import svgwrite
import fionautil.measure


def linestring(coordinates, precision=3, **kwargs):
    try:
        np.round(coordinates, precision)
    except NameError:
        coordinates = [(round(pt[0], precision), round(pt[1], precision)) for pt in coordinates]

    return svgwrite.shapes.Polyline(coordinates, **kwargs)


def multilinestring(coordinates, **kwargs):
    return [linestring(coords, **kwargs) for coords in coordinates]


def lines(geom, **kwargs):
    if geom['type'] == 'LineString':
        return [linestring(geom['coordinates'], **kwargs)]

    elif geom['type'] == 'MultiLineString':
        return multilinestring(geom['coordinates'], **kwargs)


def path(coordinates, **kwargs):
    return svgwrite.path.Path(['M'] + coordinates, **kwargs)


def polygons(geom, **kwargs):
    '''Draw polygon(s) in a feature. transform is a function to operate on coords.
    Draws first ring clockwise, and subsequent ones counter-clockwise
    '''
    if geom['type'] == 'Polygon':
        return [polygon(geom['coordinates'], **kwargs)]

    elif geom['type'] == 'MultiPolygon':
        return multipolygon(geom['coordinates'], **kwargs)


def polygon(coordinates, precision=3, **kwargs):
    '''Draw an svg polygon based on coordinates.'''
    # Drop possible Z coordinates and round. Two tracks here: numpy style and without-numpy style.
    try:
        coordinates = [np.round(np.array(ring)[:, 0:2], precision) for ring in coordinates]

    except NameError:
        coordinates = [[(round(pt[0], precision), round(pt[1], precision)) for pt in ring] for ring in coordinates]

    if len(coordinates) == 1:
        return svgwrite.shapes.Polygon(coordinates[0], **kwargs)

    # This is trickier because drawing holes in SVG.
    # We go clockwise on the first ring, then counterclockwise
    if fionautil.measure.counterclockwise(coordinates[0]):
        coordinates[0] = coordinates[0][::-1]

    pth = path(list(coordinates[0]) + ['z'], fill_rule='evenodd', class_='polygon', **kwargs)

    for ring in coordinates[1:]:
        # make all interior run the counter-clockwise
        if fionautil.measure.clockwise(ring):
            ring = ring[::-1]

        pth.push(['M'] + list(ring) + ['z'])

    return pth


def multipolygon(coordinates, **kwargs):
    return [polygon(coords, **kwargs) for coords in coordinates]


def points(geom, **kwargs):
    kwargs['r'] = kwargs.get('r', 1)

    if geom['type'] == 'Point':
        return [point(geom['coordinates'], **kwargs)]

    elif geom['type'] == 'MultiPoint':
        return points(geom['coordinates'], **kwargs)


def point(coordinates, precision=3, **kwargs):
    try:
        pt = coordinates.pop()
    except (AttributeError, TypeError):
        pt = coordinates

    center = (round(pt[0], precision), round(pt[1], precision))

    return svgwrite.shapes.Circle(center=center, **kwargs)


def multipoint(coordinates, **kwargs):
    return [point((pt[0], pt[1]), **kwargs) for pt in coordinates]


def geometry(geom, **kwargs):
    '''Draw a geometry'''

    if geom['type'] == 'Point':
        return points(geom, **kwargs)

    elif geom['type'] in 'MultiPoint':
        return multipoint(geom, **kwargs)

    elif geom['type'] in ('LineString', 'MultiLineString'):
        return lines(geom, **kwargs)

    elif geom['type'] in ('Polygon', 'MultiPolygon'):
        return polygons(geom, **kwargs)

    else:
        raise ValueError("Can't draw features like this: {}".format(geom['type']))


def feature(feat, **kwargs):
    '''Draw a feature'''
    return geometry(feat['geometry'], **kwargs)


def group(features):
    '''Return a group with features drawn into it'''
    g = svgwrite.container.Group(fill_rule="evenodd")

    elems = [feature(f) for f in features]

    for e in chain(*elems):
        g.add(e)

    return g
