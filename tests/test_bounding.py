#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests on bounding box management."""
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
import unittest

from svgis import bounding, errors


class ConvertTestCase(unittest.TestCase):
    def test_updatebounds(self):
        bounds1 = (None, 0.1, None, 1.1)
        bounds2 = (0.2, 0.2, 1.2, 1.2)
        bounds3 = (0.1, 0.3, 1.5, 1.1)
        bounds4 = (0.05, 0.4, float('inf'), 1.2)
        bounds5 = (0.05, -1 * float('inf'), 1.4, 1.2)

        self.assertSequenceEqual(bounding.update(bounds1, bounds2), (0.2, 0.1, 1.2, 1.2))
        self.assertSequenceEqual(bounding.update(bounds3, bounds2), (0.1, 0.2, 1.5, 1.2))
        self.assertSequenceEqual(bounding.update(bounds3, bounds4), (0.05, 0.3, 1.5, 1.2))
        self.assertSequenceEqual(bounding.update(bounds3, bounds5), (0.05, 0.3, 1.5, 1.2))

    def testConvertBbox(self):
        bounds = (-100, -100, 100, 100)

        self.assertSequenceEqual(bounding.pad(bounds, ext=100), (-200, -200, 200, 200))
        self.assertSequenceEqual(bounding.pad(bounds, ext=10), (-110, -110, 110, 110))

    def test_bbox_covers(self):
        a = (0, 0, 10, 10)
        b = (0, 0, 20, 10)
        c = (0, 0, 5, 11)

        self.assertFalse(bounding.covers(a, b))
        self.assertTrue(bounding.covers(b, a))
        self.assertFalse(bounding.covers(a, c))
        self.assertFalse(bounding.covers(c, a))
        self.assertTrue(bounding.covers(c, c))

    def testbounds_to_ring(self):
        fixture = [
            (0, 0),
            (0, 0.6),
            (0, 1.2),
            (0, 1.7999999999999998),
            (0, 2.4),
            (0, 3.0),
            (0, 3.6),
            (0, 4.2),
            (0, 4.8),
            (0, 5.3999999999999995),
            (0, 5.999999999999999),
            (0.6, 6),
            (1.2, 6),
            (1.7999999999999998, 6),
            (2.4, 6),
            (3.0, 6),
            (3.6, 6),
            (4.2, 6),
            (4.8, 6),
            (5.3999999999999995, 6),
            (5.999999999999999, 6),
            (6, 5.999999999999999),
            (6, 5.3999999999999995),
            (6, 4.8),
            (6, 4.2),
            (6, 3.6),
            (6, 3.0),
            (6, 2.4),
            (6, 1.7999999999999998),
            (6, 1.2),
            (6, 0.6),
            (6, 0),
            (5.999999999999999, 0),
            (5.3999999999999995, 0),
            (4.8, 0),
            (4.2, 0),
            (3.6, 0),
            (3.0, 0),
            (2.4, 0),
            (1.7999999999999998, 0),
            (1.2, 0),
            (0.6, 0),
            (0, 0),
        ]

        r = bounding.ring((0, 0, 6, 6))
        self.assertSequenceEqual(r, fixture)

    def testTransformBounds(self):
        bounds = (-74, 42, -73, 43)

        with self.assertRaises(errors.SvgisError):
            bounding.transform(bounds, in_crs=4269)

        with self.assertRaises(errors.SvgisError):
            bounding.transform(bounds, out_crs=4269)

        a = bounding.transform(bounds, in_crs=4269, out_crs=3102)

        fixture = (43332271.446783714, 15585187.3924282, 44004528.34377961, 16321716.827537995)
        for z in zip(a, fixture):
            self.assertAlmostEqual(*z, places=5)

    def testCheck(self):
        fixture = (1, 1, 2, 2)
        result = bounding.check((2, 2, 1, 1))
        self.assertSequenceEqual(result, fixture)

        result = bounding.check((2, 1, 1, 2))
        self.assertSequenceEqual(result, fixture)

        result = bounding.check((1, 2, 2, 1))
        self.assertSequenceEqual(result, fixture)

        self.assertFalse(bounding.check(None))
        self.assertFalse(bounding.check(object))
        self.assertFalse(bounding.check((1, 2, 3)))
        self.assertFalse(bounding.check((1, 2, 3, None)))


if __name__ == '__main__':
    unittest.main()
