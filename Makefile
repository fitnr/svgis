# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

PROJECTION = +proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs
QUIET ?= -q
PYTHONFLAGS = -W ignore

all: README.rst tests/test_data/cb_2014_us_nation_20m.shp

README.rst: README.md
	pandoc $< -o $@ || touch $@
	python setup.py check --restructuredtext --strict

.PHONY: all test cov deploy clean

cov:
	- coverage run --include='svgis/*' setup.py $(QUIET) test
	coverage report
	coverage html

profile: tests/profile.py
	python $(PYTHONFLAGS) -m cProfile -s tottime tests/profile.py 2>/dev/null | head -5
	@python $(PYTHONFLAGS) -m cProfile -s tottime $< | \
	grep -E '(svgis|draw|css|projection|svg|cli|clip|convert|errors).py'

test: tests/test_data/cb_2014_us_nation_20m.shp tests/test_data/test.svg
	python $(PYTHONFLAGS) setup.py $(QUIET) test

	svgis style -s 'polygon{fill:green}' $(lastword $^) > /dev/null
	svgis scale -f 10 $(lastword $^) > /dev/null
	svgis project -j utm -110.277906 35.450777 -110.000477 35.649030
	svgis project -110.277906 35.450777 -110.000477 35.649030

	svgis draw -j '$(PROJECTION)' -f 1000 $< | \
		svgis style -s 'polygon{fill:green}' - | \
		svgis scale -f 10 - > /dev/null

tests/test_data/test.svg: tests/test_data/cb_2014_us_nation_20m.shp
	svgis draw -j '$(PROJECTION)' -f 1000 -c "polygon { fill: blue }" --bounds -124 20.5 -64 49 $< -o $@

tests/test_data/cb_2014_us_nation_20m.shp: tests/test_data/cb_2014_us_nation_20m.zip
	unzip -q -o $< -d $(@D)
	@touch $@

tests/test_data/cb_2014_us_nation_20m.zip: tests/test_data
	curl -s -o $@ http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_nation_20m.zip

tests/test_data: ; mkdir -p $@

deploy: README.rst | clean
	python setup.py register
	python3 setup.py bdist_wheel
	rm -rf build
	python setup.py sdist bdist_wheel
	twine upload dist/*
	git push
	git push --tags

clean: ; rm -rf build dist
