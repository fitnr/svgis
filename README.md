SVGIS
-----
[![Build Status](http://img.shields.io/travis/fitnr/svgis/master.svg?style=flat)](https://travis-ci.org/fitnr/svgis)
[![Coverage Status](https://img.shields.io/coveralls/fitnr/svgis/master.svg?style=flat)](https://coveralls.io/r/fitnr/svgis?branch=master)


Create SVG drawings from vector geodata files (SHP, geoJSON, etc).

SVGIS is great for: creating small multiples, combining lots of datasets in a sensible projection, and drawing styled based on classes in the source data. It's perfect for creating base maps for editing in a drawing program, and its CSS-based styling gives great flexibility for styling.

```
svgis draw input.shp -o out.svg
svgis draw south_dakota.shp north_dakota.geojson -o dakota.svg
svgis draw england.shp scotland.shp wales.shp --style gb.css -o great_britain.svg
````

Documentation: http://pythonhosted.org/svgis

## Install

Requires [fiona](http://pypi.python.org/pypi/fiona), which in turn requires GDAL.

To instal GDAL:

On OS X: `brew install gdal` (requires [Homebrew](http://brew.sh))

On Linux: `sudo apt-get install libgdal1-dev`

On Windows: see [OSGeo4W](https://trac.osgeo.org/osgeo4w/wiki)

Then:
````
pip install svgis
````

An option feature of svgis is clipping polygons to a bounding box. This will speed things up if you need to draw only part of a very complex feature.

To support clipping output shapes, you'll need the [GEOS](https://trac.osgeo.org/geos/) library:

* OS X: `brew install geos`
* Linux: `sudo apt-get install geos`
* Windows: GEOS is part of OSGeo4W, so you have it!

Then, install svgis with a slightly different command:

````
pip install svgis[clip]
````

## Commands

The `svgis` command line tool includes several utilities. The most important is `svgis draw`, which draws SVG maps based on input geodata layers.

Additional commands:
* `svgis bounds`: get the bounding box for a layer in a given projection
* `svgis graticule`: create a graticule (grid) within a given bounds
* `svgis project`: determine what projection `svgis draw` will (optionally) generate for given bounding box
* `svgis scale`: change the scale of an existing SVG
* `svgis style`: add css styles to an existing SVG

Read the [docs](http://pythonhosted.org/svgis/) for complete information on these commands and their options.

### Examples

Draw the outline of the contiguous United States, projected in Albers:
````
curl -O http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_nation_20m.zip
unzip cb_2014_us_nation_20m.zip
svgis draw cb_2014_us_nation_20m.shp --crs EPSG:5070 --scale 1000 --bounds -124 20.5 -64 49 -o us.svg
````

The next two examples use the [Natural Earth](http://naturalearthdata.com) admin-0 data set.

Draw upper income countries in green, low-income countries in blue:

````css
/* style.css */
.income_grp_5_Low_income {
    fill: blue;
}
.income_grp_3_Upper_middle_income {
    fill: green
}
.ne_110m_lakes {
    fill: #09d;
    stroke: none;
}
````
````
svgis draw --style style.css --class-fields income_grp ne_110m_admin_0_countries.shp ne_110m_lakes.shp -o out.svg
````

Draw national boundaries and lakes in Europe using an [Albers projection](http://epsg.io/102013), simplifying the output polygons, and draw Germany in purple.

````bash
svgis draw ne_110m_admin_0_countries.shp ne_110m_lakes.shp \
    --crs EPSG:102013 \ 
    --scale 1000 \ 
    --simplify 90 \ 
    --style '.ne_110m_admin_0_countries { fill: tan } .Germany { fill: purple }' \
    --style '.ne_110m_lakes { fill: #09d; stroke: none; }' \ 
    --class-fields name \ 
    --bounds -10 30 40 65 \ 
    -o out.svg
````
