#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
from svgis import utils


class UtilsTestCase(unittest.TestCase):

    def test_isinf(self):
        assert utils.isinf(float('inf')) is True
        assert utils.isinf(float('-inf')) is True
        assert utils.isinf(float(10e10)) is False

    def test_between(self):
        self.assertSequenceEqual(
            list(utils.between(0., 10., 10)),
            [0., 1., 2., 3., 4., 5., 6., 7., 8., 9.]
        )

        self.assertSequenceEqual(
            list(utils.between(0., 5.)),
            [0., .5, 1., 1.5, 2., 2.5, 3., 3.5, 4., 4.5]
        )

    def test_frange(self):
        self.assertSequenceEqual(
            list(utils.frange(1., 2.15, .25)),
            [1., 1.25, 1.5, 1.75, 2.]
        )
        self.assertSequenceEqual(
            list(utils.frange(1., 2.15, .25, True)),
            [1., 1.25, 1.5, 1.75, 2., 2.25]
        )

    def test_modfloor(self):
        assert utils.modfloor(10, 3) == 9
        assert utils.modfloor(17, 4) == 16

    def test_modceil(self):
        assert utils.modceil(10, 3) == 12
        assert utils.modceil(17, 4) == 20

if __name__ == '__main__':
    unittest.main()
