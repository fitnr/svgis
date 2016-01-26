# -*- coding: utf-8 -*-
import unittest
from svgis import projection


class ProjectionTestCase(unittest.TestCase):

    def testUtm(self):
        assert projection.utm_proj4(-21, 42) == '+proj=utm +zone=27 +north +datum=WGS84 +units=m +no_defs'

        assert projection.utm_proj4(-21, -42) == '+proj=utm +zone=27 +south +datum=WGS84 +units=m +no_defs'

        with self.assertRaises(ValueError):
            projection.utm_proj4(-200, 100)


    def testLocalTm(self):
        fixture = ('+proj=lcc +lon_0=0 +lat_1=0 +lat_2=0 +lat_0=0'
                   '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0'
                   '+units=m +no_defs')
        self.assertEqual(projection.tm_proj4(0, 0, 0), fixture)

    def testReprojectBounds(self):
        bounds = [(-73, 42), (-74, 42), (-74, 43), (-73, 43), (-73, 42)]
        with self.assertRaises(TypeError):
            projection.reproject_bounds(None, {'init': 'epsg:4269'}, bounds)

        with self.assertRaises(TypeError):
            projection.reproject_bounds({'init': 'epsg:4269'}, None, bounds)

        a = projection.reproject_bounds({'init': 'epsg:4269'}, {'init': 'epsg:3102'}, bounds)

        fixture = (43332273.50269379, 15584115.894447982, 44004519.424246654, 16339179.938904058)

        for z in zip(a, fixture):
            self.assertAlmostEqual(*z)

    def testGenerateCRS(self):
        bounds = -82.2, 40.1, -78.9, 45.8
        a = projection.generatecrs(*bounds, use_proj='utm')
        self.assertEqual(a, '+proj=utm +zone=17 +north +datum=WGS84 +units=m +no_defs')

if __name__ == '__main__':
    unittest.main()
