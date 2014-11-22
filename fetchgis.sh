#!/bin/bash
# Copyright © 2014 Emily Maier
# Fetches and processes the GIS data needed to build the maps. Vector data is
# inserted into the PostGIS database, while raster data is converted to the
# EPSG:4269 projection.

# Grab a file to be extracted. Parameters are the URL to fetch and the name of
# the extracted file.
fetch() {
	if [ -f $2 ]
	then
		echo "$2 exists, skipping"
		return 1
	fi
	echo "fetching $2"
	wget -T 60 $1 || { echo "failed to fetch $2"; exit 1; }
	echo "fetched ${2}, cooling down"
	sleep 30
	return 0
}

cd /var/lib/house/input

fips_states=(01 02 04 05 06 08 09 10 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56)
for fips_state in ${fips_states[@]}
do
	fetch "ftp://ftp2.census.gov/geo/tiger/TIGER2014/PLACE/tl_2014_${fips_state}_place.zip" "tl_2014_${fips_state}_place.shp"
	if [ $? -eq 0 ]
	then
		unzip "tl_2014_${fips_state}_place.zip"
		rm "tl_2014_${fips_state}_place.zip"
		PGCLIENTENCODING="latin1" ogr2ogr -nlt PROMOTE_TO_MULTI -nln places -append -f PostgreSQL PG:"dbname=gis" tl_2014_${fips_state}_place.shp
	fi
done

fetch "ftp://ftp2.census.gov/geo/tiger/TIGER2014/STATE/tl_2014_us_state.zip" "tl_2014_us_state.shp"
if [ $? -eq 0 ]
then
	unzip "tl_2014_us_state.zip"
	rm "tl_2014_us_state.zip"
	ogr2ogr -nlt PROMOTE_TO_MULTI -nln states -f PostgreSQL PG:"dbname=gis" tl_2014_us_state.shp
	psql -c "create materialized view simplified as select ST_Simplify(wkb_geometry, 0.05) as wkb_geometry, name from states" gis
fi

fetch "ftp://ftp2.census.gov/geo/tiger/TIGER2014/PRIMARYROADS/tl_2014_us_primaryroads.zip" "tl_2014_us_primaryroads.shp"
if [ $? -eq 0 ]
then
	unzip "tl_2014_us_primaryroads.zip"
	rm "tl_2014_us_primaryroads.zip"
	PGCLIENTENCODING="latin1" ogr2ogr -nlt PROMOTE_TO_MULTI -nln roads -f PostgreSQL PG:"dbname=gis" tl_2014_us_primaryroads.shp
fi

fetch "http://dds.cr.usgs.gov/pub/data/nationalatlas/nate48i0100a.tif_nt00867.tar.gz" "nate48i0100a.tif"
if [ $? -eq 0 ]
then
	tar -xvf nate48i0100a.tif_nt00867.tar.gz
	rm nate48i0100a.tif_nt00867.tar.gz
	gdalwarp -t_srs EPSG:4269 -multi -dstalpha -r bilinear nate48i0100a.tif projected.tiff
fi

fetch "http://dds.cr.usgs.gov/pub/data/nationalatlas/nateaki0100a.tif_nt00868.tar.gz" "nateaki0100a.tif"
if [ $? -eq 0 ]
then
	tar -xvf nateaki0100a.tif_nt00868.tar.gz
	rm nateaki0100a.tif_nt00868.tar.gz
	gdalwarp -t_srs EPSG:4269 -dstnodata "193, 224, 250" -r bilinear nateaki0100a.tif projected-alaska.tif
fi

fetch "http://dds.cr.usgs.gov/pub/data/nationalatlas/natehii0100a.tif_nt00869.tar.gz" "natehii0100a.tif"
if [ $? -eq 0 ]
then
	tar -xvf natehii0100a.tif_nt00869.tar.gz
	rm natehii0100a.tif_nt00869.tar.gz
	gdalwarp -t_srs EPSG:4269 -r bilinear natehii0100a.tif projected-hawaii.tif
fi

for congress in {113..106}
do
	fetch "http://leela.sscnet.ucla.edu/districtShapes/districts${congress}.zip" "districtShapes/districts${congress}.shp"
	if [ $? -eq 0 ]
	then
		unzip districts${congress}.zip
		rm districts${congress}.zip
		ogr2ogr -nlt PROMOTE_TO_MULTI -f PostgreSQL PG:"dbname=gis" districtShapes/districts${congress}.shp
	fi
done

psql -c $'create or replace function parse_district(district text) returns integer as $$\ndeclare\nbegin\nif district::integer = 0 then\nreturn 1;\nend if;\nreturn district::integer;\nend;\n$$ language plpgsql;' gis
