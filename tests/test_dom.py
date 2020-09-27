#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest

import tinycss2

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

from svgis import dom

from . import TEST_CSS, TEST_SVG


class DomTestCase(unittest.TestCase):

    svg = TEST_SVG
    css = TEST_CSS

    def setUp(self):
        self.rules = tinycss2.parse_stylesheet(self.css, skip_whitespace=True, skip_comments=True)
        self.document = etree.fromstring(self.svg)

    def testSerializeToken(self):
        rules = tinycss2.parse_stylesheet("polygon{fill:orange}")
        token = rules[0].prelude[0]
        assert token.type == 'ident'

        assert ('svg|' + token.serialize()) == 'svg|polygon'

        prelude_value = dom.serialize_token(token)
        self.assertEqual(prelude_value, 'svg|polygon')

        prelude = dom.serialize_prelude(rules[0])
        self.assertEqual(prelude, 'svg|polygon')

        pretoken = tinycss2.ast.LiteralToken(1, 1, '.')
        serialized = dom.serialize_token(rules[0].prelude[0], pretoken)
        self.assertEqual(serialized, 'polygon')

        pretoken = tinycss2.ast.LiteralToken(1, 1, '/')
        serialized = dom.serialize_token(rules[0].prelude[0], pretoken)
        self.assertEqual(serialized, 'polygon')

    def testApplyRule(self):
        rules = tinycss2.parse_stylesheet("polygon {fill: orange}", skip_whitespace=True, skip_comments=True)
        svg = etree.fromstring(
            '<svg baseProfile="full" height="1" version="1.1" xmlns="http://www.w3.org/2000/svg">'
            '<polygon class="test" points="3,2 -2,6 8,-1 8,2 4,1 3,2" />'
            '</svg>'
        )
        dom.apply_rules(svg, rules)
        text = etree.tostring(svg).decode('ascii')
        self.assertIn('orange', text)

    def testApplyIdentRule(self):
        dom.apply_rules(self.document, self.rules)
        polygon = self.document.xpath('.//svg:polygon', namespaces={'svg': 'http://www.w3.org/2000/svg'})[0]

        self.assertIsNotNone(polygon)

        self.assertIn('fill:orange', polygon.attrib['style'])

    def testApplyHashRule(self):
        dom.apply_rules(self.document, self.rules)
        polyline = self.document.xpath(".//*[@id='meow']")[0]
        self.assertIsNotNone(polyline)
        self.assertIn('stroke-opacity:0.50', polyline.attrib.get('style', ''))

    def testChildToken(self):
        css = "#foo > #baz { stroke: green }"
        rules = tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True)
        dom.apply_rules(self.document, rules)
        polyline = self.document.find(".//*[@id='baz']")
        self.assertIn('stroke:green', polyline.attrib.get('style', ''))

    def testApplyRadiusRule(self):
        css = tinycss2.parse_stylesheet('circle { r: 1 }')
        dom.apply_rules(self.document, css)
        circ = self.document.find('.//circle', namespaces=self.document.nsmap)
        self.assertIsNotNone(circ)
        self.assertIn('1', circ.attrib.get('r', ''))


if __name__ == '__main__':
    unittest.main()
