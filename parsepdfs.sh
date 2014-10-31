#!/bin/bash

mkdir temp/
mkdir json/
year=2000
for f in pdfs/*
do
	pdftotext $f temp/$(basename $f)
	./parsetext.py temp/$(basename $f) $year
	year=$((year + 2))
done
rm -rfv temp/
