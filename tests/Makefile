TIGERS = fixtures/cb_2014_us_nation_20m.json fixtures/tl_2015_11_place.json
PROJECTION = +proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs

.PHONY: fixtures

fixtures: $(TIGERS) fixtures/test.svg fixtures/zip.svg

fixtures/zip.svg: fixtures/test.zip $(TIGERS)
	svgis draw $(addprefix zip://$</,$(filter %.json,$^)) | \
	svgis style -c 'polygon{fill:green}' | \
	svgis scale -f 10 > $@

fixtures/test.zip: $(TIGERS)
	zip -q $@ $^

fixtures/test.svg: fixtures/cb_2014_us_nation_20m.json
	- svgis draw \
	  --viewbox -j '$(PROJECTION)' -f 1000 \
	  -c "polygon { fill: blue }" \
	  --bounds -124 20.5 -64 49 $< \
	  -o $@
	@touch $@
