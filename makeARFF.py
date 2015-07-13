from readData import read_data

e = 'AR'
n = 'rook'
d = '1DAY'
w = ['0171']
b = 'Mirror'

# This script takes a single experiment's set of data and produces an ARFF file for use with WEKA. 
# Extending it to be able to handle multiple experiments at a time (producing multiple ARFF files) is a good idea

S_train, S_test = read_data(e, neighborhood=n, dataset=d, waves=w, balanceOption=b)

def make_arff():
    filename = '_'.join([e, d, '-'.join(w), b, 'train']) + '.arff'
    relation_name = 'derp'
    feature_names = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']
    classes = [e, 'null']
    cells, adj = S_train
    cells2, adj2 = S_test
    with open(filename, 'w') as f:
        f.write('@relation ' + str(relation_name) + "\n\n")

        for n in feature_names:
            f.write("@attribute " + str(n) + " numeric\n")

        s = ','.join(classes)
        f.write("@attribute label {" + s + "}\n\n")

        f.write('@data\n')

        for cell in cells:
            data = [str(cell[x]) for x in feature_names] + [cell['class']]
            s = ' '.join(data) + '\n'
            f.write(s)

    filename = '_'.join([e, d, '-'.join(w), b, 'test']) + '.arff'
    with open(filename, 'w') as f:
        f.write('@relation ' + str(relation_name) + "\n\n")

        for n in feature_names:
            f.write("@attribute " + str(n) + " numeric\n")

        s = ','.join(classes)
        f.write("@attribute label {" + s + "}\n\n")

        f.write('@data\n')

        for cell in cells2:
            data = [str(cell[x]) for x in feature_names] + [cell['class']]
            s = ' '.join(data) + '\n'
            f.write(s)
