#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
import re
from xml.dom import minidom
from svgis import svgis, errors
try:
    basestring
except NameError:
    basestring = str


class SvgisTestCase(unittest.TestCase):
    properties = {
        'apple': 'fruit',
        'pear': 1,
        'kale': 'leafy green',
    }
    classes = ('apple', 'potato')
    file = 'tests/test_data/cb_2014_us_nation_20m.shp'

    polygon = {
        "properties": properties,
        "geometry": {
            "type": "Polygon",
            "id": "Polygon",
            "coordinates": [[(0, 0), (1, 0), (0, 1), (0, 0)]]
        }
    }

    def setUp(self):
        self.svgis_obj = svgis.SVGIS(self.file)

    def testSvgisError(self):
        with self.assertRaises(errors.SvgisError):
            raise errors.SvgisError('This is an error')

    def testSvgisCreate(self):
        self.assertEqual(self.svgis_obj.files, [self.file])
        assert self.svgis_obj._projected_bounds == (None,) * 4
        assert self.svgis_obj.out_crs is None
        assert self.svgis_obj.style == svgis.STYLE

        svgis_obj2 = svgis.SVGIS([self.file])
        assert svgis_obj2.files == [self.file]

        with self.assertRaises(ValueError):
            svgis.SVGIS(12)

    def testSvgisCompose(self):
        composed = self.svgis_obj.compose()
        assert isinstance(composed, basestring)

    def testProperty(self):
        result = svgis._property('apple', self.properties)
        assert result == 'apple_fruit'

        result = svgis._property('pear', self.properties)
        assert result == 'pear_1'

        result = svgis._property('apple', {'apple': u'früit'})
        self.assertEqual(result, u'apple_früit')

    def testGetClasses(self):
        classes = svgis._get_classes(self.classes, self.properties, 'Name')
        self.assertIn('apple', classes)
        self.assertIn('Name', classes)

    def testSvgisClassFields(self):
        composed = self.svgis_obj.compose(class_fields=('NAME', 'GEOID'))

        matchiter = re.finditer(r'class="(.+?)"', composed)
        match = next(matchiter)

        self.assertIsNotNone(match)
        self.assertIn(u'AFFGEOID GEOID NAME', match.groups()[0])

        match = next(matchiter)
        self.assertIn('GEOID_US', match.groups()[0])
        self.assertIn('cb_2014_us_nation_20m', match.groups()[0])

    def testCreateClasses(self):
        classes = svgis._construct_classes(self.classes, self.properties)
        self.assertEqual(classes, u'apple_fruit potato')

        classes = svgis._construct_classes(self.classes, {'apple': u'fruit'})
        self.assertEqual(classes, u'apple_fruit potato')

        classes = svgis._construct_classes(self.classes, {'apple': u'früit'})
        self.assertEqual(classes, u'apple_früit potato')

        classes = svgis._construct_classes(self.classes, {'apple': 1})
        self.assertEqual(classes, u'apple_1 potato')

    def testCreateClassesMissing(self):
        classes = svgis._construct_classes(self.classes, {'apple': ''})
        self.assertEqual(classes, 'apple_ potato')

        classes = svgis._construct_classes(self.classes, {'apple': None})
        self.assertEqual(classes, 'apple_None potato')

    def testRepr(self):
        expected = ("SVGIS(files=['{}'], "
                    'out_crs=None)'.format(self.file))
        self.assertEqual(str(self.svgis_obj), expected)

    def testDrawGeometry(self):
        feat = {
            "geometry": {
                'type': 'LineString',
                'coordinates': [[-110.8, 35.3], [-110.9, 35.8], [-110.5, 35.1], [-110.8, 35.3]]
            },
            "properties": {
                'foo': 'bar',
                'cat': 'meow'
            }
        }
        drawn = self.svgis_obj._feature(feat, [], classes=['foo'], id_field='cat')
        assert isinstance(drawn, basestring)

        self.assertIn('id="meow"', drawn)
        self.assertIn('class="foo_bar"', drawn)

    def testConstructClasses(self):
        self.assertEqual(svgis._construct_classes('foo', {'foo': 'bar'}), 'foo_bar')
        self.assertEqual(svgis._construct_classes(['foo'], {'foo': 'bar'}), 'foo_bar')

        self.assertEqual(svgis._construct_classes(['foo'], {'foo': None}), 'foo_None')

    def testDims(self):
        bbox = 0, 0, 10, 10

        self.svgis_obj.in_crs = {'init': 'epsg:4269'}
        self.svgis_obj.out_crs = {'init': 'epsg:4269'}

        a = self.svgis_obj._dims(1, bbox)
        for z in zip(a, (10, 10, 0, 10)):
            self.assertAlmostEqual(*z)

        b = self.svgis_obj._dims(0.5, bbox)
        for z in zip(b, (5, 5, 0, 5)):
            self.assertAlmostEqual(*z)

        self.svgis_obj.padding = 10
        c = self.svgis_obj._dims(0.25, bbox)
        for z in zip(c, (22.5, 22.5, 0., 2.5)):
            self.assertAlmostEqual(*z)

        with self.assertRaises((TypeError, ValueError)):
            self.svgis_obj._dims(0.5, (1, 2, 3))

        with self.assertRaises((TypeError, ValueError)):
            self.svgis_obj._dims(0.5, None)

    def testSvgisComposeType(self):
        a = self.svgis_obj.compose(inline_css=True)
        b = self.svgis_obj.compose(inline_css=False)

        try:
            try:
                self.assertIsInstance(a, unicode)
            except AssertionError:
                raise AssertionError(type(a))

            try:
                self.assertIsInstance(b, unicode)
            except AssertionError:
                raise AssertionError(type(b))

        except NameError:
            try:
                self.assertIsInstance(a, str)
            except AssertionError:
                raise AssertionError(type(a))

            try:
                self.assertIsInstance(b, str)
            except AssertionError:
                raise AssertionError(type(b))

        self.assertEqual(type(a), type(b))

    def testMapFunc(self):
        args = {
            "scale": 1000,
            "padding": 10,
            "inline_css": True,
            "clip": False,
            'crs': 'EPSG:32117',
        }
        result = svgis.map([self.file], (-80, 40, -71, 45.1), **args)

        self.assertIn(svgis.STYLE, result)

        doc = minidom.parseString(result)

        for poly in doc.getElementsByTagName('polygon'):
            style = poly.getAttribute('style')
            assert 'fill:none' in style
            assert 'stroke-linejoin:round' in style

    def testDrawWithClasses(self):
        r0 = self.svgis_obj._feature(self.polygon, [], classes=['potato'], id_field=None)
        assert 'class="potato"' in r0

        r1 = self.svgis_obj._feature(self.polygon, [], classes=['kale'], id_field='apple')
        assert 'kale_leafy_green' in r1
        assert 'id="fruit"' in r1

        r2 = self.svgis_obj._feature(self.polygon, [], id_field='pear', classes=['apple', 'pear', 'kale'])
        self.assertIn('id="_1"', r2)
        assert 'apple_fruit' in r2
        assert 'pear_1' in r2
        assert 'kale_leafy_green' in r2

if __name__ == '__main__':
    unittest.main()
