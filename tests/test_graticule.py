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
        assert graticule._feature(0, [1, 2, 3]) == {
            'geometry': {
                'type': 'LineString',
                'coordinates': [1, 2, 3]
            },
            'type': 'Feature',
            'id': 0
        }

    def test_layer(self):
        a = graticule.layer([0, 0, 5, 5], 1)
        assert isinstance(a, dict)
        assert isinstance(a['features'], list)
        assert isinstance(a['features'][0]['geometry']['coordinates'], list)

    def testgraticule(self):
        g = graticule.graticule((0, 0, 2, 2), 1)

        assert next(g).get('geometry').get('coordinates') == [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        assert next(g).get('geometry').get('coordinates') == [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)]


if __name__ == '__main__':
    unittest.main()
