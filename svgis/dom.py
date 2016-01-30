#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, Neil Freeman <contact@fakeisthenewreal.org>

'''
Utilities for manipulating the DOM and applying styles to same.
'''

SVG_NS = 'http://www.w3.org/2000/svg'


def cdata(text):
    return '<![CDATA[' + text + ']]>'


def ns(tag):
    return '{' + SVG_NS + '}' + tag


def apply_rule(doc, rule):
    '''
    Apply a tinycss Rule to an SVG document built by SVGIS.
    '''
    tokenlist = _build_tokenlist(rule.selector)

    declaration = u' '.join(u'{}:{};'.format(d.name, d.value.as_css()) for d in rule.declarations)

    for tokens in tokenlist:
        # Starts as None as a marker to look into document,
        # instead of filtering the list.
        els = None
        while len(tokens) > 0:
            els, tokens = _process_tokens(doc, els, tokens)

        for el in els:
            el.attrib['style'] = el.attrib.get('style', u'') + declaration


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
        if token.value == ',':
            tokenlist.append([])
            continue

        if token.type == '[':
            tokenlist.append([])
            continue

        # ignore a ':' and whatever comes after the ':'.
        if token.value == ':':
            if next(itertokens).value == ':':
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
        els = doc.findall('.//')
        remaining_tokens = tokens[1:]

    # Look inside the given elements!
    elif tokens[0].type == 'S':
        try:
            els = [u for e in els for u in e.findall('./')]
            remaining_tokens = tokens[1:]

        except TypeError:
            return None, tokens[1:]

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
            if tok.type == 'S':
                break

            if tok.type == 'IDENT':
                classes.append(tok.value)

        els = _find_classes(doc, els, classes)
        remaining_tokens = []

    # first token is <IDENT>: it's an element, possibly followed by classes.
    elif tokens[0].type == 'IDENT':
        els = _get_elems_by_tagname(doc, els, ns(tokens[0].value))
        remaining_tokens = tokens[1:]

    return els, remaining_tokens
