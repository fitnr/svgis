#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

from . import test_cli
from . import test_convert
from . import test_draw
from . import test_error
from . import test_projection
from . import test_projection_draw
from . import test_svg
from . import test_svgis

__all__ = [
    'test_cli',
    'test_convert',
    'test_draw',
    'test_error',
    'test_projection',
    'test_projection_draw',
    'test_svg',
    'test_svgis',
]
