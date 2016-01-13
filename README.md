SVGIS
-----

Create SVG drawings from vector geodata files (SHP, geoJSON, etc).

```bash
svgis draw input.shp -o out.svg
svgis draw south_dakota.shp south_dakota.geojson -o dakota.svg
````

## Install

Requires [fiona](http://pypi.python.org/pypi/fiona), which in turn requires GDAL.

Before installing, run the following on OS X: `brew install gdal`.
On Linux: `sudo apt-get -qq install -y libgdal1-dev`.

## Command line tools

The `svgis` command line tool has four commands: `draw`, `project`, `scale` and `style`. `Svgis scale` and `svgis style` will add a scaling factor or CSS style to an existing SVG file. `Svgis project` is a utility for printing the projection that `svgis draw` will generate for given bounding boxes.

The main command is `svgis draw`, which generates SVGs from input geodata.

### svgis draw
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

#### --project

The project argument accept a particular projection or a keyword that helps SVGIS pick a projection for you. 

* [EPSG](http://epsg.io) code
* Proj4 string
* A text file containing a Proj4 string
* Either the 'utm' or 'local' keyword

The the flag isn't, SVGIS will check to see if the file is already in non lat-lng projection (e.g. a state plane system or the British National Grid). If the first input file is projected, that projection will be used for the output. If the first file is in lat-long coordinates, a local projection will be generated, just like if `--projection-method=local` was given.

This example will draw an svg with [EPSG:2908](http://epsg.io/2908), the New York Long Island state plane projection:
````bash
svgis draw --project EPSG:2908 nyc.shp -o nyc.svg
````

This example uses a Proj.4 string to draw with the [North America Albers Equal Area Conic](http://epsg.io/102008) projection, which doesn't have an EPSG code.
````bash
svgis draw in.shp -o out.svg \
    --project "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
````

This is equivalent to the above, and uses a proj.4 file:
````bash
echo "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs" > proj4.txt
svgis draw in.shp --project proj4.txt -o out.svg
````

With the `utm` keyword, SVGIS attempts to draw coordinates in the local UTM projection. The centerpoint of the bounding box will be used to pick the zone. Expect poor results for input data that crosses several UTM boundaries.
````bash
svgis draw --project utm in.shp -o out.svg
````

When the local argument is given, SVGIS will generate a Transverse Mercator projection that centers on the input bounding box. This generally gives good results for an region roughly the size of a large urban area.
````bash
svgis draw --project local input.shp -o out.svg
svgis draw -j local input.shp -o out.svg
````

To properly convert the input coordinate, svgis needs to know your input projection. If the input file doesn't specify an internal projection, SVGIS will assume that the coordinates are given in [WGS84](http://epsg.io/4326).

#### --style

The style parameter takes either a CSS file or a CSS string.

````bash
svgis draw --style style.css in.shp -o out.svg
svgis draw --style "line { stroke: green; }" in.shp -o out.svg
````

#### --padding

Adds a padding around the output image. Accepts an integer in svg units.

````bash
svgis draw --padding 100 in.shp -o out.svg
````

#### --no-viewbox

By default, SVGIS uses a viewbox. If you have a problem opening the created svg file in your drawing program (e.g. Adobe Illustrator), try the '--no-viewbox' option, which will create an svg where the contents are translated into the frame.

````bash
svgis draw --no-viewbox in.shp -o out.svg
svgis draw -x in.shp -o out.svg
````

#### --class-fields and --id-field

Use these options to specify fields in the source geodata file to use to determine the class or id attributes of the output SVG features. In the output fields, spaces will be replaced with underscores.

For example, the [Natural Earth admin_0](http://www.naturalearthdata.com/downloads/110m-cultural-vectors/) file contains nation polygons, and includes `continent`, `income_grp` and `name` fields:
````bash
svgis draw --class-fields continent,income_grp --id-field name ne_110m_admin_0_countries.shp -o out.svg
````

The result will include something like:
````
<g id="ne_110m_admin_0_countries">
    <g class="ne_110m_admin_0_countries continent_Asia income_grp_5_Low_income" id="Afghanistan">/* Afghanistan */</g>
    <g class="ne_110m_admin_0_countries continent_Africa income_grp_3_Upper_middle_income" id="Angola">/* Angola */</g>
    /* ... */
    <g class="ne_110m_admin_0_countries continent_Africa income_grp_5_Low_income" id="Zimbabwe">/* Zimbabwe */</g>
</g>
````
The name of a layer (`ne_110m_admin_0_countries`) will always be in the classes of its child elements. This makes writing CSS that addresses particular layers easier, given that some implementations of SVG don't properly css rules with ids (e.g. Adobe Illustrator, ImageMagick).

Note that the 'income_grp' field contains values like "4. Lower middle income", SVGIS has sanitized them for use in the output svg.

Each layer is always wrapped in a group (`<g>`) with id equal to the name of its source layer.

## Further examples

Draw the outline of the contiguous United States, projected in Albers:
````
curl -O http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_nation_20m.zip
unzip cb_2014_us_nation_20m.zip
svgis draw --project EPSG:5070 --scale 1000 --bounds -124 20.5 -64 49 cb_2014_us_nation_20m.shp -o us.svg
````
