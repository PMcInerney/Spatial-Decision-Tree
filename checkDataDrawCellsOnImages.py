from __future__ import division
import sys
import os
import os.path
sys.path.append('/data/home/pmcinerney/python')
import SOLARGenImageList
import random
import itertools
import scipy.misc as m
from readData import readData
from visualizationTools import drawSquare
random.seed(42)

# this code reads a set of data and finds the correct solar images for the data, draws the event cells on top, then saves the resulting image locally
# errors happen when the requested data has not been generated

outputFolder = 'checkDataDrawCellsOnImagesOut'
if not os.path.exists(outputFolder):# if output folder doesn't exist
  os.mkdir(outputFolder) #create it
  #This is technically vulnerable to race conditions, but this isn't an issue in these research applications


radius = 1625 # radius of the 'ignore off-disc' filter
#define some colors
black = [0,0,0]
blue = [0,0,255] 
red = [255,0,0] 
green = [0,255,0]
magenta = [255,0,255]
cyan = [0,255,255]
yellow = [255,255,0]
white = [255,255,255]

#map colors to events
colordict = dict([('FI',blue),('FL',red),('AR',yellow),('SS',white),('SG',green),('CH',magenta)])

#events = ['SS','FL','CH','AR','SG','FI'] 
#events = ['AR','CH','FL','FI','SG','SS'] 
#events = ['AR','CH','FL','FI','SG','SS'] 
events = ['AR'] 
#datasets = ['1WEEK']
datasets = ['3DAYDEMO']
for e,d in itertools.product(events,datasets):
  if not os.path.exists(os.path.join(outputFolder,e)):
    os.mkdir(os.path.join(outputFolder,e))
  #similar to above, make subfolder if doesn't exist
  n = 'rook'
  w = ['0171']
  b = 'Mirror'
  eventClass = e
  dataset = d
  print eventClass,dataset
  headers,matches = SOLARGenImageList.image_event_matches(dataset=dataset,waves = ['0171'])
  S_train,S_test, = readData(e,n,d,w,b)
  cells, adj = S_train
  cells2, adj2 = S_test
  print 'matches calculated'
  counter = 0
  total = len(matches.keys())
  for x in sorted(matches.keys()): # for each image
    paramsFilename = x[0]
    imageFilename = paramsFilename[:-4]+'_th.png'
    I = m.imread(imageFilename)
    outputname = os.path.join(outputFolder,e,os.path.basename(imageFilename)[:-4]+'_'+e+'.png')
    cellsWeWant = [x for x in cells if x['id'][3][0] == paramsFilename]
    for cell in cellsWeWant:
      cellr = cell['id'][1]
      cellc = cell['id'][2]
      I = drawSquare(I,cellr,cellc,colordict[e] if cell['class'] != 'null' else black ) 
      # null training cells are colored black, non-nulls are colored according to their class
    cellsWeWant2 = [x for x in cells2 if x['id'][3][0] == paramsFilename]
    for cell in cellsWeWant2:
      cellr = cell['id'][1]
      cellc = cell['id'][2]
      I = drawSquare(I,cellr,cellc,cyan) #color the test cells cyan
    m.imsave(outputname,I)
    counter += 1
    print counter, '/', total

