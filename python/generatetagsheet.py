# coding: utf-8

# non standard packages required:
# - mako:     templating engine to create the SVG
# - cairosvg: conversion to PDF

import os, sys, getopt, datetime, math, re
from collections import OrderedDict
from mako.template import Template
from mako import exceptions
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup

class Layout(object):
  def __init__(self):
    self.in2mm = 25.4
    
    # Letter paper
    self.page_h = 215.9 # mm
    self.page_w = 279.4
    
    # page_w = 609.6/24*18# 609.6 # mm 24in
    # page_h = 457.2/18*12 # 457.2 ## mm 18in

    # 12"x18" paper: Synaps OM 5-Mil paper
    # http://www.nekoosacoated.com/Products/Offset/Synaps-OM.aspx
    # http://www.rtape.com/product-lines/synaps-synthetic-paper/
    #self.page_h = 457
    #self.page_w = 305
    
    self.nblocksx = 1
    self.nblocksy = 1
    
    self.ntagsx = 10
    self.ntagsy = 10
    
    # Global layout
    self.axismargin_top =  0.75*self.in2mm  # Cross center
    self.axismargin_left = 0.75*self.in2mm
    
    self.tagsmargin_top =  1.00*self.in2mm  # First block top-left
    self.tagsmargin_left = 0.75*self.in2mm
    self.blockmargin     = 0.20*self.in2mm  # Margin between blocks
    
    self.title_fontsize=2.3 # 3 normally
    self.block_fontsize=1.4 # 2 normally
    
    self.custom = None
        
    # Notes:
    # Best printer:
    # - 1200 dpi -> 47.2 dot/mm --> 0.021 mm/dot
    # Tags:
    # - 8 pixels with contour for 2mm tag -> 0.25 mm/pixel
    # at 1200dpi, around 10 dot/pixel
    # at 600dpi, around 5 dot/pixel
    # Epilog laser has 
    # - repeatability of +/- 0.0005" (0.0127 mm)
    # - accuracy of +/- .01" (.254 mm) over the entire table
    # vector line weight for cutting: .001 inch = 0.0254mm
    # Laser kerf = portion of material that the laser burns when it cuts through
    # http://www.cutlasercut.com/resources/tips-and-advice/what-is-laser-kerf
    # Ranges from 0.08mm – 1mm depending on the material type
    
    # Tag parameters
    # self.tagsize = 1.6 # mm
    self.tagdpp1200 = 9   # number of dots per tagpixel at 1200 dpi
    
    self.tagcode_pix = 6          # image code
    self.tagborder_pix = 1       # inner border (included in img)
    self.tagmargin1_pix = 1      # minimal outer border for contrast
    self.tagmargin2_pix = 3      # outer border extra
    self.idheight_pix=1        # Height of extra text for label
    
    self.laserkerf_mm = 0.20
    self.cutweight_inch = 0.0015  # Minimum for Epilog is 0.001
    
    self.margin = 5.0 # pix
    
    self.family = "tag36h10inv"
    self.first_id = 0
    self.maxid = 2319 # for 36h10
    
    #self.tagdir = 'tag36h10inv/svg'
    self.tagdir = '{family}/svg'
    self.tagfiles = 'keyed{id:04d}.svg'
    
    self.output = 'tagsheet_out.svg'
    
    self.modestring = ""

    self.style=1
    self.tagbgcolor="white"
    self.border1color="white"
    self.border2color="white"
    self.textcolor="black"
    self.arrowcolor="black"
    self.crosscolor="black"

    self.fontsize_id=2
    self.fontfamily="Courier New"
    
    #self.show_opening = True
    #self.show_tagpage = True
    #self.show_closing = True
    
    self.show_page_title = True
    self.show_test_patterns = True
    self.show_footer = True
    
    self.show_block_rect = False
    self.show_block_title = True
    self.show_tag_cell = False
    self.show_tag = True
    self.show_tag_img = True
    self.show_tag_cut = False
    self.show_tag_cutkerf = False
    
    self.recompute_lengths()
  
  def apply_hint_mm(self, val_mm):
    val_in = val_mm / self.in2mm
    return round(val_in*300)/300*self.in2mm
  
  def recompute_lengths(self):
    if (self.style==1):
        self.tagbgcolor="white"
        self.border1color="white"
        self.border2color="white"
        self.textcolor="black"
        self.arrowcolor="black"
    elif (self.style==-1):
        self.tagbgcolor="lightyellow"
        self.border1color="lightcyan"
        self.border2color="lightskyblue"
        self.textcolor="black"
        self.arrowcolor="darkred"
    elif (self.style==2):
        self.tagbgcolor="white"
        self.border1color="black"
        self.border2color="black"
        self.textcolor="white"
        self.arrowcolor="white"
    elif (self.style==-2):
        self.tagbgcolor="#DFD"
        self.border1color="darkblue"
        self.border2color="mediumblue"
        self.textcolor="white"
        self.arrowcolor="lightcyan"
    else:
        print('ERROR: Unknown style={}'.format(self.style))

    # When recomputing, hint core alignments parameters to be integer at 300dpi

    self.tagsmargin_top = self.apply_hint_mm(self.tagsmargin_top)
    self.tagsmargin_left = self.apply_hint_mm(self.tagsmargin_left)

    self.last_id  = max(self.maxid, self.first_id+self.nblocksx*self.nblocksy*self.ntagsx*self.ntagsy)
  
    self.tagsize_pix = self.tagcode_pix + 2*self.tagborder_pix
    self.tagsize1_pix = self.tagsize_pix+2*self.tagmargin1_pix
    self.tagwidth2_pix = self.tagsize_pix+2*self.tagmargin2_pix
    self.tagheight2_pix = self.tagsize_pix+2*self.tagmargin2_pix+self.idheight_pix

    self.tagsize = self.tagsize_pix * self.tagdpp1200 / 1200 * self.in2mm
    
    self.pix2mm = self.tagsize/self.tagsize_pix
    self.pt2mm = (279.4/11)/72 # 1pt=1/71in
    
    self.laserkerf_pix=self.laserkerf_mm/self.pix2mm
    self.cutmargin_pix = self.laserkerf_pix/2
    
    self.cutweight_pix = self.cutweight_inch * 25.4 / self.pix2mm

    self.margin = self.apply_hint_mm(self.margin*self.pix2mm)/self.pix2mm
    self.step_x=self.apply_hint_mm((self.tagwidth2_pix+self.margin)*self.pix2mm)
    self.step_y=self.apply_hint_mm((self.tagheight2_pix+self.margin)*self.pix2mm)
    
    self.blockwidth_x=self.step_x*self.ntagsx
    self.blockwidth_y=self.step_y*self.ntagsy
    self.blockstep_x=self.apply_hint_mm(self.step_x*self.ntagsx + self.blockmargin)
    self.blockstep_y=self.apply_hint_mm(self.step_y*self.ntagsy + self.blockmargin)
    
    # Compute the relative path from output sheet to svg images so the links 
    # in the SVG will keep working wherever we create the sheet, 
    # and if we move around the sheet with the input tags
    # This does not allow to move the sheet around without the input tags
    # For this to work, first substitute the family name to obtain 
    # fully formatted strings before applying relpath
    self.abstagdir = self.tagdir.format(family=self.family)
    self.reltagdir = os.path.relpath(self.abstagdir, os.path.dirname(self.output))
    
  
from beaker.cache import CacheManager

class Generator(object):
  def __init__(self,layout):
    self.layout = layout
    self.verbose=1
    
    module_path = os.path.dirname(__file__)
    self.lookup = TemplateLookup(directories=[os.path.join(module_path,'mako_templates')],
                              strict_undefined=True,
                              cache_enabled = False)

    self.template = self.lookup.get_template(uri='template_tagsheet.svg')
    #template=Template(filename='mako_template_tagsheet.txt')
    
  def generate(self,svg=None):
    if (self.layout.custom):
        self.customsvg(svg)
    else:
        self.generatesvg(svg)
    self.topdf(svg)
    
  def getvars(self):
    self.layout.recompute_lengths()
    return vars(self.layout)
    
  def render(self, name, **kargs):
    if (self.verbose>0):
      print("Rendering template '{}'...".format(name))
    
    for field in kargs:
        setattr(self.layout, field, kargs[field])
    V = self.getvars()
      
    if (self.verbose>=3):
      for field in OrderedDict(sorted(V.items())):
          print("  {}={}".format(field,V[field]))
          
    template = self.lookup.get_template(uri=name)
    
    try:
        outstring =  template.render(**V)
    except:
        print(exceptions.text_error_template().render())
        traceback = RichTraceback()
        for (filename, lineno, function, line) in traceback.traceback:
          if (function=='render_body'):
            print("File %s, line %s" % (filename, lineno))
            print('------------------------')
            print(line, "\n")
            print('------------------------')
        print("%s: %s" % (str(traceback.error.__class__.__name__), traceback.error))
        outstring = '<!-- ERROR in name -->'
        
    return outstring
    
  def generatesvg(self,output=None):
    # Generate standard tag sheet (1 type of tag, 1 size)
    if (output is None):
        output=self.layout.output

    if (self.verbose>0):
      print("Creating SVG tag sheet '{}'...".format(output))

    svgtext = self.render('template_tagsheet.svg')
    with open(output, 'w') as out:
       out.write(svgtext)
        
  def customsvg(self,output=None):
    # Generate custom tag sheet with multiple types of tags/sizes
    if (output is None):
        output=self.layout.output

    if (self.verbose>0):
      print("Creating custom SVG tag sheet '{}'...".format(output))
    
    svgtext = self.render('template_opening.svg')
    
    self.layout.nblocksx = 2
    self.layout.nblocksy = 1
    self.layout.ntagsx = 10
    self.layout.ntagsy = 10
    
    self.layout.margin = 8.0 # pix

    self.layout.tagdpp1200 = 10  # Compute lengths for largest page
    self.layout.recompute_lengths()
    x0 = self.layout.in2mm
    y0 = self.layout.in2mm
    shift_x = self.layout.blockstep_x*self.layout.nblocksx+10
    shift_y = self.layout.blockstep_y*self.layout.nblocksy+10
        
    def pos(i,j):
        return {'tagsmargin_left': x0+i*shift_x, 'tagsmargin_top': y0+j*shift_y}
        
    def dpp4mm(tagsize_pix,tagsize_mm):
        return tagsize_mm / tagsize_pix * 1200 / 25.4
        
    def render_page(**kargs):
        print("Rendering page family={family}, tagdpp1200={tagdpp1200}".format(**kargs))
        svgtext = self.render('template_page.svg', **kargs)
        return svgtext

    if (self.layout.custom=='custom_tag36h10'):
      tag = dict(family="tag36h10", tagdir='tag36h10/svg', 
                 tagcode_pix = 6, style=1)
      taginv = dict(family="tag36h10inv", tagdir='tag36h10inv/svg', 
                    tagcode_pix = 6, style=2)

      svgtext += render_page(tagdpp1200=11, **taginv, **pos(0,0))
      svgtext += render_page(tagdpp1200=11, **tag,    **pos(1,0))
      svgtext += render_page(tagdpp1200=10, **taginv, **pos(0,1))
      svgtext += render_page(tagdpp1200=10, **tag,    **pos(1,1))
      svgtext += render_page(tagdpp1200=9,  **taginv, **pos(0,2))
      svgtext += render_page(tagdpp1200=9,  **tag,    **pos(1,2))
    elif (self.layout.custom=='custom_tag25h6'):
      tag = dict(family="tag25h6", tagdir='tag25h6/svg', 
                 tagcode_pix = 5, style=1)
      taginv = dict(family="tag25h6inv", tagdir='tag25h6inv/svg',
                    tagcode_pix = 5, style=2)

      svgtext += render_page(tagdpp1200=11, **taginv, **pos(0,0))
      svgtext += render_page(tagdpp1200=11, **tag,    **pos(1,0))
      svgtext += render_page(tagdpp1200=10, **taginv, **pos(0,1))
      svgtext += render_page(tagdpp1200=10, **tag,    **pos(1,1))
      svgtext += render_page(tagdpp1200=9,  **taginv, **pos(0,2))
      svgtext += render_page(tagdpp1200=9,  **tag,    **pos(1,2))
    elif (self.layout.custom=='custom_tag25h5'):
      tag = dict(family="tag25h5", tagdir='tag25h5/svg',
                 tagcode_pix = 5, style=1)
      taginv = dict(family="tag25h5inv", tagdir='tag25h5inv/svg',     
                    tagcode_pix = 5, style=2)

      svgtext += render_page(tagdpp1200=11, **taginv, **pos(0,0))
      svgtext += render_page(tagdpp1200=11, **tag,    **pos(1,0))
      svgtext += render_page(tagdpp1200=10, **taginv, **pos(0,1))
      svgtext += render_page(tagdpp1200=10, **tag,    **pos(1,1))
      svgtext += render_page(tagdpp1200=9,  **taginv, **pos(0,2))
      svgtext += render_page(tagdpp1200=9,  **tag,    **pos(1,2))
    elif (self.layout.custom=='custom_test'):
      tag = dict(family="tag25h5", tagdir='tag25h5/svg',
                 tagcode_pix = 5, style=1)
      taginv = dict(family="tag25h5inv", tagdir='tag25h5inv/svg',     
                    tagcode_pix = 5, style=2)

      svgtext += render_page(tagdpp1200=11, **taginv, **pos(0,0))
    else:
      print('ERROR: unknown custom layout, custom={}'.format(self.layout.custom))
      return
        
    self.layout.show_footer=True
    svgtext += self.render('template_closing.svg')
    
    with open(output, 'w') as out:
       out.write(svgtext)

  def topdf(self, output):
    if (output is None):
        output=self.layout.output

    # Command line:
    print("Converting {} to PDF...".format(output))
    os.system('svg2pdf_inkscape.sh "{}"'.format(output))
    
    # # Alternative: cairosvg produces less efficient PDF than inkscape
    #
    # print("Converting to PDF...")
    # 
    # import cairosvg
    # 
    # cairosvg.svg2pdf(
    #     file_obj=open("output_tagsheet.svg", "rb"),
    #     write_to="output_tagsheet.pdf")

  def rasterize(self, output): # FIXME
    if (output is None):
        output=self.layout.output
    # Rasterize at 1200 dpi to check quality
    print("Convert to TIFF 1200dpi:")
    print("   convert -density 1200 -background white -alpha remove -compress lzw output_tagsheet.svg_output.pdf output_tagsheet_1200dpi.tiff")
    os.system("convert -density 1200 -background white -alpha remove -compress lzw output_tagsheet.svg_output.pdf output_tagsheet_1200dpi.tiff")



if __name__ == "__main__":

    
    layout = Layout()
    generator = Generator(layout)


    import argparse

    parser = argparse.ArgumentParser(description='Generate SVG tag sheet given a directory <tagdir> of tag images', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dpp', '-d', type=int,
                        dest='tagdpp1200', default=layout.tagdpp1200,
                        help='number of printer dots per pixel of the tag at 1200 dpi.\nFor 6 pixels code, dpp=8 -> 1.37mm, dpp=9 -> 1.54mm tag, dpp=10 -> 1.71mm tag')
    parser.add_argument('-o', '--output', metavar='<tagsheet.svg>', 
                        dest='output', default=layout.output,
                        help='output file (default: %(default)s)')
    parser.add_argument('-s', '--style', metavar='<style>', type=int,
                        dest='style', default=layout.style,
                        help='color style: 1=tag, 2=invtag, -i=debug style i (default: %(default)s)')
    parser.add_argument('-f', '--family', metavar='<family>', 
                        dest='family', default=layout.family,
                        help='tag family name (default: %(default)s)')
    parser.add_argument('-td', '--tagdir', metavar='<tagdir>', 
                        dest='tagdir', default=layout.tagdir,
                        help='directory containing tag image files (default: %(default)s)')
    parser.add_argument('-tf', '--tagfiles', metavar='<tagfiles>', 
                        dest='tagfiles', default=layout.tagfiles,
                        help='pattern of tag image files, python format style (default: %(default)s)')
    parser.add_argument('-p', '--tagcode_pix', metavar='<tagcode_pix>', 
                      dest='tagcode_pix', default=layout.tagcode_pix, type=int,
                      help='width of the code in pixels, without border (default: %(default)s)')
    parser.add_argument('-u', '--first_id', metavar='<first_id>', type=int,
                        dest='first_id', default=layout.first_id,
                        help='first id, inclusive (default: %(default)s)')
    parser.add_argument('-v', '--maxid', metavar='<max_id>', type=int,
                        dest='maxid', default=layout.maxid,
                        help='last id, inclusive (default: %(default)s)')
    parser.add_argument('-m', '--mode', metavar='<mode>', type=int,
                        dest='mode', default=0,
                        help='sheet mode\n0=tags, 1=cuts, 2=cuts-preview (default: %(default)s)')
    parser.add_argument('-pw', '--page_w', metavar='<page_w>', type=float,
                        dest='page_w', default=layout.page_w,
                        help='page width in mm (default: %(default)s)')
    parser.add_argument('-ph', '--page_h', metavar='<page_h>', type=float,
                        dest='page_w', default=layout.page_h,
                        help='page width in mm (default: %(default)s)')
    parser.add_argument('-bx', '--nblocksx', metavar='<nblocksx>', type=int,
                        dest='nblocksx', default=layout.nblocksx,
                        help='number of tags in a block row (default: %(default)s)')
    parser.add_argument('-by', '--nblocksy', metavar='<nblocksy>', type=int,
                        dest='nblocksy', default=layout.nblocksy,
                        help='number of tags in a block column (default: %(default)s)')
    parser.add_argument('-nx', '--ntagsx', metavar='<ntagsx>', type=int,
                        dest='ntagsx', default=layout.ntagsx,
                        help='number of tags in a block row (default: %(default)s)')
    parser.add_argument('-ny', '--ntagsy', metavar='<ntagsy>', type=int,
                        dest='ntagsy', default=layout.ntagsy,
                        help='number of tags in a block column (default: %(default)s)')
    parser.add_argument('-r', '--rasterize',  
                        dest='rasterize', action='store_true',
                        help='rasterize output PDF')
    parser.add_argument('-c', '--custom',  metavar='<layout name>',
                        dest='custom', default=layout.custom,
                        choices='custom_tag25h5,custom_tag25h6,custom_tag36h10,,custom_test'.split(','),
                        help='Use custom layout (hardcoded %(choices)s)')
    args = parser.parse_args()    
    
    fields='tagdpp1200,output,style,tagdir,tagfiles,family,first_id,maxid,nblocksx,nblocksy,ntagsx,ntagsy,rasterize,custom'.split(',')
    for field in fields:
        #print("  Configuring '{}'".format(field))
        #print("  Configuring {}={}".format(field,getattr(args,field)))
        setattr(layout, field,getattr(args,field))
    
        
    def setMode(layout,mode):
        if (mode==0): # Tags
          layout.show_tag = True
          layout.show_tag_cut = False
          layout.show_tag_cutkerf = False
          layout.show_block_rect = False
          layout.modestring = "TAGS"
        elif (mode==1): # Cut
          layout.show_tag = False
          layout.show_tag_cut = True
          layout.show_tag_cutkerf = False
          layout.show_block_rect = False
          layout.modestring = "CUTS"
        elif (mode==2): # Preview: Both tags and cuts
          layout.show_tag = True
          layout.show_tag_cut = True
          layout.show_tag_cutkerf = True
          layout.show_block_rect = True
          layout.modestring = "PREVIEW"
        else:
          print('ERROR: Unknown mode {}'.format(mode))


    if (args.mode>=0):
        setMode(layout,args.mode)
        generator.generate()
        if (args.rasterize):
            generator.rasterize()
    else:
        basename=re.sub('\.svg$', '', args.output)
        setMode(layout,0)
        generator.generate(svg=basename+'.TAGS.svg')
        setMode(layout,1)
        generator.generate(svg=basename+'.CUTS{}.svg'.format(int(layout.laserkerf_mm*1000))) 
        setMode(layout,2)
        generator.generate(svg=basename+'.PREVIEW{}.svg'.format(int(layout.laserkerf_mm*1000)))    
    

