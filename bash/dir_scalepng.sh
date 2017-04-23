#!/bin/bash


if [ $# -ne 2 ]; then
    echo "Usage: dir_scalepng indir outdir"
    echo "  where all indir/*.png file are converted to corresponding outdir/*.pbm"
    exit
fi

indir="$1"

outdir="$2"
mkdir -p "$outdir"

for i in "$indir"/*.png; do
  in="$i"
  filename=${in##*/}
  name=${filename%.png}
  out="$outdir"/"$name".pbm

  echo "$in"' => '"$out"

  convert "$in" -sample 8x8 -depth 1 "$out"
done
