#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Mess around with SVG styling'''

# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import re
from string import ascii_letters
import os.path
import logging
import xml.etree.ElementTree as ElementTree
import tinycss
from . import dom


def _register():
    ElementTree.register_namespace('', dom.SVG_NS)
    ElementTree._serialize_xml = ElementTree._serialize['xml'] = dom._serialize_xml


def sanitize(string):
    '''
    Make input safe of use in an svg ID or class field.
    Replaces blocks of whitespace with an underscore (``_``),
    deleted periods, number signs and double-quotes (``.#"``).
    If the first character isn't an ascii letter, dash (``-``)
    or underscore (``_``), an underscore is added to the beginning.

    Args:
        string (mixed): Input to sanitize

    Returns:
        str
    '''
    try:
        string = re.sub(r'\s+', '_', re.sub(r'(\.|#|"|&)', '', string))
        return string if string[:1] in '_-' + ascii_letters else '_' + string

    except TypeError:
        return sanitize(str(string))


def construct_classes(classes, properties):
    '''
    Build a class string for an element using the properties. Class names
    take the form CLASS_PROPERTY. If a given class isn't found in properties,
    the class name is added (e.g. CLASS).

    Args:
        classes (Sequence): Column names to include in the class list
        properties (dict): A single feature's properties.

    Returns:
        (list) class names
    '''
    f = u'{}_{}'
    return [sanitize(f.format(p, properties.get(p))) for p in classes if p in properties]


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

    except (AttributeError, TypeError):
        # Probably style is None.
        return None

    except IOError:
        logging.getLogger('svgis').warning("Couldn't read %s, proceeding with default style", style)

    return style


def rescale(svgfile, factor):
    _register()
    svg = ElementTree.parse(svgfile)
    scalar = 'scale({})'.format(factor)
    g = svg.getroot().find(dom.ns('g'))
    g.attrib['transform'] = (g.attrib.get('transform') + ' ' + scalar).strip()
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
            style = _uncomment(f.read())

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
            style = (style_element.text or '') + ' ' + style

        style_element.text = ''

    else:
        style_element = ElementTree.Element(dom.ns('style'))
        defs.append(style_element)

    style_element.append(dom.cdata(style))

    return ElementTree.tostring(svg, encoding='utf-8').decode('utf-8')


def inline(svg, style=None):
    '''
    Inline the CSS rules in an SVG. This is a very rough operation,
    and full css precedence rules won't be respected. Ignores sibling
    operators (``~``, ``+``), pseudo-selectors (e.g. ``:first-child``), and
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

        if not style:
            path = './' + dom.ns('defs') + '/' + dom.ns('style')
            try:
                style = doc.findall(path).pop().text or ''
            except IndexError:
                style = ''

        stylesheet = _parse_css(style)

        for rule in stylesheet.rules:
            dom.apply_rule(doc, rule)

        return ElementTree.tostring(doc, encoding='utf-8').decode('utf-8')

    # Return plain old SVG.
    except (AttributeError, NameError) as e:
        logging.getLogger('svgis').warning("Unable to inline CSS: %s", e)
        return svg


def _uncomment(stylesheet):
    '''Remove CSS comments ('//') from a stylesheet.'''
    return re.sub(r'//.+', '', stylesheet)


def _parse_css(stylesheet):
    '''Turn a block of CSS into a tinycss stylesheet object.'''
    # remove spaces in selectors
    mini = _uncomment(re.sub(r'\s+([,>~+])\s+', r'\1', stylesheet))
    return tinycss.make_parser().parse_stylesheet(mini)
