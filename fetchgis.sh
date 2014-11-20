#!/bin/bash
# Copyright © 2014 Emily Maier
# Fetches and processes the GIS data needed to build the maps. Vector data is
# inserted into the PostGIS database, while raster data is converted to the
# EPSG:4269 projection.

mkdir TIGER
cd TIGER
fips_states=(01 02 04 05 06 08 09 10 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56)
for fips_state in ${fips_states[@]}
do
	echo "fetching TIGER info for $fips_state places..."
	filename="tl_2014_${fips_state}_place.zip"
	wget "ftp://ftp2.census.gov/geo/tiger/TIGER2014/PLACE/$filename" || (echo "failed to fetch TIGER"; exit 1)
	unzip $filename
	rm $filename
	PGCLIENTENCODING="latin1" ogr2ogr -nlt PROMOTE_TO_MULTI -nln places -append -f PostgreSQL PG:"dbname=gis" tl_2014_${fips_state}_place.shp
	echo "fetch successful, cooling down"
	sleep 30
done
echo "fetching TIGER info for states..."
wget "ftp://ftp2.census.gov/geo/tiger/TIGER2014/STATE/tl_2014_us_state.zip" || (echo "failed to fetch TIGER"; exit 1)
unzip tl_2014_us_state.zip
rm tl_2014_us_state.zip
ogr2ogr -nlt PROMOTE_TO_MULTI -nln states -f PostgreSQL PG:"dbname=gis" tl_2014_us_state.shp
psql -c "create materialized view simplified as select ST_Simplify(wkb_geometry, 0.05) as wkb_geometry, name from states" gis
echo "fetch successful, cooling down"
sleep 30
echo "fetching TIGER info for primary roads..."
wget "ftp://ftp2.census.gov/geo/tiger/TIGER2014/PRIMARYROADS/tl_2014_us_primaryroads.zip" || (echo "failed to fetch TIGER"; exit 1)
unzip tl_2014_us_primaryroads.zip
rm tl_2014_us_primaryroads.zip
PGCLIENTENCODING="latin1" ogr2ogr -nlt PROMOTE_TO_MULTI -nln roads -f PostgreSQL PG:"dbname=gis" tl_2014_us_primaryroads.shp
echo "fetch successful, cooling down"
sleep 30
cd ..

mkdir USGS/
cd USGS/
echo "fetching USGS natural earth raster..."
wget "http://dds.cr.usgs.gov/pub/data/nationalatlas/nate48i0100a.tif_nt00867.tar.gz"
tar -xvf nate48i0100a.tif_nt00867.tar.gz
rm nate48i0100a.tif_nt00867.tar.gz
gdalwarp -t_srs EPSG:4269 -multi -dstalpha nate48i0100a.tif projected.tiff
echo "fetch successful, cooling down"
sleep 30
echo "fetching USGS natural earth alaska raster..."
wget "http://dds.cr.usgs.gov/pub/data/nationalatlas/nateaki0100a.tif_nt00868.tar.gz"
tar -xvf nateaki0100a.tif_nt00868.tar.gz
rm nateaki0100a.tif_nt00868.tar.gz
gdalwarp -t_srs EPSG:4269 -dstnodata "193, 224, 250" nateaki0100a.tif projected-alaska.tif
echo "fetch successful, cooling down"
sleep 30
echo "fetching USGS natural earth hawaii raster..."
wget "http://dds.cr.usgs.gov/pub/data/nationalatlas/natehii0100a.tif_nt00869.tar.gz"
tar -xvf natehii0100a.tif_nt00869.tar.gz
rm natehii0100a.tif_nt00869.tar.gz
gdalwarp -t_srs EPSG:4269 natehii0100a.tif projected-hawaii.tif
echo "fetch successful, cooling down"
sleep 30
cd ..

for congress in {113..106}
do
	echo "fetching districts for congress ${congress}..."
	wget -T 60 "http://leela.sscnet.ucla.edu/districtShapes/districts${congress}.zip" || (echo "failed to fetch districts"; exit 1)
	unzip districts${congress}.zip
	rm districts${congress}.zip
	ogr2ogr -nlt PROMOTE_TO_MULTI -f PostgreSQL PG:"dbname=gis" districtShapes/districts${congress}.shp
	echo "fetch successful, cooling down"
	sleep 30
done
psql -c $'create function parse_district(district text) returns integer as $$\ndeclare\nbegin\nif district::integer = 0 then\nreturn 1;\nend if;\nreturn district::integer;\nend;\n$$ language plpgsql;' gis

mkdir maps/
