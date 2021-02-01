#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command-line utilities for SVGIS."""
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://www.opensource.org/licenses/GNU General Public License v3 (GPLv3)-license
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import logging
import sys
import warnings

import click
import fiona.crs

from . import __version__, bounding
from . import graticule as _graticule
from . import projection
from . import style as _style
from . import svgis
from .utils import DEFAULT_GEOID, posint

none = {'flag_value': None, 'expose_value': False, 'help': '(not enabled)'}

try:
    # pylint: disable=unused-import
    import shapely

    clipkwargs = {
        'default': True,
        'flag_value': True,
        'help': "Clip shapes to bounds. Slightly slower, produces smaller files (default: clip).",
    }
except ImportError:
    clipkwargs = none

try:
    # pylint: disable=unused-import
    import visvalingamwyatt

    simplifykwargs = {
        'type': click.IntRange(1, 100, clamp=True),
        'metavar': 'FACTOR',
        'help': (
            'Simplify geometries, '
            'accepts an integer between 1 and 100, '
            'the percentage of each geometry to retain.'
        ),
    }
except ImportError:
    simplifykwargs = none

CLICKARGS = {'context_settings': dict(help_option_names=['-h', '--help'])}

csskwargs = {
    'flag_value': True,
    'default': True,
    'help': (
        'Inline CSS styles to each element. '
        'Slightly slower, but required by some clients (e.g. Adobe) '
        '(default: inline).'
    ),
}

inp = click.argument('layer', default=sys.stdin, type=click.File('rb'))
outp = click.argument('output', default=sys.stdout, type=click.File('wb'))


# Base
@click.group(**CLICKARGS)
@click.version_option(version=__version__, message='%(prog)s %(version)s')
@click.pass_context
def main(context):
    """Entry-point for svgis command-line interface."""
    context.log = logging.getLogger('svgis')
    context.log.setLevel(logging.WARN)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    context.log.addHandler(ch)


# Style
style_help = "Style to append to SVG. Either a valid CSS string, a file path (must end in '.css'). Use '-' for stdin."


@main.command()
@inp
@outp
@click.option('-c', '--style', type=str, help=style_help, default='')
@click.option('-r', '--replace', flag_value=True, help='Replace existing styles')
@click.option('--inline/--no-inline', '-l/ ', **csskwargs)
def style(layer, output, **kwargs):
    """Add or inline the CSS styles of an SVG"""
    result = _style.add_style(layer, kwargs['style'], kwargs['replace'])
    if kwargs['inline']:
        result = _style.inline(result)
    click.echo(result.encode('utf-8'), file=output)


@main.command()
@inp
@outp
@click.option('-f', '--scale', type=int)
def scale(layer, output, **kwargs):
    '''Scale all coordinates in an SVG by a factor'''
    click.echo(_style.rescale(layer, factor=kwargs['scale']).encode('utf-8'), file=output)


crs_help = (
    'Specify a map projection. '
    'Accepts either an EPSG code (e.g. epsg:4456), '
    'a proj4 string, '
    'a file containing a proj4 string, '
    '"utm" (use local UTM), '
    '"file" (use existing), '
    '"local" (generate a local projection)'
)


@main.command()
@click.argument('layer', type=click.Path(exists=True))
@click.option('-j', '--crs', type=str, metavar='KEYWORD', default='file', help=crs_help + ' (default: file)')
@click.option('--latlon', default=False, flag_value=True, help='Print bounds in latitude, longitude order')
def bounds(layer, crs, latlon=False):
    """Return the bounds for a given layer, optionally projected."""
    with fiona.Env():
        with fiona.open(layer, "r") as f:
            meta = {'bounds': f.bounds}
            meta.update(f.meta)

    warnings.filterwarnings("ignore")

    # If crs==file, these will basically be no ops.
    out_crs = projection.pick(crs, meta['bounds'], file_crs=meta['crs'])
    result = bounding.transform(meta['bounds'], in_crs=meta['crs'], out_crs=out_crs)

    if latlon:
        fmt = '{0[1]} {0[0]} {0[3]} {0[2]}'
    else:
        fmt = '{0[0]} {0[1]} {0[2]} {0[3]}'

    click.echo(fmt.format(result), file=sys.stdout)


# Draw
@main.command()
@click.argument('layer', nargs=-1, type=str, required=True)
@click.option('-o', '--output', default=sys.stdout, type=click.File('wb'), help="Defaults to stdout")
@click.option(
    '-b',
    '--bounds',
    nargs=4,
    type=float,
    metavar="minx miny maxx maxy",
    help='In the same coordinate system as the first input layer',
    default=None,
)
@click.option('-c', '--style', type=str, metavar='CSS', help="CSS file or string", multiple=True)
@click.option('-f', '--scale', type=int, default=None, help='Scale for the map (units are divided by this number)')
@click.option('-p', '--padding', type=int, default=None, required=None, help='Buffer the map (in projection units)')
@click.option('-i', '--id-field', type=str, metavar='FIELD', help='Geodata field to use as ID')
@click.option(
    '-a',
    '--class-fields',
    type=str,
    default='',
    metavar='FIELDS',
    multiple=True,
    help='Geodata fields to use as class (comma-separated)',
)
@click.option(
    '-a',
    '--data-fields',
    type=str,
    default='',
    metavar='FIELDS',
    multiple=True,
    help='Geodata fields to add as data-* attributes (comma-separated)',
)
@click.option('-j', '--crs', metavar='KEYWORD', type=str, help=crs_help)
@click.option('-s', '--simplify', **simplifykwargs)
@click.option(
    '-P',
    '--precision',
    metavar='INTEGER',
    type=posint,
    default=5,
    help='Rounding precision for coordinates (default: 5)',
)
@click.option('--clip/--no-clip', ' /-n', **clipkwargs)
@click.option('--inline/--no-inline', '-l/ ', **csskwargs)
@click.option('--viewbox/--no-viewbox', ' /-x', default=False, help='Draw SVG using a ViewBox (default: no ViewBox)')
@click.option('-q', '--quiet', default=False, flag_value=True, help='Ignore warnings')
@click.option('-v', '--verbose', default=False, count=True, help='Talk a lot')
def draw(layer, output, **kwargs):
    """Draw SVGs from input geodata"""
    log = logging.getLogger('svgis')

    verbose = kwargs.pop('verbose', None)
    if verbose:
        level = logging.DEBUG if verbose > 1 else logging.INFO
        log.setLevel(level)
        for h in log.handlers:
            h.setLevel(level)

    if kwargs.pop('quiet', None):
        log.handlers[0].setLevel(logging.ERROR)
        log.setLevel(logging.ERROR)

    click.echo(svgis.map(layer, **kwargs).encode('utf-8'), file=output)
    log.info('writing %s', output.name)


# Proj
@main.command()
@click.argument('bounds', nargs=-1, type=float, default=None)
@click.option('-m', '--method', default='local', type=click.Choice(('utm', 'local')), help='Defaults to local')
@click.option('-j', '--crs', default=DEFAULT_GEOID, help='Projection of the bounding coordinates')
def project(bounds, method, crs):
    """
    Get a local Transverse Mercator or UTM projection for a bounding box.
    Expects WGS84 coordinates.
    """
    # pylint: disable=redefined-outer-name
    if crs in projection.METHODS:
        click.echo('CRS must be an EPSG code, a Proj4 string, or file containing a Proj4 string.', err=1)
        return

    if len(bounds) == 2:
        bounds = bounds + bounds

    if len(bounds) != 4:
        click.echo('Either two or four bounds required', err=True)
        return

    result = projection.pick(method, file_crs=crs, bounds=bounds).to_proj4()
    click.echo(result.encode('utf-8'))


crs_help2 = (
    'Specify a map projection. '
    'Accepts either an EPSG code (e.g. epsg:4456), '
    'a proj4 string, '
    'a file containing a proj4 string, '
    '"utm" (use local UTM), '
    '"local" (generate a local projection)'
)


# Graticule
@main.command()
@click.argument('bounds', nargs=4, type=float, metavar='minx miny maxx maxy')
@click.option('-s', '--step', type=float, help='Step between lines (in projected units)', required=True)
@click.option('-j', '--crs', type=str, default=None, help=crs_help2)
@click.option('-o', '--output', default=sys.stdout, type=click.File('wb'), help="Defaults to stdout")
def graticule(bounds, step, crs, output):
    """
    Generate a GeoJSON containing a graticule.
    Accepts a bounding box in longitude and latitude (WGS84).
    """
    # pylint: disable=redefined-outer-name
    click.echo(_graticule.geojson(bounds, step, crs), file=output)
