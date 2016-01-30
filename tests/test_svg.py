#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest
from xml.dom import minidom
from svgis import style, svg

try:
    basestring
except NameError:
    basestring = str


class SvgTestCase(unittest.TestCase):

    def setUp(self):
        self.file = 'tests/test_data/test.svg'
        self.newstyle = 'stroke {color:red;}'

    def test_rescale(self):
        new = style.rescale(self.file, 100)

        g = minidom.parseString(new).getElementsByTagName('g')[0]
        assert 'scale(100)' in g.attributes.get('transform').value

    def test_create(self):
        s = svg.drawing((100, 100), [])
        assert isinstance(s, basestring)

        s = svg.drawing((100, 100), [])
        assert isinstance(s, basestring)

        s = svg.drawing((100, 100), [], style=self.newstyle)

        assert self.newstyle in s

    def testviewbox(self):
        vb = svg.setviewbox([1, 1, 1, 1])
        assert 'viewBox' in vb

    def testSetGroup(self):
        g = svg.group()
        self.assertIsInstance(g, basestring)

        g = svg.group(transform="translate(10,10)")
        self.assertIn('transform="translate(10,10)"', g)

        g = svg.group(transform="scale(10)")
        assert 'transform="scale(10)"' in g

    def testAttribs(self):
        args = {
            'transform': 'translate(10, 10)',
            'fill': 'black'
        }
        assert 'transform="translate(10, 10)"' in svg.toattribs(**args)
        assert 'fill="black"' in svg.toattribs(**args)

    def testDrawCircle(self):
        point = svg.circle((0.0, 0.0), r=2)
        assert isinstance(point, basestring)
        assert 'r="2"' in point
        assert 'cy="0.0"' in point
        assert 'cx="0.0"' in point

    def testDrawPath(self):
        coordinates = [
            (0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0), 'M',
            (4.0, 4.0), (4.0, 5.0), (5.0, 5.0), (5.0, 4.0), (4.0, 4.0), 'Z'
        ]

        path = svg.path(coordinates)
        assert isinstance(path, basestring)
        assert ' M ' in path
        assert 'Z"' in path
        assert '10.0,0.0' in path
        

if __name__ == '__main__':
    unittest.main()
