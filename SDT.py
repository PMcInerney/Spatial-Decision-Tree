from DecisionTree import TreeNode
from NeighborGraph import NeighborGraph
import os
import logging
import time


def sdt_learn(s_train, s_test, alpha, c_0, theta, split_res, neighbor_functions, logging_level=0):
    """Input:
    S_train: list of cell objects
    S_test: list of cell objects
    alpha: weight vector for neighborhood autocorrelation terms in SIG measure
    alphas are affine weights, they must be between zero and one, and also sum to between zero and one
    c_0: minimum leaf node size
    theta: neighborhood-wise test ratio
    """

    # Phase I: Training
    g = NeighborGraph(s_train)
    tree = sdt_train(g, alpha, c_0, split_res, neighbor_functions)
    # Phase II: Prediction
    cells, adj_h, adj_i = s_test
    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    for cell in cells:
        s = cell
        neighbors = adj_h[cell['id']] + adj_i[cell['id']]
        tree_output = sdt_predict(tree, s, neighbors, theta)
        if tree_output == s['class']:
            if tree_output == 'null':
                true_negative += 1
            else:
                true_positive += 1
        else:
            if tree_output == 'null':
                false_negative += 1
            else:
                false_positive += 1
    return true_positive, false_positive, true_negative, false_negative


def sdt_train(G, alpha, c_0, split_res, neighbor_functions):
    # G: neighborhood graph of training pixels
    # G.F: feature set of neighborhood graph nodes
    # G.C: class label set of neighborhood graph nodes
    # alpha: weight vector for neighborhood autocorrelation terms in SIG measure
    # alphas are affine weights, they must be between zero and one, and also sum to between zero and one
    # c_0: minimum decision tree node size

    # root of a spatial decision tree model
    tree_root = TreeNode(G.major_class)
    to_process = list()
    to_process.append((tree_root, G))  # append root
    while not len(to_process) == 0:
        # this functions essentially recursively, progressing down each branch of the building tree in turn
        current_node, current_subgraph = to_process.pop()
        if current_subgraph.size() < c_0 or current_subgraph.uniform:  # if remaining examples few or uniform
            logging.debug('making leaf')
            # leave alone
        else:
            logging.debug('growing tree')
            # figure out best_split
            t1 = time.time()
            ##################
            # -----------------
            split = current_subgraph.best_split(alpha, split_res, neighbor_functions)
            # --this function is the heart of the code
            ##################
            t2 = time.time()
            runtime = t2 - t1
            logging.info('best_split function took ' + str(runtime) + ' seconds')
            if split is None:
                logging.debug('Growing won\'t help, making leaf')
                pass
            else:
                feature_0, delta_0 = split
                current_node.set_timing_data(current_subgraph.numSplits, current_subgraph.size(), runtime)
                logging.debug("splitting on", feature_0, delta_0)
                #  Create internal node I with test feature_0 <= delta_0
                G1, G2 = current_subgraph.partition(feature_0, delta_0)
                current_node.testCondition = (feature_0, delta_0)
                current_node.LeftChild = TreeNode(G1.major_class)
                current_node.RightChild = TreeNode(G2.major_class)
                to_process.append((current_node.RightChild, G2))
                to_process.append((current_node.LeftChild, G1))
    return tree_root


def sdt_predict(tree_root_node, s, neighbors, theta):
    # Input:
    # treeRootNode : root node of an SDT model
    # s: a test pixel
    # NS: neighboring pixels of s
    # theta: neighborhood wise test ratio
    current_node = tree_root_node
    while current_node.testCondition is not None:  # descend the tree to a leaf node
        parameter, value = current_node.testCondition
        test_result = s[parameter] <= value
        if len(neighbors) == 0:
            neighbor_test_ratio = 0  # no neighbors, no reason to change
        else:
            neighbor_test_ratio = sum(1 for x in neighbors if (x[parameter] <= value) != test_result) / len(neighbors)
        if neighbor_test_ratio >= theta:
            test_result = not test_result  # succumb to peer pressure
        if test_result:
            current_node = current_node.LeftChild
        else:
            current_node = current_node.RightChild
    return current_node.classification
