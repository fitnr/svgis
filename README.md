SVGIS
-----

Create SVG drawings from vector geodata files (SHP, geoJSON, etc).

SVGIS is good for: creating small multiples, combining lots of datasets in a sensible projections, and drawing maps with  basic styles based on classes in the source data.


```bash
svgis draw input.shp -o out.svg
svgis draw --project utm south_dakota.shp north_dakota.geojson -o dakota.svg
svgis draw --style my.css england.shp scotland.shp wales.shp -o great_britain.svg
````

## Install

Requires [fiona](http://pypi.python.org/pypi/fiona), which in turn requires GDAL.

Before installing, run the following on OS X: `brew install gdal`.
On Linux: `sudo apt-get -qq install libgdal1-dev`.

Then:
```
pip install svgis
```

An additional feature is available if you want to download more prerequisites:
````
# Clip output shapes to the bounding box (smaller files)
brew install geos # os x
sudo yum/apt-get geos # linux
pip install svgis[clip]
````

## Command line tools

The `svgis` command line tool has four commands: `draw`, `project`, `scale` and `style`. `svgis scale` and `svgis style` will add a scaling factor or CSS style to an existing SVG file. `svgis project` is a utility for determining what projection `svgis draw` will (optionally) generate for given bounding boxes. Read the [docs]() for complete information on these commands and their options.

### Examples

Draw the outline of the contiguous United States, projected in Albers:
````
curl -O http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_nation_20m.zip
unzip cb_2014_us_nation_20m.zip
svgis draw --project EPSG:5070 --scale 1000 --bounds -124 20.5 -64 49 cb_2014_us_nation_20m.shp -o us.svg
````

The next two examples use the [Natural Earth](http://naturalearthdata.com) admin-0 data set.

Draw upper income countries in green, low-income countries in blue:

````
/* style.css */
.income_grp_5_Low_income {
    fill: blue
}
.income_grp_3_Upper_middle_income {
    fill: green
}
````
````
svgis draw --style style.css --class-fields income_grp ne_110m_admin_0_countries.shp -o out.svg
````

Draw national boundaries in the Europe using an [Albers projection](http://epsg.io/102013), simplifying the output polygons, and draw Germany in purple.
````
svgis draw \
    --project EPSG:102013 \
    --scale 1000 \
    --simplify 0.10 \
    --style "#Germany { fill: purple }" \
    --id-field name \
    --bounds -10 30 40 65 \
    ne_110m_admin_0_countries.shp \
    -o out.svg
```
