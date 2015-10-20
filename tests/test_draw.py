import unittest
from svgis import draw


class DrawTestCase(unittest.TestCase):

    def setUp(self):
        self.lis1 = [[-110.277906, 35.590313], [-110.271087, 35.590375], [-110.26093, 35.590865], [-110.259592, 35.590881], [-110.250972, 35.590888], [-110.250543, 35.590882], [-110.248341, 35.591048], [-110.247998, 35.591065], [-110.230537, 35.59107], [-110.228281, 35.591044], [-110.2257, 35.591041], [-110.277906, 35.590313]]

    def testDrawPoint(self):
        drawn = draw.point((0, 0), r=2)
        self.assertEqual((drawn.attribs['cx'], drawn.attribs['cy']), (0, 0))
        self.assertEqual(drawn.attribs['r'], 2)

        geom = {
            'coordinates': (0, 0),
            'type': 'Point'
        }
        points = draw.points(geom)
        assert len(points) == 1
        self.assertEqual((points[0].attribs['cx'], points[0].attribs['cy']), (0, 0))

        assert draw.geometry(geom).pop(0).attribs['cy'] == 0
        assert draw.geometry(geom).pop(0).attribs['cx'] == 0

    def testDrawLine(self):
        geom = {
            'coordinates': [(0, 0), (1, 1)],
            'type': 'LineString'
        }

        assert draw.linestring(geom['coordinates']).points == geom['coordinates']

        lines = draw.lines(geom)
        assert len(lines) == 1
        assert lines[0].points == geom['coordinates']

    def testDrawMultiLine(self):
        geom = {
            'coordinates': [[(0, 0), (1, 1)], [(3, 2), (5, 1)]],
            'type': 'MultiLineString'
        }
        mls1 = draw.multilinestring(geom['coordinates'])
        mls2 = draw.lines(geom)

        assert mls1.pop(0).points == geom['coordinates'][0]
        assert mls2.pop(1).points == geom['coordinates'][1]
        assert draw.geometry(geom).pop(1).points == geom['coordinates'][1]

        with self.assertRaises(TypeError):
            draw.linestring(geom['coordinates'])

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

    def testDrawMultiPolygon(self):
        lis2 = [[-110.005828, 35.498343], [-110.008466, 35.498454], [-110.014261, 35.498655], [-110.019361, 35.499385], [-110.021204, 35.499652], [-110.025195, 35.50001], [-110.028655, 35.50001], [-110.034659, 35.496338], [-110.032935, 35.49411], [-110.005828, 35.498343]]

        geom = {
            "type": "MultiPolygon",
            "coordinates": [[self.lis1], [lis2]]
        }

        drawn = draw.multipolygon(geom['coordinates'])

        assert type(drawn) == list
        assert len(drawn[0].points) == len(geom['coordinates'][0][0])

        for (px, py), (nx, ny) in zip(drawn[1].points, geom['coordinates'][1][0]):
            self.assertAlmostEqual(px, nx, 3)
            self.assertAlmostEqual(py, ny, 3)
