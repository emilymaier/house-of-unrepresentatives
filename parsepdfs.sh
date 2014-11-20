#!/bin/bash
# Copyright © 2014 Emily Maier
# Extracts text from the PDF result files and calls the Python script to parse
# it.

mkdir temp/
mkdir charts/
for f in pdfs/*
do
	pdftohtml $f temp/$(basename $f)
done
./parsetext.py
rm -rfv temp/
