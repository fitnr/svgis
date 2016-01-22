# -*- coding: utf-8 -*-
from string import ascii_letters
import fionautil.coords

'''
Create string versions of SVG elements.
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


def circle(point, **kwargs):
    '''
    Write a svg circle element. Keyword arguments are mapped to attributes.
    :point tuple The center of the circle
    '''
    return '<circle cx="{0[0]}" cy="{0[1]}"'.format(point) + toattribs(**kwargs) + '/>'


def path(coordinates, **kwargs):
    '''
    Write an svg path element as a string.
    :coordinates Sequence A sequence of coordinates and string instructions
    '''
    attribs = toattribs(**kwargs)
    coords = []
    for i in coordinates:
        if isinstance(i, basestring):
            coords.append(i)
        else:
            coords.append('{0[0]},{0[1]}'.format(i))

    return '<path d="M ' + ' '.join(coords) + '"' + attribs + '/>'


def element(tag, coordinates, **kwargs):
    return (
        '<' + tag + ' points="' +
        ' '.join('{0[0]},{0[1]}'.format(c) for c in coordinates) +
        '"' + toattribs(**kwargs) + '/>'
    )


def toattribs(**kwargs):
    fmt = '{}="{}"'
    attribs = ' '.join(fmt.format(k, v) for k, v in kwargs.items() if v)

    if len(attribs) > 0:
        attribs = ' ' + attribs

    return attribs


def defstyle(style=None):
    '''Create a defs element with a css style'''
    if style:
        return '<defs><style type="text/css"><![CDATA[{}]]></style></defs>'.format(style)
    else:
        return '<defs />'


def group(members=None, **kwargs):
    '''Create a group with the given scale and translation'''
    attribs = toattribs(**kwargs)

    if members is None or len(members) == 0:
        return '<g' + attribs + ' />'

    return '<g' + attribs + '>' + ''.join(members) + '</g>'


def setviewbox(viewbox=None):
    if viewbox is None:
        return ''
    else:
        return ' viewBox="{},{},{},{}"'.format(*viewbox)


def drawing(size, members, viewbox=None, style=None):
    '''
    Create an SVG element.
    :size tuple width, height
    :members list Strings to add to output.
    :viewbox Sequence Four coordinates that describe a bounding box.
    :style string CSS string.
    '''
    svg = ('<svg baseProfile="full" version="1.1"'
           ' xmlns="http://www.w3.org/2000/svg"'
          )
    dimension = ' width="{}" height="{}"'.format(*size)
    vb = setviewbox(viewbox)
    defs = defstyle(style)

    return svg + dimension + vb + '>' + defs + ''.join(members) + '</svg>'
