#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest

from svgis import projection
from svgis.errors import SvgisError
from svgis.utils import DEFAULT_GEOID

SHP = 'tests/fixtures/cb_2014_us_nation_20m.json'


class ProjectionTestCase(unittest.TestCase):
    def testUtm(self):
        assert projection.utm_proj4(-21, 42) == '+proj=utm +zone=27 +north +datum=WGS84 +units=m +no_defs'

        assert projection.utm_proj4(-21, -42) == '+proj=utm +zone=27 +south +datum=WGS84 +units=m +no_defs'

        with self.assertRaises(SvgisError):
            projection.utm_proj4(-200, 100)

    def testLocalTm(self):
        fixture = (
            '+proj=lcc +lon_0=0 +lat_1=0 +lat_2=0 +lat_0=0 '
            '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'
        )
        self.assertEqual(projection.tm_proj4(0, 0, 0), fixture)

    def testGenerateCRS(self):
        bounds = -82.2, 40.1, -78.9, 45.8
        a = projection.generateproj4('utm', bounds=bounds, file_crs=DEFAULT_GEOID)
        self.assertEqual(a, '+proj=utm +zone=17 +north +datum=WGS84 +units=m +no_defs')


if __name__ == '__main__':
    unittest.main()
