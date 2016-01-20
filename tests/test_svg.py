# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest
from xml.dom import minidom
from svgis import svg
import svgwrite


class SvgTestCase(unittest.TestCase):

    def setUp(self):
        self.file = 'tests/test_data/test.svg'
        self.newstyle = 'stroke {color:red;}'

    def test_rescale(self):
        new = svg.rescale(self.file, 100)

        g = minidom.parseString(new).getElementsByTagName('g')[0]
        assert 'scale(100)' in g.attributes.get('transform').value

    def test_create(self):
        s = svg.create((100, 100), [])
        assert isinstance(s, svgwrite.drawing.Drawing)

        s = svg.create(100, [])
        assert isinstance(s, svgwrite.drawing.Drawing)

        s = svg.create(100, [], style=self.newstyle)
        assert isinstance(s, svgwrite.drawing.Drawing)
        assert len(s.defs.elements) > 0
        assert self.newstyle in s.defs.elements[0].tostring()

    def testSetGroup(self):
        g = svg.set_group()
        self.assertIsInstance(g, svgwrite.container.Group)

        g = svg.set_group(translate=(10, 10))
        assert g.attribs.get('transform') == "translate(10,10)"

        g = svg.set_group(scale=(10,))
        assert g.attribs.get('transform') == "scale(10)"

        pt = svgwrite.shapes.Circle((0, 0))
        g = svg.set_group(members=[pt])
        self.assertIn('<circle ', g.tostring())

    def testDims(self):
        boundary = (0, 0), (10, 0), (10, 10), (0, 10), (0, 0)
        assert svg.dims(boundary) == (10, 10)
        assert svg.dims(boundary, 10) == (30, 30)

    def testSanitize(self):
        assert svg.sanitize(None) == ''
        assert svg.sanitize('') == ''
        self.assertEqual(svg.sanitize('ü'), '_ü')
        self.assertEqual(svg.sanitize('!foo'), '_!foo')
        assert svg.sanitize('müller') == 'müller'
