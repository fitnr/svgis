#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>
from __future__ import unicode_literals
import unittest
import sys
import os
import subprocess
from xml.dom import minidom
from pkg_resources import resource_filename
from io import StringIO
from svgis import cli


PROJECTION = '+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
BOUNDS = (-124.0, 20.5, -64.0, 49.0)


class CliTestCase(unittest.TestCase):

    def setUp(self):
        self.testsvg = resource_filename('svgis', 'test_data/test.svg')
        self.shp = resource_filename('svgis', 'test_data/cb_2014_us_nation_20m.shp')
        self.css = 'polygon{fill:green}'

    def testSvgStyle(self):
        args = ['svgis', 'style', '-s', self.css, self.testsvg]
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = p.communicate()

        self.assertIsNone(err, 'err is not None')
        self.assertIsNotNone(out, 'out is None')

        try:
            self.assertIn(self.css, out)
        except TypeError:
            self.assertIn(self.css, out.decode())

    def testSvgScale(self):
        args = ['svgis', 'scale', '-f', '123', self.testsvg]
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = p.communicate()

        self.assertIsNone(err, 'err is not None')
        self.assertIsNotNone(out, 'out is None')

        try:
            self.assertIn('scale(123)', out)
        except (TypeError, AssertionError):
            self.assertIn('scale(123)', out.decode())

    def testSvgProjectUtm(self):
        args = ['svgis', 'project', '-j', 'utm', '-110.277906', '35.450777', '-110.000477', '35.649030']
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = p.communicate()

        self.assertIsNone(err, 'err is not None')
        self.assertIsNotNone(out, 'out is None')

        expected = '+proj=utm +zone=12 +north +datum=WGS84 +units=m +no_defs\n'

        try:
            self.assertEqual(out, expected)
        except (TypeError, AssertionError):
            self.assertEqual(out.decode(), expected)

    def testSvgProject(self):
        args = ['svgis', 'project', '-110.277906', '35.450777', '-110.000477', '35.649030']
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = p.communicate()

        self.assertIsNone(err, 'err is not None')
        self.assertIsNotNone(out, 'out is None')

        expected = ('+proj=lcc +lon_0=-111.0 +lat_1=35.64903 +lat_2=35.450777 '
                    '+lat_0=35.64903+x_0=0 +y_0=0 +ellps=GRS80 '
                    '+towgs84=0,0,0,0,0,0,0+units=m +no_defs\n')
        try:
            self.assertEqual(out, expected)
        except:
            assert out.decode() == expected

    def testCliEcho(self):
        io = StringIO()
        content = 'my content'
        cli._echo(content, io)
        io.seek(0)

        self.assertEqual(io.read(), content)

    def testCliStyle(self):
        io = StringIO()
        cli._style(self.testsvg, io, self.css)
        io.seek(0)

        self.assertIn(self.css, io.read())

        style = 'tmp.css'
        with open(style, 'w') as w:
            w.write(self.css)

        io = StringIO()

        try:
            cli._style(self.testsvg, io, style)
            io.seek(0)
            self.assertIn(self.css, io.read())

        finally:
            os.remove('tmp.css')

    def CliDrawWithStyle(self):
        io = StringIO()
        cli._draw(self.shp, io, style=self.css, scale=1000, project=PROJECTION, bounds=BOUNDS)
        io.seek(0)

        self.assertIn(self.css, io.read())

        style = 'tmp.css'
        with open(style, 'w') as w:
            w.write(self.css)

        io = StringIO()

        try:
            cli._draw(self.shp, io, style=style, scale=1000, project=PROJECTION, bounds=BOUNDS)
            io.seek(0)
            self.assertIn(self.css, io.read())

        finally:
            os.remove('tmp.css')


    def testCliScale(self):
        io = StringIO()

        cli._scale(self.testsvg, io, 1.37)
        io.seek(0)
        result = io.read()
        self.assertIn('scale(1.37)', result)

    def testCliDraw(self):
        io = StringIO()

        cli._draw(self.shp, io, scale=1000, project=PROJECTION, bounds=BOUNDS)
        io.seek(0)

        result = minidom.parseString(io.read()).getElementsByTagName('svg').item(0)
        fixture = minidom.parse(self.testsvg).getElementsByTagName('svg').item(0)

        result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
        fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

        for r, f in zip(result_vb, fixture_vb):
            self.assertAlmostEqual(r, f, 5)

    def testCli(self):
        sys.argv = (['svgis', 'draw', '-j', PROJECTION, '-f', '1000', self.shp, '--bounds'] +
                    [str(b) for b in BOUNDS] + ['-o', 'tmp.svg'])

        cli.main()

        try:
            result = minidom.parse('tmp.svg').getElementsByTagName('svg').item(0)
            fixture = minidom.parse(self.testsvg).getElementsByTagName('svg').item(0)

            result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
            fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

            for r, f in zip(result_vb, fixture_vb):
                self.assertAlmostEqual(r, f, 5)

        finally:
            os.remove('tmp.svg')

    def testErrs(self):
        sys.argv = ['svgis', 'draw', 'lksdjlksjdf']

        with self.assertRaises(IOError):
            cli.main()

if __name__ == '__main__':
    unittest.main()
