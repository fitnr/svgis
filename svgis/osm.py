"""Draw OSM geometries as SVG"""
# -*- coding: utf-8 -*-
from __future__ import division, print_function
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


def draw_way(root, way, **kwargs):
    geometry = {'coordinates': []}

    nodes = way.findall('nd')

    for ref in nodes:
        node = root.find('node[@id="' + ref.get('ref') + '"]')
        geometry['coordinates'].append((float(node.get('x')), float(node.get('y'))))

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

    project(osm, scalar, out_crs)

    group = svgwrite.container.Group()

    for way in osm.findall('way'):
        for elem in draw_way(osm, way, **kwargs):
            group.add(elem)

    return group


def project(osm, scalar=None, out_crs=None):
    nodeinfo = [(n.get('id'), float(n.get('lon')), float(n.get('lat'))) for n in osm.findall('node')]
    ids, lons, lats = zip(*nodeinfo)

    scalar = scalar or 1

    if out_crs is None:
        midx = (max(lons) + min(lons)) / 2
        midy = (max(lats) + min(lats)) / 2

        out_crs = projection.utm_proj4(midx, midy)

    xs, ys = transform('EPSG:4269', out_crs, lons, lats)

    scaled = scale(zip(xs, ys), scalar)

    for i, (x, y) in zip(ids, scaled):
        node = osm.find('node[@id="' + i + '"]')
        node.attrib['x'] = x
        node.attrib['y'] = y
