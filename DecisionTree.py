class TreeNode:
    def __init__(self,classification):
        self.testCondition = None # no test condition indicates leaf node
        # example test condition:
        # testcondition = ('entropy',1.1) 
        self.LeftChild = None 
        self.RightChild = None
        # It's a binary decision tree, so every node will, barring code errors, have either two or zero children
        self.classification = classification
        self.trainingSplits = 'Unknown'
        self.trainingCells = 'Unknown'
        self.bestSplitRuntime = 'Unknown'
    
    def setTimingData(self,a,b,c):
        self.trainingSplits = a
        self.trainingCells = b
        self.bestSplitRuntime = c


    def save(self,f): # f is an open file
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
       currentNode = toProcess.pop()
       if currentNode.testCondition == None:
            f.write(','.join(['leaf',currentNode.classification,str(currentNode.trainingSplits),str(currentNode.trainingCells),str(currentNode.bestSplitRuntime)])+"\n")
       else:
            f.write(','.join(['internal',currentNode.classification,str(currentNode.testCondition[0]),str(currentNode.testCondition[1]),str(currentNode.trainingSplits),str(currentNode.trainingCells),str(currentNode.bestSplitRuntime)])+"\n")
            toProcess.append(currentNode.RightChild)
            toProcess.append(currentNode.LeftChild)

    def load(self,f): # f is an open file
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
       currentNode = toProcess.pop()
       line = f.readline()[:-1] # nix newline
       #print line
       lineParts = line.split(',')
       nodeType = lineParts[0]
       currentNode.classification = lineParts[1]
       if nodeType == 'internal':
          currentNode.testCondition = (lineParts[2],float(lineParts[3]))
          currentNode.trainingSplits = int(lineParts[4])
          currentNode.trainingCells = int(lineParts[5])
          currentNode.bestSplitRuntime = float(lineParts[6])
          currentNode.LeftChild = TreeNode('dummy')
          currentNode.RightChild = TreeNode('dummy')
          toProcess.append(currentNode.RightChild)
          toProcess.append(currentNode.LeftChild)
       else: # leaf
          currentNode.testCondition = None
          currentNode.LeftChild = None
          currentNode.RightChild = None

    def __str__(self):
     depth = 0
     slist = []
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
        currentNode = toProcess.pop()
        if currentNode == 'surface':
          depth -= 1
        elif currentNode.testCondition == None:
          slist.append(depth*' '+currentNode.classification)
        else:
          slist.append(depth*' '+','.join([str(currentNode.trainingSplits)+'Splits',str(currentNode.trainingCells)+'Cells',str(currentNode.bestSplitRuntime)+'s',str(currentNode.testCondition)]))
          toProcess.append('surface')
          toProcess.append(currentNode.RightChild)
          toProcess.append(currentNode.LeftChild)
          depth+=1
     return "\n".join(slist)
    
    def balance(self): # use Colless imbalance measure. not sure if it's actually a good one for decision trees (originated in phylogeny), but worth looking at
     treesizes = []
     IB = 0
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
        currentNode = toProcess.pop()
        if currentNode == 'surface':
          A = treesizes.pop()
          B = treesizes.pop()
          treesizes.append(A+B+1)
          IB += abs(B-A)
        elif currentNode.testCondition == None: # leaf node
          treesizes.append(1)
        else: # non-leaf node
          toProcess.append('surface')
          toProcess.append(currentNode.RightChild)
          toProcess.append(currentNode.LeftChild)
     return IB

    def totalSplitsEvaluated(self):
     T = 0
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
        currentNode = toProcess.pop()
        if currentNode.trainingSplits != 'Unknown':
          T += currentNode.trainingSplits
        if currentNode.testCondition != None:
          toProcess.append(currentNode.RightChild)
          toProcess.append(currentNode.LeftChild)
     return T

    def totalBestSplitRuntime(self):
     T = 0
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
        currentNode = toProcess.pop()
        if currentNode.bestSplitRuntime != 'Unknown':
          T += currentNode.bestSplitRuntime
        if currentNode.testCondition != None:
          toProcess.append(currentNode.RightChild)
          toProcess.append(currentNode.LeftChild)
     return T

    def averageBestSplitRuntime(self):
     T = 0
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
        currentNode = toProcess.pop()
        if currentNode.bestSplitRuntime != 'Unknown':
          T += currentNode.bestSplitRuntime
        if currentNode.testCondition != None:
          toProcess.append(currentNode.RightChild)
          toProcess.append(currentNode.LeftChild)
     return T

    def size(self):
     S = 0
     toProcess = list()
     toProcess.append(self) # append root
     while not len(toProcess) == 0:
        currentNode = toProcess.pop()
        S+=1
        if currentNode.testCondition != None:
          toProcess.append(currentNode.RightChild)
          toProcess.append(currentNode.LeftChild)
     return S

