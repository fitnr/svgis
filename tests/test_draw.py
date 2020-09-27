#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import re
import unittest

import six

from svgis import draw, errors, svgis


class DrawTestCase(unittest.TestCase):

    properties = {'cat': u'meow', 'dog': 'woof'}

    classes = [u'foo', 'cat']

    lis1 = [
        [-110.6, 35.3],
        [-110.7, 35.5],
        [-110.3, 35.5],
        [-110.2, 35.1],
        [-110.2, 35.8],
        [-110.3, 35.2],
        [-110.1, 35.8],
        [-110.8, 35.5],
        [-110.7, 35.7],
        [-110.1, 35.4],
        [-110.7, 35.1],
        [-110.6, 35.3],
    ]

    lis2 = [
        [-110.8, 35.3],
        [-110.6, 35.4],
        [-110.1, 35.5],
        [-110.1, 35.5],
        [-110.4, 35.2],
        [-110.5, 35.1],
        [-110.5, 35.1],
        [-110.9, 35.8],
        [-110.5, 35.1],
        [-110.8, 35.3],
    ]

    def setUp(self):
        self.multipolygon = {
            "properties": self.properties,
            "geometry": {"type": "MultiPolygon", "id": "MultiPolygon", "coordinates": [[self.lis1], [self.lis2]]},
        }
        self.polygon = {
            "properties": self.properties,
            "geometry": {"type": "Polygon", "id": "Polygon", "coordinates": [self.lis1]},
        }
        self.multilinestring = {
            "properties": self.properties,
            "geometry": {'type': 'MultiLineString', "id": "MultiLineString", 'coordinates': [self.lis2, self.lis2]},
        }
        self.linestring = {
            "properties": self.properties,
            "geometry": {
                'coordinates': self.lis2,
                'type': 'LineString',
                "id": "LineString",
            },
        }
        self.point = {
            "properties": self.properties,
            "geometry": {
                'coordinates': (0.0, 0),
                'type': 'Point',
                "id": "Point",
            },
        }

        self.obj = svgis.SVGIS([])

    def testDrawPoint(self):
        feat = self.obj.feature(self.point, [], classes=self.classes, id_field=None)

        assert isinstance(feat, six.string_types)
        self.assertIn('cat_meow', feat)

    def testDrawLine(self):
        line = draw.lines(self.linestring['geometry'])
        assert isinstance(line, six.string_types)

        feat = self.obj.feature(self.linestring, [], classes=self.classes, id_field=None)

        assert isinstance(feat, six.string_types)
        assert 'cat_meow' in feat

    def testDrawMultiLine(self):
        mls1 = draw.multilinestring(self.multilinestring['geometry']['coordinates'])
        mls2 = draw.lines(self.multilinestring['geometry'])

        assert isinstance(mls1, six.string_types)
        assert isinstance(mls2, six.string_types)

        grp = self.obj.feature(self.multilinestring, [], classes=self.classes, id_field=None)

        assert isinstance(grp, six.string_types)
        assert 'cat_meow' in grp

    def testDrawPolygon(self):
        drawn = draw.polygon(self.polygon['geometry']['coordinates'])
        assert "{},{}".format(*self.lis1[0]) in drawn
        feat = self.obj.feature(self.polygon, [], classes=self.classes, id_field=None)
        assert 'cat_meow' in feat

    def testDrawMultiPolygon(self):
        drawn = draw.multipolygon(self.multipolygon['geometry']['coordinates'])

        assert isinstance(drawn, six.string_types)

    def testDrawMultiPoint(self):
        points = draw.multipoint(self.lis1, id='foo')

        self.assertIn('cy="35.1"', points)
        self.assertIn('cx="-110.6"', points)
        assert re.search(r'<g[^>]*id="foo"', points)

    def testAddClass(self):
        geom = {'coordinates': (0, 0), 'type': 'Point'}
        kwargs = {"class": "boston"}
        point = draw.points(geom, **kwargs)
        self.assertIsInstance(point, six.string_types)

        point = draw.points(geom, **kwargs)
        assert isinstance(point, six.string_types)

    def testDrawPolygonComplicated(self):
        coordinates = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
            [(4.0, 4.0), (4.0, 5.0), (5.0, 5.0), (5.0, 4.0), (4.0, 4.0)],
        ]

        polygon = draw.polygon(coordinates)
        self.assertIsInstance(polygon, six.string_types)
        assert 'class="polygon"' in polygon

        kw = {'class': 'a'}
        assert 'polygon a' in draw.polygon(coordinates, **kw)

    def testUnkownGeometry(self):
        with self.assertRaises(errors.SvgisError):
            draw.geometry({"type": "FooBar", "coordinates": []})

    def testGeometryCollection(self):
        gc = {
            "type": "GeometryCollection",
            "id": "GC",
            "geometries": [
                self.polygon['geometry'],
                self.linestring['geometry'],
                self.point['geometry'],
                self.multipolygon['geometry'],
                self.multilinestring['geometry'],
            ],
        }
        a = draw.geometry(gc, id='cats')
        assert isinstance(a, six.string_types)
        assert 'id="cats"' in a

    def testDrawAndConvertToString(self):
        draw.geometry(self.linestring['geometry'])
        draw.geometry(self.multilinestring['geometry'])
        draw.geometry(self.polygon['geometry'])
        draw.geometry(self.multipolygon['geometry'])


if __name__ == '__main__':
    unittest.main()
