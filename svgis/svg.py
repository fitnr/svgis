'''Edit SVGs'''
# -*- coding: utf-8 -*-
import sys
import warnings
import svgwrite.container
from collections import Sequence
from xml.dom import minidom
import fionautil.coords

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


def dims(boundary, padding=0):
    '''Return width and height based on an boundary ring and an optional padding'''
    x0, y0, x1, y1 = fionautil.coords.bounds(boundary)

    w = x1 - x0 + (padding * 2)
    h = y1 - y0 + (padding * 2)

    return w, h

def add_style(svgfile, newstyle, replace=False):
    '''Add to the CSS style in an SVG file.
    svgfile -- Path to an SVG file
    newstyle -- CSS string
    replace -- (boolean) If true, replace the existing CSS with newstyle (default: False)
    '''
    svg = minidom.parse(svgfile)

    defs = svg.getElementsByTagName('defs').item(0)

    if not defs:
        defs = svg.createElement('defs')

        if not hasattr(svg, 'tagName'):
            elem = svg.getElementsByTagName('svg').item(0)
            elem.insertBefore(defs, elem.firstChild)

        else:
            svg.insertBefore(defs, svg.firstChild)

    if defs.getElementsByTagName('style'):
        style = defs.getElementsByTagName('style').item(0)

        if replace:
            style.firstChild.replaceWholeText(newstyle)
        else:
            style.firstChild.nodeValue += ' ' + newstyle

    else:
        style = svg.createElement('style')
        css = svg.createTextNode(newstyle)
        style.appendChild(css)
        defs.appendChild(style)

    return svg.toxml()


def set_group(members=None, scale=None, translate=None, **kwargs):
    '''Create a group with the given scale and translation'''

    groupargs = {
        'fill': 'none',
        'stroke': 'black',
    }
    groupargs.update(kwargs)
    g = svgwrite.container.Group(**groupargs)

    members = members or []

    for m in members:
        g.add(m)

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

    if size[0] > 16384 or size[1] > 16384:
        warnings.warn("SVG is very large. May not work for all clients. "
                      "If it doesn't work, try a larger scale factor.", RuntimeWarning)

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

    except IOError:
        raise

    finally:
        try:
            if f != sys.stdout:
                f.close()
        except UnboundLocalError:
            pass
