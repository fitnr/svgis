# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

readme.rst: readme.md
	pandoc $< -o $@ || touch $@

.PHONY: test
test: tests/shp/cb_2014_us_nation_20m.shp
	python setup.py test

	svgis draw -g 102003 $< -o tests/test.svg

	svgis style --help
	
	svgis scale --help

tests/shp/cb_2014_us_nation_20m.shp: tests/shp/cb_2014_us_nation_20m.zip
	unzip $< -d $(@D)
	touch $@

tests/shp/cb_2014_us_nation_20m.zip: tests/shp
	curl -o $@ http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_nation_20m.zip

tests/shp: ; mkdir -p $@