# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

README.rst: README.md
	pandoc $< -o $@ || touch $@

.PHONY: test cov deploy

cov:
	coverage run --include='svgis/*' setup.py test
	coverage report
	coverage html
	open htmlcov/index.html

test: svgis/test_data/cb_2014_us_nation_20m.shp
	python setup.py test

	svgis draw -g 102003 -f 1000 $< -o tests/test.svg
	svgis style -s 'polygon{fill:green}' tests/test.svg > tests/test1.svg
	svgis scale -f 10 tests/test.svg > tests/test2.svg
	svgis project -m utm -110.277906 35.450777 -110.000477 35.649030
	svgis project -110.277906 35.450777 -110.000477 35.649030

	svgis draw -g 102003 -f 1000 $< | \
		svgis style -s 'polygon{fill:green}' - | \
		svgis scale -f 10 - > /dev/null

	@rm tests/test*.svg

svgis/test_data/cb_2014_us_nation_20m.shp: svgis/test_data/cb_2014_us_nation_20m.zip
	unzip -o $< -d $(@D)
	@touch $@

svgis/test_data/cb_2014_us_nation_20m.zip: svgis/test_data
	curl -o $@ http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_nation_20m.zip

svgis/test_data: ; mkdir -p $@

deploy:
	rm -rf dist build
	python3 setup.py bdist_wheel
	rm -rf build
	python setup.py sdist bdist_wheel
	twine upload dist/*
