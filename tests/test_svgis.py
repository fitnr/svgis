import unittest
from svgis import svgis
import svgwrite
from pkg_resources import resource_filename

class SvgisTestCase(unittest.TestCase):

    def setUp(self):
        self.file = resource_filename('svgis', 'test_data/cb_2014_us_nation_20m.shp')

    def testSvgisCreate(self):
        svgis_obj = svgis.SVGIS(self.file)

        self.assertEqual(svgis_obj.files, [self.file])
        assert svgis_obj.mbr == (None,) * 4
        assert svgis_obj.out_crs == None
        assert svgis_obj.style == svgis.STYLE

        svgis_obj2 = svgis.SVGIS([self.file])
        assert svgis_obj2.files == [self.file]

        with self.assertRaises(ValueError):
            svgis.SVGIS(12)

    def testSvgisCompose(self):
        svgis_obj = svgis.SVGIS(self.file)
        composed = svgis_obj.compose()
        assert type(composed) == svgwrite.drawing.Drawing


    def testSvgisClassFields(self):
        svgis_obj = svgis.SVGIS(self.file)
        composed = svgis_obj.compose(classes=('NAME', 'GEOID'))
        assert 'class="United_States US"' in composed.tostring()
