#!/bin/bash
# Copyright © 2014 Emily Maier
# Fetches the PDFs from the House of Representatives clerk's website that the
# election results will eventually be extracted from.

cd /var/lib/house/input

for year in {2012..1998..-2}
do
	echo "fetching PDF for $year results..."
	wget -T 60 "http://historycms.house.gov/Institution/Election-Statistics/${year}election" || { echo "failed to fetch PDF"; exit 1; }
	echo "fetch successful, cooling down"
	sleep 30
done
