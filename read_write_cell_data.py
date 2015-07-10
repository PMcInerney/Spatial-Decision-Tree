import cPickle
import os

# this file contains utility functions to read and write cell data, which is used by write_data for... reasons
# TODO: SPECIFY REASONS

def read_cell_data(eventclass, dataset, waves, balanceoption):
    filename = 'data/' + '_'.join([eventclass, dataset, '-'.join(waves), 'balance=' + balanceoption]) + '.cells'
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            x = cPickle.load(f)
    else:
        x = -1
    return x


def write_cell_data(eventclass, dataset, waves, balanceoption, data):
    filename = 'data/' + '_'.join([eventclass, dataset, '-'.join(waves), 'balance=' + balanceoption]) + '.cells'
    with open(filename, 'wb') as f:
        cPickle.dump(data, f)
