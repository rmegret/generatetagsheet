#!/bin/bash

in="$1"
out="${1%.svg}".ps

#/usr/bin/sed 's/optimizeSpeed/optimizeQuality/g' "$1" > tmp_svg.svg
#/usr/bin/sed 's/width="100%" height="100%"/width="8.5in" height="11in"/g' tmp_svg.svg > tmp_svg2.svg
#/usr/bin/sed 's/1pt/0.8pt/g' tmp_svg2.svg > "$1"_output.svg
/opt/local/bin/inkscape --file="$1" --without-gui --export-area-page --export-dpi=2400 --export-ps="$out"
