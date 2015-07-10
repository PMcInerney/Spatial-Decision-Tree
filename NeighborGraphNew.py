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
        self.entropy = -sum(x/totalCounts*math.log(x/totalCounts,2) if not x == 0 else 0 for x in orderedCounts)

        summ = 0
        for p in self.F:      # for each parameter
          s = set()           # build a set of unique values
          for pix in pixels:
            s.add(pix[p])
          summ+=len(s)        # add up the set lengths
        self.numSplits = summ


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
            derp = dict((x['id'],i) for i,x in enumerate(featureSortedPixels))
            
            derpRef = [ [  derp[n['id']] for n in self.Hadj[x['id']]] for x in featureSortedPixels]
            OHN = [len(self.Hadj[pix['id']]) for pix in featureSortedPixels]
            B = [0]*len(OHN) # B is the counts of Neighbors for each cell in the initially empty partition. 
                             #They all start at zero, and increase as cells are moved to the partition
            step = max( len(featureSortedPixels)//splitRes , 1 )
            featureValues = [pix[feature] for pix in featureSortedPixels[::step]]
            featureValues = sorted(list(set(featureValues)))

            A_counts = self.counts.copy() # counts of each class (we're dealing with binary classification, so this will be, e.g., 'AR' or 'null')
            B_counts = dict((key,0) for key in A_counts)
            n1 = self.size()
            n2 = 0
            thresholdPix = featureSortedPixels[0]
            NSARS = [1]*len(OHN) # used to store NSARS for reuse on different thresholds
                                     # If no partition is made, all NSARS are 1, thus the initialization
                                     # remember: NSAR is the ratio of (homogenous neighbors before):(homogenous neighbors after)
            totalNSAR = len(OHN)
            for value in featureValues[:-1]: # if we partition on final value, we may not separate at all
                changedPix = set()
                # first we move all of the cells from A to B that are above the new value
                # we tag as 'need to update' all the cells we move, as well as their neighbors
                while thresholdPix[feature] <= value: # we iterate through the potential split values
                    A_counts[thresholdPix['class']] -= 1
                    B_counts[thresholdPix['class']] += 1
                    if OHN[n2] > 0: # if the cell has no neighbors, no calculation is needed; its NSAR remains 1
                      changedPix.add(n2)
                      newNSAR = (B[n2])/OHN[n2]
                      totalNSAR = totalNSAR - NSARS[n2]+newNSAR
                      NSARS[n2]= newNSAR
                    for N in derpRef[n2]: # for each neighbor
                      if OHN[N] > 0:
                        B[N] += 1 # increment the 'Neighbors in B' count
                        changedPix.add(N)
                        newNSAR = B[N]/OHN[N] if N <= n2 else (OHN[N]-B[N])/OHN[N]
                        totalNSAR = totalNSAR - NSARS[N]+newNSAR
                        NSARS[N]= newNSAR
                    n1 -= 1 # size of low partition
                    n2 += 1 # size of high partition
                    thresholdPix = featureSortedPixels[n2] # n2 can be looked at as an iterator here, as it increases by exactly 1 each loop
                
                E1 = -sum(x/n1*math.log(x/n1,2) if not x == 0 else 0 for x in A_counts.values())
                E2 = -sum(x/n2*math.log(x/n2,2) if not x == 0 else 0 for x in B_counts.values())
                Eprime = n1/(n1+n2)*E1+n2/(n1+n2)*E2
                IG = E-Eprime
                
                # rather than using the average NSAR, we save a little time by using the 
                # total NSAR and multiplying information gain by the number of cells to preserve relative weighting
                SIG = (1-sum(alpha))*self.size()*IG + sum(x*y for x,y in zip(alpha,[totalNSAR])) # weighted sum of IG and avg_NSARs
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
          
