svgis
-----

Create SVG drawings from geodata files (SHP, geoJSON, OSM, etc).

```bash
$ svgis draw in.shp -o out.svg
$ svgis draw in.shp in.geojson -o out.svg
````

## Install

Requires [fiona](http://pypi.python.org/pypi/fiona), which in turn requires GDAL.

Before installing, run the following on OS X: `brew install gdal`.
On Linux: `sudo apt-get -qq install -y libgdal1-dev`.

## Command line tools

The `svgis` command line tool has four commands: `draw`, `project`, `scale` and `style`. `Svgis scale` and `svgis style` will add a scaling factor or CSS style to an existing SVG file. `Svgis project` is a utility for printing the projection that `svgis draw` will generate for given bounding boxes.

The main command is `svgis draw`, which generates SVGs from input geodata.

### svgis draw options
#### --bounds

Takes four arguments in min-lon, min-lat, max-lon, max-lat order.

This example draw the portion of the input file between latitudes 40 and 41 and longitudes -74 and -73 (roughly the New York City area).

````bash
svgis draw --bounds -74 40 -73 41 in.geojson out.svg
````

Note that coordinates are given in longitude, latitude order, since in the world of the computer, it's better to be consistent with things like (x, y) order.

#### --scale

A integer scale factor. The map will be scaled by the inverse of this number.

While SVG is a vector format, clients may have trouble handling very large numbers. Use the scale option to scale down the output. Dimensions in the map will be divided by this number (so larger numbers yield smaller coordinates in the output SVG). 

````bash
svgis draw --scale 1000 in.shp -o out.svg
````

### --project

There are three ways to provide projections. Using both at the same time is unsupported. If the input file doesn't specify an internal projection, SVGIS will assume that the coordinates are given in [WGS84](http://epsg.io/4326).

If none of these three flags are given, SVGIS will check to see if the file is already in non lat-lng projection (e.g. a state plane system or the British National Grid). If the first input file is projected, that projection will be used for the output. If the first file is in lat-long coordinates, a local projection will be generated, just like if `--projection-method=local` was given.

#### EPSG codes

Accepts a valid [EPSG](http://epsg.io) code.

Use this option to provide the EPSG code of a desired projection. The example will draw an svg with [EPSG:2908](http://epsg.io/2908), the New York Long Island state plane projection.

````bash
svgis draw --project EPSG:2908 in.shp -o out.svg
````

#### Proj4 strings

Accepts a string in proj4 format.

Use this option to provide a Proj4 string that defines a projection.

````bash
PROJECTION=+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs
svgis draw --project $PROJECTION in.shp -o out.svg
````

#### UTM

Accepts either 'utm' or 'local'.

For UTM, attempt to draw coordiantes in the local UTM projection. The centerpoint of the bounding box will be used to pick the zone. Expect poor results for input data that crosses several UTM boundaries.
````bash
svgis draw --project utm in.shp -o out.svg
````

#### Automatically generated projection

When the local argument is given, SVGIS will generate a Transverse Mercator projection that centers on the input bounding box. This generally gives good results for an region roughly the size of a large urban area.

````bash
svgis draw --project local in.shp -o out.svg
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

#### --class-fields and --id-field

Use these options to specify fields in the source geodata file to use to determine the class or id attributes of the output SVG features. In the output fields, spaces will be replaced with underscores.

For example, assume a SHP file with a `countrycode`, `continent` and `currency` fields:
````bash
svgis draw --class-fields continent,foobr --id-field countrycode countries.shp -o out.svg
````

By default, each layer is wrapped in a group (`<g>`) with id equal to the name of its source layer.

The result may contain something like:
````svg
<g id="countries">
    <g class="North_America dollar" id="US">/* USA */</g>
    <g class="Europe pound" id="UK">/* UK */</g>
    <g class="Europe euro" id="DE">/* Germany */</g>
    /* ... */
</g>
````

## A note on OSM files

Conversion from OSM can be quite slow. You may find it more efficient to convert to `GeoJSON` or `Shapefile` using `ogr2ogr` or a similar tool.
