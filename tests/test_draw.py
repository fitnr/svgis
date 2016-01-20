import unittest
from svgis import draw, errors, svgis
import svgwrite.shapes
import svgwrite.container
try:
    import numpy as np
except ImportError:
    pass

class DrawTestCase(unittest.TestCase):

    def setUp(self):
        self.properties = {
            'cat': u'meow',
            'dog': 'woof'
        }

        self.classes = [u'foo', 'cat']

        self.lis1 = [[-110.6, 35.3], [-110.7, 35.5], [-110.3, 35.5], [-110.2, 35.1], [-110.2, 35.8], [-110.3, 35.2],
                     [-110.1, 35.8], [-110.8, 35.5], [-110.7, 35.7], [-110.1, 35.4], [-110.7, 35.1], [-110.6, 35.3]]

    def testDrawPoint(self):
        drawn = draw.point((0.0, 0.0), r=2)
        self.assertEqual((drawn.attribs['cx'], drawn.attribs['cy']), (0.0, 0))
        self.assertEqual(drawn.attribs['r'], 2)

        geom = {
            'coordinates': (0.0, 0),
            'type': 'Point'
        }
        point = draw.points(geom)
        assert isinstance(point, svgwrite.shapes.Circle)

        self.assertEqual((point.attribs['cx'], point.attribs['cy']), (0.0, 0))

        assert draw.geometry(geom).attribs['cy'] == 0
        assert draw.geometry(geom).attribs['cx'] == 0

        feat = svgis._draw_feature(geom, self.properties, classes=self.classes)

        assert isinstance(feat, svgwrite.shapes.Circle)
        assert 'cat_meow' in feat.attribs['class']

    def testDrawLine(self):
        geom = {
            'coordinates': [(0.0, 0), (1, 1)],
            'type': 'LineString'
        }

        assert draw.linestring(geom['coordinates']).points == geom['coordinates']

        line = draw.lines(geom)
        assert isinstance(line, svgwrite.shapes.Polyline)
        assert line.points == geom['coordinates']

        feat = svgis._draw_feature(geom, self.properties, classes=self.classes)

        assert isinstance(feat, svgwrite.shapes.Polyline)
        assert 'cat_meow' in feat.attribs['class']

    def testDrawMultiLine(self):
        geom = {
            'coordinates': [[(0, 0), (1, 1)], [(3, 2), (5, 1)]],
            'type': 'MultiLineString'
        }
        mls1 = draw.multilinestring(geom['coordinates'])
        mls2 = draw.lines(geom)

        assert isinstance(mls1, svgwrite.container.Group)
        assert isinstance(mls2, svgwrite.container.Group)

        assert mls1.elements.pop(0).points == geom['coordinates'][0]
        assert mls2.elements.pop(1).points == geom['coordinates'][1]
        assert draw.geometry(geom).elements.pop(1).points == geom['coordinates'][1]

        with self.assertRaises(TypeError):
            draw.linestring(geom['coordinates'])

        grp = svgis._draw_feature(geom, self.properties, classes=self.classes)

        assert isinstance(grp, svgwrite.container.Group)
        assert 'cat_meow' in grp.elements[0].attribs['class']

    def testDrawPolygon(self):
        geom = {
            "type": "Polygon",
            "coordinates": [self.lis1]
        }

        drawn = draw.polygon(geom['coordinates'])

        assert len(drawn.points) == len(geom['coordinates'][0])

        for (px, py), (nx, ny) in zip(drawn.points, geom['coordinates'][0]):
            self.assertAlmostEqual(px, nx, 3)
            self.assertAlmostEqual(py, ny, 3)

        feat = svgis._draw_feature(geom, self.properties, classes=self.classes)
        assert 'cat_meow' in feat.attribs['class']

    def testDrawMultiPolygon(self):
        lis2 = [[-110.8, 35.3], [-110.6, 35.4], [-110.1, 35.5], [-110.1, 35.5], [-110.4, 35.2],
                [-110.5, 35.1], [-110.5, 35.1], [-110.9, 35.8], [-110.5, 35.1], [-110.8, 35.3]]

        geom = {
            "type": "MultiPolygon",
            "coordinates": [[self.lis1], [lis2]]
        }

        drawn = draw.multipolygon(geom['coordinates'])

        assert isinstance(drawn, svgwrite.container.Group)
        assert len(drawn.elements[0].points) == len(geom['coordinates'][0][0])

        for (px, py), (nx, ny) in zip(drawn.elements[1].points, geom['coordinates'][1][0]):
            self.assertAlmostEqual(px, nx, 3)
            self.assertAlmostEqual(py, ny, 3)

    def testAddClass(self):
        geom = {
            'coordinates': (0, 0),
            'type': 'Point'
        }
        point = draw.points(geom, class_=u'boston')
        self.assertIsInstance(point, svgwrite.shapes.Circle)

        point = draw.points(geom, class_='boston')
        assert isinstance(point, svgwrite.shapes.Circle)

    def testDrawPath(self):
        path = draw.path(self.lis1)
        assert isinstance(path, svgwrite.path.Path)

    def testDrawPolygonComplicated(self):
        coordinates = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
            [(4.0, 4.0), (4.0, 5.0), (5.0, 5.0), (5.0, 4.0), (4.0, 4.0)]
        ]

        polygon = draw.polygon(coordinates)
        assert isinstance(polygon, svgwrite.path.Path)
        assert polygon.attribs['class'] == 'polygon'

        polygon = draw.polygon(coordinates, class_='a')
        assert polygon.attribs['class'] == 'polygon a'

    def testRound(self):
        ring = [(10.00011111, 10.00011111), (10.00011111, 10.00011111)]
        assert draw._round_pt(ring[0], 1) == (10.0, 10.0)
        assert draw._round_ring(ring, 1) == [(10.0, 10.0), (10.0, 10.0)]

    def testRoundPolygonCoordinates(self):
        ring = [(0.00001, 0.0), (10.00111, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]

        try:
            rounded = np.round(np.array(ring)[:, 0:2], 3)
            rounded = rounded.tolist()
        except NameError:
            rounded = np.round(np.array(ring)[:, 0:2], 3)

        assert rounded[0] == [0.0, 0.0]

    def testUnkownGeometry(self):
        with self.assertRaises(errors.SvgisError):
            draw.geometry({"type": "GeometryCollection", "coordinates": []})

if __name__ == '__main__':
    unittest.main()
