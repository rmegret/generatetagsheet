#!/bin/bash


if [ $# -ne 2 ]; then
    echo "Usage: dir_png2svg indir outdir"
    echo "  where all indir/*.png file are converted to corresponding outdir/*.svg"
    exit
fi

indir="$1"
outdir="$2"
mkdir -p "$outdir"

tmppbm="tmp-convert_png2svg.pbm"

for i in "$indir"/*; do
  in="$i"
  filename=${in##*/}
  name=${filename%.png}
  out="$outdir"/"$name".svg

  echo "$in"' => '"$out"

  # 300% is enough to get rectangular paths, put 400% to be sure
  convert "$in" -scale 400% "$tmppbm"

  # Add some option to make sure paths are straight
  potrace "$tmppbm" -a 0 -t 0 -u 1 -s -W 1 -H 1 --flat -o - | sed 's/\<g /\<g id="top" /g' > "$out"
done
rm "$tmppbm"