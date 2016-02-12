#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

from os import path
import unittest
from xml.dom import minidom
from svgis import svgis

EPSG3528 = {'init': 'epsg:3528', 'no_defs': True}


class ProjectionDrawTestCase(unittest.TestCase):

    bounds = {
        # IL E (ft)
        2790: (347026, 556571, 364500, 592793),
        # NAD 83
        4269: (-87.8, 41.7, -87.5, 41.9)
    }

    def setUp(self):
        self.files = [
            path.join(path.dirname(__file__), 'test_data', 'chicago_bounds_2790.json'),
            path.join(path.dirname(__file__), 'test_data', 'cook_bounds_4269.json'),
        ]

        svgis.STYLE = ''

    def testDrawWithReProjection(self):
        s = svgis.SVGIS(self.files, self.bounds[2790], out_crs=EPSG3528, scalar=100)
        doc = minidom.parseString(s.compose())
        polygons = doc.getElementsByTagName('polygon')

        assert len(polygons) == 2

        assert 'points' in polygons[0].attributes.items()[0]
        assert 'points' in polygons[1].attributes.items()[0]


    def testDrawWithReProjectionRepeat(self):
        s = svgis.SVGIS(self.files[::-1], self.bounds[4269], out_crs=EPSG3528, scalar=100)
        s.compose()

        s.compose(bounds=(-87.6475, 42.0705, -87.5165, 42.1452))


if __name__ == '__main__':
    unittest.main()
