#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

from __future__ import print_function, division
import sys
from signal import signal, SIGPIPE, SIG_DFL
import argparse
import logging

try:
    import shapely
    clipkwargs = {
        'action': 'store_false',
        'help': "Don't clip shapes to bounds. Faster, but possibly larger files"
    }
except ImportError:
    clipkwargs = {
        'action': 'store_const',
        'const': None,
        'help': argparse.SUPPRESS
    }

try:
    import lxml
    import cssselect
    import tinycss
    csskwargs = {
        'action': 'store_true',
        'help': 'Inline CSS. Slightly slower, but required by some clients (Adobe Illustrator)',
    }
except ImportError:
    csskwargs = {
        'action': 'store_const',
        'const': None,
        'help': argparse.SUPPRESS,
    }

try:
    import visvalingamwyatt
    simplifykwargs = {
        'type': float,
        'metavar': 'FACTOR',
        'help': 'Simplify geometries. Accepts a float, which it the ratio of points to keep in each geometry',
    }
except ImportError:
    simplifykwargs = {
        'action': 'store_const',
        'const': None,
        'help': argparse.SUPPRESS,
    }

from .formatter import CommandHelpFormatter, SubcommandHelpFormatter
from ..css import rescale, add_style
from ..projection import generatecrs
from .. import svgis
from .. import __version__ as version


def _echo(content, output):
    '''Print something to either a file-like object or a file name.'''
    if hasattr(output, 'write'):
        signal(SIGPIPE, SIG_DFL)
        output.write(content)
    else:
        with open(output, 'w') as w:
            w.write(content)


def _project(_, minx, miny, maxx, maxy, project=None):
    '''Return a transverse mercator projection for the given bounds'''
    prj = generatecrs(minx, miny, maxx, maxy, project)
    return prj + '\n'


def main():
    sys.tracebacklimit = 0

    log = logging.getLogger('svgis')
    log.setLevel(logging.WARN)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    log.addHandler(ch)

    parent = argparse.ArgumentParser(add_help=None)
    parent.add_argument('input', default='/dev/stdin', help="Input SVG file. Use '-' for stdin.")
    parent.add_argument('output', nargs='?', default='/dev/stdout', help="(optional) defaults to stdout")

    parser = argparse.ArgumentParser('svgis', formatter_class=CommandHelpFormatter)
    parser.add_argument('-V', action='version', version="%(prog)s " + version)
    sp = parser.add_subparsers()

    # Style

    style = sp.add_parser('style', parents=[parent], help="Add a CSS style to an SVG",
                          usage='%(prog)s [options] input [output]', formatter_class=SubcommandHelpFormatter)

    style.add_argument('-s', '--style', type=str, metavar='css', default='',
                       help=("Style to append to SVG. "
                             "Either a valid CSS string, a file path (must end in '.css'). "
                             "Use '-' for stdin."))

    style.add_argument('-r', '--replace', action='store_true', help="Replace the SVG's style")
    style.set_defaults(function=add_style)

    scale = sp.add_parser('scale', parents=[parent], help='Scale all coordinates in an SVG by a factor')
    scale.add_argument('-f', '--scale', dest='factor', type=int)
    scale.set_defaults(function=rescale)

    # Draw

    draw = sp.add_parser('draw', help='Draw SVGs from input geodata', formatter_class=SubcommandHelpFormatter)

    draw.add_argument('input', nargs='+', default='/dev/stdin', help="Input geodata layers")
    draw.add_argument('-o', '--output', default='/dev/stdout', help="defaults to stdout")

    draw.add_argument('--bounds', nargs=4, type=float, metavar=('minx', 'miny', 'maxx', 'maxy'),
                      help='In the same coordinate system as the input layers', default=None)

    draw.add_argument('-c', '--style', type=str, metavar='CSS', help="CSS file or string")

    draw.add_argument('-f', '--scale', type=int, default=1,
                      help='Scale for the map (units are divided by this number)')

    draw.add_argument('-p', '--padding', type=int, default=0, required=None,
                      help='Buffer the map bounds (in projection units)')

    draw.add_argument('-i', '--id-field', type=str, dest='id_field', help='Geodata field to use as ID')

    draw.add_argument('-a', '--class-fields', type=str, metavar='FIELDS', dest='class_fields',
                      help='Geodata fields to use as class (comma-separated)')

    draw.add_argument('-j', '--project', default='local', metavar='KEYWORD', type=str, dest='project',
                      help=('Specify a map projection. '
                            'Accepts either a valid EPSG code (e.g. epsg:4456), '
                            'a valid proj4 string, '
                            'a file containing a proj4, '
                            '"utm", '
                            '"file" (use existing), '
                            '"local" (generate a local projection)'))

    draw.add_argument('-s', '--simplify', **simplifykwargs)

    draw.add_argument('-n', '--no-clip', dest='clip', **clipkwargs)

    draw.add_argument('-x', '--no-viewbox', action='store_false', dest='viewbox',
                      help='Draw SVG without a ViewBox. May improve compatibility.')

    draw.add_argument('-l', '--inline-css', **csskwargs)

    draw.set_defaults(function=svgis.map)

    # Proj

    proj = sp.add_parser('project', formatter_class=SubcommandHelpFormatter,
                         help='Get a local Transverse Mercator projection for a bounding box. Expects WGS 84 coordinates.')
    proj.add_argument('minx', type=float, help='west')
    proj.add_argument('miny', type=float, help='south')
    proj.add_argument('maxx', type=float, help='east')
    proj.add_argument('maxy', type=float, help='north')
    proj.add_argument('-j', '--project', dest='project', choices=('utm', 'local'), type=str,)
    proj.set_defaults(function=_project, input=None, output='/dev/stdout')

    args = parser.parse_args()

    reserved = ('function', 'layer', 'output', 'input')
    kwargs = {k: v for k, v in vars(args).items() if k not in reserved}

    if args.input in ('-', '/dev/stdin'):
        args.input = sys.stdin

    if args.output in ('-', '/dev/stdout'):
        args.output = sys.stdout

    result = args.function(args.input, **kwargs)
    _echo(result, args.output)
