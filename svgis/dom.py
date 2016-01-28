import re

'''
A very tiny implementation of XPath for SVG.
'''


SVG_NS = 'http://www.w3.org/2000/svg'


def cdata(text):
    return '<![CDATA[' + text + ']]>'


def ns(tag):
    return '{' + SVG_NS + '}' + tag


def _nsmatch(match):
    return ns(match.group(0))


def _build_tokenlist(tokens):
    tokenlists = [[]]

    for token in tokens:
        if token.value == ',':
            tokenlists.append([])
            continue

        tokenlists[-1].append(token)

    return tokenlists


def _runrules(string):
    rules = [
        (r'^_SPACE_$', '/'),
        (r'>', '/'),
        (r'^([^.^#^>^ ]+)$', _nsmatch),
        (r'^#([^.^#^>^ ]+)$', r"[@id='\1']"),
        (r'^\.([^.^#^>^ ]+)$', r"[@class='\1']"),
    ]
    for rule in rules:
        string = re.sub(*rule, string=string)
        if string == '/':
            break
    return string


def _processtokenlist(tokenlist):
    raw = ''.join(t.value for t in tokenlist)
    raw = raw.replace(' ', ' _SPACE_ ')

    # Break the CSS selector on delimiter
    units = re.sub(r'([.>#])', r' \1', raw).strip()

    if units.startswith('_SPACE_'):
        units = units[len('_SPACE_ '):]

    if units.endswith('_SPACE_'):
        units = units[:len('_SPACE_ ')]

    # Replace the CSS with XPath
    tokens = [_runrules(x) for x in units.split(' ')]

    selector = (''.join(tokens)).replace('/[', '/*[')

    if selector.startswith('['):
        selector = '*' + selector

    return './/' + selector


def xpath(tokens):
    '''
    Generate limited xpath expressions suitable for ElementTree.find.

    Args:
        tokens (list): tinycss.selector tokens

    Returns:
        list of xpath expressions
    '''

    tokenlists = _build_tokenlist(tokens)
    paths = [_processtokenlist(tl) for tl in tokenlists]
    return paths
