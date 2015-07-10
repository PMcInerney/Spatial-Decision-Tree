from __future__ import division
from multiprocessing import Pool
import SDT
import cProfile
from readData import readData
import itertools
import os.path
import signal

# this is the top level script for running the core toolchain.
# it assumes the input data has already been built by 

# we can send an email message at completion for very long runs
# Import MIMEText for creating the message to be sent
# Import smtplib for the actual sending function
import smtplib
from email.mime.text import MIMEText

class MyTimeoutException(Exception):
  pass

def handler(signum,frame):
  print 'timed Out'
  raise MyTimeoutException()

def testing():
  timeout = 0 # if timeout is zero, no timeout will be triggered; otherwise the code will cut off the runtime of the experiment at this many seconds
  skipTOs = False; # if this is true, the script will skip runs that previously timed out; otherwise they will be re-run (and potentially timeout again)
  pooling = False; # if this is true, the runs will be parallelized with Python's Pool tool; it's faster, 
                   # especially for large run sets, but debugging errors is easier when it's off

  #--------------------
  # setting parameters
  #--------------------
#  events = ['FL','SG','AR','CH']
  events = ['AR']
#  events = ['SG']
#  events = ['AR','SG']
#  events = ['FL','SG','FI','CH','AR','SS']
#  neighborhoods = ['rook','queen','rooktemp']
  neighborhoods = ['rook']
#  datasets = ['1DAY','3DAYDEMO']
  datasets = ['1DAY']
#  waves = [['0193'],['0171'],['0094']]
  waves = [['0193']]
#  balances = ['Mirror','Duplication','Random']
  balances = ['Mirror']

  c_0vals = [100]# c_0val is the _proportion_ of total values set as the minimum leaf size 
  # a value of 100 means that minimum leaf size is roughly 1/100 of the total number of cells in the dataset
  # the actual training parameter needs to be calculated from this value and the dataset

  alphas = [(0.6,)]
  NeighborFunctions = ["none"]
#  grid = [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
#  alphas = [x for x in itertools.product(grid,grid) if sum(x) <= 1]# alpha is the parameter that weights the entropy and neighbor coherence heuristics
#  NeighborFunctions = ["spatial","temporal"]

#  alphas = [(x) for x in grid]# alpha is the parameter that weights the entropy and neighbor coherence heuristics
#  NeigborFunctions = ["none"]

  thetas = [0.7] # theta is the classification parameter
  
  splitRes = 50 
  # splitRes specifies how many splits are considered among each parameter at each tree node these 
  # splits are selected uniformly according to value distribution (e.g. with 100 splits you get 0th percentile value, 1st percentile value, 2nd percentile value, etc.)
  # a very high value (e.g. 10,000,000) will cause the training to evaluate every potential split. 
  # once every potential split is being evaluated, increasing splitRes won't affect the result or runtime of the algorithm.


  experimentData = [x for x in itertools.product(events,neighborhoods,datasets,waves,balances)]
  experimentDataAndC_0Vals = [x for x in itertools.product(experimentData,c_0vals)]

  trainingParamSets = [x for x in itertools.product(alphas,thetas)]
#  trainingParamSets.append(((0.0,0.0),1.1))# add baseline experiment
#  trainingParamSets.append(((0.0,),1.1))# add baseline experiment
# this value of alpha/theta will result in a pure entropy-based classification tree

  #-----------------------
  # end parameter setup
  #-----------------------

  for experiment,cv in experimentDataAndC_0Vals:
   S_train,S_test = readData(*experiment)
   cells = S_train[0]
   cells2 = S_test[0]
   c_0 = max(len(cells)//cv,1)
   
   e,n,d,w,b = experiment
   fileBase = "results/"+"_".join([str(e),str(n),str(d),"-".join(w),'c_0='+str(c_0),'balance='+str(b)])
   constants = [(experiment,cv,S_train,S_test,c_0,splitRes,NeighborFunctions,fileBase,skipTOs,timeout)]
   runs = [x for x in itertools.product(constants,trainingParamSets)]
   incompleteRuns = []
   for run in runs:
    constants,trainingParams = run
    alpha,theta = trainingParams
    strAlpha = str(alpha).replace('(','[').replace(')',']').replace(', ','-')
    treefile = "_".join([fileBase,'alpha='+strAlpha])+".tree"
    resultsfile = "_".join([fileBase,'alpha='+strAlpha,'theta='+str(theta)])+".results"
    if os.path.exists(resultsfile) or (skipTOs and os.path.exists(resultsfile+'TO')):
     print 'already ran this',resultsfile
    else:
     incompleteRuns.append(run)



   if pooling:
     p = Pool(4) #TODO: fix magic number
     p.map(parallelized_component,incompleteRuns)
   else:
     for run in incompleteRuns:
      parallelized_component(run)

def parallelized_component(run):
    constants,y = run
    experiment,cv,S_train,S_test,c_0,splitRes,NeighborFunctions,fileBase,skipTOs,timeout = constants
    e,n,d,w,b = experiment    
    alpha,theta = y

    strAlpha = str(alpha).replace('(','[').replace(')',']').replace(', ','-')
    treefile = "_".join([fileBase,'alpha='+strAlpha])+".tree"
    resultsfile = "_".join([fileBase,'alpha='+strAlpha,'theta='+str(theta)])+".results"
    
    print 'running',resultsfile
        
    if sum(alpha) > 1:
     raise Exception('invalid alpha')

    signal.signal(signal.SIGALRM,handler)
    signal.alarm(timeout) # timeout value of zero disables alarm
    try:
       TP,FP,TN,FN = SDT.SDT_Learn(S_train,S_test,alpha,c_0,theta,splitRes,treefile,NeighborFunctions)
       didTimeout = False
    except MyTimeoutException:
       didTimeout = True
       resultsfile = resultsfile+'TO'
    signal.alarm(0)
    if didTimeout:
       print 'experiment ',constants,y,'timed out'
       TP = 'TO'
       FP = 'TO'
       TN = 'TO'
       FN = 'TO'
       ACC = 'TO'
       PREC = 'TO'
       REC = 'TO'
    else:
       ACC = 100*(TP+TN)/(TP+TN+FP+FN) 
       if TP+FP != 0:
         PREC = 100*(TP)/(TP+FP)
       else:
         PREC = 0
       if TP+FN != 0:
         REC = 100*TP/(TP+FN)
       else:
         REC = 0
    s = "".join([
                  'event:',str(e),'\n',
                  'neighborhood:',str(n),'\n',
                  'dataset:',str(d),'\n',
                  'alpha:',str(alpha),'\n',
                  'c_0:',str(c_0),'\n',
                    'theta:',str(theta),'\n',
                  'balance:',str(b),'\n',
                  ' ','\n',
                  'TP: ',str(TP),'\n',
                  'FP: ',str(FP),'\n',
                  'TN: ',str(TN),'\n',
                  'FN: ',str(FN),'\n',
                  'accuracy: ',str(ACC),'%\n',
                  'precision: ',str(PREC),'%\n',
                  'recall: ',str(REC),'%\n',
                  ' ','\n',
                  ' ','\n',
                  ' ','\n'])
    with open(resultsfile,'w') as f:
        f.write(s)


cProfile.run('testing()')
#testing()
email = False
if email:
 # Create a text/plain message
 msg = MIMEText('done!')
 me = 'CBSIR'
 you = 'benefluence@gmail.com'
 msg['Subject'] = 'Solar Spatial Decision tree experiments'
 msg['From'] = me
 msg['To'] = you
 s = smtplib.SMTP('localhost')
 s.sendmail(me, [you], msg.as_string())
 s.quit()
