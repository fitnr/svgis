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
import xml.etree.ElementTree as ElementTree
from svgis import dom, style


class CssTestCase(unittest.TestCase):
    svg = """<svg baseProfile="full" height="1" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <defs></defs>
            <g>
                <g id="test">
                    <polygon class="test" points="3,2 -2,6 8,-1 8,2 4,1 3,2" />
                </g>
                <g id="foo">
                    <polyline id="baz" class="foo" points="3,2 -2,6 8,-1"></polyline>
                </g>
                <g id="cat">
                    <polyline id="meow" class="long-class-name" points="3,2 -2,6 8,-1"></polyline>
                </g>
            </g>
        </svg>"""

    css = """polygon {fill: orange;}
                .test { stroke: green; }
                polyline { stroke: blue}
                .test, #baz { stroke-width: 2; }
                #test ~ #foo { fill: purple; }
                #cat polyline { fill: red }"""

    css1 = '''.class-name { fill: orange;}'''

    file = 'tests/test_data/test.svg'

    classes = ('apple', 'potato')

    properties = {
        'apple': 'fruit',
        'pear': 1,
        'kale': 'leafy green',
    }

    def testInlineCSS(self):
        inlined = style.inline(self.svg, self.css)
        self.assertNotEqual(inlined, self.svg)

        assert 'fill:purple' not in inlined

        doc = minidom.parseString(inlined)

        polygon = doc.getElementsByTagName('polygon').item(0).getAttribute('style')
        self.assertIn('stroke:green', polygon)
        self.assertIn('fill:orange', polygon)

        cat = doc.getElementsByTagName('polyline').item(1).getAttribute('style')
        self.assertIn('fill:red', cat)

        polyline = doc.getElementsByTagName('polyline').item(0).getAttribute('style')
        self.assertIn('stroke:blue', polyline)

    def test_add_style(self):
        new = style.add_style(self.file, self.css)
        result = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.css in result.toxml()

    def test_replace_style(self):
        new = style.add_style(self.file, self.css, replace=True)
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
        self.assertIn(self.css, result.toxml())

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
            result = style.add_style(self.file, cssfile)
            self.assertIn(self.css, result[0:2000])

        finally:
            os.remove('tmp.css')

    def testAddStyleNoDefs(self):
        svg = self.svg.replace('<defs></defs>', '')
        new = style.add_style(svg, self.css)
        result = minidom.parseString(new).getElementsByTagName('defs').item(0).getElementsByTagName('style').item(0)
        assert self.css in result.toxml()

    def testSanitize(self):
        assert style.sanitize(None) == u'None'
        assert style.sanitize(u'') == u''
        self.assertEqual(style.sanitize(u'ü'), u'_ü')
        self.assertEqual(style.sanitize(u'!foo'), u'_!foo')
        assert style.sanitize(u'müller') == u'müller'

        self.assertEqual(style.sanitize(1), u'_1')

        self.assertEqual(style.sanitize('foo.bar'), u'foobar')
        self.assertEqual(style.sanitize(u'fooba.r'), u'foobar')

        self.assertEqual(style.sanitize('.foo'), u'foo')

        self.assertEqual(style.sanitize(u'foo#bar'), u'foobar')
        self.assertEqual(style.sanitize(u'foobar#'), u'foobar')

        self.assertEqual(style.sanitize(u'x \t'), 'x_')

        self.assertEqual(style.sanitize(u'"huh"'), u'huh')

    def testConstructClasses(self):
        self.assertEqual(style.construct_classes(('foo',), {'foo': 'bar'}), 'foo_bar')
        self.assertEqual(style.construct_classes(['foo'], {'foo': 'bar'}), 'foo_bar')

        self.assertEqual(style.construct_classes(['foo'], {'foo': None}), 'foo_None')

    def testCreateClasses(self):
        classes = style.construct_classes(self.classes, self.properties)
        self.assertEqual(classes, u'apple_fruit potato')

        classes = style.construct_classes(self.classes, {'apple': u'fruit'})
        self.assertEqual(classes, u'apple_fruit potato')

        classes = style.construct_classes(self.classes, {'apple': u'früit'})
        self.assertEqual(classes, u'apple_früit potato')

        classes = style.construct_classes(self.classes, {'apple': 1})
        self.assertEqual(classes, u'apple_1 potato')

    def testCreateClassesMissing(self):
        classes = style.construct_classes(self.classes, {'apple': ''})
        self.assertEqual(classes, 'apple_ potato')

        classes = style.construct_classes(self.classes, {'apple': None})
        self.assertEqual(classes, 'apple_None potato')

    def testCDATA(self):
        
        xml = """<?xml version='1.0' encoding='utf-8'?><text>hi</text>"""
        content = 'this is some text & > <'

        style._register()
        et = ElementTree.fromstring(xml)
        e = ElementTree.Element("data")
        cd = dom.cdata(content)
        e.append(cd)
        et.append(e)

        string = ElementTree.tostring(et, encoding='utf-8')

        self.assertIn(content.encode('utf8'), string)

    def testPartialStyleName(self):
        doc = ElementTree.fromstring(self.svg).find('./' + dom.ns('g'))
        ruleset = style._parse_css(self.css1)

        dom.apply_rule(doc, ruleset.rules[0])
        svg = ElementTree.tostring(doc, encoding='utf-8').decode('utf-8')
        self.assertNotIn('orange', svg)

        inlined = style.inline(self.svg, self.css1)
        self.assertNotIn('orange', inlined)

if __name__ == '__main__':
    unittest.main()
