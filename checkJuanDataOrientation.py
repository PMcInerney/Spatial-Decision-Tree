from __future__ import division
import numpy as np
import scipy.misc as m
import csv

# this code was used to check if Juan's parameter format stored the cell numbers in row major or column major order
# SDT data is row major

datafile = '/data/SDO/AIA/2012/01/01/H0000/AIA20120101_000001_0171.txt' # pick arbitrary image
print 'checking',datafile
with open(datafile) as f2:                          # read the parameter data for this image
 c = csv.reader(f2,dialect = 'excel-tab')
 Juancells = [x for x in c]
for ii in range(10): # for each parameter
  print 'P'+str(ii+1)
  vals = [float(x[2+ii]) for x in Juancells] #grab every value of that parameter in the file (entry 1 and 2 are cell numbers)
  # set normalization factor s.t. all parameter range from 0-255
  minval = min(vals)
  print 'min:'+str(minval)
  maxval = max(vals)
  print 'max:'+str(maxval)
  norm = lambda x: int((x-minval)/(maxval-minval)*255)

  # write a parameter image to compare against the actual solar thumbnails
  I = np.zeros([64,64],dtype = int)
  for cell in Juancells:
    r = int(cell[0]) # trying row major order (this is the correct order)
    c = int(cell[1])
    I[r-1,c-1] = norm(float(cell[2+ii]))
  print 'nonzero:',len(np.nonzero(I)[0]),'/','4096' # see how many of the 4096 cells are not zero
  print 
  #for x,y in np.nonzero(I): print x,y
  m.imsave('derpy'+str(ii).zfill(2)+'.png',I) # output a parameter 
#  for ii in range(1,qwer+1):
#    derp = np.zeros([64,64],dtype = bool)
#    asdf = [x for x in cells if int(x['id'][0]) == ii]
#    for x in asdf: print x['id'],x['class']
#    for x in asdf: derp[x['id'][2],x['id'][1]] = True
#    m.imsave('derp'+str(ii).zfill(3)+'.png',derp)
#  print x
  
