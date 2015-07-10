import itertools

# These functions build the tuples of parameters iterated through for multi-experiment runs
# putting it in one place makes it easier to keep files small and avoid accidentally running different sets of experiments in different scripts

def datasetBuilder(classes,neighborhoods,datasets,waves,balances):
  return [x for x in itertools.product(classes,neighborhoods,datasets,waves,balances)]

def trainingParametersBuilder():
  raise Exception('not implemented')
