#!/bin/bash

in="$1"
out="${in%.svg}".pdf

echo "svg2pdf_inkscape.sh: Converting '$in' into '$out'"

/opt/local/bin/inkscape --file="$1" --without-gui --export-area-page --export-dpi=2400 --export-pdf="$out"