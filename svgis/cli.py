#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import sys
from signal import signal, SIGPIPE, SIG_DFL
import logging
import click
from .projection import generatecrs
from . import style as _style, svgis, __version__


none = {
    'flag_value': None,
    'expose_value': False,
    'help': '(not enabled)'
}

try:
    import shapely
    clipkwargs = {
        'default': True,
        'flag_value': True,
        'help': "Clip shapes to bounds. Slightly slower, produces smaller files (default: clip)."
    }
except ImportError:
    clipkwargs = none

try:
    import visvalingamwyatt
    simplifykwargs = {
        'type': click.IntRange(1, 100, clamp=True),
        'metavar': 'FACTOR',
        'help': ('Simplify geometries, '
                 'accepts an integer between 1 and 100, '
                 'the percentage of each geometry to retain.'),
    }
except ImportError:
    simplifykwargs = none

CLICKARGS = {
    'context_settings': dict(help_option_names=['-h', '--help'])
}

csskwargs = {
    'flag_value': True,
    'default': False,
    'help': ('Inline CSS styles to each element. '
             'Slightly slower, but required by some clients (e.g. Adobe) '
             '(default: do not inline).'
            ),
}

inp = click.argument('input', default=sys.stdin, type=click.File('rb'))
outp = click.argument('output', default=sys.stdout, type=click.File('wb'))


# Base
@click.group(**CLICKARGS)
@click.version_option(version=__version__, message='%(prog)s %(version)s')
@click.pass_context
def main(context):
    context.log = logging.getLogger('svgis')
    context.log.setLevel(logging.WARN)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    context.log.addHandler(ch)

    signal(SIGPIPE, SIG_DFL)


# Style
style_help = ("Style to append to SVG. "
              "Either a valid CSS string, a file path (must end in '.css'). "
              "Use '-' for stdin.")


@main.command()
@inp
@outp
@click.option('--style', '-s', type=str, help=style_help, default='')
@click.option('-r', '--replace', flag_value=True, help='Replace existing styles')
@click.option('--inline/--no-inline', '-l/ ', **csskwargs)
def style(input, output, **kwargs):
    """Add or inline the CSS styles of an SVG"""
    result = _style.add_style(input, kwargs['style'], kwargs['replace'])
    if kwargs['inline']:
        result = _style.inline(result)
    click.echo(result.encode('utf-8'), file=output)


@main.command()
@inp
@outp
@click.option('-f', '--scale', type=int)
def scale(input, output, **kwargs):
    '''Scale all coordinates in an SVG by a factor'''
    click.echo(_style.rescale(input, factor=kwargs['scale']).encode('utf-8'), file=output)


project_help = ('Specify a map projection. '
                'Accepts either a valid EPSG code (e.g. epsg:4456), '
                'a valid proj4 string, '
                'a file containing a proj4, '
                '"utm", '
                '"file" (use existing), '
                '"local" (generate a local projection).')


# Draw
@main.command()
@click.argument('input', nargs=-1, type=str, required=True)
@click.option('-o', '--output', default=sys.stdout, type=click.File('wb'), help="Defaults to stdout.")
@click.option('-b', '--bounds', nargs=4, type=float, metavar="minx, miny, maxx, maxy", help='In the same coordinate system as the input layers', default=None)
@click.option('-c', '--style', type=str, metavar='CSS', help="CSS file or string")
@click.option('-f', '--scale', type=int, default=None, help='Scale for the map (units are divided by this number)')
@click.option('-p', '--padding', type=int, default=None, required=None, help='Buffer the map (in projection units)')
@click.option('-i', '--id-field', type=str, metavar='FIELD', help='Geodata field to use as ID')
@click.option('-a', '--class-fields', type=str, default='', metavar='FIELDS', help='Geodata fields to use as class (comma-separated)')
@click.option('-j', '--project', default='local', metavar='KEYWORD', type=str, help=project_help)
@click.option('-s', '--simplify', **simplifykwargs)
@click.option('--clip/--no-clip', ' /-n', **clipkwargs)
@click.option('--viewbox/--no-viewbox',  ' /-x', default=True, help='Draw SVG with or without a ViewBox. Drawing without may improve compatibility.')
@click.option('--inline/--no-inline', '-l/ ', **csskwargs)
def draw(input, output, **kwargs):
    '''Draw SVGs from input geodata'''
    click.echo(svgis.map(input, **kwargs).encode('utf-8'), file=output)


# Proj
@main.command()
@click.argument('bounds', nargs=4, type=float, metavar="minx, miny, maxx, maxy", default=None)
@click.option('-m', '--method', default='local', type=click.Choice(('utm', 'local')), help='Defaults to local.')
def project(bounds, method):
    '''Get a local Transverse Mercator or UTM projection for a bounding box. Expects WGS84 coordinates.'''
    click.echo(generatecrs(*bounds, proj_method=method).encode('utf-8'))
