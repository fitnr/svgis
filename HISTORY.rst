0.5.2
-----
* Fix an error checking certain geometries (#8)
* Migrate CI workflows from Travis to Github Actions
* Remove Python 3.5 from list of supported versions

0.5.1
-----

* Improve Windows compatibility (#5)
* Improve projection handling (#4)
* Update documentation

0.5.0
-----

* Drop Python 2 support
* Add "data_fields" option to generate data attributes in output SVG.
* Update for newer pyproj and Fiona APIs
* Shift CSS handling from tinycss to tinycss2
* Add requirements for cssselect, move lxml from optional to required

0.4.6
-----

* bump fiona requirements to 1.8

0.4.5
-----

* bump requirements

0.4.4
-----

* bump fiona requirements, now compatible with GDAL v2.
* Ignore id_field in layers without that field
* Sanitize ampersands in data fields
* Allow an x/y pair argument to `svgis project`.

0.4.3
-----

* Improve CSS parsing and creating in `style`
* Simplify string conversion in `svg`
* Expand and update tests a bit

0.4.2
-----

* Bump fionautil requirement, fixing bug that occurs when Numpy is missing.

0.4.1
-----

* Add support for zipped data
* Change "svgis style --style" shorthand option from -s to -c
* Improve support for custom map drawing workflows
* Change keyword argument for SVGIS from out_crs to crs
* Shorthand reprojections now work for with data in any projection
* build as a universal wheel
* Fix bug for unicode attributes in Python 2 (0.4.0 regression)
* Fix bug with certain uses of 'file' projection keyword
* Fix error on multipolygon coordinates in unexpanded generators

0.4.0
-----

* Make --no-viewbox default in svgis draw
* Refactor internal bounds handling, squashing a few bugs
* Better handling for precision and padding in svgis.SVGIS
* Filter out successive identical coordinates in geometries
* Fix padding to truly be in output (projected) units
* Warn, don't crash, when geometry is null
* Additional verbose flags now provide more debugging infomation
* Repair bug that sometimes added styles based on a class substring, rather than exact match
* Put r attributes right on the element when inlining
* Fix bug when layer contained a field with its name
* Restructured modules: renamed 'clip' and 'convert' to 'transform' and 'bounding'

0.3.10
------

* Fix CDATA bug with svgis style
* refactoring, PEP 8 formatting
* Fix bug that ignored precision
* Correctly identify and use projections in projected files

0.3.9
-----

* Remove periods and number signs from classes and ids.
* Refactor classing functions to svgis.style
* Improve error messages when drawing features.

0.3.8
-----

* Make inlined styles default
* Handle empty files without complaining
* ignore topological errors when clipping

0.3.7
-----

* Add precision argument for `svgis draw`

0.3.6
-----

* Add `svgis graticule` command line tool
* Ensure no repeated style rules when inlining CSS.
* Round numbers at the last minute in the svg module. This is quicker.
* Improve py 2/3 compatibility, esp. when testing.

0.3.5
-----

* Fix problem reprojecting bounds with mixed projections.
* Add cli tool for getting bounds of a layer
* Repair --verbose option.
* Add `svgis bounds` command line tool for checking the bounds of a layer.
* Expand tests (coverage now above 90%)

0.3.4
-----

* change `--project` option to `--crs`.
* Fix error with empty CSS selectors
* Add quiet and verbose logging options to `svgis draw`.
* Fix simplification in `svgis draw`.
* Ensure that geojson layers get a pretty name.
* Regularize `svgis.svg`, adding tools for creating more SVG elements, even those not directly used here.
* Try, just slightly, not to have infinite bounds
* Expand docs.

0.3.3
-----

* Switch from `argparse` to `click` for cli functions. Much better performance, same options.
* Switch `--simplify` argument to accept an integer between 1-99
* Change `--project/-j` option in `svgis project` to `--method/-m`
* Remove lxml dependency for inlining CSS.
* Completely refactor functions that parse XML to use ElementTree (quicker than minidom).
* Add column names to class of layer group.
* Prevent broken pipes
* Squash several bugs related to setting class fields.
* Squash bugs in drawing certain paths.
* Remove duplicate/unused code.
* Ensure use of unicode internally, fixed some small Py3 bugs.
* More tests and more docs!

0.3.2
-----

* Fix bug introduced in 0.3.1, caused improper bounds in output SVGs.
* Add `svgis.map` function as a shorthand for working with the API

0.3.1
-----

* Add option to clip files, requires Shapely
* Add option to inline files, requires lxml
* Add line simplification option using Visivalingam algorithm, requires numpy
* Remove svgwrite as a dependency for faster file writing
* Tests expanded and code refactored, crushing lots of bugs
* --proj option can now read a file containing a proj4 string
* Allow unicode in class and id fields

0.2.5
-----

* Accept a text file containing a proj4 string in `svgis draw --project`
* fix typo in cli help
* add version option to cli

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
