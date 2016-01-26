#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

from __future__ import unicode_literals
import unittest
import os
from xml.dom import minidom
from svgis import svgis


class MapTestCase(unittest.TestCase):
    projection = '+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
    bounds = (-124.0, 20.5, -64.0, 49.0)
    fixture = 'tests/test_data/test.svg'
    shp = 'tests/test_data/cb_2014_us_nation_20m.shp'
    css = 'polygon{fill:green}'

    def testMapWithStyle(self):
        result = svgis.map(
            self.shp, style=self.css, scale=1000, project=self.projection, bounds=self.bounds, clip=None)
        self.assertIn(self.css, result)

        style = 'tmp.css'
        with open(style, 'w') as w:
            w.write(self.css)

        try:
            result = svgis.map(
                self.shp, style=style, scale=1000, project=self.projection, bounds=self.bounds, clip=None)
            self.assertIn(self.css, result)

        finally:
            os.remove('tmp.css')

    def testMap(self):
        a = svgis.map(self.shp, scale=1000, project=self.projection, bounds=self.bounds, clip=False)

        result = minidom.parseString(a).getElementsByTagName('svg').item(0)
        fixture = minidom.parse(self.fixture).getElementsByTagName('svg').item(0)

        result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
        fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

        for r, f in zip(result_vb, fixture_vb):
            self.assertAlmostEqual(r, f, 5)

    def testMapProjFile(self):
        a = svgis.map(self.shp, scale=1000, project='tests/test_data/test.proj4', bounds=self.bounds, clip=False)

        result = minidom.parseString(a).getElementsByTagName('svg').item(0)
        fixture = minidom.parse(self.fixture).getElementsByTagName('svg').item(0)

        result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
        fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

        for r, f in zip(result_vb, fixture_vb):
            self.assertAlmostEqual(r, f, 5)

if __name__ == '__main__':
    unittest.main()
