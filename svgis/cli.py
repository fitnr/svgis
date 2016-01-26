#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import sys
import logging
import click
from .css import rescale, add_style
from .projection import generatecrs
from . import svgis, __version__


none = {
    'default': None,
    'expose_value': False
}

try:
    import shapely
    clipkwargs = {
        'default': False,
        'flag_value': True,
        'help': "Don't clip shapes to bounds. Faster, but possibly larger files"
    }
except ImportError:
    clipkwargs = none

try:
    import lxml
    import cssselect
    import tinycss
    csskwargs = {
        'flag_value': True,
        'default': False,
        'help': 'Inline CSS. Slightly slower, but required by some clients (Adobe Illustrator)',
    }
except ImportError:
    csskwargs = none

try:
    import visvalingamwyatt
    simplifykwargs = {
        'type': float,
        'metavar': 'FACTOR',
        'help': 'Simplify geometries. Accepts a float, which it the ratio of points to keep in each geometry',
    }
except ImportError:
    simplifykwargs = none

CLICKARGS = {
    'context_settings': dict(help_option_names=['-h', '--help'])
}

inp = click.argument('input', default=sys.stdin, type=click.File('rb'))
outp = click.argument('output', default=sys.stdout, type=click.File('wb'))

@click.group(**CLICKARGS)
@click.version_option(version=__version__)
@click.pass_context
def main(context):
    context.log = logging.getLogger('svgis')
    context.log.setLevel(logging.WARN)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    context.log.addHandler(ch)

# Style

style_help = ("Style to append to SVG. "
              "Either a valid CSS string, a file path (must end in '.css'). "
              "Use '-' for stdin.")


# @inp
@main.command()
@inp
@outp
@click.option('--style', '-s', type=str, help=style_help, default='')
@click.option('-r', '--replace', default=False)
def style(input, output, style, replace):
    """Add a CSS style to an SVG"""
    click.echo(add_style(input, style, replace), file=output)


@main.command()
@inp
@outp
@click.option('-f', '--scale', type=int)
def scale(input, output, scale):
    '''Scale all coordinates in an SVG by a factor'''
    click.echo(rescale(input, factor=scale), file=output)


project_help = ('Specify a map projection. '
                'Accepts either a valid EPSG code (e.g. epsg:4456), '
                'a valid proj4 string, '
                'a file containing a proj4, '
                '"utm", '
                '"file" (use existing), '
                '"local" (generate a local projection)')

# Draw
@main.command()
@click.argument('input', nargs=-1, type=str, required=True)
@click.option('-o', '--output', default=sys.stdout, type=click.File('wb'), help="defaults to stdout")
@click.option('--bounds', nargs=4, type=float, metavar="minx, miny, maxx, maxy", help='In the same coordinate system as the input layers', default=None)
@click.option('-c', '--style', type=str, metavar='CSS', help="CSS file or string")
@click.option('-f', '--scale', type=int, default=None, help='Scale for the map (units are divided by this number)')
@click.option('-p', '--padding', type=int, default=None, required=None, help='Buffer the map (in projection units)')
@click.option('-i', '--id-field', type=str, metavar='FIELD', help='Geodata field to use as ID')
@click.option('-a', '--class-fields', type=str, metavar='FIELDS', help='Geodata fields to use as class (comma-separated)')
@click.option('-j', '--project', default='local', metavar='KEYWORD', type=str, help=project_help)
@click.option('-s', '--simplify', **simplifykwargs)
@click.option('-n', '--no-clip', **clipkwargs)
@click.option('-x', '--no-viewbox', default=False, flag_value=True, help='Draw SVG without a ViewBox. May improve compatibility.')
@click.option('-l', '--inline-css', **csskwargs)
def draw(input, output, **kwargs):
    '''Draw SVGs from input geodata'''
    click.echo(svgis.map(input, **kwargs), file=output)


# Proj
@main.command()
@click.argument('bounds', nargs=4, type=float, metavar="minx, miny, maxx, maxy", default=None)
@click.option('-j', '--proj', default='local', type=click.Choice(('utm', 'local')), help='Defaults to local.')
def project(bounds, proj):
    '''Get a local Transverse Mercator or UTM projection for a bounding box. Expects WGS84 coordinates.'''
    click.echo(generatecrs(*bounds, use_proj=proj))
