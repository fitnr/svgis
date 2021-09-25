#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Mess around with SVG styling'''

# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, 2020, Neil Freeman <contact@fakeisthenewreal.org>
# pylint: disable=c-extension-no-member
import logging
import os.path
import re
from string import ascii_letters

import tinycss2
from lxml import etree

from . import dom

LOG = logging.getLogger('svgis')


def sanitize(string):
    """
    Make input safe of use in an svg ID or class field.
    Replaces blocks of whitespace with an underscore (``_``),
    deletes periods, number signs and double-quotes (``.#"``).
    If the first character isn't an ascii letter, dash (``-``)
    or underscore (``_``), an underscore is added to the beginning.

    Args:
        string (mixed): Input to sanitize

    Returns:
        str
    """
    try:
        string = re.sub(r'\s+', '_', re.sub(r'(\.|#|"|&)', '', string))
        return string if string[:1] in '_-' + ascii_letters else '_' + string

    except TypeError:
        return sanitize(str(string))


def construct_classes(classes, properties):
    """
    Build a class string for an element using the properties. Class names
    take the form ``myclass_value``. If a given class isn't found in properties,
    the class name is added (e.g. ``myclass``).

    Args:
        classes (Sequence): Column names to include in the class list
        properties (dict): A single feature's properties.

    Returns:
        (list) class names
    """
    f = '{}_{}'
    return [sanitize(f.format(p, properties.get(p))) for p in classes if p in properties]


def construct_datas(fields, properties):
    """
    Build a data- attribute string for an element using the properties. Attributes
    take the form data_FIELD=PROPERTY.

    Args:
        datas (Sequence): Column names to include in the class list
        properties (dict): A single feature's properties.

    Returns:
        (dict) attribute dictionary
    """
    return {sanitize('data-' + n): str(properties.get(n)) for n in fields if n in properties}


def pick(style):
    """
    Fetch a CSS string.

    Args:
        style (str): Either a CSS string or the path of a css file.
    """
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
    """Add a ``scale()`` operation to an entire svg file."""
    svg = etree.parse(svgfile).getroot()
    scalar = f'scale({factor})'
    g = svg.find('.//g', namespaces=svg.nsmap)
    g.attrib['transform'] = (g.attrib.get('transform') + ' ' + scalar).strip()
    return etree.tostring(svg, encoding='utf-8').decode('utf-8')


def replace_comments(css):
    """
    Replace one-line non-standard comments with body-style comments::

       // non-standard comment
       /* body-style comment */

    """
    return re.sub(r'//(.+)', r'/*\1 */', css)


def add_style(svgfile, style, replace=False):
    """
    Add to or replace the CSS style in an SVG file.

    Args:
        svgfile (str): Path to an SVG file or an SVG string.
        newstyle (str): CSS string, or path to CSS file.
        replace (bool): If true, replace the existing CSS with newstyle (default: False)
    """
    if style == '-':
        style = '/dev/stdin'

    root, ext = os.path.splitext(style)

    if ext == '.css' or root == '/dev/stdin':
        with open(style) as f:
            style = replace_comments(f.read())

    try:
        svg = etree.parse(svgfile).getroot()
    except IOError:
        try:
            svg = etree.fromstring(svgfile)
        except UnicodeDecodeError:
            svg = etree.fromstring(svgfile.encode('utf-8'))

    defs = svg.find('defs', namespaces=svg.nsmap)

    if defs is None:
        defs = etree.Element('defs', nsmap=svg.nsmap)
        svg.insert(0, defs)

    style_element = defs.find('.//style', namespaces=svg.nsmap)

    if style_element is None:
        style_element = etree.Element('style', nsmap=svg.nsmap)
        defs.append(style_element)

    if replace:
        style_content = style
    else:
        # Append CSS.
        style_content = (style_element.text or '') + ' ' + style

    # append cdata
    style_element.text = etree.CDATA(style_content)

    return etree.tostring(svg, encoding='utf-8').decode('utf-8')


def inline(svg):
    """
    Inline the CSS rules in an SVG. This is a very rough operation,
    and full css precedence rules won't be respected. May ignore sibling
    operators (``~``, ``+``), pseudo-selectors (e.g. ``:first-child``), and
    attribute selectors (e.g. ``.foo[name=bar]``). Works best with rules like:

    * ``.class``
    * ``tag``
    * ``tag.class``
    * ``#layer .class``
    * ``#layer tag``

    Args:
        svg (string): An SVG document.
        style (string): CSS to use, instead of the CSS in the <defs> element of the SVG.
    """
    try:
        doc = etree.fromstring(svg.encode('utf-8'))
        style_element = doc.find('.//style', namespaces=doc.nsmap)
        if style_element is None:
            return svg

        css = style_element.text
        rules = tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True)
        dom.apply_rules(doc, rules)
        return etree.tostring(doc, encoding='utf-8').decode('utf-8')

    # Return plain old SVG.
    except (AttributeError, NameError) as e:
        logging.getLogger('svgis').warning("Unable to inline CSS: %s", e)
        return svg
