from __future__ import unicode_literals
import unittest
import re
from io import StringIO
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
