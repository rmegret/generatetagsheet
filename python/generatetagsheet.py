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
import argparse
from datetime import datetime

class Layout(object):
  def __init__(self):
    self.cmdline = ""
    self.in2mm = 25.4
    self.pt_dpi = self.in2mm/1200
    
    self.family = "tag25h5inv"
    self.tagcode_pix = 5          # image code
    
    self.first_id = 0
    self.maxid = 3008 # for 25h5
    
    self.tagdir = '{family}/svg'
    self.tagfiles = 'keyed{id:04d}.svg'
    
    self.output = None
    self.output_basename = '{family}_dpp{tagdpp1200}_{page_size}_{first_id}-{last_id}'
    
    # Letter paper
    self.page_size = 'letter'
    self.page_w = 215.9 # mm
    self.page_h = 279.4
    self.paper_sizes={
        'letter': [215.9, 279.4],
        '8.5x11': [215.9, 279.4],
        '11x8.5': [279.4, 215.9],
        '19x13':  [482.6, 330.2],
        '13x19':  [330.2, 482.6],
        '12x18':  [304.8, 457.2]
        }
    # 13"x19" paper: Synaps OM 5-Mil paper
    # (corresponds to 12"x18" paper plus margin)
    # http://www.nekoosacoated.com/Products/Offset/Synaps-OM.aspx
    # http://www.rtape.com/product-lines/synaps-synthetic-paper/

    self.nblocksx = 1
    self.nblocksy = 1
    
    self.ntagsx = 10
    self.ntagsy = 10
    
    # Global layout
    self.axismargin_left = 0.75*self.in2mm
    self.axismargin_top =  0.75*self.in2mm  # Cross center
    
    self.sheet_x0 = 1*self.in2mm  # First block top-left
    self.sheet_y0 = 1*self.in2mm  
    self.page_left = self.sheet_x0 # Default positionning
    self.page_top  = self.sheet_y0 

    self.pagemargin      = 0.15*self.in2mm  # Margin between pages    
    self.blockmargin     = 0.15*self.in2mm  # Margin between blocks
    self.tagmarginx      = 5.0 # pix
    self.tagmarginy      = 5.0 # pix
    
    self.test_patterns_x = 25.4
    self.test_patterns_y = 25.4*6
    
    self.title_fontsize=2.3 # 3mm normally
    self.block_fontsize=1.4 # 2mm normally
    self.fontfamily="Courier"
    self.fontsize_id=1.5      # pix
    self.fontsize_idext=5   # pix
    self.fontsize_scalex=2.0   # factor
    self.fontweight_id="700" #"900"
    self.letterspacing=""
    self.tagid_margin=0.2
    
    self.custom = None
    self.removesvg = False
        
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
    self.tagdpp1200 = 10   # number of dots per tagpixel at 1200 dpi
    
    self.use_local_dpi = False
    self.local_dpi = 1200  # Hack to allow tags to use 1219.2 dpi hinting
    self.ptshift = 0
    
    self.use_color = False
    
    self.tagborder_pix = 1       # inner border (included in img)
    self.tagmargin1_pix = 1      # minimal outer border for contrast
    self.tagmargin2_pix = 3      # outer border extra
    self.bicol2_margin_pix = 2   # Bicolor outer border
    self.idheight_pix=1        # Height of extra text for label
    self.tagmargin2top_pix = 3        # Height of extra text for label on top
    self.show_bitcode = False
    
    self.laserkerf_mm = 0.20
    self.laserkerf_mm_view = 0 # 0 means copy from laserkerf_mm
    self.cutweight_inch = 0.0015  # Minimum for Epilog is 0.001
    self.cut_opening_factor = 0
    
    self.modestring = ""

    self.style='auto'
    self.tagbgcolor="white"
    self.border1color="white"
    self.border2color="white"
    self.border1stroke="white"
    self.border1strokewidth=0.1
    self.textcolor="black"
    self.textbgcolor="none"
    self.textbg_margin=0.3
    self.arrowcolor="black"
    self.crosscolor="black"
    self.tagid_bgcolor="#C000C0"
    self.tagcornercolor1="#00C000"
    self.tagcornercolor2="#C0C000"
    self.show_colored_corners=False
    self.show_arrows=False
    self.show_bicolor=False
    self.show_taggrid=False
    self.taggrid_color="#FFF"
    self.taggrid_strokewidth=0.2

    self.mode = 'tags'
    self.show_crosses = True
    self.show_corner_crosses = False
    self.show_test_patterns = True
    self.show_kerftest = False
    self.show_guidelines = False
    self.guidelines_color = "magenta"
    self.kerftest_left = 90
    self.kerftest_top = 220
    
    self.show_test_tags = False
    self.test_tags_x = 80
    self.test_tags_y = 240
    
    self.show_page_title = True
    self.show_page_rect = False
    
    self.show_block_rect = False
    self.show_block_title = True
    
    self.show_tag_cell = False
    self.show_tag = True
    self.show_tag_img = True
    self.show_tag_cut = False
    self.show_tag_cutkerf = False
    self.kerf_opacity = 1
    
    self.show_footer = False
    
    self.show_cmdline = False
    self.show_cmdline_date = False
    self.cmdline_left = 80
    self.cmdline_top = 205
    self.cmdline_fontsize = 7.0
    self.cmdline_cols = 80
    self.date = ""
    
    self.recompute_lengths()
  
  def apply_hint_mm(self, val_mm):
    val_in = val_mm / self.in2mm
    return round(val_in*300)/300*self.in2mm
  
  def recompute_lengths(self):
    self.recomputeflags()
    self.recomputepagesize()
  
    if (self.style=='auto'):
        if (self.family.endswith('inv')):
            self.style1='invtag'
        else:
            self.style1='tag'
    elif (self.style=='autodebug'):
        if (self.family.endswith('inv')):
            self.style1='invtagdebug'
        else:
            self.style1='tagdebug'
    else:
        self.style1=self.style
        
    if (self.style1=='tag'):
        self.tagbgcolor="white"
        self.border1color="white"
        self.border2color="white"
        self.border1stroke="white"
        #self.textcolor="black"
        self.arrowcolor="black"
    elif (self.style1=='tagdebug'):
        self.tagbgcolor="lightyellow"
        self.border1color="lightcyan"
        self.border2color="lightskyblue"
        self.border1stroke="white"
        #self.textcolor="black"
        self.arrowcolor="darkred"
    elif (self.style1=='invtag'):
        self.tagbgcolor="white"
        self.border1color="black"
        self.border2color="black"
        self.border1stroke="white"
        #self.textcolor="white"
        self.arrowcolor="white"
    elif (self.style1=='invtagdebug'):
        self.tagbgcolor="#DFD"
        self.border1color="darkblue"
        self.border2color="mediumblue"
        self.border1stroke="white"
        #self.textcolor="white"
        self.arrowcolor="lightcyan"
    else:
        print('ERROR: Unknown style={}'.format(self.style1))
    if (self.show_bicolor):
        self.border2color="none"

    # When recomputing, hint core alignments parameters to be integer at 300dpi
    
    if (self.use_local_dpi):
        self.pt_dpi = self.in2mm/self.local_dpi
    else:
        self.pt_dpi = self.in2mm/1200

    self.sheet_y0 = self.apply_hint_mm(self.sheet_y0)
    self.sheet_x0 = self.apply_hint_mm(self.sheet_x0)

    self.last_id  = min(self.maxid, self.first_id+self.nblocksx*self.nblocksy*self.ntagsx*self.ntagsy)
  
    self.tagmargin2top_pix = self.tagmargin2_pix + self.idheight_pix
    self.tagsize_pix = self.tagcode_pix + 2*self.tagborder_pix
    self.tagsize1_pix = self.tagsize_pix+2*self.tagmargin1_pix
    self.tagwidth2_pix = self.tagsize_pix+2*self.tagmargin2_pix
    self.tagheight2_pix = self.tagsize_pix+self.tagmargin2_pix+self.tagmargin2top_pix

    self.tagsize = self.tagsize_pix * self.tagdpp1200 / 1200 * self.in2mm
    
    self.pix2mm = self.tagsize/self.tagsize_pix
    self.pt2mm = (279.4/11)/72 # 1pt=1/71in
    
    self.laserkerf_um=round(self.laserkerf_mm*1000)
    self.laserkerf_pix=self.laserkerf_mm/self.pix2mm
    #if (self.laserkerf_mm_view==0):
    #    self.laserkerf_pix_view=self.laserkerf_pix
    #else:
    self.laserkerf_pix_view=self.laserkerf_mm_view/self.pix2mm
    
    self.cutmargin_pix = self.laserkerf_pix/2
    self.cut_opening_pix = self.cut_opening_factor*self.laserkerf_pix
    
    self.cutweight_pix = self.cutweight_inch * 25.4 / self.pix2mm

    self.tagmarginx = self.apply_hint_mm(self.tagmarginx*self.pix2mm)/self.pix2mm
    self.tagmarginy = self.apply_hint_mm(self.tagmarginy*self.pix2mm)/self.pix2mm
    self.step_x=self.apply_hint_mm((self.tagwidth2_pix+self.tagmarginx)*self.pix2mm)
    self.step_y=self.apply_hint_mm((self.tagheight2_pix+self.tagmarginy)*self.pix2mm)
    
    self.blocksize_x=self.step_x*self.ntagsx
    self.blocksize_y=self.step_y*self.ntagsy
    self.blockstep_x=self.apply_hint_mm(self.blocksize_x + self.blockmargin)
    self.blockstep_y=self.apply_hint_mm(self.blocksize_y + self.blockmargin)
    
    self.page_left = self.apply_hint_mm(self.page_left)
    self.page_top = self.apply_hint_mm(self.page_top)
    self.pagesize_x = self.blockstep_x*(self.nblocksx-1)+self.blocksize_x
    self.pagesize_y = self.blockstep_y*(self.nblocksy-1)+self.blocksize_y
    self.pagestep_x = self.apply_hint_mm(self.pagesize_x+self.pagemargin)
    self.pagestep_y = self.apply_hint_mm(self.pagesize_y+self.pagemargin)
    
    overshootx = (self.page_left+self.blockstep_x*self.nblocksx) - (self.page_w-self.axismargin_left)
    if (overshootx>0):
        print('WARNING too many block X axis: overshoot by {}mm'.format(overshootx))
        print('Suggested nblockx < {}'.format((self.page_w-self.axismargin_left-self.page_left)/self.blockstep_x))
    overshooty = (self.page_top+self.blockstep_y*self.nblocksy) - (self.page_h-self.axismargin_top)
    if (overshooty>0):
        print('WARNING too many block Y axis: overshoot by {}mm'.format(overshooty))
        print('Suggested nblockx < {}'.format((self.page_h-self.axismargin_top-self.page_top)/self.blockstep_y))
    
  def recomputeflags(self):
    if (self.mode=='tags'): # Tags
      self.show_tag = True
      self.show_tag_img = True
      self.show_tag_cut = False
      self.show_tag_cutkerf = False
      #self.show_block_rect = False # Do not override explicit flag
      self.show_block_title = True
      self.show_page_title = True
      self.show_test_patterns = True
      self.show_crosses = True
      self.modestring = "TAGS"
    elif (mode=='cuts'): # Cut
      self.show_tag = False
      self.show_tag_img = False
      self.show_tag_cut = True
      self.show_tag_cutkerf = False
      #self.show_block_rect = False # Do not override explicit flag
      self.show_block_title = False
      self.show_page_title = True
      self.show_test_patterns = False
      self.show_crosses = False
      self.modestring = "CUTS"
    elif (mode=='view'): # Preview: Both tags and cuts
      self.show_tag = True
      self.show_tag_img = True
      self.show_tag_cut = True
      self.show_tag_cutkerf = (self.laserkerf_pix_view>0.0)
      self.show_block_rect = True
      self.show_block_title = True
      self.show_page_title = True
      self.show_test_patterns = True
      self.show_crosses = True
      self.modestring = "PREVIEW"
    else:
      print('ERROR: Unknown mode {}'.format(mode))
      
    
  
  def recomputepaths(self):
    # Compute the relative path from output sheet to svg images so the links 
    # in the SVG will keep working wherever we create the sheet, 
    # and if we move around the sheet with the input tags
    # This does not allow to move the sheet around without the input tags
    # For this to work, first substitute the family name to obtain 
    # fully formatted strings before applying relpath
    self.abstagdir = self.tagdir.format(family=self.family)
    self.reltagdir = os.path.relpath(self.abstagdir, os.path.dirname(self.output))
    
  def recomputepagesize(self):    
    if (self.page_size=='custom'):
        pass # rely on page_w and page_h to be defined
    else:
        size = self.paper_sizes[self.page_size]
        self.page_w = size[0]
        self.page_h = size[1]
    
#   class PageSizeAction(argparse.Action):
#     def __init__(self, option_strings=None, dest=None, nargs=None, **kwargs):
#         if nargs is not None:
#             raise ValueError("nargs not allowed")
#         super(PageSizeAction, self).__init__(option_strings, dest, **kwargs)
#         self.sizes={
#             '8.5x11': [215.9, 279.4],
#             '11x8.5': [279.4, 215.9],
#             '19x13':  [482.6, 330.2],
#             '13x19':  [330.2, 482.6]
#             }
#     def getSize(self,name):
#         return self.sizes[name]
#     def __call__(self, parser, namespace, values, option_string=None):
#         #print('--page_size: %r %r %r' % (namespace, values, option_string))
#         
#         size = self.getSize(values)
#                 
#         setattr(namespace, 'page_w', size[0])
#         setattr(namespace, 'page_h', size[1])
#         
#         print('Option --page_size {}: page_w={}, page_h={}'.format(values, size[0], size[1]))
  
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
    
  def generate(self,output=None):
    if (output is None):
        output=self.layout.output
        
    if (self.layout.custom):
        self.customsvg(output)
    else:
        self.generatesvg(output)
        
    if (self.layout.to_pdf):
        self.topdf(output)
    if (self.layout.to_cmyk):
        self.cmyk(output)
    if (self.layout.to_cmyk_bw):
        self.cmyk_bw(output)
    
    if (layout.removesvg):
        os.remove(output)
    
  def getvars(self):
    self.layout.recompute_lengths()
    return vars(self.layout)
    
  def render(self, name, **kargs):
    if (self.verbose>0):
      print("Rendering template '{}'...".format(name))
    
    layout.recomputepaths()
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
    
    self.layout.tagmarginx = 5.0 # pix
    self.layout.tagmarginy = 5.0 # pix

    class GridLayout(object):
      def __init__(self, layout, dpp=10):
        self.layout = layout
        self.setdpp(dpp)

      def setdpp(self,dpp):
        self.dpp = dpp
        self.layout.tagdpp1200 = dpp  # Compute lengths for largest page
        self.layout.recompute_lengths()
        
      def pos(self,i,j):
          return {
              'page_left': self.layout.sheet_x0+i*self.layout.pagestep_x, 
              'page_top': self.layout.sheet_y0+j*self.layout.pagestep_y
              }
    gl = GridLayout(self.layout)
        
    def dpp4mm(tagsize_pix,tagsize_mm):
        return tagsize_mm / tagsize_pix * 1200 / 25.4
        
    def render_page(**kargs):
        print("Rendering page family={family}, tagdpp1200={tagdpp1200} at (left,top)=({page_left:.1f},{page_top:.1f})".format(**kargs))
        svgtext = self.render('template_page.svg', **kargs)
        return svgtext

    if (self.layout.custom=='custom_tag36h10'):
      tag = dict(family="tag36h10", tagdir='tag36h10/svg', 
                 tagcode_pix = 6, style=1)
      taginv = dict(family="tag36h10inv", tagdir='tag36h10inv/svg', 
                    tagcode_pix = 6, style=2)
                    
      gl.setdpp(10)

      svgtext += render_page(tagdpp1200=10, **taginv, **gl.pos(0,0))
      svgtext += render_page(tagdpp1200=10, **tag,    **gl.pos(1,0))
      svgtext += render_page(tagdpp1200=9, **taginv, **gl.pos(0,1))
      svgtext += render_page(tagdpp1200=9, **tag,    **gl.pos(1,1))
      svgtext += render_page(tagdpp1200=8,  **taginv, **gl.pos(0,2))
      svgtext += render_page(tagdpp1200=8,  **tag,    **gl.pos(1,2))
    elif (self.layout.custom=='custom_tag25h6'):
      tag = dict(family="tag25h6", tagdir='tag25h6/svg', 
                 tagcode_pix = 5, style=1)
      taginv = dict(family="tag25h6inv", tagdir='tag25h6inv/svg',
                    tagcode_pix = 5, style=2)

      gl.setdpp(11)

      svgtext += render_page(tagdpp1200=11, **taginv, **gl.pos(0,0))
      svgtext += render_page(tagdpp1200=11, **tag,    **gl.pos(1,0))
      svgtext += render_page(tagdpp1200=10, **taginv, **gl.pos(0,1))
      svgtext += render_page(tagdpp1200=10, **tag,    **gl.pos(1,1))
      svgtext += render_page(tagdpp1200=9,  **taginv, **gl.pos(0,2))
      svgtext += render_page(tagdpp1200=9,  **tag,    **gl.pos(1,2))
    elif (self.layout.custom=='custom_tag25h5'):
      tag = dict(family="tag25h5", tagdir='tag25h5/svg',
                 tagcode_pix = 5, style=1)
      taginv = dict(family="tag25h5inv", tagdir='tag25h5inv/svg',     
                    tagcode_pix = 5, style=2)

      gl.setdpp(11)

      svgtext += render_page(tagdpp1200=11, **taginv, **gl.pos(0,0))
      svgtext += render_page(tagdpp1200=11, **tag,    **gl.pos(1,0))
      svgtext += render_page(tagdpp1200=10, **taginv, **gl.pos(0,1))
      svgtext += render_page(tagdpp1200=10, **tag,    **gl.pos(1,1))
      svgtext += render_page(tagdpp1200=9,  **taginv, **gl.pos(0,2))
      svgtext += render_page(tagdpp1200=9,  **tag,    **gl.pos(1,2))
    elif (self.layout.custom=='custom_test'):
      tag = dict(family="tag25h5", tagdir='tag25h5/svg',
                 tagcode_pix = 5, style=1)
      taginv = dict(family="tag25h5inv", tagdir='tag25h5inv/svg',     
                    tagcode_pix = 5, style=2)

      svgtext += render_page(tagdpp1200=11, **taginv, **gl.pos(0,0))
    elif (self.layout.custom=='custom_tag25h6_dpp10'):
      tag = dict(family="tag25h6", tagdir='tag25h6/svg', maxid=958,
                 tagcode_pix = 5, style=1)
      taginv = dict(family="tag25h6inv", tagdir='tag25h6inv/svg', maxid=958,
                    tagcode_pix = 5, style=2)

      self.layout.sheet_x0 = 25.4*1.00
      self.layout.sheet_y0 = 25.4*0.75
      self.layout.pagemargin = 10
      self.layout.nblocksx = 5
      self.layout.nblocksy = 2
      self.layout.tagmarginx = 5.0 # pix
      self.layout.tagmarginy = 5.0 # pix
      gl.setdpp(10)

      svgtext += render_page(tagdpp1200=10, **taginv, **gl.pos(0,0))
      svgtext += render_page(tagdpp1200=10, **tag,    **gl.pos(0,1))
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

  def cmyk(self, output=None): # FIXME
    if (output is None):
        output=self.layout.output
    if output.endswith('.pdf') or output.endswith('.svg'):
        name = output[:-4]
    else:
        name = output
    output_pdf = name+'.pdf'
    output_cmyk = name+'_CMYK.pdf'
    print("Convert {} to CMYK PDF {}:".format(output,output_cmyk))
    os.system('   svg2cmyk.sh "{}"'.format(output))

  def cmyk_bw(self, output=None): # FIXME
    if (output is None):
        output=self.layout.output
    if output.endswith('.pdf') or output.endswith('.svg'):
        name = output[:-4]
    else:
        name = output
    output_pdf = name+'.pdf'
    output_cmyk = name+'_BW.pdf'
    print("Convert {} to CMYK (B/W) PDF {}:".format(output,output_cmyk))
    os.system('   svg2cmyk_bw.sh "{}"'.format(output))




class CustomPageSizeAction(argparse.Action):
    def __init__(self, option_strings=None, dest=None, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(CustomPageSizeAction, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        #print('--page_size: %r %r %r' % (namespace, values, option_string))
                
        setattr(namespace, 'page_size', 'custom')
        
        print('Option {} set page_size to custom'.format(option_string))
class TagMarginAction(argparse.Action):
    def __init__(self, option_strings=None, dest=None, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(TagMarginAction, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        #print('--page_size: %r %r %r' % (namespace, values, option_string))
                
        vals = values.split(',')
        if (len(vals)==1):
            tagmarginx = float(vals[0])
            tagmarginy = float(vals[0])
        elif (len(vals)==2):
            tagmarginx = float(vals[0])
            tagmarginy = float(vals[1])
        else:
            raise argparse.ArgumentTypeError('Incorrect format. Should be either <pixels> or <pixelsx>,<pixelsy>')
                
        setattr(namespace, 'tagmarginx', tagmarginx)
        setattr(namespace, 'tagmarginy', tagmarginy)
        
        print('--tagmargin: set to {},{}'.format(tagmarginx,tagmarginy))

class MyArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        return arg_line.split()

if __name__ == "__main__":

    layout = Layout()
    generator = Generator(layout)

    parser = argparse.ArgumentParser(description='Generate SVG tag sheet given a directory <tagdir> of tag images', formatter_class=argparse.RawDescriptionHelpFormatter)
#    ,fromfile_prefix_chars='@', convert_arg_line_to_args=MyArgumentParser)
    
    parser.add_argument('--verbose', metavar='<level>', 
                        type=int,
                        dest='verbose', default=1,
                        help='Verbosity level (default: %(default)s)')
    
    group = parser.add_argument_group('Input/Output')
#     parser.add_argument('-o', '--output', metavar='<tagsheet-TAGS.svg>', 
#                         dest='output', default=layout.output,
#                         help='basename for output file (default: %(default)s)')
    group.add_argument('-ob', '--output_basename', metavar='<tagsheet>', 
                        dest='output_basename', default=layout.output_basename,
                        help='basename for output file (default: %(default)s)')
    group.add_argument('-m', '--mode', metavar='<mode>',
                        dest='mode', default='tags',
                        help='sheets to generate, as comma separated list: tags,cuts,view or all (default: %(default)s)')
    group.add_argument('-rm', '--removesvg',  
                        dest='removesvg', action='store_true',
                        help='Delete tmp SVG file on success')
    group.add_argument('-r', '--rasterize',  
                        dest='rasterize', action='store_true',
                        help='rasterize output PDF')
    group.add_argument('-pdf', '--to_pdf',  
                        dest='to_pdf', action='store_true',
                        help='convert SVG to RGB PDF (default: %(default)s)')
    group.add_argument('-no_rgb', '--no_rgb',  
                        dest='to_pdf', action='store_false',
                        help='prevent RGB PDF output (default: %(default)s)')
    group.add_argument('-cmyk', '--to_cmyk',  
                        dest='to_cmyk', action='store_true',
                        help='convert output SVG to CMYK PDF (default: %(default)s)')
    group.add_argument('-bw', '--to_cmyk_bw',  
                        dest='to_cmyk_bw', action='store_true',
                        help='convert output SVG to CMYK pure Black PDF (default: %(default)s)')
                        
    group = parser.add_argument_group('Tag family info')
    group.add_argument('-f', '--family', metavar='<family>', 
                        dest='family', default=layout.family,
                        help='tag family name (default: %(default)s)')
    group.add_argument('-td', '--tagdir', metavar='<tagdir>', 
                        dest='tagdir', default=layout.tagdir,
                        help='directory containing tag image files (default: %(default)s)')
    group.add_argument('-tf', '--tagfiles', metavar='<tagfiles>', 
                        dest='tagfiles', default=layout.tagfiles,
                        help='pattern of tag image files, python format style (default: %(default)s)')
    group.add_argument('-p', '--tagcode_pix', metavar='<tagcode_pix>', 
                      dest='tagcode_pix', default=layout.tagcode_pix, type=int,
                      help='width of the code in pixels, without border (default: %(default)s)')
    group.add_argument('-u', '--first_id', metavar='<first_id>', type=int,
                        dest='first_id', default=layout.first_id,
                        help='first id, inclusive (default: %(default)s)')
    group.add_argument('-v', '--maxid', metavar='<max_id>', type=int,
                        dest='maxid', default=layout.maxid,
                        help='last id, inclusive (default: %(default)s)')

    group = parser.add_argument_group('Style')
    group.add_argument('-s', '--style', metavar='<style>',
                        dest='style', default=layout.style,
                        help='color style: auto, tag, invtag, tagdebug, invdebug (default: %(default)s)')
    group.add_argument('-sc', '--show_colored_corners', action='store_true',
                        dest='show_colored_corners', default=layout.show_colored_corners,
                        help='Margin2 is colored (default: %(default)s)')
    group.add_argument('-sa', '--show_arrows', action='store_true',
                        dest='show_arrows', default=layout.show_arrows,
                        help='Margin2 show contrasting arrows (default: %(default)s)')
    group.add_argument('-sb', '--show_bicolor', action='store_true',
                        dest='show_bicolor', default=layout.show_bicolor,
                        help='Top/Bottom bicolors (default: %(default)s)')
    group.add_argument('-col0', '--tagid_bgcolor', 
                        dest='tagid_bgcolor', default=layout.tagid_bgcolor,
                        help='tag id color (default: %(default)s)')
    group.add_argument('-col1', '--tagcornercolor1', 
                        dest='tagcornercolor1', default=layout.tagcornercolor1,
                        help='tag color 1(default: %(default)s)')
    group.add_argument('-col2', '--tagcornercolor2', 
                        dest='tagcornercolor2', default=layout.tagcornercolor2,
                        help='tag color 2 (default: %(default)s)')
    group.add_argument('-cb', '--codebottom', 
                        dest='codebottom', default=None, type=str,
                        help='binary code for bottom (default: %(default)s)')
    group.add_argument('-cs', '--codesides', 
                        dest='codesides', default=None, type=str,
                        help='binary code for sides (default: %(default)s)')
    group.add_argument('-sbc', '--show_bitcode', action='store_true',
                        dest='show_bitcode', default=layout.show_bitcode,
                        help='Show color bitcode instead of id (default: %(default)s)')
    group.add_argument('-b1sw', '--border1strokewidth', type=float,
                        dest='border1strokewidth', default=layout.border1strokewidth,
                        help='Thickness of border stroke in tag pixels (default: %(default)s)')
    group.add_argument('-tc', '--textcolor',
                        dest='textcolor', default=layout.textcolor,
                        help='Color of tag ID text (default: %(default)s)')
    group.add_argument('-tbc', '--textbgcolor',
                        dest='textbgcolor', default=layout.textbgcolor,
                        help='Color of tag ID background (default: %(default)s)')
    group.add_argument('-tbm', '--textbg_margin', type=float,
                        dest='textbg_margin', 
                        default=layout.textbg_margin,
                        help='Additional margin around text for bg (default: %(default)s)')
    group.add_argument('-ff', '--fontfamily',
                        dest='fontfamily', default=layout.fontfamily,
                        help='Font family for tag ID text (default: %(default)s)')
    group.add_argument('-fls', '--letterspacing',
                        dest='letterspacing', default=layout.letterspacing,
                        help='Font letter spacing for tag ID text (default: %(default)s)')
    group.add_argument('-fsi', '--fontsize_id',
                        dest='fontsize_id', default=layout.fontsize_id,
                        help='Tag ID fontsize in tag pixels (default: %(default)s)')
    group.add_argument('-fwi', '--fontweight_id',
                        dest='fontweight_id', default=layout.fontweight_id,
                        help='Tag ID fontweight (default: %(default)s)')
    group.add_argument('-fsx', '--fontsize_scalex',
                        dest='fontsize_scalex', default=layout.fontsize_scalex,
                        help='X scale for tag ID (default: %(default)s)')
                        
    group = parser.add_argument_group('Geometry')
    group.add_argument('--dpp', '-d', type=int,
                        dest='tagdpp1200', default=layout.tagdpp1200,
                        help='number of printer dots per pixel of the tag at 1200 dpi.\nFor 6 pixels code, dpp=8 -> 1.37mm, dpp=9 -> 1.54mm tag, dpp=10 -> 1.71mm tag')
    group.add_argument('-udpi', '--use_local_dpi', action='store_true',
                        dest='use_local_dpi', default=layout.use_local_dpi,
                        help='Use local DPI if not 1200 (default: %(default)s)')
    group.add_argument('-ldpi', '--local_dpi', type=float,
                        dest='local_dpi', default=layout.local_dpi,
                        help='Local DPI value (default: %(default)s)')
    group.add_argument('-ptsh', '--ptshift', type=float,
                        dest='ptshift', default=layout.ptshift,
                        help='Shift in dpi pts from round hint (default: %(default)s)')
                        
    group.add_argument('-uc', '--use_color', action='store_true',
                        dest='use_color', default=layout.use_color,
                        help='Use color patterns (default: %(default)s)')
                        
    group.add_argument('-c', '--custom',  metavar='<layout name>',
                        dest='custom', default=layout.custom,
                        choices='custom_tag25h5,custom_tag25h6,custom_tag36h10,custom_tag25h6_dpp10,custom_test'.split(','),
                        help='Use custom layout (hardcoded %(choices)s)')
    group.add_argument('-pz','--page_size', metavar='<size_name>', 
                        dest='page_size', default=layout.page_size,
                        help='page size (options: {}, default: %(default)s)'.format(list(layout.paper_sizes.keys()), layout.page_size))
    group.add_argument('-pw', '--page_w', metavar='<page_w>', type=float,
                        dest='page_w', default=layout.page_w,
                        action=CustomPageSizeAction,
                        help='page width in mm (default: %(default)s)')
    group.add_argument('-ph', '--page_h', metavar='<page_h>', type=float,
                        dest='page_w', default=layout.page_h,
                        action=CustomPageSizeAction,
                        help='page width in mm (default: %(default)s)')
    group.add_argument('-px', '--page_left', metavar='<page_left>', type=float,
                        dest='page_left', default=layout.page_left,
                        help='x0 of tags in mm (default: %(default)s)')
    group.add_argument('-py', '--page_top', metavar='<page_top>', type=float,
                        dest='page_top', default=layout.page_top,
                        help='y0 of tags in mm (default: %(default)s)')
    group.add_argument('-bx', '--nblocksx', metavar='<nblocksx>', type=int,
                        dest='nblocksx', default=layout.nblocksx,
                        help='number of tags in a block row (default: %(default)s)')
    group.add_argument('-by', '--nblocksy', metavar='<nblocksy>', type=int,
                        dest='nblocksy', default=layout.nblocksy,
                        help='number of tags in a block column (default: %(default)s)')
    group.add_argument('-bm', '--blockmargin', metavar='<mm>', type=float,
                        dest='blockmargin', default=layout.nblocksy,
                        help='margin between blocks (default: %(default)s)')
    group.add_argument('-nx', '--ntagsx', metavar='<ntagsx>', type=int,
                        dest='ntagsx', default=layout.ntagsx,
                        help='number of tags in a block row (default: %(default)s)')
    group.add_argument('-ny', '--ntagsy', metavar='<ntagsy>', type=int,
                        dest='ntagsy', default=layout.ntagsy,
                        help='number of tags in a block column (default: %(default)s)')
    group.add_argument('-tm', '--tagmargin', metavar='<mx,my> or <m>', 
                        action=TagMarginAction, default="{},{}".format(round(layout.tagmarginx,3),round(layout.tagmarginy,3)),
                        help='number of pixels of margin between tags (default: %(default)s)')
    group.add_argument('-tmx', '--tagmarginx', metavar='<pixels>', type=int,
                        dest='tagmarginx', default=layout.tagmarginx,
                        help='number of pixels of margin between tags (default: %(default)s)')
    group.add_argument('-tmy', '--tagmarginy', metavar='<pixels>', type=int,
                        dest='tagmarginy', default=layout.tagmarginy,
                        help='number of pixels of margin between tags (default: %(default)s)')
    group.add_argument('-tim', '--tagid_margin', metavar='<pixels>', type=float,
                        dest='tagid_margin', default=layout.tagid_margin,
                        help='number of pixels between tag id text and tag (default: %(default)s)')
    group.add_argument('-tm2', '--tagmargin2', metavar='<pixels>', type=float,
                        dest='tagmargin2_pix', default=layout.tagmargin2_pix,
                        help='number of pixels of outer color(s), from border1 (default: %(default)s)')
    group.add_argument('-tm2b', '--bicol2_margin_pix', metavar='<pixels>', type=float,
                        dest='bicol2_margin_pix', default=layout.bicol2_margin_pix,
                        help='number of pixels of outer color(s) for bicolor (default: %(default)s)')
    group.add_argument('-sg', '--show_guidelines', action='store_true',
                        dest='show_guidelines', default=layout.show_guidelines,
                        help='show guidelines (default: %(default)s)')
                                                
    group.add_argument('-cx', '--axismargin_left', metavar='<marginleft>', 
                        type=float,
                        dest='axismargin_left', default=layout.axismargin_left,
                        help='margin to center of cross (default: %(default)s)')
    group.add_argument('-cy', '--axismargin_top', metavar='<margintop>', 
                        type=float,
                        dest='axismargin_top', default=layout.axismargin_left,
                        help='margin to center of cross (default: %(default)s)')
    group.add_argument('-tp', '--show_test_patterns', action='store_true',
                        dest='show_test_patterns', default=layout.show_kerftest,
                        help='show Siemens star patterns (default: %(default)s)')
    group.add_argument('-tpx', '--test_patterns_x', type=float,
                        dest='test_patterns_x', default=layout.kerftest_left,
                        help='left corner of Siemens test pattern (default: %(default)s)')
    group.add_argument('-tpy', '--test_patterns_y', type=float,
                        dest='test_patterns_y', default=layout.kerftest_top,
                        help='top corner of Siemens test pattern (default: %(default)s)')
    group.add_argument('-tt', '--show_test_tags', action='store_true',
                        dest='show_test_tags', default=layout.show_test_tags,
                        help='show test tags (default: %(default)s)')
    group.add_argument('-ttx', '--test_tags_x', type=float,
                        dest='test_tags_x', default=layout.test_tags_x,
                        help='left corner of test tags (default: %(default)s)')
    group.add_argument('-tty', '--test_tags_y', type=float,
                        dest='test_tags_y', default=layout.test_tags_y,
                        help='top corner of test tags (default: %(default)s)')
                        
    group.add_argument('-cl', '--show_cmdline', action='store_true',
                        dest='show_cmdline', default=layout.show_cmdline,
                        help='show command line (default: %(default)s)')
    group.add_argument('-cld', '--show_cmdline_date', action='store_true',
                        dest='show_cmdline_date', default=layout.show_cmdline_date,
                        help='show date (default: %(default)s)')
    group.add_argument('-clx', '--cmdline_left', type=float,
                        dest='cmdline_left', default=layout.cmdline_left,
                        help='left corner of cmd line (default: %(default)s)')
    group.add_argument('-cly', '--cmdline_top', type=float,
                        dest='cmdline_top', default=layout.cmdline_top,
                        help='top corner of cmd line (default: %(default)s)')
    group.add_argument('-clfs', '--cmdline_fontsize', type=float,
                        dest='cmdline_fontsize', default=layout.cmdline_fontsize,
                        help='fontsize of cmd line in pt (default: %(default)s)')
    group.add_argument('-clw', '--cmdline_cols', type=int,
                        dest='cmdline_cols', default=layout.cmdline_cols,
                        help='width of cmd line in columns (default: %(default)s)')

    group.add_argument('-tg', '--show_taggrid', action='store_true',
                        dest='show_taggrid', default=layout.show_taggrid,
                        help='show interpixel tag grid (default: %(default)s)')
    group.add_argument('-tgc', '--taggrid_color', 
                        dest='taggrid_color', default=layout.taggrid_color,
                        help='stroke color of tag grid (default: %(default)s)')
    group.add_argument('-tgsw', '--taggrid_strokewidth', type=float,
                        dest='taggrid_strokewidth', default=layout.taggrid_strokewidth,
                        help='stroke width of tag grid (default: %(default)s)')

    group.add_argument('-br', '--show_block_rect', action='store_true',
                        dest='show_block_rect', default=layout.show_block_rect,
                        help='show block bounding box (default: %(default)s)')
                        
    group = parser.add_argument_group('Lasercutting')
    group.add_argument('-kf', '--laserkerf_mm', metavar='<kerf in mm>', 
                        type=float,
                        dest='laserkerf_mm', default=layout.laserkerf_mm,
                        help='thickness of laser in mm (default: %(default)s)')
    group.add_argument('-kfv', '--laserkerf_mm_view', metavar='<kerf in mm>', 
                        type=float,
                        dest='laserkerf_mm_view', default=layout.laserkerf_mm_view,
                        help='thickness of laser in mm for the view only. 0 to copy from -kf (default: %(default)s)')
    group.add_argument('-ko', '--cut_opening_factor', metavar='<factor>', 
                        type=float,
                        dest='cut_opening_factor', default=layout.cut_opening_factor,
                        help='width of top opening as a factor of laserkerf_mm (default: %(default)s)')
    group.add_argument('-kt', '--show_kerftest', action='store_true',
                        dest='show_kerftest', default=layout.show_kerftest,
                        help='show kerf testpattern (default: %(default)s)')
    group.add_argument('-ktx', '--kerftest_left', type=float,
                        dest='kerftest_left', default=layout.kerftest_left,
                        help='left corner of kerf test pattern (default: %(default)s)')
    group.add_argument('-kty', '--kerftest_top', type=float,
                        dest='kerftest_top', default=layout.kerftest_top,
                        help='top corner of kerf test pattern (default: %(default)s)')
                        
    args = parser.parse_args()    
    fields=sorted(vars(args).keys())
    for field in fields:
        #print("  Configuring '{}'".format(field))
        print("  Configuring {}={}".format(field,getattr(args,field)))
        setattr(layout, field,getattr(args,field))
    setattr(layout, 'date', str(datetime.now()))
    setattr(layout, 'cmdline',' '.join(sys.argv[1:]))
    generator.verbose = args.verbose
        
    def computeOutputFile(generator):
        V = generator.getvars()
        base = generator.layout.output_basename.format(**V)
        if (mode=='tags'): # Tags
          suffix_pattern = '_TAGS.svg'
        elif (mode=='cuts'): # Cut
          suffix_pattern = '_CUTS{laserkerf_um}-{cut_opening_factor}.svg'
        elif (mode=='view'): # Preview: Both tags and cuts
          suffix_pattern = '_VIEW{laserkerf_um}-{cut_opening_factor}.svg'
        else:
          print('ERROR: Unknown mode {}'.format(mode))
        suffix = suffix_pattern.format(**V)
        layout.output = base+suffix

    if (args.mode == 'all'):
        args.mode = 'tags,cuts,view'
        
    for mode in args.mode.split(','):
        layout.mode = mode
        computeOutputFile(generator)
        print('Generating mode "{}" --> {}...'.format(mode,layout.output))
        generator.generate()
        if (args.rasterize):
            generator.rasterize()







