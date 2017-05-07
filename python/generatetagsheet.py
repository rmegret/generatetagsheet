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

class Layout(object):
  def __init__(self):
    self.in2mm = 25.4
    
    self.family = "tag25h5inv"
    self.tagcode_pix = 6          # image code
    
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
    
    self.title_fontsize=2.3 # 3mm normally
    self.block_fontsize=1.4 # 2mm normally
    self.fontfamily="Courier New"
    self.fontsize_id=2      # pix
    self.fontsize_idext=5   # pix
    
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
    
    self.tagborder_pix = 1       # inner border (included in img)
    self.tagmargin1_pix = 1      # minimal outer border for contrast
    self.tagmargin2_pix = 3      # outer border extra
    self.idheight_pix=1        # Height of extra text for label
    
    self.laserkerf_mm = 0.20
    self.cutweight_inch = 0.0015  # Minimum for Epilog is 0.001
    self.cut_opening_factor = 0
    
    self.modestring = ""

    self.style='auto'
    self.tagbgcolor="white"
    self.border1color="white"
    self.border2color="white"
    self.textcolor="black"
    self.arrowcolor="black"
    self.crosscolor="black"
    self.tagid_bgcolor="#600060"
    self.tagcornercolor1="#006060"
    self.tagcornercolor2="#606000"
    self.show_colored_corners=False
    self.show_arrows=False

    self.mode = 'tags'
    self.show_crosses = True
    self.show_test_patterns = True
    self.show_kerftest = False
    self.kerftest_left = 40
    self.kerftest_top = 450
    
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
        self.textcolor="black"
        self.arrowcolor="black"
    elif (self.style1=='tagdebug'):
        self.tagbgcolor="lightyellow"
        self.border1color="lightcyan"
        self.border2color="lightskyblue"
        self.textcolor="black"
        self.arrowcolor="darkred"
    elif (self.style1=='invtag'):
        self.tagbgcolor="white"
        self.border1color="black"
        self.border2color="black"
        self.textcolor="white"
        self.arrowcolor="white"
    elif (self.style1=='invtagdebug'):
        self.tagbgcolor="#DFD"
        self.border1color="darkblue"
        self.border2color="mediumblue"
        self.textcolor="white"
        self.arrowcolor="lightcyan"
    else:
        print('ERROR: Unknown style={}'.format(self.style1))

    # When recomputing, hint core alignments parameters to be integer at 300dpi

    self.sheet_y0 = self.apply_hint_mm(self.sheet_y0)
    self.sheet_x0 = self.apply_hint_mm(self.sheet_x0)

    self.last_id  = min(self.maxid, self.first_id+self.nblocksx*self.nblocksy*self.ntagsx*self.ntagsy)
  
    self.tagsize_pix = self.tagcode_pix + 2*self.tagborder_pix
    self.tagsize1_pix = self.tagsize_pix+2*self.tagmargin1_pix
    self.tagwidth2_pix = self.tagsize_pix+2*self.tagmargin2_pix
    self.tagheight2_pix = self.tagsize_pix+2*self.tagmargin2_pix+self.idheight_pix

    self.tagsize = self.tagsize_pix * self.tagdpp1200 / 1200 * self.in2mm
    
    self.pix2mm = self.tagsize/self.tagsize_pix
    self.pt2mm = (279.4/11)/72 # 1pt=1/71in
    
    self.laserkerf_um=round(self.laserkerf_mm*1000)
    self.laserkerf_pix=self.laserkerf_mm/self.pix2mm
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
      self.show_block_rect = False
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
      self.show_block_rect = False
      self.show_block_title = False
      self.show_page_title = True
      self.show_test_patterns = False
      self.show_crosses = False
      self.modestring = "CUTS"
    elif (mode=='view'): # Preview: Both tags and cuts
      self.show_tag = True
      self.show_tag_img = False
      self.show_tag_cut = True
      self.show_tag_cutkerf = True
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
    self.topdf(output)
    
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

if __name__ == "__main__":

    layout = Layout()
    generator = Generator(layout)

    parser = argparse.ArgumentParser(description='Generate SVG tag sheet given a directory <tagdir> of tag images', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dpp', '-d', type=int,
                        dest='tagdpp1200', default=layout.tagdpp1200,
                        help='number of printer dots per pixel of the tag at 1200 dpi.\nFor 6 pixels code, dpp=8 -> 1.37mm, dpp=9 -> 1.54mm tag, dpp=10 -> 1.71mm tag')
#     parser.add_argument('-o', '--output', metavar='<tagsheet-TAGS.svg>', 
#                         dest='output', default=layout.output,
#                         help='basename for output file (default: %(default)s)')
    parser.add_argument('-ob', '--output_basename', metavar='<tagsheet>', 
                        dest='output_basename', default=layout.output_basename,
                        help='basename for output file (default: %(default)s)')
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
    parser.add_argument('-s', '--style', metavar='<style>',
                        dest='style', default=layout.style,
                        help='color style: auto, tag, invtag, tagdebug, invdebug (default: %(default)s)')
    parser.add_argument('-sc', '--show_colored_corners', action='store_true',
                        dest='show_colored_corners', default=layout.show_colored_corners,
                        help='Margin2 is colored (default: %(default)s)')
    parser.add_argument('-sa', '--show_arrows', action='store_true',
                        dest='show_arrows', default=layout.show_arrows,
                        help='Margin2 show contrasting arrows (default: %(default)s)')
    parser.add_argument('-m', '--mode', metavar='<mode>',
                        dest='mode', default='tags',
                        help='sheets to generate, as comma separated list: tags,cuts,view or all (default: %(default)s)')
    parser.add_argument('-pz','--page_size', metavar='<size_name>', 
                        dest='page_size', default=layout.page_size,
                        help='page size (options: {}, default: %(default)s)'.format(list(layout.paper_sizes.keys()), layout.page_size))
    parser.add_argument('-pw', '--page_w', metavar='<page_w>', type=float,
                        dest='page_w', default=layout.page_w,
                        action=CustomPageSizeAction,
                        help='page width in mm (default: %(default)s)')
    parser.add_argument('-ph', '--page_h', metavar='<page_h>', type=float,
                        dest='page_w', default=layout.page_h,
                        action=CustomPageSizeAction,
                        help='page width in mm (default: %(default)s)')
    parser.add_argument('-px', '--page_left', metavar='<page_left>', type=float,
                        dest='page_left', default=layout.page_left,
                        help='x0 of tags in mm (default: %(default)s)')
    parser.add_argument('-py', '--page_top', metavar='<page_top>', type=float,
                        dest='page_top', default=layout.page_top,
                        help='y0 of tags in mm (default: %(default)s)')
    parser.add_argument('-bx', '--nblocksx', metavar='<nblocksx>', type=int,
                        dest='nblocksx', default=layout.nblocksx,
                        help='number of tags in a block row (default: %(default)s)')
    parser.add_argument('-by', '--nblocksy', metavar='<nblocksy>', type=int,
                        dest='nblocksy', default=layout.nblocksy,
                        help='number of tags in a block column (default: %(default)s)')
    parser.add_argument('-bm', '--blockmargin', metavar='<mm>', type=float,
                        dest='blockmargin', default=layout.nblocksy,
                        help='margin between blocks (default: %(default)s)')
    parser.add_argument('-nx', '--ntagsx', metavar='<ntagsx>', type=int,
                        dest='ntagsx', default=layout.ntagsx,
                        help='number of tags in a block row (default: %(default)s)')
    parser.add_argument('-ny', '--ntagsy', metavar='<ntagsy>', type=int,
                        dest='ntagsy', default=layout.ntagsy,
                        help='number of tags in a block column (default: %(default)s)')
    parser.add_argument('-tm', '--tagmargin', metavar='<mx,my> or <m>', 
                        action=TagMarginAction, default="{},{}".format(round(layout.tagmarginx,3),round(layout.tagmarginy,3)),
                        help='number of pixels of margin between tags (default: %(default)s)')
    parser.add_argument('-tmx', '--tagmarginx', metavar='<pixels>', type=int,
                        dest='tagmarginx', default=layout.tagmarginx,
                        help='number of pixels of margin between tags (default: %(default)s)')
    parser.add_argument('-tmy', '--tagmarginy', metavar='<pixels>', type=int,
                        dest='tagmarginy', default=layout.tagmarginy,
                        help='number of pixels of margin between tags (default: %(default)s)')
    parser.add_argument('-rm', '--removesvg',  
                        dest='removesvg', action='store_true',
                        help='Delete tmp SVG file on success')
    parser.add_argument('-r', '--rasterize',  
                        dest='rasterize', action='store_true',
                        help='rasterize output PDF')
    parser.add_argument('-c', '--custom',  metavar='<layout name>',
                        dest='custom', default=layout.custom,
                        choices='custom_tag25h5,custom_tag25h6,custom_tag36h10,custom_tag25h6_dpp10,custom_test'.split(','),
                        help='Use custom layout (hardcoded %(choices)s)')
    parser.add_argument('-cx', '--axismargin_left', metavar='<marginleft>', 
                        type=float,
                        dest='axismargin_left', default=layout.axismargin_left,
                        help='margin to center of cross (default: %(default)s)')
    parser.add_argument('-cy', '--axismargin_top', metavar='<margintop>', 
                        type=float,
                        dest='axismargin_top', default=layout.axismargin_left,
                        help='margin to center of cross (default: %(default)s)')
    parser.add_argument('-kf', '--laserkerf_mm', metavar='<kerf in mm>', 
                        type=float,
                        dest='laserkerf_mm', default=layout.laserkerf_mm,
                        help='thickness of laser in mm (default: %(default)s)')
    parser.add_argument('-ko', '--cut_opening_factor', metavar='<factor>', 
                        type=float,
                        dest='cut_opening_factor', default=layout.cut_opening_factor,
                        help='width of top opening as a factor of laserkerf_mm (default: %(default)s)')
    parser.add_argument('-kt', '--show_kerftest', action='store_true',
                        dest='show_kerftest', default=layout.show_kerftest,
                        help='show kerf testpattern (default: %(default)s)')
    parser.add_argument('-ktx', '--kerftest_left', type=float,
                        dest='kerftest_left', default=layout.kerftest_left,
                        help='left corner of kerf test pattern (default: %(default)s)')
    parser.add_argument('-kty', '--kerftest_top', type=float,
                        dest='kerftest_top', default=layout.kerftest_top,
                        help='top corner of kerf test pattern (default: %(default)s)')
    parser.add_argument('--verbose', metavar='<level>', 
                        type=int,
                        dest='verbose', default=1,
                        help='Verbosity level (default: %(default)s)')
    args = parser.parse_args()    
    fields=sorted(vars(args).keys())
    for field in fields:
        #print("  Configuring '{}'".format(field))
        print("  Configuring {}={}".format(field,getattr(args,field)))
        setattr(layout, field,getattr(args,field))
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







