#!/bin/bash

mkdir pdfs
cd pdfs
for year in {2012..2000..-2}
do
	echo "fetching PDF for $year results..."
	wget "http://historycms.house.gov/Institution/Election-Statistics/${year}election" || (echo "failed to fetch PDF"; exit 1)
	echo "fetch successful, cooling down"
	sleep 30
done
cd ..
