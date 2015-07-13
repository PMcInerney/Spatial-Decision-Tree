from __future__ import division
import cPickle
import logging


def read_data(eventClass, neighborhood='rook', dataset='1MONTH', waves=['0171'], balanceOption='None'):
    logging.log(logging.INFO + 5, 'reading data')
    file_train = "data/" + "_".join(
        [eventClass, neighborhood, dataset, "-".join(waves), 'balance=' + balanceOption]) + ".train"
    file_test = "data/" + "_".join(
        [eventClass, neighborhood, dataset, "-".join(waves), 'balance=' + balanceOption]) + ".test"
    with open(file_train) as f:
        s_train = cPickle.load(f)
    with open(file_test) as f:
        s_test = cPickle.load(f)
    logging.log(logging.INFO + 5, 'data read')
    return s_train, s_test

