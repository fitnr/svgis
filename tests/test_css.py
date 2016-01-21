from __future__ import unicode_literals
import unittest
import re
from io import BytesIO, StringIO
from xml.dom import minidom
from svgis import css

class CssTestCase(unittest.TestCase):

    def setUp(self):
        self.svg = """<svg baseProfile="full" height="1" version="1.1">
                <defs></defs>
                <g id="test">
                    <polygon class="test" points="3,2 -2,6 8,-1 8,2 4,1 3,2" />
                </g>
                <g id="foo">
                    <polyline class="foo" points="3,2 -2,6 8,-1"></polyline>
                </g>
            </svg>"""

        self.css = """polygon {fill: orange;}
        .test { stroke: green; }
        polyline { stroke: blue}
        #foo polyline { fill: red }"""

        self.file = 'tests/test_data/test.svg'

    def testinlinecss(self):
        try:
            from lxml import etree
            import cssselect
            import tinycss
        except ImportError:
            return

        inlined = css.inline(self.svg, self.css)
        assert inlined != self.svg

        doc = minidom.parseString(inlined)
        polyline = doc.getElementsByTagName('polyline').item(0).getAttribute('style')
        polygon = doc.getElementsByTagName('polygon').item(0).getAttribute('style')

        assert 'stroke:blue' in polyline
        assert 'fill:red' in polyline

        assert 'fill:orange' in polygon
        assert 'stroke:green' in polygon

    def test_add_style(self):
        new = css.add_style(self.file, self.css)
        result = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.css in result.toxml()

    def test_add_style_missing_def(self):
        with open(self.file) as f:
            replaced_svg = re.sub(r'<defs></defs>', '', f.read())

        try:
            io_svg = BytesIO(replaced_svg)
        except TypeError:
            io_svg = StringIO(replaced_svg)

        new = css.add_style(io_svg, self.css)
        result = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.css in result.toxml()

if __name__ == '__main__':
    unittest.main()
