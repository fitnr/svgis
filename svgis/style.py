#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

import re

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
import os.path
import logging
import tinycss


'''
Utilities for messing with SVG styling.
'''

SVG_NS = 'http://www.w3.org/2000/svg'


def _register():
    ElementTree.register_namespace('', SVG_NS)


def _cdata(text):
    return '<![CDATA[' + text + ']]>'


def _ns(tag):
    return '{' + SVG_NS + '}' + tag


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


def rescale(svgfile, factor):
    _register()
    try:
        svg = ElementTree.parse(svgfile)
        scalar = 'scale({})'.format(factor)
        g = svg.getroot().find(_ns('g'))
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
        try:
            svg = ElementTree.fromstring(svgfile)
        except UnicodeDecodeError:
            svg = ElementTree.fromstring(svgfile.encode('utf-8'))

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

    return ElementTree.tostring(svg, encoding='utf-8').decode('utf-8')


def inline(svg, style=None):
    '''
    Inline the CSS rules into the SVG. This is a very rough operation,
    and full css precedence rules won't be respected.

    Args:
        svg (string): An SVG document.
        css (string): CSS to use, instead of the CSS in the <defs> element of the SVG.
    '''
    _register()
    try:
        doc = ElementTree.fromstring(svg.encode('utf-8'))
        wrap = doc.find('./' + _ns('g'))

        if not style:
            path = './' + _ns('defs') + '/' + _ns('style')
            style = doc.findall(path).pop().text

        stylesheet = tinycss.make_parser().parse_stylesheet(_minify(style))

        for rule in stylesheet.rules:
            tokenlist = _build_tokenlist(rule.selector)

            declaration = u' '.join(u'{}:{};'.format(d.name, d.value.as_css()) for d in rule.declarations)

            for tokens in tokenlist:
                # Starts as None as a marker to look into document,
                # instead of filtering the list.
                els = None
                while len(tokens) > 0:
                    els, tokens = _process_tokens(wrap, els, tokens)

                for el in els:
                    el.attrib['style'] = el.attrib.get('style', u'') + declaration

        return ElementTree.tostring(doc, encoding='utf-8').decode('utf-8')

    # Return plain old SVG.
    except (AttributeError, NameError):
        raise


def _minify(stylesheet):
    return re.sub(r',\s+', ',', stylesheet)


def _match_classes(elem_classes, rule_classes):
    '''Check if rule_classes all fall in elem_classes.'''
    return all([c in elem_classes for c in rule_classes])


def _isgroup(el):
    return el.tag == '{http://www.w3.org/2000/svg}g'


def _idrule(idname):
    # Get rid of the hash here.
    return "*[@id='{}']".format(idname[1:])


def _build_tokenlist(tokens):
    tokenlist = [[]]
    itertokens = iter(tokens)

    for token in itertokens:
        if token.value == ',':
            tokenlist.append([])
            continue

        if token.type == '[':
            tokenlist.append([])
            continue

        # ignore a ':' and whatever comes after the ':'.
        if token.value == ':':
            n = next(itertokens)
            if n.value == ':':
                next(itertokens)
            continue

        tokenlist[-1].append(token)

    return tokenlist


def _find_classes(doc, els, classes):
    '''Get elements in doc that match given classes.'''
    if els is None:
        els = doc.iter()

    return [e for e in els if _match_classes(e.attrib.get('class', []), classes)]


def _get_elems_by_tagname(doc, els, tagname):
    '''Find elems in els (or doc) that have the given tagname.'''
    if els is None:
        return doc.findall('.//' + tagname)
    else:
        return [e for e in els if e.tag == tagname]


def _unsupported_token(token):
    return token.type == 'DELIM' and token.value in ('+', '~', '')


def _process_tokens(doc, els, tokens):
    if any(_unsupported_token(t) for t in tokens):
        return [], []

    if tokens[0].value == '*':
        els = doc.findall('.//')
        remaining_tokens = tokens[1:]

    # Look inside the given elements!
    elif tokens[0].type == 'S':
        try:
            els = [u for e in els for u in e.findall('./')]
            remaining_tokens = tokens[1:]

        except TypeError:
            return None, tokens[1:]

    # Is there a <HASH>: it's an ID, find that, then look for other classes or tags.
    elif any(t.type == 'HASH' for t in tokens):
        idtokens = [t for t in tokens if t.type == 'HASH']

        # Remove all the id hashes.
        remaining_tokens = [t for t in tokens if t not in idtokens]

        # Allow for multiple id hashes, but we only want the first one
        els = doc.findall('.//' + _idrule(idtokens[0].value))

    # first token is <DELIM '.'>: make a list of classes
    elif tokens[0].value == '.' and tokens[0].type == 'DELIM':
        classes = []

        for tok in tokens:
            if tok.type == 'S':
                break

            if tok.type == 'IDENT':
                classes.append(tok.value)

        els = _find_classes(doc, els, classes)
        remaining_tokens = []

    # first token is <IDENT>: it's an element, possibly followed by classes.
    elif tokens[0].type == 'IDENT':
        els = _get_elems_by_tagname(doc, els, _ns(tokens[0].value))
        remaining_tokens = tokens[1:]

    return els, remaining_tokens
