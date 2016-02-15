#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

import tinycss
from svgis import dom


class DomTestCase(unittest.TestCase):

    parser = tinycss.make_parser()

    svg = """<svg baseProfile="full" height="1" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <defs><style></style></defs>
            <g>
                <g id="test">
                    <polygon class="test" points="3,2 -2,6 8,-1 8,2 4,1 3,2" />
                </g>
                <g id="foo">
                    <polyline id="baz" class="foo" points="3,2 -2,6 8,-1"></polyline>
                    <polyline id="bozo" class="squa" points="3,2 -2,6 8,-1"></polyline>
                </g>
                <g id="cat">
                    <polyline id="meow" class="squa tront" points="3,2 -2,6 8,-1"></polyline>
                </g>
            </g>
        </svg>"""

    css = """polygon {fill: orange;}
            .test { stroke: green; }
            polyline { stroke: blue}
            .test, #baz { stroke-width: 2; }
            #test ~ #foo { fill: purple; }
            #cat polyline { fill: red }
            .squa.tront { stroke-opacity: 0.50; }
            """

    def setUp(self):
        self.rules = self.parse(self.css).rules

    def parse(self, css):
        return self.parser.parse_stylesheet(css)

    def document(self):
        return ElementTree.fromstring(self.svg).find('./{http://www.w3.org/2000/svg}g')

    def testApplyRule(self):
        document = self.document()
        dom.apply_rule(document, self.rules[0])

        polygon = document.find('.//{http://www.w3.org/2000/svg}polygon')
        self.assertIn('fill:orange', polygon.attrib['style'])

        dom.apply_rule(document, self.rules[6])

        polyline = document.find(".//*[@id='meow']")
        self.assertIn('stroke-opacity:0.50', polyline.attrib.get('style', ''))

    def testProcessTokens(self):
        document = self.document()
        asterisk = '* { fill: tan; }'
        rule = self.parse(asterisk).rules[0]

        els, toks = dom._process_tokens(document, None, rule.selector)
        assert toks == []
        assert els == document.findall('.//')

    def testChildToken(self):
        css = "#cat>.squa { stroke: green }"
        rules = self.parse(css).rules
        document = self.document()
        dom.apply_rule(document, rules[0])
        polyline = document.find(".//*[@id='meow']")
        self.assertIn('stroke:green', polyline.attrib.get('style', ''))

    def testBuildTokenList(self):
        css = """
            #foo[name=foo] {}
            .foo~.squa {}
            .pizza::first-child {}
            .salad>kale {}
            """
        rules = self.parse(css).rules

        for r in rules:
            parsed = [getattr(t, 'value', '') for t in r.selector]
            built = dom._build_tokenlist(r.selector)
            self.assertEqual(parsed, [getattr(t, 'value', '') for t in built[0]])

    def testStyleDecoding(self):
        assert dom._style_dict('fill:none;') == {'fill': 'none'}
        self.assertEqual(dom._style_dict('fill:none;   stroke    : 3px  ; '), {'fill': 'none', 'stroke': '3px'})
        assert dom._style_string({'fill': 'none'}) == 'fill:none'

if __name__ == '__main__':
    unittest.main()
