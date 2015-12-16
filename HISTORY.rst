0.2.3
-----

* Fix class bug for NULL values

0.2.2
-----

* Prefix data classes with field name
* Remove test data from build

0.2.1
-----

* Add layer name to class list to get around ID issues in some SVG clients.

0.2.0
-----
* Simplify and update the draw api: draw.geometry now returns either a single svgwrite shape object or a svgwrite group.
* Fix errors when input has a Z coordinate
* Better bounds handling
* Fix numpy errors when drawing MultiPolygons
* --style flag now accepts a css file
* Expand tests
* Remove OSM support, which was broken and not easily fixable
* Move scale functions to sibling project fionautil

0.1.4
-----

* Project bounds as each file is parsed, rather than fussily at the end
* Simplify feature drawing and argument-passing
* Fix a NAD32-for-WGS84 typo in osm.
* Add 'svgis project' command line tool, for generating proj.4 strings
* Add tests

0.1.3
-----

* Add ability to read OSM files (if slowly)
* bug fixes in reading, writing

0.1.2
-----

* Add --no-viewbox option to create translated SVGs, rather than viewboxed ones
