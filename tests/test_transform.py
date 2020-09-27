#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>
import functools
import unittest

from svgis import transform

try:
    import shapely.geometry

    class ClipTestCase(unittest.TestCase):
        def setUp(self):
            self.bounds = (1, 1, 9, 9)
            self.coords = [[(2, 2), (100, 2), (11, 11), (12, 12), (2, 10), (2, 2)]]
            self.expected = [((2.0, 9.0), (9.0, 9.0), (9.0, 2.0), (2.0, 2.0), (2.0, 9.0))]
            self.gen = (x for x in self.coords[0])

        def testShapely(self):
            minx, miny, maxx, maxy = self.bounds
            bounds = {
                "type": "Polygon",
                "coordinates": [[(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)]],
            }
            coords = {"type": "Polygon", "coordinates": self.coords}

            b = shapely.geometry.shape(bounds)
            c = shapely.geometry.shape(coords)
            i = b.intersection(c)

            result = shapely.geometry.mapping(i)
            self.assertSequenceEqual(result['coordinates'], self.expected)

        def testClip(self):
            clipped = transform.clip({"type": "Polygon", "coordinates": self.coords}, self.bounds)
            self.assertSequenceEqual(clipped['coordinates'], self.expected)

        def testClipGeometry(self):
            geometry = {"type": "Polygon", "coordinates": self.coords}
            clipped = transform.clip(geometry, self.bounds)

            self.assertSequenceEqual(set(self.expected), set(clipped['coordinates']))


except ImportError:
    pass


class SimplifyTestCase(unittest.TestCase):
    def testSimplify(self):
        a = transform.simplifier(None)
        self.assertIsNone(a)

        b = transform.simplifier(100)
        self.assertIsNone(b)

        c = transform.simplifier(50)

        try:
            import visvalingamwyatt

            self.assertIsInstance(c, functools.partial)
        except ImportError:
            self.assertIsNone(c)


class ExpandTestCase(unittest.TestCase):
    def setUp(self):
        self.bounds = (1, 1, 9, 9)
        self.coords = [[(2, 2), (100, 2), (11, 11), (12, 12), (2, 10), (2, 2)]]
        self.expected = [((2.0, 9.0), (9.0, 9.0), (9.0, 2.0), (2.0, 2.0), (2.0, 9.0))]
        self.gen = (x for x in self.coords[0])

    def testExpand(self):
        expanded = transform.expand(self.gen)

        try:
            expanded = expanded.tolist()
        except AttributeError:
            pass

        self.assertSequenceEqual([tuple(x) for x in expanded], self.coords[0])

        self.assertSequenceEqual(expanded, transform.expand(expanded))

    def testExpandGeometry(self):
        geom = {"type": "LineString", "coordinates": self.gen}

        expanded = transform.expand_geom(geom)

        try:
            expanded['coordinates'] = expanded['coordinates'].tolist()
        except AttributeError:
            pass

        self.assertSequenceEqual([tuple(x) for x in expanded['coordinates']], self.coords[0])

    def testExpandGeomCollection(self):
        gen = (x for x in self.coords[0])

        GC = {
            "type": "GeometryCollection",
            "geometries": [{"type": "LineString", "coordinates": self.gen}, {"type": "LineString", "coordinates": gen}],
        }
        a = transform.expand_geom(GC)

        assert len(a['geometries']) == 2

        try:
            b = a['geometries'][0]['coordinates'].tolist()

        except AttributeError:
            b = a['geometries'][0]['coordinates']

        self.assertSequenceEqual(b[0], [2, 2])

    def testStrangeGeometry(self):
        with self.assertRaises(NotImplementedError):
            transform.expand_geom({"type": "Magic", "coordinates": [], "geometries": []})


if __name__ == '__main__':
    unittest.main()
