#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

from __future__ import unicode_literals
import unittest
import functools
from svgis import convert


class ConvertTestCase(unittest.TestCase):

    def test_rect(self):
        pass

    def test_updatebounds(self):
        bounds1 = (None, 0.1, None, 1.1)
        bounds2 = (0.2, 0.2, 1.2, 1.2)
        bounds3 = (0.1, 0.3, 1.5, 1.1)
        bounds4 = (0.05, 0.4, float('inf'), 1.2)
        bounds5 = (0.05, -1 * float('inf'), 1.4, 1.2)

        self.assertSequenceEqual(convert.updatebounds(bounds1, bounds2), (0.2, 0.1, 1.2, 1.2))
        self.assertSequenceEqual(convert.updatebounds(bounds3, bounds2), (0.1, 0.2, 1.5, 1.2))
        self.assertSequenceEqual(convert.updatebounds(bounds3, bounds4), (0.05, 0.3, 1.5, 1.2))
        self.assertSequenceEqual(convert.updatebounds(bounds3, bounds5), (0.05, 0.3, 1.5, 1.2))

    def testConvertBbox(self):
        bounds = (-100, -100, 100, 100)

        self.assertSequenceEqual(convert.extend_bbox(bounds, ext=100), (-200, -200, 200, 200))
        self.assertSequenceEqual(convert.extend_bbox(bounds, ext=10), (-110, -110, 110, 110))

    def testSimplify(self):
        a = convert.simplifier(None)
        assert a is None

        b = convert.simplifier(100)
        assert b is None

        c = convert.simplifier(50)

        try:
            import visvalingamwyatt
            assert isinstance(c, functools.partial)
        except ImportError:
            assert c is None

    def test_bbox_covers(self):
        b1 = (0, 0, 10, 10)
        b2 = (0, 0, 20, 10)
        b3 = (0, 0, 5, 11)

        self.assertFalse(convert.bbox_covers(b1, b2))
        self.assertTrue(convert.bbox_covers(b2, b1))
        self.assertFalse(convert.bbox_covers(b1, b3))
        self.assertFalse(convert.bbox_covers(b3, b1))
        self.assertTrue(convert.bbox_covers(b3, b3))

    def testbounds_to_ring(self):
        fix=[
            (0, 0), (0, 0.6), (0, 1.2), (0, 1.7999999999999998), (0, 2.4), (0, 3.0),
            (0, 3.6), (0, 4.2), (0, 4.8), (0, 5.3999999999999995), (0, 5.999999999999999),
            (0.6, 6), (1.2, 6), (1.7999999999999998, 6), (2.4, 6), (3.0, 6), (3.6, 6), (4.2, 6),
            (4.8, 6), (5.3999999999999995, 6), (5.999999999999999, 6), (6, 5.999999999999999),
            (6, 5.3999999999999995), (6, 4.8), (6, 4.2), (6, 3.6), (6, 3.0), (6, 2.4), (6, 1.7999999999999998),
            (6, 1.2), (6, 0.6), (6, 0), (5.999999999999999, 0), (5.3999999999999995, 0), (4.8, 0), (4.2, 0),
            (3.6, 0), (3.0, 0), (2.4, 0), (1.7999999999999998, 0), (1.2, 0), (0.6, 0), (0, 0)
        ]

        r=convert.bounds_to_ring(0, 0, 6, 6)
        self.assertSequenceEqual(r, fix)


if __name__ == '__main__':
    unittest.main()
