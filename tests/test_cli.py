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
from svgis.cli import formatter
from svgis.cli.main import _echo

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
            self.assertIn(self.css, out, ' '.join(args))
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
        _echo(content, io)
        io.seek(0)

        self.assertEqual(io.read(), content)


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


if __name__ == '__main__':
    unittest.main()
