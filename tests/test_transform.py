#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>
# pylint: disable=unused-import
import functools
import unittest

from svgis import transform

try:
    import shapely.geometry

    NO_SHAPELY = False

except ImportError:
    NO_SHAPELY = True
try:
    import visvalingamwyatt

    VW = True
except ImportError:
    VW = False


class ClipTestCase(unittest.TestCase):
    """Test svgis.transform.clip"""

    def setUp(self):
        self.bounds = (1, 1, 9, 9)
        self.coords = [[(2, 2), (100, 2), (11, 11), (12, 12), (2, 10), (2, 2)]]
        self.expected = [((2.0, 9.0), (9.0, 9.0), (9.0, 2.0), (2.0, 2.0), (2.0, 9.0))]
        self.gen = (x for x in self.coords[0])

    @unittest.skipIf(NO_SHAPELY, "Shapely not installed")
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

    @unittest.skipIf(NO_SHAPELY, "Shapely not installed")
    def testClip(self):
        clipped = transform.clip({"type": "Polygon", "coordinates": self.coords}, self.bounds)
        self.assertSequenceEqual(clipped['coordinates'], self.expected)

    @unittest.skipIf(NO_SHAPELY, "Shapely not installed")
    def testClipGeometry(self):
        geometry = {"type": "Polygon", "coordinates": self.coords}
        clipped = transform.clip(geometry, self.bounds)

        self.assertSequenceEqual(set(self.expected), set(clipped['coordinates']))


class SimplifyTestCase(unittest.TestCase):
    """Test svgis.transform.simplifier"""

    def testSimplifyNone(self):
        a = transform.simplifier(None)
        self.assertIsNone(a)

    @unittest.skipIf(not VW, "visvalingamwyatt is not installed")
    def testSimplifyTypeVV(self):
        c = transform.simplifier(50)
        self.assertIsInstance(c, functools.partial)

    @unittest.skipIf(VW, "visvalingamwyatt is installed")
    def testSimplifyTypeNoVW(self):
        c = transform.simplifier(50)
        self.assertIsNone(c)


if __name__ == '__main__':
    unittest.main()
