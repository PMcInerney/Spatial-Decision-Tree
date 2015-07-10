from readData import readData
import csv
from collections import Counter

def checkDatasetSizes(experiments):
# this function checks specified  dataset structures and prints out the number of training cells and the number of entries in
# the adjacency matrix. These numbers should be the same    

# if the specified data hasn't been built, errors will happen
  for experiment in experiments:
    print experiment
    S_train,S_test = readData(*experiment)
    cells, adj = S_train
    print len(cells)
    print len(adj.keys())
    print

def checkDatasetSplits(experiments):
# this function checks specified dataset structures and prints out the number _different_values_ for each parameter
# this helps see how large the decision space for split selection is.

# if the specified data hasn't been built, errors will happen

  for experiment in experiments:
    print experiment
    summ = 0
    S_train,S_test = readData(*experiment)
    cells, adj = S_train
    print 'numcells: ', len(cells)
    P = dict()
    for p in ['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10']:
      s = set()
      P[p] = set()
      for cell in cells:
        s.add(cell[p])
      print p,': ',len(s)
      summ+=len(s)
    print 'total:',summ
    print


def checkDataOrientation(experiments):
# This code reads through every produced training file and prints the number of positive and negative cells
# It's old, from back when I was still getting orientation wrong. 
# Its purpose is to check indexing across my data and the original data.

# if the specified data hasn't been built, errors will happen

  for experiment in experiments:
    print experiment
    S_train, S_test = readData(*experiment)
    cells,adj = S_train
    qwer = max([int(x['id'][0]) for x in cells])
    #check balance
    pos = len([x for x in cells if x['class'] != 'null'])
    neg = len([x for x in cells if x['class'] == 'null'])
    print 'pos:',pos
    print 'neg:',neg
    #pick an arbitrary image
    arbImageNum = cells[0]['id'][0]
    arbImageCells = [x for x in cells if x['id'][0] == arbImageNum]
    dataFile = arbImageCells[0]['id'][3][0] # grab the original data file this images cells come from
                                            # id structure is (imageCounter,row,col,(dataFileName,timeStamp))
    print dataFile
    with open(dataFile) as f2:                          # read the parameter data for this image
      c = csv.reader(f2,dialect = 'excel-tab')
      Juancells = [x for x in c]
    for cell in arbImageCells:
      myx = cell['id'][1]#these should be zero based
      myy = cell['id'][2]
      juanx = myx+1      # Juan's indexing is 1-based
      juany = myy+1
      juanCell = [x for x in Juancells if x[0] == str(juanx) and x[1] == str(juany)][0]
    print
      #print cell
      #print juanCell


def checkDatasetNeighbors(experiments):
# This code checks the number of temporal neighbors each cell has and prints a detailing ot the distribution

# if the specified data hasn't been built, errors will happen
  for experiment in experiments:
    print experiment
    S_train, S_test = readData(*experiment)
    cells,adj = S_train
    allNeighbors = [len(adj[cell['id']]) for cell in cells] # this is all neighbors
    c = Counter(allNeighbors)
    print c
    print
#      temporalNeighbors = [x for x in adj[cell['id']] if not cell['id'][0] == x['id'][0]]
#      print cell

