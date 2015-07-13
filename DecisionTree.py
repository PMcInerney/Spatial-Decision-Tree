class TreeNode:
    def __init__(self, classification):
        self.testCondition = None  # no test condition indicates leaf node
        # example test condition:
        # test_condition = ('entropy',1.1)
        self.LeftChild = None
        self.RightChild = None
        # It's a binary decision tree, so every node will, barring code errors, have either two or zero children
        self.classification = classification
        self.trainingSplits = 'Unknown'
        self.trainingCells = 'Unknown'
        self.bestSplitRuntime = 'Unknown'

    def set_timing_data(self, a, b, c):
        self.trainingSplits = a
        self.trainingCells = b
        self.bestSplitRuntime = c

    def save(self, f):  # f is an open file
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            if current_node.testCondition is None:
                f.write(','.join(['leaf', current_node.classification, str(current_node.trainingSplits),
                                  str(current_node.trainingCells), str(current_node.bestSplitRuntime)]) + "\n")
            else:
                f.write(','.join(['internal', current_node.classification, str(current_node.testCondition[0]),
                                  str(current_node.testCondition[1]), str(current_node.trainingSplits),
                                  str(current_node.trainingCells), str(current_node.bestSplitRuntime)]) + "\n")
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)

    def load(self, f):  # f is an open file
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            line = f.readline()[:-1]  # nix newline
            # print line
            line_parts = line.split(',')
            node_type = line_parts[0]
            current_node.classification = line_parts[1]
            if node_type == 'internal':
                current_node.testCondition = (line_parts[2], float(line_parts[3]))
                current_node.trainingSplits = int(line_parts[4])
                current_node.trainingCells = int(line_parts[5])
                current_node.bestSplitRuntime = float(line_parts[6])
                current_node.LeftChild = TreeNode('dummy')
                current_node.RightChild = TreeNode('dummy')
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)
            else:  # leaf
                current_node.testCondition = None
                current_node.LeftChild = None
                current_node.RightChild = None

    def __str__(self):
        depth = 0
        slist = []
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            if current_node == 'surface':
                depth -= 1
            elif current_node.testCondition is None:
                slist.append(depth * ' ' + current_node.classification)
            else:
                slist.append(depth * ' ' + ','.join(
                    [str(current_node.trainingSplits) + 'Splits', str(current_node.trainingCells) + 'Cells',
                     str(current_node.bestSplitRuntime) + 's', str(current_node.testCondition)]))
                to_process.append('surface')
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)
                depth += 1
        return "\n".join(slist)

    def balance(
            self):  # use Colless imbalance measure. not sure if it's actually a good one for decision trees (originated in phylogeny), but worth looking at
        tree_sizes = []
        IB = 0
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            if current_node == 'surface':
                A = tree_sizes.pop()
                B = tree_sizes.pop()
                tree_sizes.append(A + B + 1)
                IB += abs(B - A)
            elif current_node.testCondition is None:  # leaf node
                tree_sizes.append(1)
            else:  # non-leaf node
                to_process.append('surface')
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)
        return IB

    def total_splits_evaluated(self):
        T = 0
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            if current_node.trainingSplits != 'Unknown':
                T += current_node.trainingSplits
            if current_node.testCondition is not None:
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)
        return T

    def total_best_split_runtime(self):
        T = 0
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            if current_node.bestSplitRuntime != 'Unknown':
                T += current_node.bestSplitRuntime
            if current_node.testCondition is not None:
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)
        return T

    @property
    def average_best_split_runtime(self):
        T = 0
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            if current_node.bestSplitRuntime != 'Unknown':
                T += current_node.bestSplitRuntime
            if current_node.testCondition is not None:
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)
        return T

    def size(self):
        S = 0
        to_process = list()
        to_process.append(self)  # append root
        while not len(to_process) == 0:
            current_node = to_process.pop()
            S += 1
            if current_node.testCondition is not None:
                to_process.append(current_node.RightChild)
                to_process.append(current_node.LeftChild)
        return S
