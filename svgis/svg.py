import sys
import svgwrite.container
from collections import Sequence
from xml.dom import minidom

def rescale(svgfile, factor):
    svg = minidom.parse(svgfile)

    scalar = 'scale({})'.format(factor)

    gs = svg.getElementsByTagName('g')[0]

    transform = gs[0].attributes.get('transform')

    if transform:
        transform.value = transform.value + ' ' + scalar
    else:
        gs[0].setAttribute('transform', scalar)

    return svg.toxml()


def add_style(svgfile, newstyle):
    svg = minidom.parse(svgfile)

    defs = svg.getElementsByTagName('defs').item(0)

    if defs.getElementsByTagName('style'):
        defs.getElementsByTagName('style').item(0).firstChild.replaceWholeText(newstyle)
    else:
        style = svg.createElement('style')
        css = svg.createTextNode(newstyle)
        style.appendChild(css)
        defs.appendChild(style)

    return svg.toxml()


def set_group(scale=None, translate=None, **kwargs):
    '''Create a group with the given scale and translation'''

    groupargs = {
        'fill': 'none',
        'stroke': 'black',
        'stroke_width': '0.1'
    }
    groupargs.update(kwargs)
    g = svgwrite.container.Group(**groupargs)

    if scale:
        g.scale(*scale)

    if translate:
        g.translate(*translate)

    return g


def save(filename, diameter, groups, profile=None):
    dwg = create(diameter, groups, profile)
    dwg.filename = filename
    dwg.save()


def create(size, groups, profile=None, style=None):
    profile = profile or 'full'

    if not isinstance(size, Sequence):
        size = (int(size), int(size))

    dwg = svgwrite.Drawing(profile=profile, size=size)

    if style:
        dwg.defs.add(dwg.style(style))

    for g in groups:
        dwg.add(g)

    return dwg


def write(filename, drawing):
    try:
        if filename == '-':
            f = sys.stdout
        else:
            f = open(filename, 'w')

        f.write(drawing.tostring())

    finally:
        if f != sys.stdout:
            f.close()
