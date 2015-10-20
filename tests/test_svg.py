import unittest
import re
from os import path
from io import BytesIO
from svgis import svg
from xml.dom import minidom
import svgwrite

class SvgTestCase(unittest.TestCase):

    def setUp(self):
        self.SVG = path.join(path.dirname(__file__), './data/test.svg')
        self.newstyle = 'stroke {color:red;}'

    def test_add_style(self):
        new = svg.add_style(self.SVG, self.newstyle)
        css = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.newstyle in css.toxml()

    def test_add_style_missing_def(self):
        with open(self.SVG) as f:
            replaced_svg = re.sub(r'<defs>.+?</defs>', '', f.read())

        io_svg = BytesIO(replaced_svg)

        new = svg.add_style(io_svg, self.newstyle)
        css = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.newstyle in css.toxml()

    def test_rescale(self):
        new = svg.rescale(self.SVG, 100)

        g = minidom.parseString(new).getElementsByTagName('g')[0]
        assert 'scale(100)' in g.attributes.get('transform').value

    def test_create(self):
        s = svg.create((100, 100), [])
        assert type(s) == svgwrite.drawing.Drawing

        s = svg.create(100, [])
        assert type(s) == svgwrite.drawing.Drawing

        s = svg.create(100, [], style=self.newstyle)
        assert type(s) == svgwrite.drawing.Drawing
        assert len(s.defs.elements) > 0
        assert self.newstyle in s.defs.elements[0].tostring()
