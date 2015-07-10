from __future__ import division
import sys
sys.path.append('/data/home/pmcinerney/python')
import cPickle as pickle
import logging

def readData(eventClass,neighborhood='rook',dataset='1MONTH',waves=['0171'],balanceOption = 'None'):
  logging.log(logging.INFO+5,'reading data')
  fileTrain = "data/"+"_".join([eventClass,neighborhood,dataset,"-".join(waves),'balance='+balanceOption])+".train"
  fileTest = "data/"+"_".join([eventClass,neighborhood,dataset,"-".join(waves),'balance='+balanceOption])+".test"
  with open(fileTrain) as f:
    S_train = pickle.load(f)
  with open(fileTest) as f:
    S_test = pickle.load(f)
  logging.log(logging.INFO+5,'data read')
  return S_train,S_test

