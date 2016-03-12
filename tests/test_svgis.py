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
import six
from svgis import svgis, errors


class SvgisTestCase(unittest.TestCase):
    file = 'tests/test_data/cb_2014_us_nation_20m.json'

    polygon = {
        "properties": {
            'apple': 'fruit',
            'pear': 1,
            'kale': 'leafy green',
        },
        "geometry": {
            "type": "Polygon",
            "id": "Polygon",
            "coordinates": [[(0, 0), (1, 0), (0, 1), (0, 0)]]
        }
    }

    def setUp(self):
        self.svgis_obj = svgis.SVGIS(self.file)

    def assertSequenceAlmostEqual(self, a, b):
        for z in zip(a, b):
            self.assertAlmostEqual(*z)

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
        assert isinstance(composed, six.string_types)

    def testSvgisClassFields(self):
        composed = self.svgis_obj.compose(class_fields=('NAME', 'GEOID'))

        matchiter = re.finditer(r'class="(.+?)"', composed)
        match = next(matchiter)

        self.assertIsNotNone(match)
        self.assertIn(u'AFFGEOID', match.groups()[0])
        self.assertIn(u'GEOID', match.groups()[0])
        self.assertIn(u'NAME', match.groups()[0])

        match = next(matchiter)
        self.assertIn('GEOID_US', match.groups()[0])
        self.assertIn('cb_2014_us_nation_20m', match.groups()[0])

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
        drawn = self.svgis_obj.feature(feat, [], classes=['foo'], id_field='cat', name='quux')
        assert isinstance(drawn, six.string_types)

        self.assertIn('id="meow"', drawn)
        self.assertIn('class="quux foo_bar"', drawn)

        drawn2 = self.svgis_obj.feature(feat, [], classes=['foo'], id_field='cat')
        self.assertIn('class="foo_bar"', drawn2)

        feat['geometry'] = None
        drawn3 = self.svgis_obj.feature(feat, [], classes=['foo'], id_field='cat')
        assert drawn3 == ''

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
            self.assertIn('polygon', poly.toxml())
            self.assertIn('style', poly.toxml())
            style = poly.getAttribute('style')
            self.assertIn('fill:none', style)
            self.assertIn('stroke-linejoin:round', style)

    def testOpenZips(self):
        archive = 'zip://tests/test_data/test.zip/tests/test_data/cb_2014_us_nation_20m.json'

        result = svgis.SVGIS([archive], simplify=60).compose()

        self.assertIn('cb_2014_us_nation_20m', result)

    def testDrawWithClasses(self):
        r0 = self.svgis_obj.feature(self.polygon, [], classes=[], id_field=None, name='potato')
        self.assertIn('class="potato"', r0)

        r1 = self.svgis_obj.feature(self.polygon, [], classes=['kale'], id_field='apple')
        assert 'kale_leafy_green' in r1
        assert 'id="fruit"' in r1

        r2 = self.svgis_obj.feature(self.polygon, [], id_field='pear', classes=['apple', 'pear', 'kale'])
        self.assertIn('id="_1"', r2)
        assert 'apple_fruit' in r2
        assert 'pear_1' in r2
        assert 'kale_leafy_green' in r2

if __name__ == '__main__':
    unittest.main()
