#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest
from xml.dom import minidom

import six

from svgis import style, svg


class SvgTestCase(unittest.TestCase):
    def setUp(self):
        self.file = 'tests/fixtures/test.svg'
        self.newstyle = 'stroke {color:red;}'

    def test_rescale(self):
        new = style.rescale(self.file, 100)

        g = minidom.parseString(new).getElementsByTagName('g')[0]
        assert 'scale(100)' in g.attributes.get('transform').value

    def test_create(self):
        s = svg.drawing((100, 100), [])
        self.assertIsInstance(s, six.string_types)

        s = svg.drawing((100, 100), [])
        self.assertIsInstance(s, six.string_types)

        s = svg.drawing((100, 100), [], style=self.newstyle)
        self.assertIn(self.newstyle, s)

    def testGroup(self):
        g = svg.group()
        self.assertIsInstance(g, six.string_types)

        g = svg.group(transform="translate(10,10)")
        self.assertIn('transform="translate(10,10)"', g)

        g = svg.group(transform="scale(10)")
        self.assertIn('transform="scale(10)"', g)

    def testAttribs(self):
        args = {'transform': 'translate(10, 10)', 'fill': 'black'}
        self.assertIn('transform="translate(10, 10)"', svg.toattribs(**args))
        self.assertIn('fill="black"', svg.toattribs(**args))

    def testDrawCircle(self):
        point = svg.circle((0.0, 0.0), r=2)
        self.assertIsInstance(point, six.string_types)
        assert 'r="2"' in point
        self.assertIn('cy="0.0"', point)
        assert 'cx="0.0"' in point

    def testDrawPath(self):
        coordinates = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
            (0.0, 0.0),
            'M',
            (4.0, 4.0),
            (4.0, 5.0),
            (5.0, 5.0),
            (5.0, 4.0),
            (4.0, 4.0),
            'Z',
        ]

        path = svg.path(coordinates)
        self.assertIsInstance(path, six.string_types)
        self.assertIn(' M ', path)
        self.assertIn('Z"', path)
        self.assertIn('10.0,0.0', path)

    def assertPartsIn(self, fixture, test):
        for f in fixture:
            self.assertIn(f, test)

    def testRect(self):
        rect = svg.rect((0, 0), 10, 10)
        self.assertIsInstance(rect, type(''))
        fix = '<rect', 'x="0"', 'y="0"', 'width="10"', 'height="10"', '/>'
        self.assertPartsIn(fix, rect)

    def testLine(self):
        line = svg.line((0, 0), (10, 10))
        assert isinstance(line, type(''))
        fix = '<line', 'x1="0"', 'y1="0"', 'x2="10"', 'y2="10"', '/>'
        self.assertPartsIn(fix, line)

    def testText(self):
        text = svg.text('hi', (2, 2))
        assert isinstance(text, type(''))
        fix = '<text', 'x="2"', 'y="2"', 'hi', '</text>'

        self.assertPartsIn(fix, text)

        text = svg.text('hi', (2.22222, 2.222222), precision=2)
        assert isinstance(text, type(''))
        fix = '<text', 'x="2.22"', 'y="2.22"', 'hi', '</text>'

        self.assertPartsIn(fix, text)


if __name__ == '__main__':
    unittest.main()
