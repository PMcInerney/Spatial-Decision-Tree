from __future__ import division
import numpy as np
import parseEventData as pt
import scipy.ndimage as img
import scipy.misc as m
import glob
import os
import csv


def find_grid_cells(cc):
    # input is list of points [[x1,y1],[x2,y2]...] in order around the polygon. last and first point are the same
    # output is a 64x64 boolean grid with the cells containing parts of the polygon assigned true.
    cells = set()
    edges = zip(cc[:-1], cc[1:])  # build the edges of the polygon
    for edge in edges:
        if edge[0][0] > edge[1][0]:  # point 1 is always the leftmost point
            point2 = edge[0]
            point1 = edge[1]
        else:
            point1 = edge[0]
            point2 = edge[1]
        slope_Is_Positive = point1[1] < point2[1]
        cellx = point1[0] // 64  # integer division
        celly = point1[1] // 64  # integer division
        end_cellx = point2[0] // 64  # integer division
        end_celly = point2[1] // 64  # integer division
        cells.add((cellx, celly))
        count = 0
        while not (cellx == end_cellx and celly == end_celly):
            count += 1
            if count > 64:
                raise Exception('infinite loop, time to bugfix')
            if slope_Is_Positive:
                # use perpindicular dot product to test if UL corner of rightward grid neighbor is above or below edge
                ##(Bx - Ax) * (Cy - Ay) - (By - Ay) * (Cx - Ax)
                if (point2[0] - point1[0]) * ((celly + 1) * 64 - point1[1]) - (point2[1] - point1[1]) * (
                                (cellx + 1) * 64 - point1[0]) >= 0:
                    cellx += 1  # if above, go right
                else:
                    celly += 1  # if below, go up
            else:
                # use perpindicular dot product to test if LL corner of rightward grid neighbor is above or below edge
                ##(Bx - Ax) * (Cy - Ay) - (By - Ay) * (Cx - Ax)
                if (point2[0] - point1[0]) * ((celly) * 64 - point1[1]) - (point2[1] - point1[1]) * (
                                (cellx + 1) * 64 - point1[0]) <= 0:
                    cellx += 1  # if below, go right
                else:
                    celly -= 1  # if above, go down
            cells.add((cellx, celly))
    # we now have a list of the boundary grid cells for the polygon
    # next we convert that into an array and fill the interior
    mask = np.zeros([64, 64], dtype=np.bool)
    for cell in cells:
        mask[cell[1], cell[0]] = True  ## go from x,y to row,column
    mask = ~mask
    labeled_array, num_features = img.measurements.label(mask)  # label 4-connected black regions
    x = 0
    y = 0
    for i in range(1, num_features + 1):  # we assume the largest black region is the exterior of the event
        size_region = np.sum(labeled_array == i)
        if size_region > y:
            x = i
            y = size_region
    mask = labeled_array != x  # everything that's not the exterior is our mask
    return mask


def generate_event_im_pairs(events, waves, im_files):
    # takes a data structure listing HEK events and a list of image files and
    # associates each event with the closest image in the list
    # is NOT inherently wavelength sensitive. you need to specify wave filters
    im_names = [(os.path.splitext(os.path.basename(x)))[0] for x in im_files]
    read_data = events
    headers = read_data[0]
    all_events = read_data[1:]  # the first row is column headers
    if not len(waves) == 0:
        events_we_want = [event for event in all_events if int(pt.parseWave(event, headers)) in waves]
    else:
        events_we_want = all_events
    # now we have a list of the events we want. next we need to find the image closest to each event
    # images
    image_times = [pt.parseAIADate(name[3:18]) for name in im_names]  # times in unix form
    ims = zip(im_files, image_times)
    # pair up the events and their associated images
    if verbose:
        event_im_pairs = []
        count = 0
        for event in events_we_want:
            count += 1
            print count, '/', len(events_we_want)
            x = find_closest_image(event, headers, ims)
            event_im_pairs.append([event, x])
    else:
        event_im_pairs = [[event,find_closest_image(event,headers,ims)] for event in events_we_want]
    return event_im_pairs


def find_closest_image(event, headers, ims):
    # ims expected to be formatted as above
    # binarySearch the imagelist for the closest image time
    if len(ims) == 0:
        return 'derp'
    if len(ims) == 1:
        return ims[0]
    else:
        index = len(ims) // 2  # integer division
        if abs(ims[index][1] - pt.parseMidTime(event, headers)) < abs(
                        ims[index - 1][1] - pt.parseMidTime(event, headers)):
            return find_closest_image(event, headers, ims[index:])
        else:
            return find_closest_image(event, headers, ims[:index])
