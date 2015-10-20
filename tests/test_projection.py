import unittest
from svgis import projection


class ProjectionTestCase(unittest.TestCase):

    def testUtm(self):
        assert projection.utm_proj4(-21, 42) == '+proj=utm +zone=27 +north +datum=WGS84 +units=m +no_defs'

        assert projection.utm_proj4(-21, -42) == '+proj=utm +zone=27 +south +datum=WGS84 +units=m +no_defs'

    def testLocalTm(self):
        self.assertEqual(projection.tm_proj4(0, 0, 0), ('+proj=lcc +lon_0=0 +lat_1=0 +lat_2=0 +lat_0=0'
                                                        '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0'
                                                        '+units=m +no_defs'))
