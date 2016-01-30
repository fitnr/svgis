#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
import re
import os
from io import BytesIO, StringIO
from xml.dom import minidom
from svgis import style


class CssTestCase(unittest.TestCase):
    svg = """<svg baseProfile="full" height="1" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <defs></defs>
            <g id="test">
                <polygon class="test" points="3,2 -2,6 8,-1 8,2 4,1 3,2" />
            </g>
            <g id="foo">
                <polyline class="foo" points="3,2 -2,6 8,-1"></polyline>
            </g>
        </svg>"""

    css = """polygon {fill: orange;}
                .test { stroke: green; }
                polyline { stroke: blue}
                #foo polyline { fill: red }"""

    file = 'tests/test_data/test.svg'

    def testinlinecss(self):
        inlined = style.inline(self.svg, self.css)
        assert inlined != self.svg

        doc = minidom.parseString(inlined)
        polyline = doc.getElementsByTagName('polyline').item(0).getAttribute('style')
        polygon = doc.getElementsByTagName('polygon').item(0).getAttribute('style')

        assert 'stroke:green' in polygon
        self.assertIn('fill:orange', polygon)
        self.assertIn('fill:red', polyline)
        self.assertIn('stroke:blue', polyline)

    def test_add_style(self):
        new = style.add_style(self.file, self.css)
        result = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.css in result.toxml()

    def test_add_style_missing_def(self):
        with open(self.file) as f:
            replaced_svg = re.sub(r'<defs></defs>', '', f.read())

        try:
            io_svg = BytesIO(replaced_svg)
        except TypeError:
            io_svg = StringIO(replaced_svg)

        new = style.add_style(io_svg, self.css)
        result = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.css in result.toxml()

    def testReScale(self):
        result = style.rescale('tests/test_data/test.svg', 1.37)
        self.assertIn('scale(1.37)', result[0:2000])

    def testPickStyle(self):
        stylefile = 'tmp.css'

        with open(stylefile, 'w') as w:
            w.write(self.css)

        try:
            result = style.pick(stylefile)
            self.assertEqual(self.css, result)

        finally:
            os.remove('tmp.css')

        result = style.pick(self.css)
        self.assertEqual(self.css, result)

        assert style.pick(None) is None

    def testAddCli(self):
        result = style.add_style(self.file, self.css)
        self.assertIn(self.css, result[0:2000])

        cssfile = 'tmp.css'

        with open(cssfile, 'w') as w:
            w.write(self.css)

        try:
            result = style.add_style(self.file, style)
            self.assertIn(self.css, result[0:2000])

        finally:
            os.remove('tmp.css')

    def testAddStyleNoDefs(self):
        svg = self.svg.replace('<defs></defs>', '')
        new = style.add_style(svg, self.css)
        result = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.css in result.toxml()

if __name__ == '__main__':
    unittest.main()
