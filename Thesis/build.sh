#!/bin/bash

cd ./Thesis

pdflatex thesis
bibtex thesis
pdflatex thesis
pdflatex thesis

rm chapter/*.aux
rm ./*.aux
rm ./*.bbl
rm ./*.blg
rm ./*.log
rm ./*.thm
rm ./*.toc
