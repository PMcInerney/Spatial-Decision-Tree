from DecisionTree import TreeNode
from NeighborGraph import NeighborGraph
import cPickle as pickle
import os
import logging
import random
import time

def SDT_Learn(S_train,S_test,alpha,c_0,theta,splitRes,treefile,NeighborFunctions, loggingLevel = 0,randomGuessing = False):
#Input:
# S_train: list of pixel objects
# S_test: list of pixel objects
# alpha: weight vector for neighborhood autocorrelation terms in SIG measure
# alphas are affine weights, they must be between zero and one, and also sum to between zero and one
# c_0: minimum leaf node size
# theta: neighborhood wise test ratio
# randomGuessing is a simple flag that skips training and tests by random, evenly distributed guessing

# Phase I: Training
  if not randomGuessing: # skip training when random Guessing
     if not os.path.exists(treefile) or treefile == 'temp.tree': 
       G = NeighborGraph(S_train)
       Tree = SDT_Train(G, alpha, c_0,splitRes,NeighborFunctions)
       with open(treefile,'w') as f:
         Tree.save(f)
     else:
       print 'tree exists'
       Tree = TreeNode('dummy')
       with open(treefile) as f:
         Tree.load(f)
  else: # build the list of options to guess from
    Tree = TreeNode('dummy')
    cells, Hadj, Iadj = S_train
    randomGuessing = list(set(x['class'] for x in cells))
    print randomGuessing
#Phase II: Prediction
  pixels,Hadj,Iadj = S_test
  TP = 0
  FP = 0
  TN = 0
  FN = 0
  for pix in pixels:
       s = pix
       NS =  Hadj[pix['id']]+Iadj[pix['id']]
       DTOutput = SDT_Predict(Tree, s, NS, theta, randomGuessing = randomGuessing)
       if DTOutput == s['class']:
         if DTOutput == 'null':
           TN += 1
         else :
           TP += 1
       else:
         if DTOutput == 'null':
           FN += 1
         else :
           FP += 1
  return TP,FP,TN,FN

def SDT_Train(G,alpha,c_0,splitRes,NeighborFunctions):
# G: neighborhood graph of training pixels
# G.F: feature set of neighborhood graph nodes
# G.C: class label set of neighborhood graph nodes
# alpha: weight vector for neighborhood autocorrelation terms in SIG measure
# alphas are affine weights, they must be between zero and one, and also sum to between zero and one
# c_0: minimum decision tree node size

# root of a spatial decision tree model
     treeRoot = TreeNode(G.majorClass())
     toProcess = list()
     toProcess.append((treeRoot,G)) # append root
     while not len(toProcess) == 0: # this functions essentially recursively, progressing down each branch of the building tree in turn
       currentNode,current_subgraph = toProcess.pop()
       if current_subgraph.size() < c_0 or current_subgraph.uniform(): #if remaining examples few or uniform
          logging.debug('making leaf')
          # leave alone
       else:
          logging.debug('growing tree')
          #figure out bestSplit
          t1 = time.time()
          ##################
          #-----------------
          split = current_subgraph.bestSplit(alpha,splitRes,NeighborFunctions)
          #--this function is the heart of the code
          ##################
          t2 = time.time()
          runTime = t2-t1
          logging.info('bestSplit function took '+str(runTime)+' seconds')
          if split is None: 
               logging.debug('Growing won\'t help, making leaf')
               pass
          else:
               feature_0,delta_0 = split
               currentNode.setTimingData(current_subgraph.numSplits,current_subgraph.size(),runTime)
               logging.debug("splitting on", feature_0, delta_0)
               #  Create internal node I with test feature_0 <= delta_0
               G1,G2 = current_subgraph.partition(feature_0,delta_0)
               currentNode.testCondition = (feature_0,delta_0)
               currentNode.LeftChild = TreeNode(G1.majorClass())
               currentNode.RightChild = TreeNode(G2.majorClass())
               toProcess.append((currentNode.RightChild,G2))
               toProcess.append((currentNode.LeftChild,G1))
     return treeRoot

def SDT_Predict(treeRootNode , s, NS, theta,randomGuessing = False):
#Input:
# treeRootNode : root node of an SDT model
# s: a test pixel
# NS: neighboring pixels of s
# theta: neighborhood wise test ratio
  if randomGuessing:
# if randomGuessing is not false, it is assumed to contain a list of choices from which to select randomly
    return random.sample(randomGuessing,1)[0]    
  else:
     currentNode = treeRootNode
     while currentNode.testCondition is not None: # descend the tree to a leaf node
          parameter, value = currentNode.testCondition
          testResult = s[parameter] <= value
          if len(NS) == 0:
            neighborTestRatio = 0 # no neighbors, no reason to change
          else:
            neighborTestRatio = sum(1 for x in NS if (x[parameter] <= value) != testResult)/len(NS)
          if neighborTestRatio >= theta:
               testResult = not testResult # succumb to peer pressure
          if testResult:
               currentNode = currentNode.LeftChild
          else:
               currentNode = currentNode.RightChild
     return currentNode.classification;
