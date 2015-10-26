# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>
from os import path
import json
try:
    from lxml import etree as ElementTree
except ImportError:
    from xml.etree import ElementTree
from ..scale import scale


def base(filename):
    return ''.join(path.basename(filename).split(path.extsep)[:-1])


def wrapper(filename, fmt=None):
    '''
    return either an XML wrapper or a JSON wrapper
    :filename string A file containing xml or json flavor OSM data
    :fmt string optionally 'json' or 'xml'
    '''
    if fmt == 'xml' or filename[-4:] == '.xml':
        return OsmWrapperXML(filename)

    if fmt == 'json' or filename[-5:] == '.json':
        return OsmWrapperJSON(filename)

    # Try reading file
    try:
        first_line = open(filename).readline()

    except IOError:
        first_line = filename[:100]

    if 'xml' in first_line:
        return OsmWrapperXML(filename)
    else:
        return OsmWrapperJSON(filename)


class OsmWrapper(object):

    _nodes = None

    def get_bounds(self):
        '''Calculate the bounds of an osm file or element'''
        lons, lats = zip(*[(n.get('lon'), n.get('lat')) for n in self.nodes])

        return float(min(lons)), float(min(lats)), float(max(lons)), float(max(lats))

    @property
    def nodes(self):
        return self._nodes

    def find_id(self, *_):
        raise NotImplementedError

    def membergeometry(self, geometry, member, project, scalar, bounds):
        way = self.find_id(member.get('ref'), 'way')
        coordinates = self.waycoordinates(way, project, scalar, bounds)

        if coordinates is None:
            return None

        if member.get('role') == 'outer':
            geometry['coordinates'].append([coordinates])
        else:
            try:
                geometry['coordinates'][-1].append(coordinates)
            except IndexError:
                # FIXME: This has to be a lot more complicated.
                pass

    def waygeometry(self, way, project, scalar, bounds=None):
        '''Draw a way as a Polygon or LineString'''
        scalar = scalar or 1

        coordinates = self.waycoordinates(way, project, scalar, bounds)

        if coordinates is None:
            return None

        geometry = {
            'coordinates': coordinates
        }

        if geometry['coordinates'][0] == geometry['coordinates'][-1]:
            geometry['type'] = 'Polygon'
            geometry['coordinates'] = [geometry['coordinates']]

        else:
            geometry['type'] = 'LineString'

        return geometry

    def waycoordinates(self, way, project, scalar, bounds=None):
        '''Return x and y coordinates that make up a way'''

        cx, cy = [], []
        for nd in way.findall('nd'):
            node = self.find_id(nd.get('ref'), 'node')
            cx.append(float(node.get('lon')))
            cy.append(float(node.get('lat')))

        # check for intersection with bounds
        if bounds:
            minx, miny, maxx, maxy = bounds

            if all(x < minx for x in cx) or all(y < miny for y in cy) or all(x > maxx for x in cx) or all(y > maxy for y in cy):
                return None

        px, py = project(cx, cy)
        return scale(zip(px, py), scalar)


class OsmWrapperXML(OsmWrapper):

    """Convenience methods for abstracting away dealing with OSM XML"""

    id = None

    def __init__(self, osmfile):
        if isinstance(osmfile, str):
            self.root = ElementTree.parse(osmfile).getroot()
            self.id = base(osmfile)
        else:
            self.root = osmfile

        self._nodes = self.root.findall('node')

    def find_id(self, ID, tipe):
        return self.root.find(tipe + '[@id="' + ID + '"]')

    def relationgeometry(self, relation, project, scalar, bounds=None):
        '''Draw a relation as a MultiPolygon geometry'''
        geometry = {
            'type': 'MultiPolygon',
            'coordinates': []
        }

        for member in relation.iterfind('member'):
            self.membergeometry(geometry, member, project, scalar, bounds)

        return geometry

    def geometries(self, project, scalar, bounds):
        '''
        Return all ways, including relations but not doubling up at all.
        '''
        # collect all relations with type == multipolygon
        way_blacklist = []
        scalar = scalar or 1

        for relation in self.root.iter('relation'):
            try:
                if relation.find('tag[@k="type"]').get('v') == 'multipolygon':
                    way_blacklist = way_blacklist + [m.get('ref') for m in relation.iter('member')]
                    yield self.relationgeometry(relation, project, scalar, bounds)

            except AttributeError:
                continue

        # collect all ways not included in this collection
        for way in self.root.iter('way'):
            if way.get('id') in way_blacklist:
                continue

            yield self.waygeometry(way, project, scalar, bounds)


class OsmWrapperJSON(OsmWrapper):

    """Convenience methods for abstracting away dealing with OSM JSON"""

    id = None

    def __init__(self, jsonfile):
        '''
        :jsonfile string/object Path to a JSON-flavor OSM file, JSON OSM string, or an object
        '''
        try:
            osm = json.load(jsonfile)
            self.id = base(jsonfile)
        except IOError:
            try:
                osm = json.loads(jsonfile)
            except TypeError:
                # Assume we were actually passed a JSON object
                osm = jsonfile

        self.root = osm['elments']
        self._nodes = [x for x in self.root if x['type'] == 'node']

    def find_id(self, ID, _):
        return [x for x in self.root if x['id'] == ID][0]

    def relationgeometry(self, relation, project, scalar, bounds=None):
        '''Draw a relation as a MultiPolygon geometry'''
        geometry = {
            'type': 'MultiPolygon',
            'coordinates': []
        }

        for member in relation['members']:
            self.membergeometry(geometry, member, project, scalar, bounds)

        return geometry

    def geometries(self, project, bounds=None, scalar=None):
        blacklist = []
        scalar = scalar or 1

        for x in self.root:
            if x['type'] != 'relation' or x.get('tags', {}).get('type') != 'multipolygon':
                continue
            blacklist = blacklist + [w['ref'] for w in x['members']]
            yield self.relationgeometry(x, project, scalar, bounds)

        for w in self.root:
            if w['type'] != 'way' or w['id'] in blacklist:
                continue
            yield self.waygeometry(w, project, scalar, bounds)
