#!/bin/bash

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
	echo "fetch successful, cooling down"
	sleep 30
done
echo "fetching TIGER info for primary roads..."
wget "ftp://ftp2.census.gov/geo/tiger/TIGER2014/PRIMARYROADS/tl_2014_us_primaryroads.zip" || (echo "failed to fetch TIGER"; exit 1)
unzip tl_2014_us_primaryroads.zip
rm tl_2014_us_primaryroads.zip
echo "fetch successful, cooling down"
sleep 30
echo "fetching TIGER info for urban areas..."
wget "ftp://ftp2.census.gov/geo/tiger/TIGER2014/UAC/tl_2014_us_uac10.zip" || (echo "failed to fetch TIGER"; exit 1)
unzip tl_2014_us_uac10.zip
rm tl_2014_us_uac10.zip
echo "fetch successful, cooling down"
sleep 30
cd ..

for congress in {113..106}
do
	echo "fetching districts for congress ${congress}..."
	wget -T 60 "http://leela.sscnet.ucla.edu/districtShapes/districts${congress}.zip" || (echo "failed to fetch districts"; exit 1)
	unzip districts${congress}.zip
	rm districts${congress}.zip
	echo "fetch successful, cooling down"
	sleep 30
done

mkdir districts/
