#!/bin/bash

mkdir temp/
for f in pdfs/*
do
	pdftotext $f temp/$(basename $f)
	./parsetext.py temp/$(basename $f)
done
rm -rfv temp/
