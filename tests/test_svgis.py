import unittest
import re
import svgwrite.shapes
from svgis import svgis, errors
try:
    basestring
except NameError:
    basestring = str

class SvgisTestCase(unittest.TestCase):

    def setUp(self):
        self.file = 'tests/test_data/cb_2014_us_nation_20m.shp'
        self.svgis_obj = svgis.SVGIS(self.file)

    def testSvgisError(self):
        with self.assertRaises(errors.SvgisError):
            raise errors.SvgisError('This is an error')

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
        assert isinstance(composed, basestring)

    def testSvgisClassFields(self):
        composed = self.svgis_obj.compose(classes=('NAME', 'GEOID'))
        match = re.search(r'class="(.+)"', composed)
        self.assertIsNotNone(match)
        self.assertIn('NAME_United_States', match.groups()[0])
        self.assertIn('GEOID_US', match.groups()[0])
        self.assertIn('cb_2014_us_nation_20m', match.groups()[0])

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
        expected = ("SVGIS(files=['tests/test_data/cb_2014_us_nation_20m.shp'], "
                    'out_crs=None, bounds=(), padding=0, scalar=1)')
        self.assertEqual(str(self.svgis_obj), expected)

    def testDrawGeometry(self):
        geom = {
            'type': 'LineString',
            'coordinates': [[-110.8, 35.3], [-110.9, 35.8], [-110.5, 35.1], [-110.8, 35.3]]
        }
        props = {
            'foo': 'bar',
            'cat': 'meow'
        }
        drawn = svgis._draw_feature(geom, properties=props, classes=['foo'], id_field='cat')
        assert isinstance(drawn, svgwrite.shapes.Polyline)
        stringed = drawn.tostring()
        self.assertIn('id="meow"', stringed)
        assert 'class="foo_bar"' in stringed

    def testConstructClasses(self):
        self.assertEqual(svgis._construct_classes('foo', {'foo': 'bar'}), 'foo_bar')
        self.assertEqual(svgis._construct_classes(['foo'], {'foo': 'bar'}), 'foo_bar')

        self.assertEqual(svgis._construct_classes(['foo'], {'foo': None}), 'foo_None')

if __name__ == '__main__':
    unittest.main()
