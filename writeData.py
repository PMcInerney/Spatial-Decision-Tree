from __future__ import division
import sys
import os.path

sys.path.append('/data/home/pmcinerney/python')
from SolarCBIRTools import find_grid_cells
import SOLARGenImageList
from parseEventData import parseChainCode, parseBoundingBox
import numpy as np
import random
import csv
from maskFunctions import gridCells, circleMask
import pickle
import itertools
from read_write_cell_data import read_cell_data, write_cell_data

random.seed(42)


def get_image_file(imFileTracker, n):
    try:
        out = imFileTracker[n]
    except KeyError:
        out = 'HERPFLERPDERP'
    return out


def buffer_binmat(matrix):
    # this expands the size of an event to include its surrounding cells
    xs, ys = np.nonzero(matrix)
    for x, y in zip(xs, ys):
        matrix[x + 1, y] = True
        matrix[x - 1, y] = True
        matrix[x, y + 1] = True
        matrix[x, y - 1] = True
    return matrix


def reposition_event(matrix):
    x = random.randint(4, 16)
    y = random.randint(4, 16)
    signx = random.sample([-1, 1], 1)[0]
    signy = random.sample([-1, 1], 1)[0]
    return np.roll(np.roll(matrix, signx * x, axis=1), signy * y, axis=0)


def mirror_event(matrix):
    l = np.min(np.nonzero(matrix)[1])
    newl = 63 - l
    diffl = l - newl
    r = np.max(np.nonzero(matrix)[1])
    newr = 63 - r
    diffr = r - newr
    e = diffl if abs(diffl) < abs(diffr) else diffr
    e -= 1 if e > 0 else -1  # reduce abs(e) by 1
    mirror = np.fliplr(matrix)
    return np.roll(mirror, e, axis=1)


def write_data(circleMask, balanceOption='None'):
    if balanceOption not in ['None', 'Mirror', 'Duplication', 'Random']:
        print balanceOption
        raise Exception('balance option not supported')
    #  events = ['AR','CH','SS','SG','FL','FI']
    events = ['AR', 'CH', 'SG', 'FL']
    neighborhoods = ['rook', 'rooktemp', 'rooktemplong']
    datasets = ['1DAY', '3DAYDEMO']
    waveSets = [['0171'], ['0193'], ['0094']]
    X = [x for x in itertools.product(events, neighborhoods, datasets, waveSets)]
    for e, n, d, w in X:
        write_experiment_data(circleMask, e, n, d, w, balanceOption)


def write_experiment_data(circleMask, eventClass, neighborhood, dataset, waves, balanceOption):
    gridForRandSample = [x for x in itertools.product(range(64), range(64))]  # build a set of cells for picking from
    outputfileTrain = "data/" + "_".join(
        [eventClass, neighborhood, dataset, "-".join(waves), 'balance=' + balanceOption]) + ".train"
    outputfileTest = "data/" + "_".join(
        [eventClass, neighborhood, dataset, "-".join(waves), 'balance=' + balanceOption]) + ".test"
    if not (os.path.exists(outputfileTrain) and os.path.exists(outputfileTest)):
        print eventClass, neighborhood, dataset, waves, balanceOption
        readAttemptData = read_cell_data(eventClass, dataset, waves, balanceOption)
        if readAttemptData != -1:  # read success
            allPixels = readAttemptData
            cellTracker = dict([(x['id'], x) for x in allPixels])
            imFileTracker = dict([(x['id'][0], x['id'][3]) for x in allPixels])
            # we need to know the individual events to generate the balancing filter
            print 'read data successfully'
        else:  # read Failure
            ###################################
            headers, matches = SOLARGenImageList.image_event_matches([eventClass], dataset=dataset, waves=waves)
            print 'matches calculated', eventClass, dataset, waves
            imageCounter = 0
            allPixels = []
            # build a 'what cell is FI' matrix
            if balanceOption == 'None':
                balancingFilter = np.ones([len(matches), 64, 64], dtype=bool)  # keep everything
            else:  # filter will be filled as we process images
                balancingFilter = np.zeros([len(matches), 64, 64], dtype=bool)
            for imageKey in sorted(matches.keys()):  # for every image
                eventBinMat = np.zeros([64, 64], dtype=bool)
                imageBalancingFilter = np.zeros([64, 64], dtype=bool)
                for E in matches[imageKey]:  # for each event in that image
                    cc = parseChainCode(E, headers)
                    if cc == "NA":
                        cc = parseBoundingBox(E, headers)
                    eventLocationMat = find_grid_cells(cc)
                    eventBinMat = np.logical_or(
                        eventBinMat,
                        eventLocationMat)  # combine all the events into one binary matrix for the image
                    bufferedEventLocationMat = buffer_binmat(eventLocationMat)
                    imageBalancingFilter = np.logical_or(
                        imageBalancingFilter,
                         bufferedEventLocationMat)  # add the positive examples to the training set
                    if balanceOption == 'Mirror':
                        mirrorMat = mirror_event(bufferedEventLocationMat)
                        imageBalancingFilter = np.logical_or(
                            imageBalancingFilter,
                            mirrorMat)  # add some negative examples to the training set
                    if balanceOption == 'Duplication':
                        dupMat = reposition_event(bufferedEventLocationMat)
                        imageBalancingFilter = np.logical_or(
                            imageBalancingFilter,
                            dupMat)  # add some negative examples to the training set
                # end of 'for event' loop
                if balanceOption == 'Random':  # randomly undersample negative class
                    numPos = np.sum(eventBinMat)  # calc the number of event cells in this image
                    NegGridCells = [x for x in gridForRandSample if not eventBinMat[x[0], x[1]]]
                    randSampleOfGrid = random.sample(NegGridCells, numPos)  # randomly pick some negative cells
                    for x in randSampleOfGrid:
                        imageBalancingFilter[x] = True
                balancingFilter[imageCounter, :, :] = imageBalancingFilter

                imagePixels = []
                with open(imageKey[0]) as f:  # read the parameter data for this image
                    c = csv.reader(f, dialect='excel-tab')
                    cells = [x for x in c]
                for cell in cells:  # compile data/classification for all cells in image
                    row = int(cell[0]) - 1  # silly juan 1 based index
                    col = int(cell[1]) - 1
                    if not circleMask[row, col]:  # if cell off disk,
                        pass  # do nothing
                    else:  # else
                        s = dict()  # build the cell data structure
                        s['id'] = (imageCounter, row, col, imageKey)
                        if eventBinMat[row, col]:
                            s['class'] = eventClass
                        else:
                            s['class'] = 'null'
                        s['P1'] = float(cell[2])
                        s['P2'] = float(cell[3])
                        s['P3'] = float(cell[4])
                        s['P4'] = float(cell[5])
                        s['P5'] = float(cell[6])
                        s['P6'] = float(cell[7])
                        s['P7'] = float(cell[8])
                        s['P8'] = float(cell[9])
                        s['P9'] = float(cell[10])
                        s['P10'] = float(cell[11])
                        imagePixels.append(s)
                allPixels.extend(imagePixels)
                imageCounter += 1
            # end of images loop
            allPixels = [x for x in allPixels if balancingFilter[x['id'][0], x['id'][1], x['id'][2]] or x['id'][1] < 32]
            imFileTracker = dict([(x['id'][0], x['id'][3]) for x in allPixels])
            cellTracker = dict([(x['id'], x) for x in allPixels])
            write_cell_data(eventClass, dataset, waves, balanceOption, allPixels)

        ####################################
        # done generating cells, now we setup neighbor relationships
        fullHAdj = dict()
        fullIAdj = dict()
        for pix in allPixels:  # this part correctly assigns neighbors to each cell of the image
            # it's done after all the pixels are processed because we want the neighbors to exist

            imNum, iir, iic, imFile = pix['id']
            if neighborhood == 'rook':
                neighbors = [
                    (imNum, iir - 1, iic, imFile),
                    (imNum, iir, iic - 1, imFile),
                    (imNum, iir, iic + 1, imFile),
                    (imNum, iir + 1, iic, imFile)
                ]

            elif neighborhood == 'rooktemp':
                neighbors = [
                    (imNum, iir - 1, iic, imFile),
                    (imNum, iir, iic - 1, imFile),
                    (imNum, iir, iic + 1, imFile),
                    (imNum, iir + 1, iic, imFile),
                    (imNum + 1, iir, iic, get_image_file(imFileTracker, imNum + 1)),
                    (imNum - 1, iir, iic, get_image_file(imFileTracker, imNum - 1))
                ]

            elif neighborhood == 'rooktemplong':
                neighbors = [
                    (imNum, iir - 1, iic, imFile),
                    (imNum, iir, iic - 1, imFile),
                    (imNum, iir, iic + 1, imFile),
                    (imNum, iir + 1, iic, imFile),
                    (imNum + 1, iir, iic, get_image_file(imFileTracker, imNum + 1)),
                    (imNum - 1, iir, iic, get_image_file(imFileTracker, imNum - 1)),
                    (imNum + 2, iir, iic, get_image_file(imFileTracker, imNum + 2)),
                    (imNum - 2, iir, iic, get_image_file(imFileTracker, imNum - 2)),
                    (imNum + 3, iir, iic, get_image_file(imFileTracker, imNum + 3)),
                    (imNum - 3, iir, iic, get_image_file(imFileTracker, imNum - 3))
                ]

            elif neighborhood == 'queen':
                neighbors = [
                    (imNum, iir - 1, iic - 1, imFile),
                    (imNum, iir - 1, iic + 0, imFile),
                    (imNum, iir - 1, iic + 1, imFile),
                    (imNum, iir + 0, iic - 1, imFile),
                    (imNum, iir + 0, iic + 1, imFile),
                    (imNum, iir + 1, iic - 1, imFile),
                    (imNum, iir + 1, iic + 0, imFile),
                    (imNum, iir + 1, iic + 1, imFile)
                ]
            else:
                raise Exception('neighborhood option not supported')
            hl = []  # list of homogenous neighbors (actual object, not just index) for pix
            il = []  # list of inhomogenous neighbors (actual object, not just index) for pix
            for Nindex in neighbors:
                try:
                    N = cellTracker[Nindex]
                    if N['class'] == pix['class']:
                        hl.append(N)
                    else:
                        il.append(N)
                except KeyError:  # key errors will occur due to mask-based removal of cells and OOB issues
                    pass
            fullHAdj[pix['id']] = hl
            fullIAdj[pix['id']] = il
        # end for pix loop
        random.shuffle(allPixels)  # I think this is an artifact of when we were dividing train and test sets randomly?
        trainPixels = [x for x in allPixels if x['id'][1] >= 32]  # train on the top half of every image
        testPixels = [x for x in allPixels if x['id'][1] < 32]  # test on the bottom half of every image

        A = set(x['id'] for x in trainPixels)
        B = set(x['id'] for x in testPixels)
        trainHAdj = dict()
        trainIAdj = dict()
        testHAdj = dict()
        testIAdj = dict()
        for key in fullHAdj:  # both adjacency mats have the same keys
            HNlist = fullHAdj[key]
            INlist = fullIAdj[key]
            if key in A:
                newHNlist = [x for x in HNlist if x['id'] in A]
                newINlist = [x for x in INlist if x['id'] in A]
                trainHAdj[key] = newHNlist
                trainIAdj[key] = newINlist
            else:
                newHNlist = [x for x in HNlist if x['id'] in B]
                newINlist = [x for x in INlist if x['id'] in B]
                testHAdj[key] = newHNlist
                testIAdj[key] = newINlist

        s_train = trainPixels, trainHAdj, trainIAdj
        s_test = testPixels, testHAdj, testIAdj
        with open(outputfileTrain, 'wb') as f:
            pickle.dump(s_train, f)
        with open(outputfileTest, 'wb') as f:
            pickle.dump(s_test, f)
    else:  # file we would write to already exists
        print "already generated", eventClass, neighborhood, dataset


radius = 1625
[H, W] = (4096, 4096)
circleMask = gridCells(
    circleMask([H, W], [H / 2, W / 2], radius))  # this mask is for eliminating the edges of the sun from our filter
for derp in ['Mirror']:
    write_data(circleMask,
               balanceOption=derp)  # don't have to worry about accidently reusing data, as this is a function call
