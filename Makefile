# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

PROJECTION = +proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs
QUIET ?= -q
PYTHONFLAGS = -W ignore

.PHONY: test deploy clean test-cli fixtures

docs.zip: $(wildcard docs/*.rst docs/*/*.rst) src/svgis/__init__.py
	$(MAKE) -C $(<D) html
	cd $(<D)/_build/html; \
	zip -qr ../../../$@ . -x '*/.DS_Store' .DS_Store

profile: tests/profile.py
	python $(PYTHONFLAGS) -m cProfile -s tottime tests/profile.py 2>/dev/null | head -5
	@python $(PYTHONFLAGS) -m cProfile -s tottime $< | \
	grep -E '(svgis|draw|css|projection|svg|cli|clip|convert|errors).py'

coords = -110.277906 35.450777 -110.000477 35.649030

test-cli: tests/fixtures/cb_2014_us_nation_20m.json
	svgis project -m utm -- $(coords)
	svgis project -- $(coords)
	svgis project -m local -- $(wordlist 1,2,$(coords))
	svgis graticule -s 1 -- $(coords) | wc -l
	svgis bounds $<
	-svgis draw -f 1000 -j utm $< | wc -l
	svgis bounds $< | \
		xargs -n4 svgis draw -f 1000 -j '$(PROJECTION)' $< -b | \
		svgis style -c 'polygon{fill:green}' | \
		svgis scale -f 10 - | wc

coverage: | test
	coverage report
	coverage html

test: pyproject.toml
	coverage run --rcfile=$< -m unittest $(QUIET)

fixtures:
	$(MAKE) -C tests $@

format:
	black src tests

deploy: docs.zip | clean
	git push
	git push --tags
	flit publish

clean: ; rm -rf build dist
