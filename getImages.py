from __future__ import division
import sys
import os.path
import shutil
sys.path.append('/data/home/pmcinerney/python')
import SOLARGenImageList
import random
import itertools
random.seed(42)

#This code copies the images of the specified datasets from their stored location on CBSIR to a local folder

#events = ['SS','FL','CH','AR','SG','FI']
events = ['AR']
datasets = ['1WEEK']
radius = 1625
for e,d in itertools.product(events,datasets):
  eventClass = e
  dataset = d
  print eventClass,dataset
  headers,matches = SOLARGenImageList.image_event_matches([eventClass],dataset=dataset,waves = ['0171'])
  print 'matches calculated'
  for x in matches.keys():
    paramsFilename = x[0]
    imageFilename = paramsFilename[:-4]+'_th.png'
    shutil.copyfile(imageFilename,os.path.join('images',e+'_'+os.path.basename(imageFilename)))
#  for imageKey in matches[0]:                                # for every image
#    eventBinMat = np.zeros([64,64],dtype = bool)
#    for E in matches[imageKey]:                           # for each event in that image
#      cc = pt.parseChainCode(E,headers)               
#      if cc == "NA":                                  
#        cc = pt.parseBoundingBox(E,headers)           
#      eventBinMat = np.logical_or(eventBinMat, stuff.find_grid_cells(cc)) # combine all the events into one binary matrix for the image


