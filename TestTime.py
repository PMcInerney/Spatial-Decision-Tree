from __future__ import division
import time
import SDT
import cProfile
from readData import read_data
import itertools
import os.path
import cPickle as pickle
import logging
# python's logging library is used for data output because it allows us to read the output file as it is being
# constructed (i.e. while only some experiments have been run)

logging.basicConfig(format='%(asctime)s:%(message)s', filename='TestTime.log', level=logging.INFO)

# the general form of this script is patterned after 'runExperiments,' with adjustments made for time keeping
# #TODO: see if this should be modified to reduce copypasta

def testing():
    dataFile = 'TestTimeOutput'
    if os.path.exists(dataFile):
        with open(dataFile) as f:
            results = pickle.load(f)
    else:
        results = []
    completedExperiments = [x[0] for x in results]
    #  events = ['FL','SG','AR','CH']
    events = ['SG']
    #  events = ['FL','SG','FI','CH','AR','SS']
    #  neighborhoods = ['rook','queen','rooktemp']
    #  neighborhoods = ['rook','rooktemp','rooktemplong']
    neighborhoods = ['rook']
    datasets = ['1DAY']

    thetas = [0.7]  # theta is the classification parameter

    #  grid = [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
    #  alphas = [x for x in itertools.product(grid,grid) if sum(x) <= 1]
    #  alpha is the parameter that weights the entropy and neighbor
    #  alphas = [(0.3,0.3),(0.6,0.3),(0.3,0.6)]
    alphas = [(0.3, 0.3)]

    NeighborFunctions = ["spatial", "temporal"]

    splitRes = 10000000  # splitRes affects how many splits are considered among each parameter at each tree node
    c_0vals = [100]  # c_0val is the _proportion_ of total values set as the minimum leaf size
    waves = [['0193'], ['0171'], ['0094']]
    #  balances = ['Mirror','Duplication','Random']
    balances = ['Mirror']
    X = [x for x in itertools.product(events, neighborhoods, datasets, waves, balances, c_0vals)]
    Y = [x for x in itertools.product(alphas, thetas)]
    counter = 1
    total = len(X) * len(Y)
    for e, n, d, w, b, cv in X:
        S_train, S_test = read_data(e, neighborhood=n, dataset=d, waves=w, balanceOption=b)
        cells, adj = S_train
        cells2, adj2 = S_test
        c_0 = max(len(cells) // cv, 1)
        for alpha, theta in Y:
            print counter, '/', total
            counter += 1
            parameters = (e, n, d, w, b, c_0, alpha, theta)
            if parameters in completedExperiments:
                print 'already ran:', parameters
            else:
                t1 = time.time()
                if sum(alpha) > 1:
                    raise Exception('invalid alpha')
                treefile = "temp.tree"
                TP, FP, TN, FN = SDT.sdt_learn(S_train, S_test, alpha, c_0, theta, splitRes, NeighborFunctions)
                ACC = 100 * (TP + TN) / (TP + TN + FP + FN)
                if TP + FP != 0:
                    PREC = 100 * (TP) / (TP + FP)
                else:
                    PREC = 0
                if TP + FN != 0:
                    REC = 100 * TP / (TP + FN)
                else:
                    REC = 0
                F1 = 0 if PREC + REC == 0 else (2 * PREC * REC) / (PREC + REC)
                summ = 0
                for p in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']:  # for each parameter
                    s = set()  # build a set of all of the values of that parameter
                    for cell in cells:  # the set data structure will eliminate duplicates
                        s.add(cell[p])  # so its length is the number of distinct values for that
                    summ += len(s)  # parameter
                splits = summ  # add all these together to get the number of potential
                # splits in the dataset
                t2 = time.time()
                runTime = t2 - t1

                strr = "".join([
                    'timestamp',
                    'experiment:', str(parameters), '\n',
                    'numcells: ', str(len(cells)), '\n',
                    'splits:', str(splits), '\n',
                    'Runtime:', str(t2 - t1), '\n'
                                              'F1:', str(F1), '\n',
                    ' ', '\n'])
                logging.debug(strr)
                results.append((parameters, F1, runTime))

            with open(dataFile, 'wb') as f:
                pickle.dump(results, f)

# cProfile.run('testing()')
testing()
