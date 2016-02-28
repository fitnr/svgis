#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import re
from string import ascii_letters
import os.path
import logging
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
import tinycss
from . import dom

'''
Utilities for messing with SVG styling.
'''


def _register():
    ElementTree.register_namespace('', dom.SVG_NS)


def sanitize(string):
    '''
    Make input safe of use in an svg ID or class field.
    Replaces blocks of whitespace with an underscore (``_``).
    If the first character isn't an ascii letter, dash (``-``)
    or underscore (``_``), an underscore is added to the beginning.

    Args:
        string (mixed): Input to sanitize. Will be immediately coerced to
                        unicode. If that fails, returns an empty string.
    '''
    try:
        string = re.sub(r'\s+', u'_', unicode(string))
        string = string if string[0] in ('_-' + ascii_letters) else '_' + string
        return unicode(string)

    except (AttributeError, IndexError):
        return u''


def pick(style):
    '''
    Fetch a CSS string.

    Args:
        style (str): Either a CSS string or the path of a css file.
    '''
    try:
        _, ext = os.path.splitext(style)
        if ext == '.css':
            with open(style) as f:
                return f.read()

    except AttributeError:
        # Probably style is None.
        return None

    except IOError:
        logging.getLogger('svgis').warning("Couldn't read %s, proceeding with default style", style)

    return style


def rescale(svgfile, factor):
    _register()
    try:
        svg = ElementTree.parse(svgfile)
        scalar = 'scale({})'.format(factor)
        g = svg.getroot().find(dom.ns('g'))
        g.attrib['transform'] = (g.attrib.get('transform') + ' ' + scalar).strip()

    except AttributeError:
        raise

    return ElementTree.tostring(svg.getroot(), encoding='utf-8').decode('utf-8')


def add_style(svgfile, style, replace=False):
    '''
    Add to or replace the CSS style in an SVG file.

    Args:
        svgfile (str): Path to an SVG file or an SVG string.
        newstyle (str): CSS string, or path to CSS file.
        replace (bool): If true, replace the existing CSS with newstyle (default: False)
    '''
    _register()

    if style == '-':
        style = '/dev/stdin'

    root, ext = os.path.splitext(style)

    if ext == '.css' or root == '/dev/stdin':
        with open(style) as f:
            style = f.read()

    try:
        svg = ElementTree.parse(svgfile).getroot()
    except IOError:
        try:
            svg = ElementTree.fromstring(svgfile)
        except UnicodeDecodeError:
            svg = ElementTree.fromstring(svgfile.encode('utf-8'))

    if svg.find(dom.ns('defs')) is not None:
        defs = svg.find(dom.ns('defs'))

    else:
        defs = ElementTree.Element(dom.ns('defs'))
        svg.insert(0, defs)

    if defs.find(dom.ns('style')) is not None:
        style_element = defs.find(dom.ns('style'))

        if not replace:
            # Append CSS.
            existing = style_element.text or ''
            style = dom.cdata(existing + ' ' + style)
            style_element.text = ''

    else:
        style_element = ElementTree.Element(dom.ns('style'))
        defs.append(style_element)

    style_element.text = dom.cdata(style)

    return ElementTree.tostring(svg, encoding='utf-8').decode('utf-8')


def inline(svg, style=None):
    '''
    Inline the CSS rules in an SVG. This is a very rough operation,
    and full css precedence rules won't be respected. Ignores sibling
    operators (``~``, ``+``), psuedo-selectors (e.g. ``:first-child``), and
    attribute selectors (e.g. ``.foo[name=bar]``). Works best with rules like:

    * ``.class``
    * ``tag``
    * ``tag.class``
    * ``#layer .class``
    * ``#layer tag``

    Args:
        svg (string): An SVG document.
        css (string): CSS to use, instead of the CSS in the <defs> element of the SVG.
    '''
    _register()
    try:
        doc = ElementTree.fromstring(svg.encode('utf-8'))
        wrap = doc.find('./' + dom.ns('g'))

        if not style:
            path = './' + dom.ns('defs') + '/' + dom.ns('style')
            try:
                style = doc.findall(path).pop().text
            except IndexError:
                style = ''

        stylesheet = _parse_css(style)

        for rule in stylesheet.rules:
            dom.apply_rule(wrap, rule)

        return ElementTree.tostring(doc, encoding='utf-8').decode('utf-8')

    # Return plain old SVG.
    except (AttributeError, NameError) as e:
        logging.getLogger('svgis').warning("Unable to inline CSS becuase: %s", e)
        return svg


def _parse_css(stylesheet):
    mini = re.sub(r'\s+([,>~+])\s+', r'\1', stylesheet)
    return tinycss.make_parser().parse_stylesheet(mini)
