#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests on the svgis command line tool"""
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
# pylint: disable=duplicate-code
import io
import os
import re
import sys
import unittest
from xml.dom import minidom

import click.testing
import fiona.errors

import svgis.cli

PROJECTION = '+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
BOUNDS = (-124.0, 20.5, -64.0, 49.0)


class CliTestCase(unittest.TestCase):
    runner = click.testing.CliRunner()
    fixture = 'tests/fixtures/test.svg'

    shp = 'tests/fixtures/cb_2014_us_nation_20m.json'
    dc = 'tests/fixtures/tl_2015_11_place.json'
    css = 'polygon{fill:green}'

    def setUp(self):
        self.assertTrue(os.path.exists(self.dc))
        self.assertTrue(os.path.exists(self.fixture))
        self.assertTrue(os.path.exists(self.shp))

    def invoke(self, argument, **kwargs):
        return self.runner.invoke(svgis.cli.main, argument, catch_exceptions=False, **kwargs)

    def testSvgStyle(self):
        sys.stdout = io.StringIO()
        self.invoke(['style', '--style', self.css, self.fixture, 'tmp.svg'])
        try:
            with open('tmp.svg') as f:
                self.assertIn(self.css, f.read()[0:1000])
        finally:
            os.remove('tmp.svg')

    def testSvgScale(self):
        self.invoke(['scale', '--scale', '123', self.fixture, 'tmp.svg'])
        try:
            with open('tmp.svg') as f:
                self.assertIn('scale(123)', f.read()[0:1000])

        finally:
            os.remove('tmp.svg')

    def testBounds(self):
        result = self.invoke(['bounds', self.shp])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), '-179.174265 17.913769 179.773922 71.352561')

    def testSvgProjectUtm(self):
        p = self.invoke(['project', '--method', 'utm', '--', '-110.277906', '35.450777', '-110.000477', '35.649030'])
        expected = set('+proj=utm +zone=12 +datum=WGS84 +units=m +no_defs +type=crs'.split(' '))
        self.assertSetEqual(set(p.output.strip().split(' ')), expected)

    def testSvgProject(self):
        p = self.invoke(['project', '--', '-110.277906', '35.450777', '-110.000477', '35.649030'])

        self.assertEqual(p.exit_code, 0)

        expected = set(
            [
                '+type=crs',
                '+lat_0=35.64903',
                '+x_0=0',
                '+units=m',
                '+lon_0=-111',
                '+towgs84=0,0,0,0,0,0,0',
                '+y_0=0',
                '+lat_1=35.64903',
                '+proj=lcc',
                '+no_defs',
                '+lat_2=35.450777',
                '+ellps=GRS80',
            ]
        )
        self.assertSetEqual(set(p.output.strip().split(' ')), expected)

    def testCliDraw(self):
        self.invoke(
            ['draw', '--crs', PROJECTION, '--scale', '1000', self.shp, '-o', 'tmp.svg', '--viewbox', '--bounds']
            + [str(b) for b in BOUNDS]
        )

        try:
            result = minidom.parse('tmp.svg').getElementsByTagName('svg').item(0)

            fixture = minidom.parse(self.fixture).getElementsByTagName('svg').item(0)

            result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
            fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

            for r, f in zip(result_vb, fixture_vb):
                self.assertAlmostEqual(r, f, 5, 'viewbox doesnt match fixture')

        finally:
            os.remove('tmp.svg')

    def testDrawProjected(self):
        f = os.path.expanduser('~/tmp.svg')
        result = self.invoke(['draw', self.dc, '--output', f, '--precision', '10'])

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(f))

        try:
            with open(f) as g:
                svg = g.read()
                match = re.search(r'points="([^"]+)"', svg)
                self.assertIsNotNone(match)

            result = match.groups()[0]
            points = [[float(x) for x in p.split(',')] for p in result.split(' ')]

            with fiona.open(self.dc) as src:
                ring = next(src)['geometry']['coordinates'][0]

            for points in zip(ring, points):
                for z in zip(*points):
                    self.assertAlmostEqual(*z)

        finally:
            os.remove(f)

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
        with self.assertRaises(fiona.errors.DriverError):
            self.invoke(('draw', 'lksdjlksjdf'))

        with self.assertRaises(fiona.errors.DriverError):
            self.invoke(('draw', 'zip://lksdjlksjdf.zip/foo'))


if __name__ == '__main__':
    unittest.main()
