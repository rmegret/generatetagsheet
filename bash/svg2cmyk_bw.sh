#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

in="$1"
outps="${in%.svg}"_temporary.ps
out="${in%.svg}"_BW.pdf

echo "svg2cmyk_bw.sh: Converting '$in' into '$out'"

echo "svg2cmyk_bw.sh:   Convert to '$outps'"

/opt/local/bin/inkscape --file="$1" --without-gui --export-area-page --export-dpi=2400 --export-ps="$outps"

echo "svg2cmyk_bw.sh:   Convert to '$out' with CMYK colors"

gs -sDEVICE=pdfwrite -dNOPAUSE -dBATCH -dSAFER -sOutputFile="$out" "$DIR"/Hack-fastCMYK-bw.ps "$outps"

echo "To check separation, type:"
echo "gs -dNOPAUSE -dBATCH -dSAFER -sDEVICE=tiffsep -dFirstPage=1 -dLastPage=1 -sOutputFile=p%02d.tif '$out'"

rm "$outps"
