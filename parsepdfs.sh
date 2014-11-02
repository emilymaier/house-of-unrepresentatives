#!/bin/bash

mkdir temp/
for f in pdfs/*
do
	pdftotext $f temp/$(basename $f)
done
./parsetext.py
rm -rfv temp/
