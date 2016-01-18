import os
import svgis.cli

shp = 'tests/test_data/cb_2014_us_nation_20m.shp'
css = 'polygon{fill:green}'
PROJECTION = '+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
BOUNDS = (-124.0, 20.5, -64.0, 49.0)

svgis.cli._draw(shp, os.devnull, style=css, scale=1000, project=PROJECTION, bounds=BOUNDS, clip=None)
