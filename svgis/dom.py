#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>
import logging

'''
Utilities for manipulating the DOM and applying styles to same.
'''

SVG_NS = 'http://www.w3.org/2000/svg'


def cdata(text):
    '''Wrap text in CDATA section.'''
    return '<![CDATA[' + text + ']]>'


def ns(tag):
    '''Apply the SVG namespace to a tag, e.g. ``g`` to ``{http://www.w3.org/2000/svg}g``.'''
    return '{' + SVG_NS + '}' + tag


def apply_rule(doc, rule):
    '''
    Apply a tinycss Rule to an ElementTree.Element
    (only tested on documents created by SVGIS).
    '''
    tokenlist = _build_tokenlist(rule.selector)

    declaration = {d.name: d.value.as_css() for d in rule.declarations}

    for tokens in tokenlist:
        # Starts as None as a marker to look into document,
        # instead of filtering the list.
        els = None
        while len(tokens) > 0:
            els, tokens = _process_tokens(doc, els, tokens)

        if els:
            for el in els:
                style = _style_dict(el.attrib.get('style'))
                style.update(declaration)
                el.attrib['style'] = _style_string(style)


def _style_dict(style):
    '''Convert a style attribute into a dict.'''
    try:
        styles = [r.split(u':', 1) for r in style.strip(u'; \n\t').split(u';')]
        return {x[0].strip(): x[1].strip() for x in styles}

    except AttributeError:
        return {}


def _style_string(declaration):
    '''Convert a dict into a style attribute.'''
    return u';'.join(k + u':' + v for k, v in declaration.items())


def _match_classes(elem_classes, rule_classes):
    '''Check if rule_classes all fall in elem_classes.'''
    return all([c in elem_classes for c in rule_classes])


def _idrule(idname):
    # Get rid of the hash here.
    return "*[@id='{}']".format(idname[1:])


def _build_tokenlist(tokens):
    tokenlist = [[]]
    itertokens = iter(tokens)

    for token in itertokens:
        if token.is_container:
            tokenlist[-1].append(token)
            continue

        if token.value == ',':
            tokenlist.append([])
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
    return token.is_container or token.type == 'ATKEYWORD' or token.value in ('+', '~', ':')


def _process_tokens(doc, els, tokens):
    '''
    Work through the given selector tokens, attempting to return the subset
    of ``els`` that match.

    Args:
        doc (ElementTree.Element): Parent element to search within.
        els (list): Current list of elements. For the first pass, this is None.
        tokens (list): List of ``tinycss.Token``s.
    '''
    if any(_unsupported_token(t) for t in tokens):
        return [], []

    if tokens[0].value == '*':
        if els is None:
            els = doc.findall('.//')

        remaining_tokens = tokens[1:]

    # Look inside the given elements!
    elif tokens[0].type == 'S':
        try:
            els = [u for e in els for u in e.findall('.//')]
            remaining_tokens = tokens[1:]

        except TypeError:
            els = None
            remaining_tokens = tokens[1:]

    # Child operator is easy.
    elif tokens[0].value == '>' and tokens[0].type == 'DELIM':
        remaining_tokens = tokens[1:]
        els = [u for e in els for u in e.findall('./')]

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
            if tok.value == '.' and tok.type == 'DELIM':
                continue

            elif tok.type == 'IDENT':
                classes.append(tok)

            else:
                break

        try:
            els = _find_classes(doc, els, [c.value for c in classes])
            # All tokens after the last class in classes.
            remaining_tokens = tokens[tokens.index(classes[-1]) + 1:]
        except ValueError:
            remaining_tokens = tokens[1:]

    # first token is <IDENT>: it's an element, possibly followed other stuff.
    elif tokens[0].type == 'IDENT':
        els = _get_elems_by_tagname(doc, els, ns(tokens[0].value))
        remaining_tokens = tokens[1:]

    # Didn't recognize that token!
    else:
        logging.getLogger('svgis').warning('Unknown CSS: %s', tokens[0].value)
        remaining_tokens = tokens[1:]

    return els, remaining_tokens
