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

    def testGroup(self):
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
        self.assertIn('cy="0.0"', point)
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
    
    def assertPartsIn(self, fixture, test):
        for f in fixture:
            self.assertIn(f, test)

    def testRect(self):
        rect = svg.rect((0, 0), 10, 10).encode('utf-8')
        fix = '<rect', 'x="0"', 'y="0"', 'width="10"', 'height="10"', '/>'
        self.assertPartsIn(fix, rect)

    def testLine(self):
        line = svg.line((0, 0), (10, 10)).encode('utf-8')
        fix = '<line', 'x1="0"', 'y1="0"', 'x2="10"', 'y2="10"', '/>'
        self.assertPartsIn(fix, line)

    def testText(self):
        text = svg.text('hi', (2, 2))
        fix = '<text', 'x="2"', 'y="2"', 'hi', '</text>'

        self.assertPartsIn(fix, text)

        text = svg.text('hi', (2.22222, 2.222222), precision=2)
        fix = '<text', 'x="2.22"', 'y="2.22"', 'hi', '</text>'

        self.assertPartsIn(fix, text)


if __name__ == '__main__':
    unittest.main()
