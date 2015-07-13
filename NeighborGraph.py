from __future__ import division
import math
from collections import Counter
from operator import itemgetter


class NeighborGraph:
    # pixels is a dict of pixel entries
    # each pixel entry has feature and class data

    """derp"""

    def __init__(self, s):
        cells, adj_h, adj_i = s
        self.cells = cells
        self.adj_h = adj_h
        self.adj_i = adj_i
        self.C = set(pix['class'] for pix in cells)
        self.F = set(cells[0].keys).difference({'class', 'adj_h', 'adj_i'})
        # Assumption here that all cells have the exact same set of features
        c = Counter(pix['class'] for pix in self.cells)
        counts = c.most_common()
        self.counts = dict(counts)
        ordered_counts = [x[1] for x in counts]
        total_counts = sum(ordered_counts)
        sum_ = 0
        for p in self.F:  # for each parameter
            s = set([cell[p] for cell in cells])  # build a set of unique values
            sum_ += len(s)  # add up the set lengths
        self.numSplits = sum_
        self.entropy = -sum(
            x / total_counts * math.log(x / total_counts, 2) if not x == 0 else 0 for x in ordered_counts)

    def size(self):
        return len(self.cells)

    @property
    def major_class(self):
        """



        :rtype : object
        :return:
        """
        c = Counter(pix['class'] for pix in self.cells)
        return c.most_common(1)[0][0]

    @property
    def uniform(self):
        return len(self.C) == 1

    def best_split(self, alpha, split_res, neighbor_functions):
        if len(alpha) != len(neighbor_functions):
            raise Exception("dimension mismatch in Neighborhood weights\n" + str(alpha) + "\n" + str(neighbor_functions))
        E = self.entropy
        best_split_out = None
        max_sig = 0
        for feature in self.F:
            feature_sorted_pixels = sorted(self.cells, key=itemgetter(feature))
            step = max(len(feature_sorted_pixels) // split_res, 1)
            feature_values = [pix[feature] for pix in feature_sorted_pixels[::step]]
            feature_values = sorted(list(set(feature_values)))
            a_counts = self.counts.copy()
            b_counts = dict((key, 0) for key in a_counts)
            n1 = self.size()
            n2 = 0
            threshold_pix = feature_sorted_pixels[0]
            # whenever a cell is moved from one partition to the other, we need to recalculate the cell's NSAR
            # as the transition will cause it to gain/lose/change neighbors
            update_set = set()
            update_list = []
            nsars = [dict((key, 1) for key in self.adj_h) for func in
                     neighbor_functions]  # used to store NSARS for reuse on different thresholds
            # If no partition is made, all NSARS are 1, thus the initialization
            # remember: NSAR is the ratio of (homogeneous neighbors before):(homogeneous neighbors after)
            total_nsar = [len(nsars[0]) for func in neighbor_functions]
            for value in feature_values[:-1]:  # if we partition on final value, we may not separate at all
                # first we move all of the cells from A to B that are above the new value
                # we tag as 'need to update' all the cells we move, as well as their neighbors
                while threshold_pix[feature] <= value:  # we iterate through the potential split values
                    if threshold_pix['id'] not in update_set and len(self.adj_h[threshold_pix['id']]) > 0:
                        update_set.add(threshold_pix['id'])
                        update_list.append(threshold_pix)
                    n1 -= 1  # size of low partition
                    n2 += 1  # size of high partition
                    a_counts[threshold_pix['class']] -= 1
                    b_counts[threshold_pix['class']] += 1

                    for N in self.adj_h[threshold_pix['id']]:
                        if N['id'] not in update_set:
                            update_set.add(N['id'])
                            update_list.append(N)
                    threshold_pix = feature_sorted_pixels[
                        n2]  # n2 can be looked at as an iterator here, as it increases by exactly 1 each loop

                # information gain calculation

                E1 = -sum(x / n1 * math.log(x / n1, 2) if not x == 0 else 0 for x in a_counts.values())
                E2 = -sum(x / n2 * math.log(x / n2, 2) if not x == 0 else 0 for x in b_counts.values())
                Eprime = n1 / (n1 + n2) * E1 + n2 / (n1 + n2) * E2
                IG = E - Eprime
                # TODO: compare these calculations against the one in check_split_info_gain
                # NSAR calculation

                if any([x > 0 for x in alpha]):  # if alpha is zero vector NSAR doesn't matter
                    for pix in update_list:
                        # we don't want to go through every cell, just the ones that need to be updated
                        old_homogeneous_neighbors = self.adj_h[pix['id']]
                        if pix[feature] <= value:
                            new_homogenous_neighbors = [x for x in self.adj_h[pix['id']] if
                                                        x[feature] <= value]  # HERP DERP
                        else:
                            new_homogenous_neighbors = [x for x in self.adj_h[pix['id']] if
                                                        x[feature] > value]  # HERP DERP

                        for i, func in enumerate(neighbor_functions):
                            if func == "spatial":
                                # spatial neighbors are the ones from the same image
                                func_old_homogeneous_neighbors = [x for x in old_homogeneous_neighbors if
                                                                  pix['id'][0] == x['id'][0]]
                                func_new_homogeneous_neighbors = [x for x in new_homogenous_neighbors if
                                                                  pix['id'][0] == x['id'][0]]
                            elif func == "temporal":
                                # temporal neighbors are the ones _not_ from the same image
                                func_old_homogeneous_neighbors = [x for x in old_homogeneous_neighbors if
                                                                  not pix['id'][0] == x['id'][0]]
                                func_new_homogeneous_neighbors = [x for x in new_homogenous_neighbors if
                                                                  not pix['id'][0] == x['id'][0]]
                            elif func == "none":
                                # none means take all neighbors without any filter
                                func_old_homogeneous_neighbors = [x for x in old_homogeneous_neighbors]
                                func_new_homogeneous_neighbors = [x for x in new_homogenous_neighbors]
                            else:
                                raise Exception('Unsupported Neighbor Function: ' + func)
                            if len(func_old_homogeneous_neighbors) == 0:
                                NSAR = 1  # If there are no old neighbors, NSAR is one
                            else:
                                NSAR = len(func_new_homogeneous_neighbors) / len(func_old_homogeneous_neighbors)
                            total_nsar[i] = total_nsar[i] - nsars[i][pix['id']] + NSAR  #
                            nsars[i][pix['id']] = NSAR
                avg_nsar = [x / self.size() for x in total_nsar]
                update_set = set()
                update_list = []
                # TODO: figure out why there's two things here
                sig = (1 - sum(alpha)) * IG * self.size() + sum(x * y for x, y in zip(alpha, total_nsar))  # weighted sum of IG and avg_NSARs
                sig = (1 - sum(alpha)) * IG +               sum(x * y for x, y in zip(alpha, avg_nsar)) # weighted sum of IG and avg_NSARs
                if sig >= max_sig:
                    max_sig = sig
                    best_split_out = feature, value
        return best_split_out

    def partition(self, parameter, value):
        pixels1 = []
        pixels2 = []
        Hadj1 = dict()
        Hadj2 = dict()
        Iadj1 = dict()
        Iadj2 = dict()
        for x in self.cells:
            if x[parameter] <= value:
                pixels1.append(x)
                Hadj1[x['id']] = [pix for pix in self.adj_h[x['id']] if pix[parameter] <= value]
                Iadj1[x['id']] = [pix for pix in self.adj_i[x['id']] if pix[parameter] <= value]
            else:
                pixels2.append(x)
                Hadj2[x['id']] = [pix for pix in self.adj_h[x['id']] if pix[parameter] > value]
                Iadj2[x['id']] = [pix for pix in self.adj_i[x['id']] if pix[parameter] > value]
        g1 = NeighborGraph((pixels1, Hadj1, Iadj1))
        g2 = NeighborGraph((pixels2, Hadj2, Iadj2))
        # we want to partition the graph according to some test
        # do stuff here
        # I'm pretty sure object copying is going to be an issue
        return g1, g2

    def check_split_info_gain(self, split):
        # this only tests on entropy
        parameter, value = split
        partition_a = []
        partition_b = []
        for x in self.cells:
            if x[parameter] <= value:
                partition_b.append(x)
            else:
                partition_a.append(x)
        tot = len(self.cells)
        pos = len([x for x in self.cells if x['class'] == 'null'])
        neg = len([x for x in self.cells if x['class'] != 'null'])
        rpos = pos / tot
        rneg = neg / tot
        logpos = math.log(rpos, 2) if rpos > 0 else 0
        logneg = math.log(rneg, 2) if rneg > 0 else 0
        entropy = -rpos * logpos - rneg * logneg

        posa = len([x for x in partition_a if x['class'] == 'null'])
        nega = len([x for x in partition_a if x['class'] != 'null'])
        tota = len(partition_a)
        rposa = posa / tota
        rnega = nega / tota
        logposa = math.log(rposa, 2) if rposa > 0 else 0
        lognega = math.log(rnega, 2) if rnega > 0 else 0
        entropy_a = -rposa * logposa - rnega * lognega

        posb = len([x for x in partition_b if x['class'] == 'null'])
        negb = len([x for x in partition_b if x['class'] != 'null'])
        totb = len(partition_b)
        rposb = posb / totb
        rnegb = negb / totb
        logposb = math.log(rposb, 2) if rposb > 0 else 0
        lognegb = math.log(rnegb, 2) if rnegb > 0 else 0
        entropy_b = -rposb * logposb - rnegb * lognegb

        new_entropy = (entropy_a * tota + entropy_b * totb) / tot
        info_gain = entropy - new_entropy
        return info_gain
