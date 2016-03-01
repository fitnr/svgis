Styling maps
============

You can use any kind of CSS that you like to style maps
made with SVGIS. However, when using the ``inline`` option,
SVGIS supports a subset of CSS.

This applies both to the selectors, which are limited by 
Python's built-in XML support, and to the declarations, 
which are limited by the
`styling rules for SVG <http://www.w3.org/TR/SVG11/styling.html>`_.

A few useful things to know about how SVGIS draws maps:

* SVGIS places all the features in a layer in a group. This group has an ``id`` equal to the layer's name, and a ``class`` equal to the column names of the layer.
* The ``class-fields`` and ``id-field`` options can be used to add a ``class`` and ``id`` to the the drawing's elements. SVGIS always adds the layer name as a class to each feature.
* Polygons with holes are drawn as ``path`` elements with the class ``polygon``.
* SVGIS can set the id and class of features based on the input data.
* By default, SVGIS draws black lines and no fill on shapes.


Style the features in a layer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This works because every element of layer ``cb_2014_us_nation_20m.shp`` will have
the class ``cb_2014_us_nation_20m``.

.. code:: css
    
    .cb_2014_us_nation_20m {
        fill: blue;
        stroke: green;
        stroke-width: 1px;
        stroke-dasharray: 5, 3, 2;
    }


Style certain layers
^^^^^^^^^^^^^^^^^^^^^

Say that we're combining geodata from the US Census with data from Natural
Earth. All Census layers have a GEOID field, and we use this to draw these
layers with a ``opacity: 0.50``.

.. code:: css

    /* example.css */
    .GEOID * {
        opacity: 0.50;
    }
    .tl_2015_us_aiannh {
        fill: orange;
    }
    .ne_10m_time_zones {
        stroke-width: 2px;
    }


Use this style to create a map projected in
`North America Equidistant Conic <http://epsg.io/102010>`_.

.. code:: bash

    svgis draw --style example.css \
        --project EPSG:102010 \
        tl_2015_us_state.shp \
        tl_2015_us_aiannh.shp \
        ne_10m_time_zones.shp \
        -o out.svg



Style all polygons in a drawing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Polygons with holes are drawn as paths, and multipolygons are drawn in groups.
To style all polygons, use the ``.polygon`` class:

.. code:: css

    polygon,
    .polygon {
        fill: orange;
        stroke: black;
        stroke-opacity: 0.8;
    }


Styling with data
^^^^^^^^^^^^^^^^^

The SVGIS ``class-fields`` and ``id-field`` options can be used to add ``class``
and ``id`` attributes to the output SVG. These, in turn, can be used to style
the map based on the data.

Note that the SVGIS has to do minor clean up on the data. Whitespace is replaced
with underscores, and periods, numbers signs and double-quote characters (``.#"``)
are removed. Null values are represented with the Pythonic "None".

Additionally, CSS classes and IDs technically must begin with ascii letters,
underscores or dashes. Classes and IDs that begin with other characters (after
stripping illegal characters) are prefixed with an underscore (``_``).

Style a specific element
~~~~~~~~~~~~~~~~~~~~~~~~

To style just Germany in the `Natural Earth <http://naturalearthdata.com>`_
countries layer, use the ``id-field`` option to set the ID of all
features to their ``name_long``. This example also includes lakes. Because
lakes don't have a ``name_long`` atribute, the individual polygons won't
have an ID field.

.. code:: bash

    svgis draw --style purple.css \
        --id-field name_long \
        ne_110m_admin_0_countries.shp \
        ne_110m_lakes.shp \
        -o out.svg

.. code:: css

    /* purple.css */
    #Germany {
        fill: purple;
    }

    #ne_110m_admin_0_countries polygon,
    #ne_110m_admin_0_countries .polygon {
        fill: tan;
    }

    #ne_110m_lakes polygon,
    #ne_110m_lakes .polygon {
        fill: blue;
    }


Styling groups of elements
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``class-fields`` option to add classes to data based on their data.
In this example, the ``income_grp`` field in the admin-0 data set it used.
This is ideal of SVGIS, since the data is already broken into bins. These bins
have names like "5. Low Income", which SVGIS is sanitized to
``5_Low_Income``.

.. code:: css

    /* style.css */
    .income_grp_5_Low_income {
        fill: blue;
    }
    .income_grp_3_Upper_middle_income {
        fill: green;
    }

.. code:: bash

    svgis draw --style style.css \
    --class-fields income_grp \
    ne_110m_admin_0_countries.shp \
    -o out.svg
