#!/usr/bin/python
from __future__ import print_function, division
import sys
from signal import signal, SIGPIPE, SIG_DFL
import argparse
import fiona.crs
from . import projection, svg
from .svgis import SVGIS


sys.tracebacklimit = 0


def _echo(content, output):
    '''Print something to either a file-like object or a file name.'''
    if hasattr(output, 'write'):
        signal(SIGPIPE, SIG_DFL)
        output.write(content)
    else:
        with open(output, 'w') as w:
            w.write(content)


def _scale(layer, output, scale, **_):
    '''Rescale an SVG by a factor'''
    result = svg.rescale(layer, scale)
    _echo(result, output)


def _style(layer, output, style, replace=None, **_):
    '''Add a CSS string to an SVG's style attribute.
    :layer string Input svg file location
    :output mixed Either a file handle or filename
    :style string The input CSS, css file or '-'. Strings ending in ".css" are treated as files, "-" reads from stdin.
    '''
    if style == '-':
        style = sys.stdin.read()

    elif style[-4:] == '.css' or style == '/dev/stdin':
        with open(style) as f:
            style = f.read()

    result = svg.add_style(layer, style, replace=replace)
    _echo(result, output)


def _draw(layers, output, bounds=None, scale=1, padding=0, **kwargs):
    '''Draw a geodata layer to a simple SVG'''
    scalar = (1 / scale) if scale else 1
    style = None
    out_crs = None
    use_proj = None

    if kwargs.get('project', 'local').lower() in ('local', 'utm'):
        use_proj = kwargs.pop('project', 'local').lower()

    elif kwargs['project'][:4].lower() == 'epsg':
        epsg = kwargs.pop('project')
        out_crs = fiona.crs.from_epsg(int(epsg[5:]))

    else:  # I guess it's a proj4
        out_crs = fiona.crs.from_string(kwargs.pop('project'))

    # Try to read style file
    if kwargs.get('style'):
        if kwargs['style'][-3:] == 'css':
            try:
                with open(kwargs['style']) as f:
                    style = f.read()

            except IOError:
                print("Couldn't read {}, proceeding with default style".format(kwargs['style']), file=sys.stderr)

            finally:
                del kwargs['style']

        else:
            style = kwargs.pop('style')

    if kwargs.get('class_fields'):
        kwargs['classes'] = kwargs.pop('class_fields').split(',')

    kwargs.pop('class_fields', None)

    drawing = SVGIS(
        layers,
        bounds=bounds,
        scalar=scalar,
        use_proj=use_proj,
        out_crs=out_crs,
        padding=padding,
        style=style
    ).compose(**kwargs)

    _echo(drawing.tostring(), output)


def _proj(_, output, minx, miny, maxx, maxy, project=None):
    '''Return a transverse mercator projection for the given bounds'''
    prj = projection.generatecrs(minx, miny, maxx, maxy, project)
    _echo(prj + '\n', output)


def main():
    parent = argparse.ArgumentParser(add_help=None)
    parent.add_argument('input', default='/dev/stdin', help="Input SVG file. Use '-' for stdin.")
    parent.add_argument('output', nargs='?', default='/dev/stdout', help="(optional) defaults to stdout")

    parser = argparse.ArgumentParser('svgis')
    sp = parser.add_subparsers()

    style = sp.add_parser(
        'style', parents=[parent], usage='%(prog)s [options] input [output]', help="Add a CSS style to an SVG")
    style.add_argument('-s', '--style', type=str, metavar='css', default='',
                       help=("Style to append to SVG. "
                             "Either a valid CSS string, a file path (must end in '.css'). "
                             "Use '-' for stdin."))

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
    draw.add_argument('--class-fields', type=str, dest='class_fields',
                      help='Geodata fields to use as class (comma-separated)')

    draw.add_argument('-j', '--project', default='local', metavar='PROJECTION/KEYWORD', type=str, dest='project',
                      help=('Specify a map projection. '
                            'Accepts either a valid EPSG code (e.g. epsg:4456), '
                            'a valid proj4 string, '
                            'the keyword "utm" (use local UTM zone) or'
                            'the keyword "local" (generate a local projection)'))

    draw.set_defaults(function=_draw)

    proj = sp.add_parser(
        'project', help='Get a local Transverse Mercator projection for a bounding box. Expects WGS 84 coordinates.')
    proj.add_argument('minx', type=float, help='west')
    proj.add_argument('miny', type=float, help='south')
    proj.add_argument('maxx', type=float, help='east')
    proj.add_argument('maxy', type=float, help='north')
    proj.add_argument('-j', '--project', dest='project', choices=('utm', 'local'), type=str,)
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
