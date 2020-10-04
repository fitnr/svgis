# -*- coding: utf-8 -*-
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2015-16, Neil Freeman <contact@fakeisthenewreal.org>

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import logging

logger = logging.getLogger('svgis')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

TEST_SVG = """<svg baseProfile="full" height="1" version="1.1" xmlns="http://www.w3.org/2000/svg">
    <defs></defs>
    <g>
        <g id="test">
            <polygon class="test" points="3,2 -2,6 8,-1 8,2 4,1 3,2" />
        </g>
        <g id="foo">
            <polyline id="baz" class="foo" points="3,2 -2,6 8,-1"></polyline>
        </g>
        <g id="cat">
            <polyline id="meow" class="long-class-name" points="3,2 -2,6 8,-1"></polyline>
            <circle id="orb" cx="1" cy="1"></circle>
        </g>
    </g>
</svg>"""

TEST_CSS = """
polygon {fill: orange;}
.test { stroke: green; }
polyline { stroke: blue}
.test, #baz { stroke-width: 2; }
#test ~ #foo { fill: purple; }
#cat polyline { fill: red }
#meow { stroke-opacity: 0.50 }
circle { r: 1; }
"""
