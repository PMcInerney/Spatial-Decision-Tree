from __future__ import division
import math
from collections import Counter
from operator import itemgetter
import logging
class NeighborGraph:

## pixels is a dict of pixel entries
## each pixel entry has feature and class data

    '''derp'''
    def __init__(self,S):
        pixels,Hadj,Iadj = S
        self.pixels = pixels
        self.Hadj = Hadj
        self.Iadj = Iadj
        self.C = set(pix['class'] for pix in pixels)
##        self.F = set(['entropy','mean','stdDev','skewness','kurtosis','TamDir','TamCon','FracDim','RS','Uniformity'])
        self.F = ['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10']
        c = Counter(pix['class'] for pix in self.pixels)
        counts = c.most_common()
        self.counts = dict(counts)
        orderedCounts = [x[1] for x in counts]
        totalCounts = sum(orderedCounts)
        summ = 0
        for p in self.F:      # for each parameter
          s = set()           # build a set of unique values
          for pix in pixels:
            s.add(pix[p])
          summ+=len(s)        # add up the set lengths
        self.numSplits = summ
        self.entropy = -sum(x/totalCounts*math.log(x/totalCounts,2) if not x == 0 else 0 for x in orderedCounts)


    def size(self):
        return len(self.pixels)
    
    def majorClass(self):
        c = Counter(pix['class'] for pix in self.pixels)
        return c.most_common(1)[0][0]

    def uniform(self):
        return len(self.C) == 1
    
    def bestSplit(self,alpha,splitRes,NeighborFunctions):
        if len(alpha) != len(NeighborFunctions):
          raise Exception("dimension mismatch in Neighborhood weights\n"+str(alpha)+"\n"+str(NeighborFunctions))
        E = self.entropy
        bestSplit_out = None
        maxSIG = 0
        for feature in self.F:
            featureSortedPixels = sorted(self.pixels, key = itemgetter(feature))
            step = max( len(featureSortedPixels)//splitRes , 1 )
            featureValues = [pix[feature] for pix in featureSortedPixels[::step]]
            featureValues = sorted(list(set(featureValues)))
            A_counts = self.counts.copy()
            B_counts = dict((key,0) for key in A_counts)
            n1 = self.size()
            n2 = 0
            thresholdPix = featureSortedPixels[0]
            updateSet = set() # whenever a cell is moved from one partition to the other, we need to recalculate the cell's NSAR
            updateList = []   # as the transition will cause it to gain/lose/change neighbors
            NSARS = [dict((key,1) for key in self.Hadj) for func in NeighborFunctions] # used to store NSARS for reuse on different thresholds
                                                        # If no partition is made, all NSARS are 1, thus the initialization
                                                        # remember: NSAR is the ratio of (homogenous neighbors before):(homogenous neighbors after)
            TotalNSAR = [len(NSARS[0]) for func in NeighborFunctions]
            for value in featureValues[:-1]: # if we partition on final value, we may not separate at all
                # first we move all of the cells from A to B that are above the new value
                # we tag as 'need to update' all the cells we move, as well as their neighbors
                while thresholdPix[feature] <= value: # we iterate through the potential split values
                    if thresholdPix['id'] not in updateSet:
                        updateSet.add(thresholdPix['id'])
                        updateList.append(thresholdPix)
                    n1 -= 1 # size of low partition
                    n2 += 1 # size of high partition
                    A_counts[thresholdPix['class']] -= 1
                    B_counts[thresholdPix['class']] += 1
                    
                    # if we assume neighborship is symmetric, then we know where to look to add/remove neighbor relations
                    # if neighborship _isn't_ symmetric, do we even know we would want to remove? probably, still
                    # if given assymetry environment, 'is neighbor of' data would probably be valuable. Wait on it for now
                        
                    for N in self.Hadj[thresholdPix['id']]:
                       if N['id'] not in updateSet:
                           updateSet.add(N['id'])
                           updateList.append(N)
                    thresholdPix = featureSortedPixels[n2] # n2 can be looked at as an iterator here, as it increases by exactly 1 each loop
                
                #information gain calculation
                
                E1 = -sum(x/n1*math.log(x/n1,2) if not x == 0 else 0 for x in A_counts.values())
                E2 = -sum(x/n2*math.log(x/n2,2) if not x == 0 else 0 for x in B_counts.values())
                Eprime = n1/(n1+n2)*E1+n2/(n1+n2)*E2
                IG = E-Eprime
                
                #NSAR calculation
                
                if any([x > 0 for x in alpha]): # if alpha is zero vector NSAR doesn't matter
                  for pix in updateList: # we don't want to go through every cell, just the ones that need to be updated
                      oldHomogenousNeighbors = self.Hadj[pix['id']]
                      newHomogenousNeighbors = [x for x in self.Hadj[pix['id']] if x[feature] <= value] 

                      for i,func in enumerate(NeighborFunctions):
                        if func == "spatial":
                          funcOHN = [x for x in oldHomogenousNeighbors if pix['id'][0] == x['id'][0]] # spatial neighbors are the ones from the same image
                          funcNHN = [x for x in newHomogenousNeighbors if pix['id'][0] == x['id'][0]]
                        elif func == "temporal":
                          funcOHN = [x for x in oldHomogenousNeighbors if not pix['id'][0] == x['id'][0]] # temporal neighbors are the ones _not_ from the same image
                          funcNHN = [x for x in newHomogenousNeighbors if not pix['id'][0] == x['id'][0]]
                        elif func == "none":
                          funcOHN = [x for x in oldHomogenousNeighbors] # none means take all neighbors without any filter
                          funcNHN = [x for x in newHomogenousNeighbors]
                        else:
                          raise Exception('Unsupported Neighbor Function: '+ func)
                        if len(funcOHN) == 0:
                            NSAR = 1 # If there are no old neighbors, NSAR is one
                        else:
                            NSAR = len(funcNHN)/len(funcOHN)
                        TotalNSAR[i] = TotalNSAR[i] - NSARS[i][pix['id']] + NSAR # 
                        NSARS[i][pix['id']] = NSAR
                avg_NSAR = [x/self.size() for x in TotalNSAR]

                updateSet = set()
                updateList = [] # why is the updateList reinitialized every partition value, but the set is not?
                SIG = (1-sum(alpha))*IG + sum(x*y for x,y in zip(alpha,avg_NSAR)) # weighted sum of IG and avg_NSARs
                if SIG >= maxSIG:
                    maxSIG = SIG
                    bestSplit_out = feature,value
        return bestSplit_out

    def partition(self,parameter,value):
        pixels1 = []
        pixels2 = []
        Hadj1 = dict()
        Hadj2 = dict()
        Iadj1 = dict()
        Iadj2 = dict()
        for x in self.pixels:
            if x[parameter] <= value:
                pixels1.append(x)
                Hadj1[x['id']] = [pix for pix in self.Hadj[x['id']] if pix[parameter] <= value]
                Iadj1[x['id']] = [pix for pix in self.Iadj[x['id']] if pix[parameter] <= value]
            else:
                pixels2.append(x)
                Hadj2[x['id']] = [pix for pix in self.Hadj[x['id']] if pix[parameter] > value]
                Iadj2[x['id']] = [pix for pix in self.Iadj[x['id']] if pix[parameter] > value]
        G1 = NeighborGraph((pixels1,Hadj1,Iadj1))
        G2 = NeighborGraph((pixels2,Hadj2,Iadj2))
        # we want to partition the graph according to some test
        ## do stuff here 
        #I'm pretty sure object copying is going to be an issue
        return (G1,G2)
    
    def checkSplitIG(self,split):
          # this only tests on entropy
          parameter,value = split
          A = []
          B = []
          for x in self.pixels:
            if x[parameter] <= value:
              B.append(x)
            else:
              A.append(x)
          Tot = len(self.pixels)
          Pos = len([x for x in self.pixels if x['class'] == 'null'])
          Neg = len([x for x in self.pixels if x['class'] != 'null'])
          RPos = Pos/Tot
          RNeg = Neg/Tot
          logPos = math.log(RPos,2) if RPos > 0 else 0
          logNeg = math.log(RNeg,2) if RNeg > 0 else 0
          E = -RPos*logPos-RNeg*logNeg

          PosA = len([x for x in A if x['class'] == 'null'])
          NegA = len([x for x in A if x['class'] != 'null'])
          TotA = len(A)
          RPosA = PosA/TotA
          RNegA = NegA/TotA
          logPosA = math.log(RPosA,2) if RPosA > 0 else 0
          logNegA = math.log(RNegA,2) if RNegA > 0 else 0
          EA = -RPosA*logPosA-RNegA*logNegA

          PosB = len([x for x in B if x['class'] == 'null'])
          NegB = len([x for x in B if x['class'] != 'null'])
          TotB = len(B)
          RPosB = PosB/TotB
          RNegB = NegB/TotB
          logPosB = math.log(RPosB,2) if RPosB > 0 else 0
          logNegB = math.log(RNegB,2) if RNegB > 0 else 0
          EB = -RPosB*logPosB-RNegB*logNegB

          Eprime = (EA*TotA+EB*TotB)/Tot
          IG = E-Eprime
          return IG
          
