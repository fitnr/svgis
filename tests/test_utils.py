#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import unittest

from svgis import utils
from svgis.errors import SvgisError


class UtilsTestCase(unittest.TestCase):
    def testPosInt(self):
        with self.assertRaises(SvgisError):
            utils.posint(-1)
        self.assertEqual(utils.posint(1), 1)
        self.assertEqual(utils.posint(111), 111)
        self.assertEqual(utils.posint(1.11), 1)

    def test_isinf(self):
        self.assertTrue(utils.isinf(float('inf')))
        self.assertTrue(utils.isinf(float('-inf')))
        self.assertFalse(utils.isinf(float(10e10)))

    def test_between(self):
        self.assertSequenceEqual(list(utils.between(0.0, 10.0, 10)), [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])

        self.assertSequenceEqual(list(utils.between(0.0, 5.0)), [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5])

    def test_frange(self):
        self.assertSequenceEqual(list(utils.frange(1.0, 2.15, 0.25)), [1.0, 1.25, 1.5, 1.75, 2.0])
        self.assertSequenceEqual(list(utils.frange(1.0, 2.15, 0.25, True)), [1.0, 1.25, 1.5, 1.75, 2.0, 2.25])

    def test_modfloor(self):
        self.assertEqual(utils.modfloor(10, 3), 9)
        self.assertEqual(utils.modfloor(17, 4), 16)

    def test_modceil(self):
        self.assertEqual(utils.modceil(10, 3), 12)
        self.assertEqual(utils.modceil(17, 4), 20)

    def test_dedupe(self):
        test = [1, 2, 2, 3, 4, 5, 4]
        fixture = [1, 2, 3, 4, 5, 4]
        self.assertSequenceEqual(list(utils.dedupe(test)), fixture)

        test = [(1, 2), (3, 4), (3, 4), (5, 4), 'M', (3, 4)]
        fixture = [(1, 2), (3, 4), (5, 4), 'M', (3, 4)]

        self.assertSequenceEqual(list(utils.dedupe(test)), fixture)


if __name__ == '__main__':
    unittest.main()
