#!/bin/bash


if [ $# -le 1 ]; then
    echo "Usage: dir_inverse_png indir outdir"
    echo "  where all indir/*.png file are converted to corresponding outdir/*.png"
    exit
fi

indir="$1"
outdir="$2"
mkdir -p "$outdir"

for i in "$indir"/*; do
  in="$i"
  filename=${in##*/}
  out="$outdir"/"$filename"

  echo "$in"' => '"$out"

  convert "$in" -negate "$out"

done
