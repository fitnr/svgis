#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

import unittest
from svgis import convert

class ConvertTestCase(unittest.TestCase):
    def test_rect(self):
        pass

    def test_replacebounds(self):
        bounds1 = (None, 0.1, None, 1.1)
        bounds2 = (0.2, 0.2, 1.2, 1.2)

        self.assertEqual(convert.replacebounds(bounds1, bounds2), (0.2, 0.1, 1.2, 1.1))
