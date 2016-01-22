# -*- coding: utf-8 -*-
import sys
from xml.dom import minidom
from collections import Sequence
from string import ascii_letters
import fionautil.coords
import svgwrite.container

'''
Edit SVGs.
'''

def dims(boundary, padding=0):
    '''Return width and height based on an boundary ring and an optional padding'''
    x0, y0, x1, y1 = fionautil.coords.bounds(boundary)

    w = x1 - x0 + (padding * 2)
    h = y1 - y0 + (padding * 2)

    return w, h


def sanitize(x):
    '''Make input safe of use in an svg ID or class field'''
    try:
        string = x.replace(' ', '_')
        return string if string[0] in ('_-' + ascii_letters) else '_' + string

    except (AttributeError, IndexError):
        return ''


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
