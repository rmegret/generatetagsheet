# generatetagsheet
Tools to generate sheets of tags for insect tracking

## HOWTO create tag sheets

0. Add utils directory to PATH:

```
    export PATH=/Users/megret/Documents/Research/BeeTracking/Soft/createtagsheet/bash:$PATH
```

1. Create directory of tag images

```
    tags/tag36h10inv/pbm/keyed????.pbm
```
  or
```
    tags/tag36h10inv/png/keyed????.png
```

  where ???? represents the tag id

  If the tags contain the external inverted border, crop it using dir_crop_png.sh

```
    dir_crop_png.sh  pngraw/ png/ 1
```

2. Convert tag images into SVG

```
    cd tags/tag36h10inv
    dir_pbm2svg.sh pbm svg
```
  or
```
    dir_png2svg.sh png svg
```


3. Create main SVG sheet

```
  cd tags
```
  # make sure SVG files are available as `svg/keyed????.svg`

  e.g.:
```
  python ../python/generatetagsheet.py --dpp 10 -o tag25h5_sheet.svg -bx=1 -by=1 -td tag25h5/svg -tf tag25_05_{id:05d}.svg
```

  for help:
```
  python ../python/generatetagsheet.py -h
```
  # this creates the sheet as SVG using mako template engine
  # then convert it to PDF using svg2pdf_inkscape.sh

      Tag structure and parameters:
        +-----------------+
        |    2            |
        |    I   id       |   [I = idtext is idheight_pix high]
        |   X2XXXXXXXXX   |   
        |   X.........X   |   
        |   X.       .X   |   
        |   X.       .X   |                          values for 36h10
        |2222.       .2222|    
        |   X.       .X   |   tagsize_pix=tagcode_pix+2*tagborder_pix = 8                      
        |   X.       .X   |   [  = code img,         tagcode_pix=6]
        |   X.........X   |   [. = tag inner border, tagborder_pix=1]
        |   X2XXXXXXXXX   |   [X = border1,          border1_pix=1]
        |    2            |   [2 = border2,          border2_pix=3]
        +-----------------+

## MISC

      at 2400dpi:
      2mm = 0.0787402in = 188dots
      for 9x9 tag, 1 tag pixel = 21 dots  
      (spatial resolution is 5% pixel when rasterizing at printer)

      at 72pt/pixel, 21dots=3.4pt


