#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>

"""
Create SVG drawings from vector geodata files (SHP, geoJSON, etc).
"""

from . import bounding
from . import draw
from . import errors
from . import projection
from . import svg
from . import style
from . import svgis
from . import transform
from .svgis import map, SVGIS

__version__ = '0.5.0'

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
