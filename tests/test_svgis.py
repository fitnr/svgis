import unittest
from svgis import svgis
import svgwrite


class SvgisTestCase(unittest.TestCase):

    def setUp(self):
        self.file = 'tests/test_data/cb_2014_us_nation_20m.shp'

    def testSvgisCreate(self):
        svgis_obj = svgis.SVGIS(self.file)

        self.assertEqual(svgis_obj.files, [self.file])
        assert svgis_obj.mbr == (None,) * 4
        assert svgis_obj.out_crs is None
        assert svgis_obj.style == svgis.STYLE

        svgis_obj2 = svgis.SVGIS([self.file])
        assert svgis_obj2.files == [self.file]

        with self.assertRaises(ValueError):
            svgis.SVGIS(12)

    def testSvgisCompose(self):
        svgis_obj = svgis.SVGIS(self.file)
        composed = svgis_obj.compose()
        assert isinstance(composed, svgwrite.drawing.Drawing)

    def testSvgisClassFields(self):
        svgis_obj = svgis.SVGIS(self.file)
        composed = svgis_obj.compose(classes=('NAME', 'GEOID'))
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


if __name__ == '__main__':
    unittest.main()
