#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import os
import re
import unittest
from io import BytesIO, StringIO
from xml.dom import minidom

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

from svgis import dom, style

from . import TEST_CSS, TEST_SVG


class CssTestCase(unittest.TestCase):
    svg = TEST_SVG
    css = TEST_CSS

    css1 = '''.class-name { fill: orange;}'''

    file = 'tests/fixtures/test.svg'

    classes = ('apple', 'potato')

    properties = {
        'apple': 'fruit',
        'pear': 1,
        'kale': 'leafy green',
    }

    def testInlineCSS(self):
        svg = style.add_style(self.svg, self.css)
        inlined = style.inline(svg)
        self.assertNotEqual(inlined, self.svg)

        doc = minidom.parseString(inlined)
        self.assertIn('fill:purple', inlined)

        polygon_style = doc.getElementsByTagName('polygon').item(0).getAttribute('style')
        self.assertIn('stroke:green', polygon_style)
        self.assertIn('fill:orange', polygon_style)

        cat_style = doc.getElementsByTagName('polyline').item(1).getAttribute('style')
        self.assertIn('fill:red', cat_style)

        polyline_style = doc.getElementsByTagName('polyline').item(0).getAttribute('style')
        self.assertIn('stroke:blue', polyline_style)

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
        result = style.rescale('tests/fixtures/test.svg', 1.37)
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

        self.assertIsNone(style.pick(None))

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
        self.assertEqual(style.construct_classes(('foo',), {'foo': 'bar'}), [u'foo_bar'])
        self.assertEqual(style.construct_classes(['foo'], {'foo': 'bar'}), [u'foo_bar'])

        self.assertEqual(style.construct_classes(['foo'], {'foo': None}), [u'foo_None'])

    def testCreateClasses(self):
        classes = style.construct_classes(self.classes, self.properties)
        self.assertEqual(classes, [u'apple_fruit'])

        classes = style.construct_classes(self.classes, {'apple': u'fruit'})
        self.assertEqual(classes, [u'apple_fruit'])

        classes = style.construct_classes(self.classes, {'apple': u'früit'})
        self.assertEqual(classes, [u'apple_früit'])

        classes = style.construct_classes(self.classes, {'apple': 1})
        self.assertEqual(classes, [u'apple_1'])

    def testCreateClassesMissing(self):
        classes = style.construct_classes(self.classes, {'apple': ''})
        self.assertEqual(classes, [u'apple_'])

        classes = style.construct_classes(self.classes, {'apple': None})
        self.assertEqual(classes, [u'apple_None'])

    def testPartialStyleName(self):
        inlined = style.inline(self.svg)
        self.assertNotIn('orange', inlined)

    def testReplaceComments(self):
        css = """
        // foo
        """
        result = style.replace_comments(css)
        self.assertIn('/* foo */', result)

    def testConstructDataFields(self):
        fields = style.construct_datas(['a', 'b'], {'a': '1', 'b': '_ _'})
        self.assertEqual(fields['data-a'], '1')
        self.assertEqual(fields['data-b'], '_ _')
        self.assertNotIn('data-c', fields)


if __name__ == '__main__':
    unittest.main()
