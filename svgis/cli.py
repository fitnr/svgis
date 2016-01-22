#!/usr/bin/python
from __future__ import print_function, division
import os.path
import sys
from signal import signal, SIGPIPE, SIG_DFL
import argparse
import logging
import fiona.crs

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
    import visvalingamwyatt as vw
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

from . import css, projection, svg
from . import __version__ as version
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
    result = css.rescale(layer, scale)
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

    result = css.add_style(layer, style, replace=replace)
    _echo(result, output)


def _draw(layers, output, bounds=None, scale=1, padding=0, **kwargs):
    '''
    Draw a geodata layer to a simple SVG.
    :layers sequence Input geodata files.
    :output path Output file name
    :bounds sequence (minx, miny, maxx, maxy)
    :scale int Map scale. Larger numbers -> smaller maps
    :padding int Pad around bounds by this much. In projection units.
    :project string EPSG code, PROJ.4 string, or file containing a PROJ.4 string
    '''
    scalar = (1 / scale) if scale else 1
    style = None
    out_crs = None
    use_proj = None

    if kwargs.get('project', 'local').lower() in ('local', 'utm'):
        use_proj = kwargs.pop('project', 'local').lower()

    elif os.path.exists(kwargs['project']):
        # Is a file
        with open(kwargs.pop('project')) as f:
            out_crs = fiona.crs.from_string(f.read())

    elif kwargs['project'][:5].lower() == 'epsg:':
        # Is an epsg code
        _, epsg = kwargs.pop('project').split(':')
        out_crs = fiona.crs.from_epsg(int(epsg))

    else:
        # Assume it's a proj4 string.
        # fiona.crs.from_string returns {} if it isn't.
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
        style=style,
        clip=kwargs.pop('clip', True)
    ).compose(**kwargs)

    _echo(drawing, output)


def _proj(_, output, minx, miny, maxx, maxy, project=None):
    '''Return a transverse mercator projection for the given bounds'''
    prj = projection.generatecrs(minx, miny, maxx, maxy, project)
    _echo(prj + '\n', output)


class CommandHelpFormatter(argparse.RawDescriptionHelpFormatter):

    def _format_action(self, action):
        parts = super(CommandHelpFormatter, self)._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):

    def _format_action_invocation(self, action):
        sup = super(SubcommandHelpFormatter, self)

        if not action.option_strings:
            default = action.dest
            metavar, = sup._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)
            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            else:
                default = action.dest
                args_string = self._format_args(action, default)
                for option_string in action.option_strings[:-1]:
                    parts.append('%s' % (option_string))
                parts.append('%s %s' % (action.option_strings[-1], args_string))

            return ', '.join(parts)


def main():
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
    style.set_defaults(function=_style)

    scale = sp.add_parser('scale', parents=[parent], help='Scale all coordinates in an SVG by a factor')
    scale.add_argument('-f', '--scale', type=int)
    scale.set_defaults(function=_scale)

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

    draw.set_defaults(function=_draw)

    # Proj

    proj = sp.add_parser('project', formatter_class=SubcommandHelpFormatter,
                         help='Get a local Transverse Mercator projection for a bounding box. Expects WGS 84 coordinates.')
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
