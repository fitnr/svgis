#!/usr/bin/python
from __future__ import print_function, division
import argparse
from . import svg
from .import projection
from .svgis import SVGIS
import sys


def _echo(content, output):
    if hasattr(output, 'write'):
        output.write(content)
    else:
        open(output, 'w').write(content)


def _scale(layer, output, scale, **_):
    '''Rescale an SVG by a factor'''
    result = svg.rescale(layer, scale)
    _echo(result, output)


def _style(layer, output, style, replace=None, **_):
    '''Add a CSS string to an SVG's style attribute'''
    result = svg.add_style(layer, style, replace=replace)
    _echo(result, output)


def _draw(layers, output, bounds=None, scale=1, padding=0, **kwargs):
    '''Draw a geodata layer to a simple SVG'''
    scalar = (1 / scale) if scale else 1
    out_crs = None

    use_proj = None

    if kwargs.get('epsg'):
        out_crs = 'EPSG:' + kwargs.pop('epsg')
    elif kwargs.get('proj4'):
        out_crs = kwargs.pop('proj4')
    else:
        use_proj = kwargs.pop('use_proj', None)

    # get rid of pesky kwargs
    for x in ('use_proj', 'epsg', 'proj4'):
        kwargs.pop(x, None)

    # Try to read style file
    if kwargs.get('style'):
        try:
            kwargs['style'] = open(kwargs['style'], 'r').read()
        except IOError:
            pass

    if kwargs.get('class_fields'):
        kwargs['classes'] = kwargs.pop('class_fields').split(',')

    kwargs.pop('class_fields', None)

    drawing = SVGIS(layers, bounds=bounds, scalar=scalar, use_proj=use_proj,
                    out_crs=out_crs, padding=padding).compose(**kwargs)

    _echo(drawing.tostring(), output)


def _proj(_, output, minx, miny, maxx, maxy, use_proj=None):
    '''Return a transverse mercator projection for the given bounds'''
    prj = projection.generatecrs(minx, miny, maxx, maxy, use_proj)
    _echo(prj + '\n', output)


def main():
    parent = argparse.ArgumentParser(add_help=None)
    parent.add_argument('input', default='/dev/stdin', help="Input svg file")
    parent.add_argument('output', nargs='?', default='/dev/stdout', help="defaults to stdout")

    parser = argparse.ArgumentParser('svgis')
    sp = parser.add_subparsers()

    style = sp.add_parser('style', parents=[parent], help="Add a CSS style to an SVG")
    style.add_argument('-s', '--style', type=str, help="Style string to append to SVG")
    style.add_argument('-r', '--replace', action='store_true', help="Replace the SVG's style")
    style.set_defaults(function=_style)

    scale = sp.add_parser('scale', parents=[parent], help='Scale all coordinates in an SVG by a factor')
    scale.add_argument('-f', '--scale', type=int)
    scale.set_defaults(function=_scale)

    draw = sp.add_parser('draw', help='Draw SVGs from input geodata ')
    draw.add_argument('input', nargs='+', default='/dev/stdin', help="Input geodata layers")
    draw.add_argument('-o', '--output', default='/dev/stdout', help="defaults to stdout")
    draw.add_argument('--bounds', nargs=4, type=float, metavar=('minx', 'miny', 'maxx', 'maxy'),
                      help='In the same coordinate system as the input layers', default=None)

    draw.add_argument('-c', '--style', type=str, metavar='CSS', help="CSS file or string")
    draw.add_argument('-f', '--scale', type=int, default=1,
                      help='Scale for the map (units are divided by this number)')
    draw.add_argument('-p', '--padding', type=int, default=0, required=None,
                      help='Buffer the map bounds (in projection units)')

    draw.add_argument('-x', '--no-viewbox', action='store_false', dest='viewbox',
                      help='Draw SVG without a ViewBox. May improve compatibility.')

    draw.add_argument('--id-field', type=str, dest='id_field', help='Geodata field to use as ID')
    draw.add_argument('--class', type=str, dest='class_fields',
                      help='Geodata fields to use as class (comma-separated)')

    group = draw.add_mutually_exclusive_group()
    group.add_argument('-g', '--epsg', type=str, help='EPSG code to use in projecting output')
    group.add_argument('-j', '--proj4', type=str, help='Proj4 string defining projection use in output')
    group.add_argument('-m', '--projection-method', choices=('utm', 'local'), type=str, dest='use_proj',
                       help=('Projection to use: ',
                             'either the local UTM zone, or a custom Transverse Mercator projection'
                             'centered on the bounding box'))

    draw.set_defaults(function=_draw)

    proj = sp.add_parser('project', help='Get a local Transverse Mercator projection for a bounding box')
    proj.add_argument('minx', type=float, help='west')
    proj.add_argument('miny', type=float, help='south')
    proj.add_argument('maxx', type=float, help='east')
    proj.add_argument('maxy', type=float, help='north')
    proj.add_argument('-m', '--projection-method', dest='use_proj', choices=('utm', 'local'), type=str,)
    proj.set_defaults(function=_proj, input=None, output='/dev/stdout')

    args = parser.parse_args()

    non_keywords = ('function', 'layer', 'output', 'input')
    kwargs = {k: v for k, v in vars(args).items() if k not in non_keywords}

    if args.input in ('-', '/dev/stdin'):
        args.input = sys.stdin

    if args.output in ('-', '/dev/stdout'):
        args.output = sys.stdout

    args.function(args.input, args.output, **kwargs)


if __name__ == '__main__':
    main()
