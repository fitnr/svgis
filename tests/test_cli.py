#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

from __future__ import unicode_literals
import unittest
import argparse
import sys
import os
import subprocess
from xml.dom import minidom
from io import BytesIO, StringIO
from svgis import cli
from svgis.cli import actions, formatter
from svgis.cli.main import echo

PROJECTION = '+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
BOUNDS = (-124.0, 20.5, -64.0, 49.0)


class CliTestCase(unittest.TestCase):

    def setUp(self):
        self.fixture = 'tests/test_data/test.svg'
        self.shp = 'tests/test_data/cb_2014_us_nation_20m.shp'
        self.css = 'polygon{fill:green}'
        sys.tracebacklimit = 99

    def testSvgStyle(self):
        args = ['svgis', 'style', '-s', self.css, self.fixture]
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = p.communicate()

        self.assertIsNone(err, 'err is not None')
        self.assertIsNotNone(out, 'out is None')

        try:
            self.assertIn(self.css, out)
        except TypeError:
            self.assertIn(self.css, out.decode())

    def testSvgScale(self):
        args = ['svgis', 'scale', '-f', '123', self.fixture]
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
            self.assertEqual(out.decode(), expected)

    def testCliEcho(self):
        io = StringIO()
        content = 'my content'
        echo(content, io)
        io.seek(0)

        self.assertEqual(io.read(), content)

    def testCliStyle(self):
        result = actions.add_style(self.fixture, self.css)
        self.assertIn(self.css, result)

        style = 'tmp.css'

        with open(style, 'w') as w:
            w.write(self.css)

        try:
            result = actions.add_style(self.fixture, style)
            self.assertIn(self.css, result)

        finally:
            os.remove('tmp.css')

    def CliDrawWithStyle(self):
        result = actions.draw(self.shp, style=self.css, scale=1000, project=PROJECTION, bounds=BOUNDS, clip=None)
        self.assertIn(self.css, result)

        style = 'tmp.css'
        with open(style, 'w') as w:
            w.write(self.css)

        try:
            result = actions.draw(self.shp, style=style, scale=1000, project=PROJECTION, bounds=BOUNDS, clip=None)
            self.assertIn(self.css, result)

        finally:
            os.remove('tmp.css')

    def testCliScale(self):
        result = actions.scale(self.fixture, 1.37)
        self.assertIn('scale(1.37)', result)

    def testCliDraw(self):
        a = actions.draw(self.shp, scale=1000, project=PROJECTION, bounds=BOUNDS, clip=False)

        result = minidom.parseString(a).getElementsByTagName('svg').item(0)
        fixture = minidom.parse(self.fixture).getElementsByTagName('svg').item(0)

        result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
        fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

        for r, f in zip(result_vb, fixture_vb):
            self.assertAlmostEqual(r, f, 5)

    def testCliDrawProjFile(self):
        a = actions.draw(self.shp, scale=1000, project='tests/test_data/test.proj4', bounds=BOUNDS, clip=False)

        result = minidom.parseString(a).getElementsByTagName('svg').item(0)
        fixture = minidom.parse(self.fixture).getElementsByTagName('svg').item(0)

        result_vb = [float(x) for x in result.attributes.get('viewBox').value.split(',')]
        fixture_vb = [float(x) for x in fixture.attributes.get('viewBox').value.split(',')]

        for r, f in zip(result_vb, fixture_vb):
            self.assertAlmostEqual(r, f, 5)

    def testCli(self):
        sys.argv = (['svgis', 'draw', '-j', PROJECTION, '-f', '1000', self.shp,
                     '-o', 'tmp.svg', '--bounds'] + [str(b) for b in BOUNDS])

        cli.main()

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
        if sys.version_info.major == 2:
            sys.stdout = BytesIO()
        else:
            sys.stdout = StringIO()

        sys.argv = (['svgis', '-h'])
        with self.assertRaises(SystemExit):
            cli.main()

        sys.argv = (['svgis', 'style', '-h'])
        with self.assertRaises(SystemExit):
            cli.main()

        sys.argv = (['svgis', 'draw', '-h'])
        with self.assertRaises(SystemExit):
            cli.main()

        sys.argv = (['svgis', 'project', '-h'])
        with self.assertRaises(SystemExit):
            cli.main()

        sys.argv = (['svgis', 'scale', '-h'])
        with self.assertRaises(SystemExit):
            cli.main()

    def testErrs(self):
        sys.argv = ['svgis', 'draw', 'lksdjlksjdf']

        with self.assertRaises(IOError):
            cli.main()

    def testCliFormatter(self):
        assert issubclass(formatter.CommandHelpFormatter, argparse.HelpFormatter)
        assert issubclass(formatter.SubcommandHelpFormatter, argparse.HelpFormatter)

    def testPickStyle(self):
        stylefile = 'tmp.css'

        with open(stylefile, 'w') as w:
            w.write(self.css)

        try:
            result = actions.pick_style(stylefile)
            self.assertEqual(self.css, result)

        finally:
            os.remove('tmp.css')

        result = actions.pick_style(self.css)
        self.assertEqual(self.css, result)

        assert actions.pick_style(None) is None


if __name__ == '__main__':
    unittest.main()
