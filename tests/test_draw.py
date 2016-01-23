import unittest
from svgis import draw, errors, svgis
try:
    import numpy as np
except ImportError:
    pass

try:
    basestring
except NameError:
    basestring = str


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
            "id": "MultiPolygon",
            "coordinates": [[self.lis1], [lis2]]
        }
        self.polygon = {
            "type": "Polygon",
            "id": "Polygon",
            "coordinates": [self.lis1]
        }
        self.multilinestring = {
            'type': 'MultiLineString',
            "id": "MultiLineString",
            'coordinates': [lis2, lis2]
        }
        self.linestring = {
            'coordinates': lis2,
            'type': 'LineString',
            "id": "LineString",
        }
        self.point = {
            'coordinates': (0.0, 0),
            'type': 'Point',
            "id": "Point",
        }

    def testDrawPoint(self):
        feat = svgis._draw_feature(self.point, self.properties, classes=self.classes)

        assert isinstance(feat, basestring)
        self.assertIn('cat_meow', feat)

    def testDrawLine(self):
        line = draw.lines(self.linestring)
        assert isinstance(line, basestring)

        feat = svgis._draw_feature(self.linestring, self.properties, classes=self.classes)

        assert isinstance(feat, basestring)
        assert 'cat_meow' in feat

    def testDrawMultiLine(self):
        mls1 = draw.multilinestring(self.multilinestring['coordinates'])
        mls2 = draw.lines(self.multilinestring)

        assert isinstance(mls1, basestring)
        assert isinstance(mls2, basestring)

        grp = svgis._draw_feature(self.multilinestring, self.properties, classes=self.classes)

        assert isinstance(grp, basestring)
        assert 'cat_meow' in grp

    def testDrawPolygon(self):
        drawn = draw.polygon(self.polygon['coordinates'])
        assert "{},{}".format(*self.lis1[0]) in drawn
        feat = svgis._draw_feature(self.polygon, self.properties, classes=self.classes)
        assert 'cat_meow' in feat

    def testDrawMultiPolygon(self):
        drawn = draw.multipolygon(self.multipolygon['coordinates'])

        assert isinstance(drawn, basestring)

    def testAddClass(self):
        geom = {
            'coordinates': (0, 0),
            'type': 'Point'
        }
        kwargs = {
            "class": "boston"
        }
        point = draw.points(geom, **kwargs)
        self.assertIsInstance(point, basestring)

        point = draw.points(geom, **kwargs)
        assert isinstance(point, basestring)

    def testDrawPolygonComplicated(self):
        coordinates = [
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
            [(4.0, 4.0), (4.0, 5.0), (5.0, 5.0), (5.0, 4.0), (4.0, 4.0)]
        ]

        polygon = draw.polygon(coordinates)
        self.assertIsInstance(polygon, basestring)
        assert 'class="polygon"' in polygon

        kw = {'class': 'a'}
        assert 'polygon a' in draw.polygon(coordinates, **kw)

    def testUnkownGeometry(self):
        with self.assertRaises(errors.SvgisError):
            draw.geometry({"type": "FooBar", "coordinates": []})

    def testGeometryCollection(self):
        gc = {
            "type": "GeometryCollection",
            "id": "GC",
            "geometries": [
                self.polygon,
                self.linestring,
                self.point,
                self.multipolygon,
                self.multilinestring
            ],
        }
        a = draw.geometry(gc, id='cats')
        assert isinstance(a, basestring)
        assert 'id="cats"' in a

    def testDrawAndConvertToString(self):
        draw.geometry(self.linestring)
        draw.geometry(self.multilinestring)
        draw.geometry(self.polygon)
        draw.geometry(self.multipolygon)

if __name__ == '__main__':
    unittest.main()
