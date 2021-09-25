#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create SVG drawings from vector geodata files (SHP, geoJSON, etc)."""
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>
# pylint: disable=redefined-builtin
from . import bounding, draw, errors, projection, style, svg, svgis, transform
from .svgis import SVGIS, map

__version__ = '0.5.2'

__all__ = [
    'bounding',
    'draw',
    'errors',
    'projection',
    'style',
    'svg',
    'svgis',
    'transform',
]
