#!/bin/bash

mkdir temp/
mkdir charts/
for f in pdfs/*
do
	pdftohtml $f temp/$(basename $f)
done
./parsetext.py
rm -rfv temp/
