from __future__ import division
import SDT
import cProfile
from readData import read_data
import experimentBuilder as EX
import itertools
from DecisionTree import TreeNode


#treefile = 'results/FL_rook_3DAYDEMO_0171_c_0=14_balance=Mirror_alpha=[0.8-0.2].tree'
#treefile = 'results/SG_rook_3DAYDEMO_0193_c_0=9_balance=Mirror_alpha=[0.0-0.0].tree'
def stuff():
#  events = ['FL','SG','AR','CH']
#  events = ['SG']
  events = ['AR']
#  events = ['FL','SG','FI','CH','AR','SS']
#  neighborhoods = ['rook','queen','rooktemp']
#  neighborhoods = ['rook','rooktemp','rooktemplong']
  neighborhoods = ['rook']
  datasets = ['1DAY']

  thetas = [0.7] # theta is the classification parameter

  grid = [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
  alphas = [x for x in itertools.product(grid,grid) if sum(x) <= 1]
#  alphas = [(0.3,0.3),(0.6,0.3),(0.3,0.6)]
#  alphas = [(0.3,0.3)]

#  waves = [['0193'],['0171'],['0094']]
  waves = [['0193']]
#  balances = ['Mirror','Duplication','Random']
  balances = ['Mirror']
  c_0Dict = dict([( ('AR','1DAY'    ),    40 ),
                  ( ('SG','3DAYDEMO'),     9 ),
                  ( ('AR','3DAYDEMO'),   111 )])
  X = [x for x in itertools.product(events,neighborhoods,datasets,waves,balances,alphas)]
  for event,neighborhood,dataset,wave,balance,alpha in X:
    alphastr = str(alpha).replace(',','-').replace('(','[').replace(')',']').replace(' ','')
    wavestr = wave[0]
    c_0 = c_0Dict[(event,dataset)]
    treefile = 'results/'+'_'.join([event,neighborhood,dataset,wavestr,'c_0='+str(c_0),'balance='+balance,'alpha='+alphastr])+'.tree'
    Tree = TreeNode('dummy')
    with open(treefile) as f:
     Tree.load(f)
  
  #  print str(Tree)
    print event,neighborhood,dataset,wave,balance,alpha
    S = Tree.size()
    print 'size:', S
    print 'balance:', Tree.balance()
    print 'splits:', Tree.total_splits_evaluated()
    TBSR = Tree.total_best_split_runtime()
    print 'total time:', TBSR
    print 'avg time:', TBSR/((S-1)/2)
    print
stuff()
