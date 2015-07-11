from __future__ import division
import sys
import os.path
sys.path.append('/data/home/pmcinerney/python')
import SOLARGenImageList
import numpy as np
import random
import itertools
import scipy.misc as m
from readData import readData
import SDT
from DecisionTree import TreeNode
from visualizationTools import drawSquare
random.seed(42)

# This replicates Mike's style of imagery for visualizing the output of classification on top of the solar images
# true positives: green square
# false positives: red square
# false negatives: yellow square
# true negatives: no mark

# It reads a specified set of results and finds the correct solar images for the data, draws the visualization on top, then saves the result locally
# errors happen when the requested experiments have not been run


outputFolder = 'checkResultsVisualizeOut'

if not os.path.exists(outputFolder):# if output folder doesn't exist
  os.mkdir(outputFolder) #create it
  #This is technically vulnerable to race conditions, but this isn't an issue in these research applications

radius = 1625 
black = [0,0,0]
blue = [0,0,255] 
red = [255,0,0] 
green = [0,255,0]
magenta = [255,0,255]
cyan = [0,255,255]
yellow = [255,255,0]
white = [255,255,255]
colordict = dict([('FI',blue),('FL',red),('AR',yellow),('SS',white),('SG',green),('CH',magenta)])

#events = ['AR','CH','FL','FI','SG','SS'] 
events = ['AR','CH','FL','SG'] 
#events = ['AR'] 
#datasets = ['1DAY']
datasets = ['3DAYDEMO']

# this reads the inpute data, and draws the train and test set on the image

# cref is the value of c_0 (minimum leaf size)used for the experiment. it is typically picked as a specific proportion of 
#  the total number of training cells

# cref = dict([('AR',40),('CH',56),('SG',11),('FL',7)])
cref = dict([('AR',111),('CH',584),('SG',9),('FL',14)])
for e,d in itertools.product(events,datasets): 
  if not os.path.exists(os.path.join(outputFolder,e)):
    os.mkdir(os.path.join(outputFolder,e))
  #similar to above, make subfolder if doesn't exist

  n = 'rooktemp'
  w = ['0193']
  b = 'Mirror'
  theta = 0.7
  alphaSpatial = '[0.3-0.0]'
  alphaSpatiotemp = '0.3-0.4]'
  alphaNonSpatial = '[0.0-0.0]'
  c_0 = cref[e]
  eventClass = e
  dataset = d
  print eventClass,dataset
  headers,matches = SOLARGenImageList.image_event_matches(dataset=d,waves = w)
  print 'matches calculated'
  treefileSpatial = "results/"+"_".join([str(e),str(n),str(d),"-".join(w),'c_0='+str(c_0),'balance='+str(b),'alpha='+str(alphaSpatial)])+".tree"
  treefileNonSpatial = "results/"+"_".join([str(e),str(n),str(d),"-".join(w),'c_0='+str(c_0),'balance='+str(b),'alpha='+str(alphaNonSpatial)])+".tree"
  treeSpatial = TreeNode('dummy')
  treeNonSpatial = TreeNode('dummy')
  with open(treefileSpatial) as f:
    treeSpatial.load(f)
  with open(treefileNonSpatial) as f:
    treeNonSpatial.load(f)
  S_train,S_test, = readData(e,n,d,w,b) # read the data set
  cells_train, adj = S_train
  cells_test, adj_test = S_test
  counter = 0
  for x in sorted(matches.keys()): # for each image of the data set
    paramsFilename = x[0]
    imageFilename = paramsFilename[:-4]+'_th.png'
    ISpatial = m.imread(imageFilename) # read the image
    INonSpatial = ISpatial.copy()
    outputname = os.path.join(outputFolder,e,os.path.basename(imageFilename)[:-4]+'_'+e+'_'+d+'.png')
    cells_testWeWant = [x for x in cells_test if x['id'][3][0] == paramsFilename] # get the test cells tied to this image
    for x in range(2):
      if x == 0:
        I = ISpatial
        tree = treeSpatial
      else:
        I = INonSpatial
        tree = treeNonSpatial
      for cell in cells_testWeWant:
        cellr = cell['id'][1]
        cellc = cell['id'][2]
        cellNeighbors =  adj_test[cell['id']]
        DTOutput = SDT.sdt_predict(tree, cell, cellNeighbors, theta)
        if DTOutput == cell['class']:#Correct result
          if DTOutput == 'null': # TN
            pass
          else : # TP
             I = drawSquare(I,cellr,cellc,green)
        else: # incorrect result
          if DTOutput == 'null': #FN
            I = drawSquare(I,cellr,cellc,yellow)
          else : # FP
            I = drawSquare(I,cellr,cellc,red)
      if x == 0:
        ISpatial = I
      else:
        INonSpatial = I
    IFinal = np.concatenate((INonSpatial,ISpatial), axis = 1)
    m.imsave(outputname,IFinal)
    counter += 1
    print counter    

