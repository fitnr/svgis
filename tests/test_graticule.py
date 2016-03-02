#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest
from svgis import graticule


class GraticuleTestCase(unittest.TestCase):

    def testCRS(self):
        g = graticule.graticule((16.34, -34.81, 32.83, -22.09), step=10000, crs='utm')
        a = next(g)
        assert isinstance(a, dict)

    def testErr(self):
        with self.assertRaises(ValueError):
            g = graticule.graticule((16.34, -34.81, 32.83, -22.09), step=10000, crs='file')
            next(g)

    def test_feature(self):
        g = graticule._feature(0, [1, 2, 3])
        assert g['geometry'] == {
                'type': 'LineString',
                'coordinates': [1, 2, 3]
            }
        assert g['type'] == 'Feature'
        assert g['id'] ==  0


    def test_layer(self):
        a = graticule.layer([0, 0, 5, 5], 1)
        assert isinstance(a, dict)
        assert isinstance(a['features'], list)
        try:
            self.assertIsInstance(a['features'][0]['geometry']['coordinates'], list)
        except AssertionError:
            self.assertIsInstance(a['features'][0]['geometry']['coordinates'], zip)

    def testgraticule(self):
        g = graticule.graticule((0, 0, 2, 2), 1)

        fixture1 = [(0, i / 2.) for i in range(9)]
        fixture2 = [(1, i / 2.) for i in range(9)]

        self.assertSequenceEqual(list(next(g).get('geometry').get('coordinates')), fixture1)
        self.assertSequenceEqual(list(next(g).get('geometry').get('coordinates')), fixture2)


if __name__ == '__main__':
    unittest.main()
