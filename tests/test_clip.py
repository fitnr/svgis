#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
from svgis import clip
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
                "coordinates": [[(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)]]
            }
            coords = {
                "type": "Polygon",
                "coordinates": self.coords
            }

            b = shapely.geometry.shape(bounds)
            c = shapely.geometry.shape(coords)
            i = b.intersection(c)

            result = shapely.geometry.mapping(i)
            self.assertSequenceEqual(result['coordinates'], self.expected)

        def testClip(self):
            clipped = clip.clip({"type": "Polygon", "coordinates": self.coords}, self.bounds)
            self.assertSequenceEqual(clipped['coordinates'], self.expected)

        def testClipGeometry(self):
            geometry = {"type": "Polygon", "coordinates": self.coords}
            clipped = clip.clip(geometry, self.bounds)

            self.assertSequenceEqual(set(self.expected), set(clipped['coordinates']))

        def testExpand(self):
            expanded = clip.expand(self.gen)

            try:
                expanded = expanded.tolist()
            except AttributeError:
                pass

            self.assertSequenceEqual([tuple(x) for x in expanded], self.coords[0])

        def testExpandGeometry(self):
            geom = {
                "type": "LineString",
                "coordinates": self.gen
            }

            expanded = clip.expand_geom(geom)

            try:
                expanded['coordinates'] = expanded['coordinates'].tolist()
            except AttributeError:
                pass

            self.assertSequenceEqual([tuple(x) for x in expanded['coordinates']], self.coords[0])

        def testStrangeGeometry(self):
            with self.assertRaises(NotImplementedError):
                clip.expand_geom({"type": "GeometryCollection", "coordinates": self.coords})

except ImportError:
    class EmptyTestCase(unittest.TestCase):

        def setUp(self):
            self.bounds = (1, 1, 9, 9)
            self.coords = [[(2, 2), (100, 2), (11, 11), (12, 12), (2, 10), (2, 2)]]
            self.expected = [((2.0, 9.0), (9.0, 9.0), (9.0, 2.0), (2.0, 2.0), (2.0, 9.0))]
            self.gen = (x for x in self.coords[0])

        def testClip(self):
            geometry = {"type": "Polygon", "coordinates": self.coords}
            assert clip.clip(geometry, self.bounds) == geometry

        def testStrangeGeometry(self):
            with self.assertRaises(NotImplementedError):
                clip.expand_geom({"type": "GeometryCollection", "coordinates": self.coords})


if __name__ == '__main__':
    unittest.main()
