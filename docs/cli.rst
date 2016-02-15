==================
Command-line usage
==================

The main function of the SVGIS command line tool is to draw maps. SVGIS also comes with several helper tools for modifying maps and getting generating map projections.

svgis draw
==========

Draw SVGs from input geodata.
::

    Usage: svgis draw [OPTIONS] INPUT...

    Options:
      -o, --output FILENAME           Defaults to stdout.
      -b, --bounds minx, miny, maxx, maxy
                                      In the same coordinate system as the input
                                      layers
      -c, --style CSS                 CSS file or string
      -f, --scale INTEGER             Scale for the map (units are divided by this
                                      number)
      -p, --padding INTEGER           Buffer the map (in projection units)
      -i, --id-field FIELD            Geodata field to use as ID
      -a, --class-fields FIELDS       Geodata fields to use as class (comma-
                                      separated)
      -j, --crs KEYWORD               Specify a map projection. Accepts either an
                                      EPSG code (e.g. epsg:4456), a proj4 string,
                                      a file containing a proj4, "utm" (use local
                                      UTM), "file" (use existing), "local"
                                      (generate a local projection).
      -s, --simplify FACTOR           Simplify geometries. Accepts an integer
                                      between 1 and 100, the percentage points in
                                      each geometry to retain
      --clip / -n, --no-clip          Clip shapes to bounds. Slower, produces
                                      smaller files (default: clip).
      -x, --no-viewbox                Draw SVG without a ViewBox. May improve
                                      compatibility.
      -l, --inline / --no-inline      Inline CSS. Slightly slower, but required by
                                      some clients (e.g. Adobe) (default: do not
                                      inline).
      -q, --quiet                     Ignore warnings.
      -v, --verbose                   Talk a lot.
      -h, --help                      Show this message and exit.


bounds
^^^^^^

Takes four arguments in min-lon, min-lat, max-lon, max-lat order.

This example draw the portion of the input file between latitudes 40 and
41 and longitudes -74 and -73 (roughly the New York City area).

.. code:: bash

    svgis draw --bounds -74 40 -73 41 in.geojson out.svg

Note that coordinates are given in longitude, latitude order, since in
the world of the computer, it's better to be consistent with things like
(x, y) order.

scale
^^^^^

A integer scale. The map will be scaled by 1 over this number. In other words,
for a map at a 1:1000 scale, use:

.. code:: bash

    svgis draw --scale 1000 in.shp -o out.svg

While SVG is a vector format, clients may interpret the internal units as
a certain display unit e.g. (pixels, fractions of an inch). Additionally, 
clients may have trouble handling very large numbers, using the scale option
will produce smaller units.

(The shorthand option for ``--scale`` is ``-f`` as in factor.)

crs
^^^^^^^

The ``crs`` argument accepts a particular projection or a keyword that
helps SVGIS pick a projection for you.

-  `EPSG <http://epsg.io>`__ code
-  Proj4 string
-  A text file containing a Proj4 string
-  Either the 'utm' or 'local' keyword

If this flag isn't given, SVGIS will check to see if the file is already in
non lat-lng projection (e.g. a state plane system or the British
National Grid). If the first input file is projected, that projection
will be used for the output. If the first file is in lat-long
coordinates, a local projection will be generated, just like if
``--crs=local`` was given.

This example will draw an svg with `EPSG:2908 <http://epsg.io/2908>`__,
the New York Long Island state plane projection:

.. code:: bash

    svgis draw --crs EPSG:2908 nyc.shp -o nyc.svg

This example uses a Proj.4 string to draw with the `North America Albers
Equal Area Conic <http://epsg.io/102008>`__ projection, which doesn't
have an EPSG code.

.. code:: bash

    svgis draw in.shp -o out.svg \
        --crs "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 \
        +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"

This is equivalent to the above, and uses a proj.4 file:

.. code:: bash

    echo "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 \
    +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs" > proj4.txt

    svgis draw in.shp --crs proj4.txt -o out.svg

With the ``utm`` keyword, SVGIS attempts to draw coordinates in the
local UTM projection. The centerpoint of the bounding box will be used
to pick the zone. Expect poor results for input data that crosses
several UTM boundaries.

.. code:: bash

    svgis draw --crs utm in.shp -o out.svg
    svgis draw -j utm in2.shp -o out2.svg

When the local argument is given, SVGIS will generate a Transverse
Mercator projection that centers on the input bounding box. This
generally gives good results for an region roughly the size of a large
urban area.

.. code:: bash

    svgis draw --crs local input.shp -o out.svg
    svgis draw -j local input.shp -o out.svg

If, for some reason you want to draw an SVG in lat-long coordinates,
use the ``file`` keyword to force the projection of the first passed file:

.. code:: bash
    svgis draw --crs file input.shp -o out.svg
    svgis draw -j file one.shp two.geojson -o out.svg


To properly convert the input coordinate, svgis needs to know your input
projection. If the input file doesn't specify an internal projection,
SVGIS will assume that the coordinates are given in
`WGS84 <http://epsg.io/4326>`__.

(The shorthand option for ``--crs`` is ``-j`` as in ject.)

style
^^^^^

The style parameter takes either a CSS file or a CSS string.

.. code:: bash

    svgis draw --style style.css in.shp -o out.svg
    svgis draw --style "line { stroke: green; }" in.shp -o out.svg

SVGIS adds a ``polygon`` class to paths that drawn to represent
multi-part polygons (polygons with holes).

This argument can be provided multiple times.

(The shorthand option for ``--style`` is ``-c`` as in CSS.)

padding
^^^^^^^

Adds a padding around the output image. Accepts an integer in svg units.

.. code:: bash

    svgis draw --padding 100 in.shp -o out.svg

no-viewbox
^^^^^^^^^^

By default, SVGIS uses a viewbox. If you have a problem opening the
created svg file in your drawing program (e.g. Adobe Illustrator), try
the '--no-viewbox' option, which will create an svg where the contents
are translated into the frame.

.. code:: bash

    svgis draw --no-viewbox in.shp -o out.svg
    svgis draw -x in.shp -o out.svg

class-fields and id-field
^^^^^^^^^^^^^^^^^^^^^^^^^

Use these options to specify fields in the source geodata file to use to
determine the class or id attributes of the output SVG features. In the
output fields, spaces will be replaced with underscores.

For example, the `Natural Earth
admin\_0 <http://www.naturalearthdata.com/downloads/110m-cultural-vectors/>`__
file contains nation polygons, and includes ``continent``,
``income_grp`` and ``name`` fields:

.. code:: bash

    svgis draw --class-fields continent,income_grp --id-field name \
      ne_110m_admin_0_countries.shp -o out.svg

The result will include something like:

.. code:: xml

    <g id="ne_110m_admin_0_countries" class="scalerank featurecla labelrank ...">
        <g id="Afghanistan" class="ne_110m_admin_0_countries continent_Asia income_grp_5._Low_income">/* Afghanistan */</g>
        <g id="Angola" class="ne_110m_admin_0_countries continent_Africa income_grp_3._Upper_middle_income">/* Angola */</g>
        /* ... */
        <g id="Zimbabwe" class="ne_110m_admin_0_countries continent_Africa income_grp_5._Low_income">/* Zimbabwe */</g>
    </g>

Note that each layer is always wrapped in a group with ``id`` set to the its name,
and ``class`` set to the names of the its fields.

The ``id`` (``ne_110m_admin_0_countries``) is repeated as a classes
in each element of a layer. This makes writing CSS that addresses
particular layers easier, given that some implementations of SVG don't
properly implement css rules with ids (e.g. Adobe Illustrator, ImageMagick).

Note that the ``income\_grp`` field contains values like "5. Low income",
which resultes in a class like ``income_grp_5._Low_income``. Classes
like this can be used in CSS by escaping the period with a bash slash (``\``):

.. code::

    .income_grp_5\._Low_income {
        fill: teal;
        stroke: none;
    }

The ``class-fields`` argument can be provided multiple times.

simplify
^^^^^^^^

Requires numpy. Install with ``pip install svgis[simplify]`` to make
this available.

This option uses the `Visvalingam <http://bost.ocks.org/mike/simplify/>`_ 
algorithm to draw smaller shapes. The ideal setting will depend on source data
and the requirements of the map.

The ``--simplify`` option takes a number between 1 and 100, which is the 
percentage of points to retain. Numbers above 80 usually produce output with
few visible changes.

.. code:: bash

    svgis draw --simplify 75 in.shp -o out.svg
    svgis draw -s 25 in.shp -o out.svg

inline
^^^^^^

Run with this option to add style information onto each element.
Some SVG clients (Adobe Illustrator) prefer inline styles.

When ``--inline`` is given, SVG elements will look like:

.. code:: xml

    <polyline style="stroke: green; ..." points="0,0 1,1">

.. code:: bash

    svgis draw --style example.css --inline in.geojson -o out.svg
    svgis draw -s example.css -l in.geojson -o out.svg

clip/no-clip
^^^^^^^^^^^^

Install with ``pip install svgis[clip]`` to make this available. This
requires additional libraries, see the `shapely installation
notes <https://github.com/Toblerity/Shapely>`__.

When installed with the clip option, SVGIS will try to clip output
shapes to just outside of the bounding box. Use this option to disable
that behavior.

::
    svgis draw --bounds -170 40 -160 30 --no-clip in.shp --o out.shp
    svgis draw -b 125 30 150 50 -n in.shp --o out.shp

SVGIS always omits features that fall completely outside the bounding 
box, clipping edits the shapes so that the parts that lie outside of
the bounding box are omitted.

Clipping won't occur when no bounding box is given.


Helpers
=======

svgis bounds
^^^^^^^^^^^^

Get the bounds of a layer. The ``--crs`` option will transform the 
bounds into the given projection, otherwise the native coordinates 
are returned.

The result is four coordinates in minx, miny, maxx, maxy order:

::

    svgis bounds in.shp
    -87.8098 41.6444 -87.5209 42.0201


This is useful for setting the bounds of a drawing based on the bounds
of a layer:

::

    svgis bounds in.shp |
    xargs -n 4 svgis draw --crs EPSG:3003 in.shp in2.json in3.shp --bounds > out.svg


Or, check what projection SVGIS will generate given a file:

::

    svgis bounds in.shp |
    xargs -n 4 svgis project --

Keep in mind that when converting between projections, ``svgis bounds`` is lazy.
The returned bounding box will cover the geometry, but for certain extreme
reprojections it may include extra space.

::

    Usage: svgis bounds [OPTIONS] [LAYER]

      Return the bounds for a given layer.

    Options:
      -j, --crs KEYWORD  Specify a map projection. Accepts either an EPSG code
                     epsg:4456), a proj4 string, a file containing a proj4, "utm"
                     (use local UTM), "file" (use existing), "local" (generate a
                     local projection).
      -h, --help     Show this message and exit.



svgis graticule
^^^^^^^^^^^^^^^^

Generate a graticule (grid) in a given projection. The output file is in geojson format.

For coordinates with negative numbers, use the ``--`` argument separator to prevent the utility
getting confused:

::
    svgis graticule -o graticule.json -- 16.3 -34.8 32.8 -22.0

::

    Usage: svgis graticule [OPTIONS] minx miny maxx maxy

      Generate a GeoJSON containing a graticule. Accepts a bounding box in
      longitude and latitude (WGS84).

    Options:
      -s, --step FLOAT       Step between lines (in projected units)  [required]
      -j, --crs TEXT         Specify a map projection. Accepts either an EPSG code
                             (e.g. epsg:4456), a proj4 string, a file containing a
                             proj4, "utm" (use local UTM), "local" (generate a
                             local projection).
      -o, --output FILENAME  Defaults to stdout.
      -h, --help             Show this message and exit.


svgis scale
^^^^^^^^^^^

Scale all coordinates in an SVG by a given factor.

::

    Usage: svgis scale [OPTIONS] [INPUT] [OUTPUT]

    Options:
      -f, --scale INTEGER
      -h, --help           Show this message and exit.


svgis style
^^^^^^^^^^^

Add or replace the CSS style in an SVG.

::

    Usage: svgis style [OPTIONS] [INPUT] [OUTPUT]

    Options:
      -s, --style TEXT    Style to append to SVG. Either a valid CSS string, a
                          file path (must end in '.css'). Use '-' for stdin.
      -r, --replace TEXT
      -h, --help          Show this message and exit.


svgis project
^^^^^^^^^^^^^

SVGIS can automatically generate local projections or pick the local UTM projection for input geodata. This utility gives the projection SVGIS would pick for a given boundary box. It expects WGS84 coordinates.

For coordinates with negative numbers, use the ``--`` argument separator to prevent the utility
getting confused:

::
    svgis project -m utm -- 16.3449768409 -34.8191663551 32.830120477 -22.0913127581
    +proj=utm +zone=35 +south +datum=WGS84 +units=m +no_defs

::

    Usage: svgis project [OPTIONS] minx, miny, maxx, maxy

    Options:
      -j, --proj [utm|local]  Defaults to local.
      -h, --help              Show this message and exit.
