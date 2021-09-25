# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest
import logging
from os import path
from xml.dom import minidom

from svgis import svgis

EPSG3528 = {'init': 'epsg:3528', 'no_defs': True}
# logging.getLogger('svgis').setLevel(logging.DEBUG)

class ProjectionDrawTestCase(unittest.TestCase):

    bounds = {
        # IL E (ft)
        2790: (347026, 556571, 364500, 592793),
        # NAD 83
        4269: (-87.8, 41.7, -87.5, 41.9),
    }

    def setUp(self):
        self.files = [
            path.join(path.dirname(__file__), 'fixtures', 'chicago_bounds_2790.json'),
            path.join(path.dirname(__file__), 'fixtures', 'cook_bounds_4269.json'),
        ]

        svgis.STYLE = ''

    def testDrawWithReProjection(self):
        s = svgis.SVGIS(self.files, self.bounds[2790], out_crs=EPSG3528, scalar=100)
        svg = s.compose()

        self.assertIn('points', svg)
        i = svg.index('points')
        self.assertIn('points', svg[i:])

        polygons = minidom.parseString(svg).getElementsByTagName('polygon')

        self.assertEqual(len(polygons), 2)

        self.assertIn('points', dict(polygons[0].attributes.items()))
        self.assertIn('points', dict(polygons[1].attributes.items()))

    def testDrawWithReProjectionRepeat(self):
        s = svgis.SVGIS(self.files[1], self.bounds[4269], out_crs=EPSG3528, scalar=100)
        s.compose()
        u = s.compose()
        self.assertIn('points', u)
        i = u.index('points')
        self.assertIn('points', u[i:])

    def testDrawWithSameProjection(self):
        s = svgis.SVGIS(self.files, crs=2790)
        a = s.compose()
        self.assertIn('points', a)
        i = a.index('points')
        self.assertIn('points', a[i:])


if __name__ == '__main__':
    unittest.main()
