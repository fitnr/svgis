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

* SVGIS places all the features in a layer in a group. This group has an ``id`` equal to
the layer's name, and a ``class`` equal to the column names of the layer.
* The ``class-fields`` and ``id-field`` options can be used to add ``class``es and ``id``s
to the data. SVGIS always adds the layer name as a class to each feature.
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


Style a specific feature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Style based on data
^^^^^^^^^^^^^^^^^^^^

Use the ``class-fields`` option to add classes to data based on their data.
In this example, the ``income_grp`` field in the admin-0 data set it used.
This is ideal of SVGIS, since the data is already broken into bins. These bins
have names like "5. Low Income", which SVGIS is partially sanitized to
``5._Low_Income``. The period can be escaped with a ``\``.

.. code:: css

    /* style.css */
    .income_grp_5\._Low_income {
        fill: blue;
    }
    .income_grp_3\._Upper_middle_income {
        fill: green;
    }

.. code:: bash

    svgis draw --style style.css \
    --class-fields income_grp \
    --project EPSG:54030 \
    ne_110m_admin_0_countries.shp \
    -o out.svg
