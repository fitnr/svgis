# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
import logging
import unittest

from svgis import SVGIS, draw, errors


class ErrorTestCase(unittest.TestCase):

    feature = {'geometry': {'type': 'Bizarro', 'coordinates': [[(1, 2), (3, 4)], [(7, 8), (9, 10)]]}, 'properties': {}}

    def setUp(self):
        logging.getLogger('svgis').setLevel(logging.CRITICAL)

    def testDrawInvalidGeometry(self):
        with self.assertRaises(errors.SvgisError):
            draw.geometry(self.feature['geometry'])

    def testSvgisDrawInvalidGeometry(self):
        a = SVGIS([]).feature(self.feature, [], [])
        assert a == u''


if __name__ == '__main__':
    unittest.main()
