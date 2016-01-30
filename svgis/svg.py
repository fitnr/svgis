#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

'''
Create string versions of SVG elements.
'''



def circle(point, **kwargs):
    '''
    Write a svg circle element. Keyword arguments are mapped to attributes.

    Args:
        point (tuple): The center of the circle
    '''
    return u'<circle cx="{0[0]}" cy="{0[1]}"'.format(point) + toattribs(**kwargs) + '/>'


def _isstr(x):
    return isinstance(x, basestring)


def path(coordinates, **kwargs):
    '''
    Write an svg path element as a string.

    Args:
        coordinates (Sequence): A sequence of coordinates and string instructions
    '''
    attribs = toattribs(**kwargs)
    coords = [i if _isstr(i) else u'{0[0]},{0[1]}'.format(i) for i in coordinates]

    return u'<path d="M ' + ' '.join(coords) + '"' + attribs + '/>'


def element(tag, coordinates, **kwargs):
    return (
        u'<' + tag + ' points="' +
        ' '.join('{0[0]},{0[1]}'.format(c) for c in coordinates) +
        '"' + toattribs(**kwargs) + '/>'
    )


def toattribs(**kwargs):
    attribs = u' '.join(u'{}="{}"'.format(k, v) for k, v in kwargs.items() if v)

    if len(attribs) > 0:
        attribs = ' ' + attribs

    return attribs


def defstyle(style=None):
    '''
    Create a defs element that wraps a CSS style.

    Args:
        style (string): A CSS string.

    Returns:
        unicode
    '''
    if style:
        return u'<defs><style type="text/css"><![CDATA[{}]]></style></defs>'.format(style)
    else:
        return u'<defs />'


def group(members=None, **kwargs):
    '''
    Create a group with the given scale and translation.

    Args:
        members (Sequence): unicode SVG elements
        kwargs (dict): elements of this dictionary will be converted to
                        attributes of the group, i.e. key="value".

    Returns:
        unicode
    '''
    attribs = toattribs(**kwargs)

    if not members:
        return u'<g' + attribs + ' />'

    return u'<g' + attribs + '>' + ''.join(members) + '</g>'


def setviewbox(viewbox=None):
    if not viewbox:
        return ''
    else:
        return u' viewBox="{},{},{},{}"'.format(*viewbox)


def drawing(size, members, viewbox=None, style=None):
    '''
    Create an SVG element.

    Args:
        size (tuple): width, height
        members (list): Strings to add to output.
        viewbox (Sequence): Four coordinates that describe a bounding box.
        style (string): CSS string.
    '''
    svg = (u'<svg baseProfile="full" version="1.1"'
           ' xmlns="http://www.w3.org/2000/svg"'
          )
    dimension = u' width="{}" height="{}"'.format(*size)
    vb = setviewbox(viewbox)
    defs = defstyle(style)

    return svg + dimension + vb + u'>' + defs + u''.join(members) + u'</svg>'
