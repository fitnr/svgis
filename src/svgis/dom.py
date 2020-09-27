#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Utilities for manipulating the DOM and applying styles to same'''
# This file is part of svgis.
# https://github.com/fitnr/svgis
# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2016, 2020, Neil Freeman <contact@fakeisthenewreal.org>
# pylint: disable=c-extension-no-member
import logging
import re

from lxml.cssselect import CSSSelector

SVG_NS = 'http://www.w3.org/2000/svg'
LOG = logging.getLogger('svgis')


def ampencode(value):
    """Escape an ampersand that isn't already url encoded"""
    return re.sub(r'&(?!amp;)', r'&amp;', str(value))


def serialize_token(token, previous_token=None):
    """
    Convert a tinycss2 selector to string in preparation for use with cssselect.
    This involves prepending 'svg|'  to element selectors.

    Arguments:
        token (tinycss2.ast.Node): The selector to serialize.
    """
    prev_type = 'whitespace' if previous_token is None else previous_token.type
    if token.type == 'ident' and prev_type == 'whitespace':
        return 'svg|' + token.serialize()
    return token.serialize()


def serialize_prelude(rule):
    """Convert the selector section of a CSS rule to string."""
    p = (serialize_token(a, b) for a, b in zip(rule.prelude, [None] + rule.prelude[:-1]))
    return ''.join(p).strip()


def rule_content(rule):
    """Except the content from CSS rules."""
    return [token.serialize() for token in rule.content if token.type != 'whitespace']


def apply_rules(doc, rules, nsmap=None):
    """
    Apply tinycss2 rules to an etree.Element (only tested on documents created by SVGIS).

    Args:
        doc (ElementTree.Element): The svg document to scan.
        rules (list): List of tinycss2 Rules to apply.
        nsmap (dict): namespace map.  Default: ``{ "svg": "http://www.w3.org/2000/svg" }``
    """
    nsmap = nsmap or {'svg': SVG_NS}
    for rule in rules:
        apply_rule(doc, rule, nsmap)

    return doc


def apply_rule(doc, rule, nsmap):
    """
    Apply a tinycss2 rule to an etree.Element
    Args:
        doc (ElementTree.Element): The svg document to scan.
        rule (QualifiedRule): tinycss2 rule
        nsmap (dict): namespace map
    """
    declaration = serialize_prelude(rule)
    selector = CSSSelector(declaration, namespaces=nsmap)

    tokens = rule_content(rule)
    rvalue = None
    if 'r' in tokens:
        i = tokens.index('r')
        token = rule.content[i]
        for token in rule.content[i + 1 :]:
            if token.type == 'number':
                rvalue = token.serialize()
                break

    rule_attrib = ''.join(tokens)
    LOG.debug('rule :%s', rule)

    for el in selector(doc):
        style_attrib = el.attrib.get('style', '') + ';'
        el.attrib['style'] = (style_attrib + rule_attrib).strip('; ')
        if rvalue:
            el.attrib['r'] = rvalue
