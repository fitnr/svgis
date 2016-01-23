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


def add_style(svgfile, newstyle, replace=False):
    '''Add to the CSS style in an SVG file.
    svgfile -- Path to an SVG file or an SVG string
    newstyle -- CSS string
    replace -- (boolean) If true, replace the existing CSS with newstyle (default: False)
    '''
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
        style = defs.getElementsByTagName('style').item(0)

        if replace:
            style.firstChild.replaceWholeText(newstyle)
        else:
            style.firstChild.nodeValue += ' ' + newstyle

    else:
        style = svg.createElement('style')
        css = svg.createTextNode(newstyle)
        style.appendChild(css)
        defs.appendChild(style)

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
