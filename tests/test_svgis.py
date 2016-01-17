import unittest
from svgis import svgis
import svgwrite


class SvgisTestCase(unittest.TestCase):

    def setUp(self):
        self.file = 'tests/test_data/cb_2014_us_nation_20m.shp'
        self.svgis_obj = svgis.SVGIS(self.file)

    def testSvgisCreate(self):
        self.assertEqual(self.svgis_obj.files, [self.file])
        assert self.svgis_obj.mbr == (None,) * 4
        assert self.svgis_obj.out_crs is None
        assert self.svgis_obj.style == svgis.STYLE

        svgis_obj2 = svgis.SVGIS([self.file])
        assert svgis_obj2.files == [self.file]

        with self.assertRaises(ValueError):
            svgis.SVGIS(12)

    def testSvgisCompose(self):
        composed = self.svgis_obj.compose()
        assert isinstance(composed, svgwrite.drawing.Drawing)

    def testSvgisClassFields(self):
        composed = self.svgis_obj.compose(classes=('NAME', 'GEOID'))
        self.assertIn('class="NAME_United_States GEOID_US cb_2014_us_nation_20m"', composed.tostring())

    def testCreateClasses(self):
        classes = svgis._construct_classes(('apple', 'potato'), {'apple': 'fruit'})
        self.assertEqual(classes, 'apple_fruit potato')

        classes = svgis._construct_classes(('apple', 'potato'), {'apple': u'fruit'})
        self.assertEqual(classes, 'apple_fruit potato')

    def testCreateClassesMissing(self):
        classes = svgis._construct_classes(('apple', 'potato'), {'apple': ''})
        self.assertEqual(classes, 'apple_ potato')

        classes = svgis._construct_classes(('apple', 'potato'), {'apple': None})
        self.assertEqual(classes, 'apple_None potato')

    def testRepr(self):
        self.assertEqual(str(self.svgis_obj), ("SVGIS(files=['tests/test_data/cb_2014_us_nation_20m.shp'], "
                'out_crs=None, '
                'bounds=(), padding=0, '
                'scalar=1)'))


if __name__ == '__main__':
    unittest.main()
