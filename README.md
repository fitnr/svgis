svgis
-----

Create simple SVG drawings from geodata files (SHP, geoJSON, OSM, etc).

```bash
$ svgis draw in.shp -o out.svg
$ svgis draw in.shp in.geojson -o out.svg
````

## Install

Requires [fiona](http://pypi.python.org/pypi/fiona), which in turn requires GDAL.

Before installing, run the following on OS X: `brew install gdal`.
On Linux: `sudo apt-get -qq install -y libgdal1-dev`.

## Command line options

#### --bounds

Only draw the portion of the input file between latitudes 40 and 41 and longitudes -74 and -73 (roughly the New York City area). Note that coordinates are given as 'minx miny maxx maxy'.

````bash
svgis draw --bounds -74 40 -73 41 in.geojson out.svg
````

#### --scale

While SVG is a vector format, clients may have trouble handling very large numbers. Use the scale option to scale down the output. Dimensions in the map will be divided by this number (so larger numbers yield smaller coordinates in the output SVG). 

````bash
svgis draw --scale 1000 in.shp -o out.svg
````

### Projections

There are two ways to provide projections. Using both at the same time is unsupported. If the input file doesn't have an internal projection, SVGIS will assume [WGS84](http://epsg.io/4326).

#### --epsg

Use this option to provide the EPSG code of a desired projection. The example will draw an svg with [EPSG:2908](http://epsg.io/2908), the New York Long Island state plane projection.

````bash
svgis draw --epsg 2908 in.shp -o out.svg
````

#### --proj4

Use this option to provide a Proj4 string that defines a projection.

````bash
svgis draw --epsg 2908 in.shp -o out.svg
````

### --utm

Attempt to use a local UTM projection to draw the input geodata.

````bash
svgis draw --utm in.shp -o out.svg
````

### Style

#### --style

The style parameter takes either a CSS file or a CSS string.

````bash
svgis draw --style style.css in.shp -o out.svg
svgis draw --style "line { stroke: green; }" in.shp -o out.svg
````

#### --padding

Adds a padding around the output image.

````bash
svgis draw --padding 100 in.shp -o out.svg
````

#### --no-viewbox

By default, SVGIS uses a viewbox. If you have a problem opening the created svg file, try the '--no-viewbox' option, which will create an svg where the contents are translated into the frame

````bash
svgis draw --no-viewbox in.shp -o out.svg
svgis draw -x in.shp -o out.svg
````

## A note on OSM files

Conversion from OSM can be quite slow. You may find it more efficient to convert to `GeoJSON` or `Shapefile` using `ogr2ogr` or a similar tool.
