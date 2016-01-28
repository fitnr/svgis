#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import os.path
import logging
import xml.etree.ElementTree as ElementTree
import cssselect
import tinycss

SVG_NS = 'http://www.w3.org/2000/svg'


def _register():
    ElementTree.register_namespace('', SVG_NS)


def _cdata(text):
    return '<![CDATA[' + text + ']]>'


def _ns(tag):
    return '{' + SVG_NS + '}' + tag


def rescale(svgfile, factor):
    _register()
    try:
        svg = ElementTree.parse(svgfile)
        scalar = 'scale({})'.format(factor)
        g = svg.getroot().find(_ns('g'))
        g.attrib['transform'] = (g.attrib.get('transform') + ' ' + scalar).strip()

    except AttributeError:
        raise

    return unicode(ElementTree.tostring(svg.getroot(), encoding='utf-8'))


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

    if svg.find(_ns('defs')) is not None:
        defs = svg.find(_ns('defs'))

    else:
        defs = ElementTree.Element(_ns('defs'))
        svg.insert(0, defs)

    if defs.find(_ns('style')) is not None:
        style_element = defs.find(_ns('style'))

        if not replace:
            # Append CSS.
            existing = style_element.text or ''
            style = _cdata(existing + ' ' + style)
            style_element.text = ''

    else:
        style_element = ElementTree.Element(_ns('style'))
        defs.append(style_element)

    style_element.text = _cdata(style)

    try:
        return unicode(ElementTree.tostring(svg, encoding='utf-8'))
    except AttributeError:
        print(svg)
        raise


def inline(svg, css=None):
    '''
    Inline the CSS rules into the SVG. This is a very rough operation,
    and full css precedence rules won't be respected.

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
