#!/usr/bin/python
from __future__ import print_function, division
import argparse
from . import svg
from . import layer as Layer


def _echo(content, output):
    if hasattr(output, 'write'):
        output.write(content)
    else:
        open(output, 'w').write(content)


def _scale(layer, output, scale):
    '''Rescale an SVG by a factor'''
    result = svg.rescale(layer, scale)
    _echo(result, output)


def _style(layer, output, style):
    '''Add a CSS string to an SVG's style attribute'''
    result = svg.add_style(layer, style)
    _echo(result, output)


def _draw(layer, output, minx=None, maxx=None, miny=None, maxy=None, scale=None):
    '''Draw a geodata layer to a simple SVG'''
    scale = scale or 1
    mbr = (minx, miny, maxx, maxy)

    result = Layer.compose(layer, mbr, scalar=(1 / scale))

    _echo(result, output)


def main():
    parent = argparse.ArgumentParser(add_help=None)
    parent.add_argument('layer', default='/dev/stdin')
    parent.add_argument('output', nargs='?', default='/dev/stdout')

    parser = argparse.ArgumentParser('svgis')
    sp = parser.add_subparsers()

    style = sp.add_parser('addstyle', parents=[parent])
    style.add_argument('-s', '--style', type=str, help="Style string to append to SVG")
    style.set_defaults(function=_style)

    scale = sp.add_parser('scale', parents=[parent])
    scale.add_argument('-f', '--scale', type=int)
    scale.set_defaults(function=_scale)

    draw = sp.add_parser('draw', parents=[parent])
    draw.add_argument('-w', '--minx', type=float, required=None)
    draw.add_argument('-s', '--miny', type=float, required=None)
    draw.add_argument('-e', '--maxx', type=float, required=None)
    draw.add_argument('-n', '--maxy', type=float, required=None)
    draw.add_argument('-f', '--scale', type=int, default='100', help='Scale for the map (units are divided by this number)')
    draw.set_defaults(function=_draw)

    args = parser.parse_args()
    kwargs = {k: v for k, v in vars(args).items() if k not in ('function', 'layer', 'output')}

    args.function(args.layer, args.output, **kwargs)


if __name__ == '__main__':
    main()
