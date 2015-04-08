#!/usr/bin/python
from __future__ import print_function, division
import argparse
from fiona.crs import from_epsg
from . import svg
from .svgis import compose
from . import convert


def _echo(content, output):
    if hasattr(output, 'write'):
        output.write(content)
    else:
        open(output, 'w').write(content)


def _scale(layer, output, scale):
    '''Rescale an SVG by a factor'''
    result = svg.rescale(layer, scale)
    _echo(result, output)


def _style(layer, output, style, replace=None):
    '''Add a CSS string to an SVG's style attribute'''
    result = svg.add_style(layer, style, replace=replace)
    _echo(result, output)


def _draw(layer, output, mbr, scale, epsg, **kwargs):
    '''Draw a geodata layer to a simple SVG'''
    scale = scale or 1

    if epsg:
        crs = from_epsg(epsg)
    else:
        crs = None

    drawing = compose(layer, mbr, out_crs=crs, scalar=(1 / scale), **kwargs)

    _echo(drawing.tostring(), output)


def main():
    parent = argparse.ArgumentParser(add_help=None)
    parent.add_argument('output', nargs='?', default='/dev/stdout')

    parser = argparse.ArgumentParser('svgis')
    sp = parser.add_subparsers()

    style = sp.add_parser('style', parents=[parent])
    style.add_argument('-s', '--style', type=str, help="Style string to append to SVG")
    style.add_argument('-r', '--replace', action='store_true', help="Replace the SVG's style")
    style.set_defaults(function=_style)

    scale = sp.add_parser('scale', parents=[parent])
    scale.add_argument('-f', '--scale', type=int)
    scale.set_defaults(function=_scale)

    draw = sp.add_parser('draw', parents=[parent])
    draw.add_arguments('--bounds', nargs=4, type=float, help='The bounds in minx, miny, maxx, maxy format')
    draw.add_argument('-w', '--minx', type=float)
    draw.add_argument('-s', '--miny', type=float)
    draw.add_argument('-e', '--maxx', type=float)
    draw.add_argument('-n', '--maxy', type=float)
    draw.add_argument('-c', '--style', type=str, help="CSS string")
    draw.add_argument('-f', '--scale', type=int, default=1,
                      help='Scale for the map (units are divided by this number)')
    draw.add_argument('-p', '--padding', type=int, default=0, required=None,
                      help='Buffer the map bounds (in projection units)')
    draw.add_argument('-g', '--epsg', type=str, help='EPSG code to use in output map.')
    draw.add_argument('--utm', action='store_true', dest='use_utm', help='Draw map in local UTM projection.')
    draw.set_defaults(function=_draw)

    args = parser.parse_args()

    if hasattr(args, 'bounds'):
        bounds = convert.replacebounds(args.bounds, (args.minx, args.miny, args.maxx, args.maxy))

    non_keywords = ('function', 'layer', 'output', 'bounds', 'minx', 'miny', 'maxx', 'maxy')
    kwargs = {k: v for k, v in vars(args).items() if k not in non_keywords}

    args.function(args.layer, args.output, bounds, **kwargs)


if __name__ == '__main__':
    main()
