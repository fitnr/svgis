#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest
import tinycss
from svgis import dom


class DomTestCase(unittest.TestCase):

    def setUp(self):
        self.parse = tinycss.make_parser().parse_stylesheet

    def tokens(self, css):
        return self.parse(css).rules[0].selector

    def testXpath(self):
        tokens = self.tokens('polygon{fill:green}')
        self.assertEqual(dom.xpath(tokens)[0], './/{http://www.w3.org/2000/svg}polygon')

    def testClassRule(self):
        tokens = self.tokens('.test { fill: blue}')
        self.assertEqual(dom.xpath(tokens)[0], ".//*[@class='test']")

    def testIdRule(self):
        tokens = self.tokens('#test { fill: blue}')
        self.assertEqual(dom.xpath(tokens)[0], ".//*[@id='test']")

    def testChildRules(self):
        tokens = self.tokens('g>.test { fill: blue}')
        self.assertEqual(dom.xpath(tokens)[0], ".//{http://www.w3.org/2000/svg}g/*[@class='test']")

        tokens = self.tokens('g .test { fill: blue}')
        self.assertEqual(dom.xpath(tokens)[0], ".//{http://www.w3.org/2000/svg}g/*[@class='test']")

        tokens = self.tokens('g polygon.test { fill: blue}')
        self.assertEqual(dom.xpath(tokens)[0], ".//{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}polygon[@class='test']")

    def testAttachedClass(self):
        tokens = self.tokens('g.test { fill: blue}')
        self.assertEqual(dom.xpath(tokens)[0], ".//{http://www.w3.org/2000/svg}g[@class='test']")

if __name__ == '__main__':
    unittest.main()
