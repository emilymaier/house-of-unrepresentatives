#!/bin/bash
# Copyright © 2014 Emily Maier
# Extracts text from the PDF result files and calls the Python script to parse
# it.

source_tree=$(pwd)
cd /var/lib/house/input
mkdir temp/
for f in *election
do
	pdftohtml $f temp/$(basename $f)
done
${source_tree}/parsetext.py
rm -rfv /var/lib/house/input/temp/
