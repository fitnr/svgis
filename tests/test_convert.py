#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
import functools
import collections
from svgis import convert


class ConvertTestCase(unittest.TestCase):

    def test_rect(self):
        pass

    def test_updatebounds(self):
        bounds1 = (None, 0.1, None, 1.1)
        bounds2 = (0.2, 0.2, 1.2, 1.2)
        bounds3 = (0.1, 0.3, 1.5, 1.1)

        self.assertSequenceEqual(convert.updatebounds(bounds1, bounds2), (0.2, 0.1, 1.2, 1.2))
        self.assertSequenceEqual(convert.updatebounds(bounds3, bounds2), (0.1, 0.2, 1.5, 1.2))

    def testConvertBbox(self):
        bounds = (-100, -100, 100, 100)

        assert convert.extend_bbox(bounds, ext=100) == (-200, -200, 200, 200)
        assert convert.extend_bbox(bounds, ext=10) == (-110, -110, 110, 110)

    def testSimplify(self):
        a = convert.simplifier(None)
        assert a.__name__ == '<lambda>'
        assert isinstance(a, collections.Callable)

        b = convert.simplifier(100)
        assert b.__name__ == '<lambda>'
        assert isinstance(b, collections.Callable)

        c = convert.simplifier(50)

        try:
            import visvalingamwyatt
            assert isinstance(c, functools.partial)
        except ImportError:
            assert c.__name__ == '<lambda>'

    def test_bbox_covers(self):
        b1 = (0, 0, 10, 10)
        b2 = (0, 0, 20, 10)
        b3 = (0, 0, 5, 11)

        assert convert.bbox_covers(b1, b2) is False
        assert convert.bbox_covers(b2, b1) is True
        assert convert.bbox_covers(b1, b3) is False
        assert convert.bbox_covers(b3, b1) is False
        assert convert.bbox_covers(b3, b3) is True
