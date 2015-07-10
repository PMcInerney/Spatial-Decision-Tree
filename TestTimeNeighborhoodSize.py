from __future__ import division
import time
import SDT
import cProfile
from readData import readData
import itertools
import cPickle as pickle

# logging is used for data output because it allows us to read the output file as it is being constructed
import logging
logging.basicConfig(filename='TestTimeNeighborhoodSize.log',level=logging.DEBUG)

# the general form of this script is patterned after 'runExperiments,' with adjustments made for time keeping
# 

def testing():
#  events = ['FL','SG','AR','CH']
  events = ['SG']
#  events = ['FL','SG','FI','CH','AR','SS']
#  neighborhoods = ['rook','queen','rooktemp']
  neighborhoods = ['rook','rooktemp','rooktemplong']
  datasets = ['3DAYDEMO']

  thetas = [0.7] # theta is the classification parameter

#  grid = [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
#  alphas = [x for x in itertools.product(grid,grid) if sum(x) <= 1]# alpha is the parameter that weights the entropy and neighb$
  alphas = [(0.3,0.3),(0.6,0.3),(0.3,0.6)]

  NeighborFunctions = ["spatial","temporal"]


  splitRes = 10000000 # splitRes affects how many splits are considered among each parameter at each tree node
  c_0vals = [100]# c_0val is the _proportion_ of total values set as the minimum leaf size
  waves = [['0193'],['0171'],['0094']]
#  balances = ['Mirror','Duplication','Random']
  balances = ['Mirror']
  X = [x for x in itertools.product(events,neighborhoods,datasets,waves,balances,c_0vals)]
  Y = [x for x in itertools.product(alphas,thetas)]
  results = []
  for e,n,d,w,b,cv in X:
   S_train,S_test = readData(e,neighborhood = n, dataset = d, waves = w,balanceOption = b)
   cells, adj = S_train
   cells2, adj2 = S_test
   c_0 = max(len(cells)//cv,1)
   for alpha,theta in Y:
    t1 = time.time()
    if sum(alpha) > 1:
     raise Exception('invalid alpha')
    treefile = "temp.tree"
    TP,FP,TN,FN = SDT.SDT_Learn(S_train,S_test,alpha,c_0,theta,splitRes,treefile,NeighborFunctions)
    ACC = 100*(TP+TN)/(TP+TN+FP+FN) 
    if TP+FP != 0:
      PREC = 100*(TP)/(TP+FP)
    else:
      PREC = 0
    if TP+FN != 0:
      REC = 100*TP/(TP+FN)
    else:
      REC = 0
    F1 = 0 if PREC+REC == 0 else (2*PREC*REC)/(PREC+REC)
    summ = 0
    for p in ['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10']: # for each parameter
      s = set()                                                    # build a set of all of the values of that parameter
      for cell in cells:                                           # the set data structure will eliminate duplicates
        s.add(cell[p])                                             # so its length is the number of distinct values for that 
      summ+=len(s)                                                 # parameter
    splits = summ                                                  # add all these together to get the number of potential 
                                                                   # splits in the dataset
    t2 = time.time()
    runTime = t2-t1
    
    strr = "".join([
                  'event:',str(e),'\n',
                  'neighborhood:',str(n),'\n',
                  'numcells: ', str(len(cells)),'\n',
                  'wave:',str(w),'\n',
                  'dataset:',str(d),'\n',
                  'alpha:',str(alpha),'\n',
                  'c_0:',str(c_0),'\n',
                  'theta:',str(theta),'\n',
                  'balance:',str(b),'\n',
                  'splits:',str(splits),'\n',
                  'Runtime:',str(t2-t1),'\n'
                  'F1:',str(F1),'\n',
                  ' ','\n',
                  ' ','\n',
                  ' ','\n'])
    logging.debug(strr)
    parameters = (n,w,alpha)
    results.append((parameters,F1,runTime))
    
  with open('TestTimeNeighborhoodSize.results','wb') as f:
    pickle.dump(results,f)

#cProfile.run('testing()')
testing()
