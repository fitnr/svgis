#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import os.path
import logging
from xml.dom import minidom
try:
    from lxml import etree
    import cssselect
    import tinycss
except ImportError:
    pass


def rescale(svgfile, factor):
    svg = minidom.parse(svgfile)

    scalar = 'scale({})'.format(factor)

    gs = svg.getElementsByTagName('g')[0]

    transform = gs.attributes.get('transform')

    if transform:
        transform.value = transform.value + ' ' + scalar
    else:
        gs.setAttribute('transform', scalar)

    return svg.toxml()


def add_style(svgfile, style, replace=False):
    '''Add to the CSS style in an SVG file.
    svgfile -- Path to an SVG file or an SVG string.
    newstyle -- CSS string, or path to CSS file.
    replace -- (boolean) If true, replace the existing CSS with newstyle (default: False)
    '''
    if style == '-':
        style = '/dev/stdin'

    root, ext = os.path.splitext(style)

    if ext == '.css' or root == '/dev/stdin':
        with open(style) as f:
            style = f.read()

    try:
        svg = minidom.parse(svgfile)
    except IOError:
        svg = minidom.parseString(svgfile)

    defs = svg.getElementsByTagName('defs').item(0)

    if not defs:
        defs = svg.createElement('defs')

        if not hasattr(svg, 'tagName'):
            elem = svg.getElementsByTagName('svg').item(0)
            elem.insertBefore(defs, elem.firstChild)

        else:
            svg.insertBefore(defs, svg.firstChild)

    if defs.getElementsByTagName('style'):
        style_element = defs.getElementsByTagName('style').item(0)

        if replace:
            style_element.firstChild.replaceWholeText(style)
        else:
            style_element.firstChild.nodeValue += ' ' + style

    else:
        style_element = svg.createElement('style')
        css = svg.createTextNode(style)
        style_element.appendChild(css)
        defs.appendChild(style_element)

    return svg.toxml()


def inline(svg, css):
    '''Inline given css rules into SVG'''
    try:
        etree.register_namespace('svg', 'http://www.w3.org/2000/svg')

        document = etree.fromstring(svg)
        stylesheet = tinycss.make_parser().parse_stylesheet(css)
        translator = cssselect.GenericTranslator()

        def xpath(selector):
            return document.xpath(translator.css_to_xpath(selector))

        pattern = "{}:{};"
        for rule in stylesheet.rules:

            declaration = ' '.join(pattern.format(d.name, d.value.as_css()) for d in rule.declarations)
            selector = rule.selector.as_css()

            for el in xpath(selector):
                el.attrib['style'] = el.attrib.get('style', '') + declaration

        return etree.tounicode(document)

    # Return plain old SVG.
    except NameError:
        return svg


def pick(style):
    '''
    Fetch a CSS string.
    :style str Either a CSS string or the path of a css file.
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
