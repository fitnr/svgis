#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
import sys
import os
import io
import functools
from xml.dom import minidom

import click.testing
import svgis.cli


PROJECTION = '+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
BOUNDS = (-124.0, 20.5, -64.0, 49.0)


class CliTestCase(unittest.TestCase):
    fixture = 'tests/test_data/test.svg'

    shp = 'tests/test_data/cb_2014_us_nation_20m.shp'
    css = 'polygon{fill:green}'

    def setUp(self):
        self.runner = runner = click.testing.CliRunner()
        self.invoke = functools.partial(runner.invoke, svgis.cli.main, catch_exceptions=False)

    def testSvgStyle(self):
        sys.stdout = io.StringIO()
        self.invoke(['style', '-s', self.css, self.fixture, 'tmp.svg'])
        try:
            with open('tmp.svg') as f:
                self.assertIn(self.css, f.read()[0:1000])
        finally:
            os.remove('tmp.svg')

    def testSvgScale(self):
        self.invoke(['scale', '-f', '123', self.fixture, 'tmp.svg'])
        try:
            with open('tmp.svg') as f:
                self.assertIn('scale(123)', f.read()[0:1000])

        finally:
            os.remove('tmp.svg')

    def testSvgProjectUtm(self):
        p = self.invoke(['project', '-m', 'utm', '--', '-110.277906', '35.450777', '-110.000477', '35.649030'])
        expected = '+proj=utm +zone=12 +north +datum=WGS84 +units=m +no_defs\n'
        self.assertEqual(p.output, expected)

    def testSvgProject(self):
        p = self.invoke(['project', '--', '-110.277906', '35.450777', '-110.000477', '35.649030'])

        try:
            self.assertEqual(p.exit_code, 0)
        except AssertionError:
            # print(p.exc_info)
            raise

        expected = ('+proj=lcc +lon_0=-111.0 +lat_1=35.64903 +lat_2=35.450777 '
                    '+lat_0=35.64903+x_0=0 +y_0=0 +ellps=GRS80 '
                    '+towgs84=0,0,0,0,0,0,0+units=m +no_defs\n')

        self.assertEqual(p.output, expected)

    def testCliDraw(self):
        self.invoke(['draw', '-j', PROJECTION, '-f', '1000', self.shp,
                     '-o', 'tmp.svg', '--bounds'] + [str(b) for b in BOUNDS])

        try:
            result = minidom.parse('tmp.svg').getElementsByTagName('svg').item(0)
            fixture = minidom.parse(self.fixture).getElementsByTagName('svg').item(0)

            result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
            fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

            for r, f in zip(result_vb, fixture_vb):
                self.assertAlmostEqual(r, f, 5)

        finally:
            os.remove('tmp.svg')

    def testCliHelp(self):
        result = self.invoke(('--help',))
        self.assertEqual(result.exit_code, 0)

        result = self.invoke(['style', '--help'])
        assert result.exit_code == 0

        result = self.invoke(['draw', '--help'])
        assert result.exit_code == 0

        result = self.invoke(['project', '--help'])
        assert result.exit_code == 0

        result = self.invoke(['scale', '--help'])
        assert result.exit_code == 0

    def testErrs(self):
        with self.assertRaises(IOError):
            self.invoke(('draw', 'lksdjlksjdf'))


if __name__ == '__main__':
    unittest.main()
