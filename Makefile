# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

PROJECTION = +proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs

OSMQUERY = [out:xml][timeout:25]; \
    (way["highway"](41.8869593761126,12.486283779144287,41.89302938034043,12.49769926071167);); \
    out body;>;out skel qt;

all: README.rst svgis/test_data/cb_2014_us_nation_20m.shp

README.rst: README.md
	pandoc $< -o $@ || touch $@

.PHONY: all test cov deploy

cov:
	coverage run --include='svgis/*' setup.py test
	coverage report
	coverage html
	open htmlcov/index.html

test: svgis/test_data/cb_2014_us_nation_20m.shp svgis/test_data/test.svg
	python setup.py test

	svgis style -s 'polygon{fill:green}' $(lastword $^) > /dev/null
	svgis scale -f 10 $(lastword $^) > /dev/null
	svgis project -j utm -110.277906 35.450777 -110.000477 35.649030
	svgis project -110.277906 35.450777 -110.000477 35.649030

	svgis draw -j '$(PROJECTION)' -f 1000 $< | \
		svgis style -s 'polygon{fill:green}' - | \
		svgis scale -f 10 - > /dev/null

svgis/test_data/test.svg: svgis/test_data/cb_2014_us_nation_20m.shp
	svgis draw -j '$(PROJECTION)' -f 1000  --bounds -124 20.5 -64 49 $< -o $@

svgis/test_data/cb_2014_us_nation_20m.shp: svgis/test_data/cb_2014_us_nation_20m.zip
	unzip -q -o $< -d $(@D)
	@touch $@

svgis/test_data/cb_2014_us_nation_20m.zip: svgis/test_data
	curl -s -o $@ http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_nation_20m.zip

svgis/test_data/sample.osm:
	curl -s -o $@ http://overpass-api.de/api/interpreter --data "$(OSMQUERY)"

svgis/test_data: ; mkdir -p $@

deploy:
	rm -rf dist build
	python3 setup.py bdist_wheel
	rm -rf build
	python setup.py sdist bdist_wheel
	twine upload dist/*
