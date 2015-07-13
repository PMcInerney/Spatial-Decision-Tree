import random
def rg_learn(s_train, s_test):
    """Input:
    S_train: list of cell objects
    S_test: list of cell objects
    """

    # Build the list of options to guess from
    cells, adj_h, adj_i = s_train
    random_guesses = list(set(x['class'] for x in cells))

    # make some guesses
    cells, adj_h, adj_i = s_test
    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    for cell in cells:
        output = random.sample(random_guesses, 1)[0]
        if output == cell['class']:
            if output == 'null':
                true_negative += 1
            else:
                true_positive += 1
        else:
            if output == 'null':
                false_negative += 1
            else:
                false_positive += 1
    return true_positive, false_positive, true_negative, false_negative
