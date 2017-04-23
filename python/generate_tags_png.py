# coding: utf-8

import sys, getopt, datetime

sys.path.append('/Users/megret/Documents/Research/BeeTracking/Soft/apriltag/swatbotics-apriltag/python')
import apriltag


import numpy as np
from scipy.misc import imsave
import scipy.misc

## Load tags information
import csv

def load_family(incsv):
    ids=[]
    tags={}
    with open(incsv,'rU') as csvfile:
      #has_header = csv.Sniffer().has_header(csvfile.read(1024))
      #csvfile.seek(0)  # rewind
      keyreader = csv.reader(csvfile, delimiter=',')
      #if has_header:
      #  next(csvfile)  # skip header row
      for row in keyreader:
        if row[0].startswith("#"):
            continue
        key = int(row[0])
        id = int(row[1], 16) # hex
        ids.append( (key,id) )
        tags[key]=id
        #print 'key={key}, num={num}'.format(key=row[0],num=row[1])
        pass
    return ids
    
## Output functions    

def create_png(key, id, out, d=6, scale=1, margin=1):
    A = np.zeros((d+margin*2,d+margin*2))
    
    # Convert hex to bool array
    # array: row-major, left to right, then top to bottom
    # binary: MSB to LSB
    bcode = [id >> i & 1 for i in range(d*d-1,-1,-1)]
    
    # Fill in 2D array with binary code
    for x, y in np.ndindex((d,d)):
        n = x+y*d
        
        # print(x,y, bcode[n])
        
        A[y+margin,x+margin]=255*bcode[n]
    
    if scale!=1:
        A = scipy.misc.imresize(A, float(scale), 'nearest')

    imsave(out,  A)


import os

def main(argv):
    input = 'taglist_tag36h11.txt'
    outdir = 'tags_tag36h11'
    dim = 6
    scale = 1
    try:
      opts, args = getopt.getopt(argv,"hi:o:d:s:",["help","input","output","dim","scale"])
    except getopt.GetoptError:
      sys.stderr.write('create_tags_png.py [-h] [-i <input>] [-o <outdir>] [-d <codesize>] [-s <scale>]\n')
      sys.exit(2)
    for opt, arg in opts:
      if opt in ('-h', "--help"):
         sys.stderr.write('create_tags_png.py [-h] [-i <input>] [-o <output>]\n')
         sys.exit()
      elif opt in ("-i", "--input"):
         input = arg
      elif opt in ("-o", "--outdir"):
         outdir = arg
      elif opt in ("-d", "--dim"):
         dim = int(arg)
      elif opt in ("-s", "--scale"):
         scale = float(int(arg))
         
    ids = load_family(input) # load csv   (key, hex_code, binary_code)
    
    os.makedirs(outdir,exist_ok=True)
        
    for (k,code) in ids:
        out="%(base)s/keyed%(k)04d.png" % {'base':outdir, 'k':k}
        print("Creating code #{}: {} --> {}".format(k,code,out))
        create_png(k, code, out=out, d=dim, scale=scale)

if __name__ == "__main__":
    main(sys.argv[1:])
