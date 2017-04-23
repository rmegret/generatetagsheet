#!/bin/bash


if [ $# -le 2 ]; then
    echo "Usage: dir_crop_png indir outdir margin"
    echo "  where all indir/*.png file are converted to corresponding outdir/*.png"
    echo "  to remove 1 pixel margin, 'dir_crop_png indir outdir 1'"
    exit
fi

indir="$1"
outdir="$2"
if [ $# -ge 3 ]; then
    margin="$3"
else
    margin=1
fi
mkdir -p "$outdir"

for i in "$indir"/*; do
  in="$i"
  filename=${in##*/}
  out="$outdir"/"$filename"

  echo "$in"' => '"$out"

  convert "$in" -shave "$margin"x"$margin" "$out"

done
