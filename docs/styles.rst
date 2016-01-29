Styling maps
============

SVGIS supports a limited subset of CSS for styling maps.

This applies both to the selectors, which are limited by 
Python's built-in XML support, and to the declarations, 
which are limited by the
`styling rules for SVG <http://www.w3.org/TR/SVG11/styling.html>`_.

A few useful things to know about how SVGIS draws maps:

* SVGIS places all the features in a layer in a group with an id set to
the layer's name.
* Polygons with holes are drawn as path elements with the class ``polygon``.
* SVGIS can set the id and class of features based on the input data.
* By default, SVGIS draws black lines and no fill on shapes.

Style the features in a layer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: css

    #cb_2014_us_nation_20m polygon {
        fill: blue;
        stroke: green;
        stroke-width: 1px;
        stroke-dasharray: 5, 3, 2;
    }


Style all polygons in a drawing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
        fill: tan
    }

    #ne_110m_lakes polygon,
    #ne_110m_lakes .polygon {
        fill: blue
    }



Style based on data
^^^^^^^^^^^^^^^^^^^^

Use the ``class-fields`` option to add classes to data based on their data.
In this example, the ``income_grp`` field in the admin-0 data set it used.
This is ideal of SVGIS, since the data is already broken into bins. These bins
have names like "5. Low Income", which SVGIS will sanitize to ``5_Low_Income``.

.. code:: css

    /* style.css */
    .income_grp_5_Low_income {
        fill: blue
    }
    .income_grp_3_Upper_middle_income {
        fill: green
    }

.. code:: bash

    svgis draw --style style.css \
    --class-fields income_grp \
    --project EPSG:54030 \
    ne_110m_admin_0_countries.shp \
    -o out.svg
