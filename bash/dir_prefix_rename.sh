#!/bin/bash

if [ $# -lt 3 ]; then
    #echo "Called with $# parameters"
    echo "Usage: dir_prefix_rename indir namein nameout"
    echo '  where all indir/namein*.* file are renamed to corresponding indir/nameout*.*'
    exit
fi

indir="$1"
namein="$2"
nameout="$3"



echo "Renaming all files:"
echo "  ${indir}/${namein}XXXX.yyy => ${indir}/${nameout}XXXX.yyy"
read -p "Do you wish to proceed ? [Y/n] " yn
case $yn in
    "" ) echo "Renaming..."; break;;
    [Yy]* ) echo "Renaming..."; break;;
    [Nn]* ) echo "Aborted."; exit;;
    * ) echo "Aborted."; exit;;
esac

for i in "$indir/${namein}"*.*; do
  in="$i"
  filename="${in##*/}"
  suffix="${filename##${namein}}"
  out="$indir"/"${nameout}${suffix}"

  echo "$in"' => '"$out"

  mv "$in" "$out"

done
