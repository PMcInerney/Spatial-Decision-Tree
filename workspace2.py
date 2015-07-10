from __future__ import division
import SDT
import cProfile
from readData import readData
import experimentBuilder as EX
import NeighborGraph
import itertools
from DecisionTree import TreeNode
from collections import Counter


def stuff():
  treefileA = 'results/AR_rook_1DAY_0193_c_0=40_balance=Mirror_alpha=[0.0-0.0].tree'
  treefileB = 'hopefullyslowerresults/AR_rook_1DAY_0193_c_0=40_balance=Mirror_alpha=[0.0-0.0].tree'
  for treefile in [treefileA,treefileB]:
    Tree = TreeNode('dummy')
    with open(treefile) as f:
     Tree.load(f)
    print treefile
    S = Tree.size()
    print 'size:', S
    print 'balance:', Tree.balance()
    print 'splits:', Tree.totalSplitsEvaluated()
    TBSR = Tree.totalBestSplitRuntime()
    print 'total time:', TBSR
    print 'avg time:', TBSR/((S-1)/2)
    print

def stuff2():
  print 'looking at the value distributions of the different parameters'
  S_train,S_test = readData('AR',neighborhood='rook',dataset='1DAY',waves=['0094'],balanceOption = 'Mirror')
  G = NeighborGraph.NeighborGraph(S_train)

  for p in G.F: # for each parameter
    l = [pix[p] for pix in G.pixels] # grab the pixels
    print p
    print 'Max:',max(l)
    print 'Min:',min(l)
    print 'Avg:',sum(l)/len(l)
    print 'Most Common:',Counter(l).most_common(10)
    print

#  print len(G.pixels)
#  for p in G.F:      # for each parameter
#    s = set()           # build a set of unique values
#    for pix in G.pixels:
#      s.add(pix[p])
#    print p,len(s)

stuff2()
