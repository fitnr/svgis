#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Create string versions of SVG elements.'''

# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, 2020, Neil Freeman <contact@fakeisthenewreal.org>

from six import string_types

from . import dom, utils


def _element(tag, contents=None, **kwargs):
    """
    Draw an element, optionally wrapping contents.

    Args:
        tag (str): tag name
        contents (str): contents to be wrapped in the tag
        kwargs: to be transformed into attributes

    Returns:
        ``str``
    """
    attribs = toattribs(**kwargs)
    if contents:
        return f"<{tag}{attribs}>{contents}</{tag}>"

    return f"<{tag}{attribs}/>"


def _fmt(precision):
    if precision is None:
        return '{0[0]},{0[1]}'
    return '{{0[0]:.{0}f}},{{0[1]:.{0}f}}'.format(precision)


def _poly(name):
    def poly(coordinates, precision=None, **kwargs):
        fmt = _fmt(precision)

        points = utils.dedupe(fmt.format(c) for c in coordinates)
        return _element(name(), points=' '.join(points), **kwargs)

    return poly


def circle(point, precision=None, **kwargs):
    """
    Create a svg circle element. Keyword arguments are mapped to attributes.

    Args:
        point (tuple): The center of the circle
        precision (int): rounding precision

    Returns:
        ``str``
    """
    return _element('circle', cx=utils.rnd(point[0], precision), cy=utils.rnd(point[1], precision), **kwargs)


def text(string, start, precision=None, **kwargs):
    """
    Create an svg text element.

    Args:
        string (str): text for element
        start (tuple): starting coordinate

    Returns:
        ``str``
    """
    start = [utils.rnd(i, precision) for i in start]
    return _element('text', string, x=start[0], y=start[1], **kwargs)


def rect(start, width, height, precision=None, **kwargs):
    """
    Create an svg rect element.

    Args:
        start (tuple): starting coordinate
        width (int): rect width
        height (int): rect height
        precision (int): rounding precision

    Returns:
        ``str``
    """
    start = [utils.rnd(i, precision) for i in start]
    width = utils.rnd(width, precision)
    height = utils.rnd(height, precision)

    return _element('rect', x=start[0], y=start[1], width=width, height=height, **kwargs)


def line(start, end, precision=None, **kwargs):
    """
    Create an svg line element.

    Args:
        start (tuple): starting coordinate
        end (tuple): ending coordinate
        precision (int): rounding precision

    Returns:
        ``str``
    """
    start = [utils.rnd(i, precision) for i in start]
    end = [utils.rnd(i, precision) for i in end]

    return _element('line', x1=start[0], y1=start[1], x2=end[0], y2=end[1], **kwargs)


def path(coordinates, precision=None, **kwargs):
    """
    Create an svg path element as a string.

    Args:
        coordinates (Sequence): A sequence of coordinates and string instructions
        precision (int): rounding precision

    Returns:
        ``str``
    """
    fmt = _fmt(precision)
    coords = utils.dedupe(i if isinstance(i, string_types) else fmt.format(i) for i in coordinates)
    return _element('path', d=' '.join(coords), **kwargs)


@_poly
def polyline():
    """
    Create an svg polyline element

    Args:
        coordinates (Sequence): x, y coordinates
        precision (int): rounding precision

    Returns:
        ``str``
    """
    return 'polyline'


@_poly
def polygon():
    """
    Create an svg polygon element

    Args:
        coordinates (Sequence): x, y coordinates
        precision (int): rounding precision

    Returns:
        ``str``
    """
    return 'polygon'


def toattribs(**kwargs):
    """
    Convert keyword arguments to SVG attribute definitions.

    Returns:
        ``str``
    """
    attribs = ' '.join(f'{k}="{dom.ampencode(v)}"' for k, v in kwargs.items() if v is not None and v != '')
    if attribs:
        return ' ' + attribs

    return attribs


def defstyle(style=None):
    """
    Create a defs element that wraps a CSS style.

    Args:
        style (string): A CSS string.

    Returns:
        ``str``
    """
    if style:
        return f'<defs><style type="text/css"><![CDATA[{style}]]></style></defs>'

    return '<defs />'


def group(members=None, **kwargs):
    """
    Create a group with the given scale and translation.

    Args:
        members (Sequence): unicode SVG elements
        kwargs (dict): elements of this dictionary will be converted to
                        attributes of the group, i.e. key="value".

    Returns:
        ``str``
    """
    members = members or ''
    return _element('g', ''.join(members), **kwargs)


def drawing(size, members, precision=None, viewbox=None, style=None):
    """
    Create an SVG element.

    Args:
        size (tuple): width, height
        members (list): Strings to add to output.
        viewbox (Sequence): Four coordinates that describe an SVG viewBox.
        style (string): CSS string.

    Returns:
        ``str``
    """
    kwargs = {
        'width': size[0],
        'height': size[1],
        'baseProfile': 'full',
        'version': '1.1',
        'xmlns': 'http://www.w3.org/2000/svg',
    }

    if precision:
        fmt = ('{:.{precision}f}',)
    else:
        fmt = ('{:f}',)

    if viewbox:
        kwargs['viewBox'] = (','.join(fmt * 4)).format(*viewbox, precision=precision)

    contents = defstyle(style) + ''.join(members)
    return _element('svg', contents, **kwargs)
