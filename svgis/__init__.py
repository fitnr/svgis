#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

from . import clip
from . import convert
from . import draw
from . import errors
from . import projection
from . import svg
from . import style
from . import svgis
from .svgis import map, SVGIS

__version__ = '0.3.9'

__all__ = [
    'convert',
    'clip',
    'draw',
    'errors',
    'projection',
    'style',
    'svg',
    'svgis',
]
