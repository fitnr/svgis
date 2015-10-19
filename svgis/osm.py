# -*- coding: utf-8 -*-

"""Draw OSM geometries as SVG"""

from __future__ import division, print_function
try:
    from lxml.etree import ElementTree
except ImportError:
    from xml.etree import ElementTree
import svgwrite
from fiona.transform import transform
from . import projection
from .scale import scale
from . import draw as svgisdraw


def get_root(osmfile):
    if type(osmfile) == str:
        return ElementTree.parse(osmfile).getroot()
    else:
        return osmfile


def bounds(osmfile):
    '''Calculate the bounds of an osm file or element'''
    osm = get_root(osmfile)
    lons, lats = zip(*[(n.get('lon'), n.get('lat')) for n in osm.findall('node')])

    return float(min(lons)), float(min(lats)), float(max(lons)), float(max(lats))


def draw_way(root, way, project, **kwargs):
    """Draw an OSM way as an svgwrite geometry."""
    scalar = kwargs.get('scalar', 1)

    nodes = way.findall('nd')
    cx, cy = [], []

    for ref in nodes:
        node = root.find('node[@id="' + ref.get('ref') + '"]')
        cx.append(float(node.get('lon')))
        cy.append(float(node.get('lat')))

    px, py = project(cx, cy)

    geometry = {
        'coordinates': scale(zip(px, py), scalar)
    }

    tipe = way.find('tag[@key="type"]')

    if tipe and tipe.get('v', None) == 'multipolygon':
        geometry['type'] = 'MultiPolygon'

    elif geometry['coordinates'][0] == geometry['coordinates'][-1]:
        geometry['type'] = 'Polygon'
        geometry['coordinates'] = [geometry['coordinates']]

    else:
        geometry['type'] = 'LineString'

    return svgisdraw.geometry(geometry, **kwargs)


def draw(osmfile, scalar=None, out_crs=None, **kwargs):
    """Draw ways in a OSM file"""
    osm = get_root(osmfile)

    out_crs = make_projection(osm, out_crs)
    project = lambda xs, ys: transform('EPSG:4269', out_crs, xs, ys)

    group = svgwrite.container.Group()

    for way in osm.findall('way'):
        for elem in draw_way(osm, way, project, scalar=scalar, **kwargs):
            group.add(elem)

    return group


def make_projection(osm, out_crs=None):
    if out_crs is None:
        coords = [(float(n.get('lon')), float(n.get('lat'))) for n in osm.findall('node')]
        lons, lats = zip(*coords)

        midx = (max(lons) + min(lons)) / 2
        midy = (max(lats) + min(lats)) / 2

        out_crs = projection.utm_proj4(midx, midy)

    return out_crs
