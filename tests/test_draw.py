import unittest
from svgis import draw, errors, svgis
import svgwrite.shapes
import svgwrite.container


class DrawTestCase(unittest.TestCase):

    def setUp(self):
        self.properties = {
            'cat': u'meow',
            'dog': 'woof'
        }

        self.classes = [u'foo', 'cat']

        self.lis1 = [[-110.6, 35.3], [-110.7, 35.5], [-110.3, 35.5], [-110.2, 35.1], [-110.2, 35.8], [-110.3, 35.2],
                     [-110.1, 35.8], [-110.8, 35.5], [-110.7, 35.7], [-110.1, 35.4], [-110.7, 35.1], [-110.6, 35.3]]

        lis2 = [[-110.8, 35.3], [-110.6, 35.4], [-110.1, 35.5], [-110.1, 35.5], [-110.4, 35.2],
                [-110.5, 35.1], [-110.5, 35.1], [-110.9, 35.8], [-110.5, 35.1], [-110.8, 35.3]]

        self.multipolygon = {
            "type": "MultiPolygon",
            "coordinates": [[self.lis1], [lis2]]
        }
        self.polygon = {
            "type": "Polygon",
            "coordinates": [self.lis1]
        }
        self.multilinestring = {
            'type': 'MultiLineString',
            'coordinates': [[(0, 0), (1, 1)], [(3, 2), (5, 1)]]
        }
        self.linestring = {
            'coordinates': [(0.0, 0), (1, 1)],
            'type': 'LineString'
        }
        self.point = {
            'coordinates': (0.0, 0),
            'type': 'Point'
        }

    def testDrawPoint(self):
        drawn = draw.point((0.0, 0.0), r=2)
        self.assertEqual((drawn.attribs['cx'], drawn.attribs['cy']), (0.0, 0))
        self.assertEqual(drawn.attribs['r'], 2)

        point = draw.points(self.point)
        assert isinstance(point, svgwrite.shapes.Circle)

        self.assertEqual((point.attribs['cx'], point.attribs['cy']), (0.0, 0))

        assert draw.geometry(self.point).attribs['cy'] == 0
        assert draw.geometry(self.point).attribs['cx'] == 0

        feat = svgis._draw_feature(self.point, self.properties, classes=self.classes)

        assert isinstance(feat, svgwrite.shapes.Circle)
        assert 'cat_meow' in feat.attribs['class']

    def testDrawLine(self):
        assert draw.linestring(self.linestring['coordinates']).points == self.linestring['coordinates']

        line = draw.lines(self.linestring)
        assert isinstance(line, svgwrite.shapes.Polyline)
        assert line.points == self.linestring['coordinates']

        feat = svgis._draw_feature(self.linestring, self.properties, classes=self.classes)

        assert isinstance(feat, svgwrite.shapes.Polyline)
        assert 'cat_meow' in feat.attribs['class']

    def testDrawMultiLine(self):
        mls1 = draw.multilinestring(self.multilinestring['coordinates'])
        mls2 = draw.lines(self.multilinestring)

        assert isinstance(mls1, svgwrite.container.Group)
        assert isinstance(mls2, svgwrite.container.Group)

        self.assertSequenceEqual(mls1.elements.pop(0).points, self.multilinestring['coordinates'][0])
        self.assertSequenceEqual(mls2.elements.pop(1).points, self.multilinestring['coordinates'][1])

        points = draw.geometry(self.multilinestring).elements.pop(1).points

        try:
            c0 = self.multilinestring['coordinates'][1][0].tolist()
            c1 = self.multilinestring['coordinates'][1][1].tolist()
            p0 = points[0].tolist()
            p1 = points[1].tolist()
        except AttributeError:
            c0 = self.multilinestring['coordinates'][1][0]
            c1 = self.multilinestring['coordinates'][1][1]
            p0 = points[0]
            p1 = points[1]

        self.assertSequenceEqual(p0, c0)
        self.assertSequenceEqual(p1, c1)

        with self.assertRaises(TypeError):
            draw.linestring(self.multilinestring['coordinates'])

        grp = svgis._draw_feature(self.multilinestring, self.properties, classes=self.classes)

        assert isinstance(grp, svgwrite.container.Group)
        assert 'cat_meow' in grp.elements[0].attribs['class']

    def testDrawPolygon(self):
        drawn = draw.polygon(self.polygon['coordinates'])

        assert len(drawn.points) == len(self.polygon['coordinates'][0])

        for (px, py), (nx, ny) in zip(drawn.points, self.polygon['coordinates'][0]):
            self.assertAlmostEqual(px, nx, 3)
            self.assertAlmostEqual(py, ny, 3)

        feat = svgis._draw_feature(self.polygon, self.properties, classes=self.classes)
        assert 'cat_meow' in feat.attribs['class']

    def testDrawMultiPolygon(self):
        drawn = draw.multipolygon(self.multipolygon['coordinates'])

        assert isinstance(drawn, svgwrite.container.Group)
        assert len(drawn.elements[0].points) == len(self.multipolygon['coordinates'][0][0])

        for (px, py), (nx, ny) in zip(drawn.elements[1].points, self.multipolygon['coordinates'][1][0]):
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
        self.assertIsInstance(polygon, svgwrite.path.Path)
        assert polygon.attribs['class'] == 'polygon'

        polygon = draw.polygon(coordinates, class_='a')
        assert polygon.attribs['class'] == 'polygon a'

    def testUnkownGeometry(self):
        with self.assertRaises(errors.SvgisError):
            draw.geometry({"type": "FooBar", "coordinates": []})

    def testGeometryCollection(self):
        gc = {
            "type": "GeometryCollection",
            "geometries": [
                self.polygon,
                self.linestring,
                self.point,
                self.multipolygon,
                self.multilinestring
            ],
        }
        a = draw.geometry(gc, id='cats')
        assert isinstance(a, svgwrite.container.Group)
        assert a.attribs['id'] == 'cats'

        assert any([isinstance(x, svgwrite.shapes.Polygon) for x in a.elements])
        assert any([isinstance(x, svgwrite.shapes.Circle) for x in a.elements])
        assert any([isinstance(x, svgwrite.shapes.Polyline) for x in a.elements])

if __name__ == '__main__':
    unittest.main()
