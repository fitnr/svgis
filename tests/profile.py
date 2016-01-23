#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

from svgis.cli import actions

if __name__ == '__main__':
    shp = 'tests/test_data/cb_2014_us_nation_20m.shp'
    css = 'polygon{fill:green}'
    PROJECTION = '+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
    BOUNDS = (-124.0, 20.5, -64.0, 49.0)

    actions.draw(shp, style=css, scale=1000, project=PROJECTION, bounds=BOUNDS, clip=None)
