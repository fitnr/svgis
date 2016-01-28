#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import os.path
import logging
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
import tinycss
from . import dom


def _register():
    ElementTree.register_namespace('', dom.SVG_NS)


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
    '''Add to the CSS style in an SVG file.

    Args:
        svgfile (string): Path to an SVG file or an SVG string.
        newstyle (string): CSS string, or path to CSS file.
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
        svg = ElementTree.fromstring(svgfile)

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


def inline(svg, css=None):
    '''
    Inline the CSS rules into the SVG. This is a very rough operation,
    and full css precedence rules won't be respected.

    Args:
        svg (string): An SVG document.
        css (string): CSS to use, instead of the CSS in the <defs> element of the SVG.
    '''
    _register()
    try:
        doc = ElementTree.fromstring(svg)

        if not css:
            path = './' + dom.ns(defs) + '/' + dom.ns(style)
            css = doc.findall(path).pop().text

        stylesheet = tinycss.make_parser().parse_stylesheet(css)
        pattern = "{}:{};"

        for rule in stylesheet.rules:
            declaration = ' '.join(pattern.format(d.name, d.value.as_css()) for d in rule.declarations)
            expressions = dom.xpath(rule.selector)

            for expression in expressions:
                for el in doc.findall(expression):
                    el.attrib['style'] = el.attrib.get('style', '') + declaration

        return ElementTree.tostring(doc, encoding='utf-8').decode('utf-8')

    # Return plain old SVG.
    except (AttributeError, NameError):
        raise


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
        logging.getLogger('svg').warn("Couldn't read %s, proceeding with default style", style)

    return style
