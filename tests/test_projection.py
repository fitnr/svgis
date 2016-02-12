#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
from svgis import projection

SHP = 'tests/test_data/cb_2014_us_nation_20m.shp'


class ProjectionTestCase(unittest.TestCase):

    def testUtm(self):
        assert projection.utm_proj4(-21, 42) == '+proj=utm +zone=27 +north +datum=WGS84 +units=m +no_defs'

        assert projection.utm_proj4(-21, -42) == '+proj=utm +zone=27 +south +datum=WGS84 +units=m +no_defs'

        with self.assertRaises(ValueError):
            projection.utm_proj4(-200, 100)

    def testlayer_bounds(self):
        assert projection.layer_bounds(SHP) == (-179.174265, 17.913769, 179.773922, 71.352561)
        fix = (-9183694.888482913, -2282590.8349678256, 9343945.82964409, 10263876.62548214)
        for a in zip(fix, projection.layer_bounds(SHP, 'EPSG:102009')):
            self.assertAlmostEqual(*a)

    def testLocalTm(self):
        fixture = ('+proj=lcc +lon_0=0 +lat_1=0 +lat_2=0 +lat_0=0'
                   '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0'
                   '+units=m +no_defs')
        self.assertEqual(projection.tm_proj4(0, 0, 0), fixture)

    def testTransformBounds(self):
        bounds = (-74, 42, -73, 43)

        with self.assertRaises(TypeError):
            projection.transform_bounds(None, {'init': 'epsg:4269'}, bounds)

        with self.assertRaises(TypeError):
            projection.transform_bounds({'init': 'epsg:4269'}, None, bounds)

        a = projection.transform_bounds({'init': 'epsg:4269'}, {'init': 'epsg:3102'}, bounds)

        fixture = (43332273.50269379, 15584115.894447982, 44004519.424246654, 16320640.928220816)

        for z in zip(a, fixture):
            self.assertAlmostEqual(*z)

    def testGenerateCRS(self):
        bounds = -82.2, 40.1, -78.9, 45.8
        a = projection.generatecrs(*bounds, proj_method='utm')
        self.assertEqual(a, '+proj=utm +zone=17 +north +datum=WGS84 +units=m +no_defs')

if __name__ == '__main__':
    unittest.main()
