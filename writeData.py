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


def get_image_file(image_file_tracker, n):
    try:
        out = image_file_tracker[n]
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
    # pick a random distance
    x = random.randint(4, 16)
    y = random.randint(4, 16)
    # pick a random direction
    signx = random.sample([-1, 1], 1)[0]
    signy = random.sample([-1, 1], 1)[0]
    # move the event
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


def write_data(circle_mask, balance_option='None'):
    if balance_option not in ['None', 'Mirror', 'Duplication', 'Random']:
        print balance_option
        raise Exception('balance option not supported')
    # events = ['AR','CH','SS','SG','FL','FI']
    events = ['AR', 'CH', 'SG', 'FL']
    neighborhoods = ['rook', 'rooktemp', 'rooktemplong']
    datasets = ['1DAY', '3DAYDEMO']
    wavesets = [['0171'], ['0193'], ['0094']]
    X = [x for x in itertools.product(events, neighborhoods, datasets, wavesets)]
    for e, n, d, w in X:
        write_experiment_data(circle_mask, e, n, d, w, balance_option)


def write_experiment_data(circle_mask, event_class, neighborhood, dataset, waves, balance_option):
    grid_for_random_sample = [x for x in
                              itertools.product(range(64), range(64))]  # build a set of cells for picking from
    # TODO: fix magic numbers
    output_file_train = "data/" + "_".join(
        [event_class, neighborhood, dataset, "-".join(waves), 'balance=' + balance_option]) + ".train"
    output_file_test = "data/" + "_".join(
        [event_class, neighborhood, dataset, "-".join(waves), 'balance=' + balance_option]) + ".test"
    if not (os.path.exists(output_file_train) and os.path.exists(output_file_test)):
        print event_class, neighborhood, dataset, waves, balance_option
        read_attempt_data = read_cell_data(event_class, dataset, waves, balance_option)
        if read_attempt_data != -1:  # read success
            all_pixels = read_attempt_data
            cell_tracker = dict([(x['id'], x) for x in all_pixels])
            imagefile_tracker = dict([(x['id'][0], x['id'][3]) for x in all_pixels])
            # we need to know the individual events to generate the balancing filter
            print 'read data successfully'
        else:  # read Failure
            ###################################
            headers, matches = SOLARGenImageList.image_event_matches([event_class], dataset=dataset, waves=waves)
            print 'matches calculated', event_class, dataset, waves
            image_counter = 0
            all_pixels = []
            # build a 'what cell is FI' matrix
            if balance_option == 'None':
                balancing_filter = np.ones([len(matches), 64, 64], dtype=bool)  # keep everything
            else:  # filter will be filled as we process images
                balancing_filter = np.zeros([len(matches), 64, 64], dtype=bool)
            for imagekey in sorted(matches.keys()):  # for every image
                event_binmat = np.zeros([64, 64], dtype=bool)
                image_balancing_filter = np.zeros([64, 64], dtype=bool)
                for E in matches[imagekey]:  # for each event in that image
                    cc = parseChainCode(E, headers)
                    if cc == "NA":
                        cc = parseBoundingBox(E, headers)
                    event_location_mat = find_grid_cells(cc)
                    event_binmat = np.logical_or(
                        event_binmat,
                        event_location_mat)  # combine all the events into one binary matrix for the image
                    buffered_event_location_mat = buffer_binmat(event_location_mat)
                    image_balancing_filter = np.logical_or(
                        image_balancing_filter,
                        buffered_event_location_mat)  # add the positive examples to the training set
                    if balance_option == 'Mirror':
                        mirror_mat = mirror_event(buffered_event_location_mat)
                        image_balancing_filter = np.logical_or(
                            image_balancing_filter,
                            mirror_mat)  # add some negative examples to the training set
                    if balance_option == 'Duplication':
                        dup_mat = reposition_event(buffered_event_location_mat)
                        image_balancing_filter = np.logical_or(
                            image_balancing_filter,
                            dup_mat)  # add some negative examples to the training set
                # end of 'for event' loop
                if balance_option == 'Random':  # randomly undersample negative class
                    num_pos = np.sum(event_binmat)  # calc the number of event cells in this image
                    neg_grid_cells = [x for x in grid_for_random_sample if not event_binmat[x[0], x[1]]]
                    rand_sample_of_grid = random.sample(neg_grid_cells, num_pos)  # randomly pick some negative cells
                    for x in rand_sample_of_grid:
                        image_balancing_filter[x] = True
                balancing_filter[image_counter, :, :] = image_balancing_filter

                image_pixels = []
                with open(imagekey[0]) as f:  # read the parameter data for this image
                    c = csv.reader(f, dialect='excel-tab')
                    cells = [x for x in c]
                for cell in cells:  # compile data/classification for all cells in image
                    row = int(cell[0]) - 1  # silly juan 1 based index
                    col = int(cell[1]) - 1
                    if not circle_mask[row, col]:  # if cell off disk,
                        pass  # do nothing
                    else:  # else
                        s = dict()  # build the cell data structure
                        s['id'] = (image_counter, row, col, imagekey)
                        if event_binmat[row, col]:
                            s['class'] = event_class
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
                        image_pixels.append(s)
                all_pixels.extend(image_pixels)
                image_counter += 1
            # end of images loop
            all_pixels = [x for x in all_pixels if
                          balancing_filter[x['id'][0], x['id'][1], x['id'][2]] or x['id'][1] < 32]
            imagefile_tracker = dict([(x['id'][0], x['id'][3]) for x in all_pixels])
            cell_tracker = dict([(x['id'], x) for x in all_pixels])
            write_cell_data(event_class, dataset, waves, balance_option, all_pixels)

        ####################################
        # done generating cells, now we setup neighbor relationships
        fullHAdj = dict()
        fullIAdj = dict()
        for pix in all_pixels:  # this part correctly assigns neighbors to each cell of the image
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
                    (imNum + 1, iir, iic, get_image_file(imagefile_tracker, imNum + 1)),
                    (imNum - 1, iir, iic, get_image_file(imagefile_tracker, imNum - 1))
                ]

            elif neighborhood == 'rooktemplong':
                neighbors = [
                    (imNum, iir - 1, iic, imFile),
                    (imNum, iir, iic - 1, imFile),
                    (imNum, iir, iic + 1, imFile),
                    (imNum, iir + 1, iic, imFile),
                    (imNum + 1, iir, iic, get_image_file(imagefile_tracker, imNum + 1)),
                    (imNum - 1, iir, iic, get_image_file(imagefile_tracker, imNum - 1)),
                    (imNum + 2, iir, iic, get_image_file(imagefile_tracker, imNum + 2)),
                    (imNum - 2, iir, iic, get_image_file(imagefile_tracker, imNum - 2)),
                    (imNum + 3, iir, iic, get_image_file(imagefile_tracker, imNum + 3)),
                    (imNum - 3, iir, iic, get_image_file(imagefile_tracker, imNum - 3))
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
                    N = cell_tracker[Nindex]
                    if N['class'] == pix['class']:
                        hl.append(N)
                    else:
                        il.append(N)
                except KeyError:  # key errors will occur due to mask-based removal of cells and OOB issues
                    pass
            fullHAdj[pix['id']] = hl
            fullIAdj[pix['id']] = il
        # end for pix loop
        random.shuffle(all_pixels)  # I think this is an artifact of when we were dividing train and test sets randomly?
        train_Pixels = [x for x in all_pixels if x['id'][1] >= 32]  # train on the top half of every image
        test_pixels = [x for x in all_pixels if x['id'][1] < 32]  # test on the bottom half of every image

        A = set(x['id'] for x in train_Pixels)
        B = set(x['id'] for x in test_pixels)
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

        s_train = train_Pixels, trainHAdj, trainIAdj
        s_test = test_pixels, testHAdj, testIAdj
        with open(output_file_train, 'wb') as f:
            pickle.dump(s_train, f)
        with open(output_file_test, 'wb') as f:
            pickle.dump(s_test, f)
    else:  # file we would write to already exists
        print "already generated", event_class, neighborhood, dataset


radius = 1625
[H, W] = (4096, 4096)
circleMask = gridCells(
    circleMask([H, W], [H / 2, W / 2], radius))  # this mask is for eliminating the edges of the sun from our filter
for derp in ['Mirror']:
    write_data(circleMask,
               balance_option=derp)  # don't have to worry about accidently reusing data, as this is a function call
