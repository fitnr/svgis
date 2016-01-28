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


def _CDATA(text=None):
    element = ElementTree.Element('![CDATA[')
    element.text = text
    return element


def _prepare_cdata():
    ElementTree._original_serialize_xml = ElementTree._serialize_xml

    def _serialize_xml(write, elem, *args):
        if elem.tag == '![CDATA[':
            write("\n<{}{}]]>\n".format(elem.tag, elem.text))
            return

        return ElementTree._original_serialize_xml(write, elem, *args)

    ElementTree._serialize_xml = ElementTree._serialize['xml'] = _serialize_xml


def add_style(svgfile, style, replace=False):
    '''Add to the CSS style in an SVG file.

    Args:
        svgfile (string): Path to an SVG file or an SVG string.
        newstyle (string): CSS string, or path to CSS file.
        replace (bool): If true, replace the existing CSS with newstyle (default: False)
    '''
    _prepare_cdata()

    if style == '-':
        style = '/dev/stdin'

    root, ext = os.path.splitext(style)

    if ext == '.css' or root == '/dev/stdin':
        with open(style) as f:
            style = f.read()

    try:
        svg = ElementTree.parse(svgfile)
    except IOError:
        svg = ElementTree.fromstring(svgfile)

    defs = svg.findall('defs').pop(0)

    if not defs:
        defs = ElementTree.Element('defs')
        svg.insert(0, defs)

    if defs.find('style'):
        style_element = defs.find('style').item(0)

        if replace:
            # Replace CSS.
            cdata = _CDATA(style)

        else:
            # Append CSS.
            existing = svg.findall('defs')[1].find('style').text
            svg.findall('defs')[1].find('style').text = ''
            cdata = _CDATA(existing + ' ' + style)

        style_element.append(cdata)

    else:
        style_element = ElementTree.Element('style')
        defs.appendChild(style_element)
        cdata = _CDATA(style)

    style_element.append(cdata)

    return ElementTree.tostring(svg)


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
