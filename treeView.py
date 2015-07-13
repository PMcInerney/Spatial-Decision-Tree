from __future__ import division
from DecisionTree import TreeNode


def print_tree(event, neighborhood, dataset, wave, c_0, balance, alpha):
    treefile = 'results/' + '_'.join(
        [event, neighborhood, dataset, wave, 'c_0=' + str(c_0), 'balance=' + balance, 'alpha=' + alpha]) + '.tree'
    tree = TreeNode('dummy')
    with open(treefile) as f:
        tree.load(f)
    print str(tree)


e = 'AR'
n = 'rook'
d = '1DAY'
w = '0193'
c = 40
b = 'Mirror'
alpha = '[0.0-0.0]'
print_tree(e, n, d, w, c, b, alpha)
