SVGIS
-----

Create SVG drawings from vector geodata files (SHP, geojson, etc).

SVGIS is great for: creating small multiples, combining lots of datasets in a sensible projection, and drawing styled based on classes in the source data. It's perfect for creating base maps for editing in a drawing program, and its CSS-based styling gives great flexibility for styling.

```
svgis draw input.shp -o out.svg
svgis draw south_dakota.shp north_dakota.geojson -o dakota.svg
svgis draw england.shp scotland.shp wales.shp --style gb.css -o great_britain.svg
````

Complete documentation, with more examples and explanation of classes and methods: https://svgis.readthedocs.io/en/stable/

## Install

Requires [fiona](http://pypi.python.org/pypi/fiona), which in turn requires GDAL.

See the [GDAL docs](https://gdal.org/download.html#binaries) for install info.

Then:
````
pip install svgis
````

An optional feature of svgis is clipping polygons to a bounding box. This will speed things up if you need to draw only part of a very complex feature.

````
pip install 'svgis[clip]'
````

## Commands

The `svgis` command line tool includes several utilities. The most important is `svgis draw`, which draws SVG maps based on input geodata layers.

Additional commands:
* `svgis bounds`: get the bounding box for a layer in a given projection
* `svgis graticule`: create a graticule (grid) within a given bounds
* `svgis project`: determine what projection `svgis draw` will (optionally) generate for given bounding box
* `svgis scale`: change the scale of an existing SVG
* `svgis style`: add css styles to an existing SVG

Read the [docs](https://svgis.readthedocs.io/en/stable/) for complete information on these commands and their options.

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

Draw national boundaries and lakes in Europe using the [LAEA Europe projection](https://epsg.io/3035), simplifying the output polygons, and coloring Germany in purple.

````bash
svgis draw ne_110m_admin_0_countries.shp ne_110m_lakes.shp \
    --crs EPSG:3035 \ 
    --scale 1000 \ 
    --simplify 90 \ 
    --style '.ne_110m_admin_0_countries { fill: tan } #Germany { fill: purple }' \
    --style '.ne_110m_lakes { fill: #09d; stroke: none; }' \ 
    --id-field name \ 
    --bounds -10 30 40 65 \ 
    -o out.svg
````
