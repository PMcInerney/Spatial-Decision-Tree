import SolarCBIRTools
import parseEventData
import csv
import SOLARFileTools
import os

EVENT_FILE = '/data/SDO/DATASET/files/events.csv'
THREE_DAY_DEMO_START = 1327017600
JAN_END = 1328054400
JAN_START = 1325376000
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY

def make_images_list(start_folder, end_folder, waves=None):
    l = []
    if not waves:
        waves = []
    folder = '/data/SDO/AIA'
    walker = os.walk(folder)
    current_folder, subfolders, files = walker.next()
    # This lexical comparison relies heavily on the upon the way SDO AIA folders are structured to provide correct
    # behavior, including consistent folder name length and use of numbers for months
    while current_folder < start_folder:
        current_folder, subfolders, files = walker.next()
    while current_folder < end_folder:
        for f in files:
            if len(waves) == 0:  # return all waves
                l.append(os.path.join(current_folder, f))
            else:
                if f[19:23] in waves:
                    l.append(f)
        current_folder, subfolders, files = walker.next()
    return l



def simple_pairs(dataset='1MONTH', waves=None):  # waves here indicates a filter on images, not events
    if not waves:
        waves = []
    print 'calculating simple pairs'

    with open(EVENT_FILE) as f2:
        r = csv.reader(f2)
        read_data = [x for x in r]
    headers = read_data[0]
    events = read_data[1:]
    if dataset == '6MONTH':
        l = SOLARFileTools.make_6month_images_list(waves=waves)  # images list gets ALL images
        some_events = events  # January-June 2012
    elif dataset == '1MONTH':
        l = SOLARFileTools.make_1month_images_list(waves=waves)
        jan_events = [event for event in events if parseEventData.parseMidTime(event, headers) <= JAN_END]
        some_events = jan_events  # month of January 2012
    elif dataset == '1WEEK':
        l = SOLARFileTools.make_1week_images_list(waves=waves)
        week_events = [event for event in events if
                       THREE_DAY_DEMO_START <= parseEventData.parseMidTime(event, headers) and parseEventData.parseMidTime(event,
                                                                                                   headers) <= THREE_DAY_DEMO_START + WEEK]
        some_events = week_events  # 20 -26 Jan 2012 (full week of 3DAY demo)
    elif dataset == '3DAYDEMO':
        l = SOLARFileTools.make_3daydemo_images_list(waves=waves)
        three_day_events = [event for event in events if
                            THREE_DAY_DEMO_START <= parseEventData.parseMidTime(event, headers) and parseEventData.parseMidTime(event,
                                                                                                        headers) <= THREE_DAY_DEMO_START + 3 * DAY + 12 * HOUR]
        some_events = three_day_events  # 20 - 23 Jan 2012 (chosen for high flare activity during this period?) - actually 3.5 days
    elif dataset == '1DAY':
        l = SOLARFileTools.make_1day_images_list(waves=waves)
        one_day_events = [event for event in events if
                        JAN_START <= parseEventData.parseMidTime(event, headers) and parseEventData.parseMidTime(event,
                                                                                         headers) <= JAN_START + DAY]  # January 1st
        some_events = one_day_events
    else:
        raise Exception('dataset not supported')
    print 'read events'

    ###############################################################
    # this filters to an even number of chosen events
    # per class
    ###############################################################
    # first we figure out which is the smallest class,
    # and put its number of events in smallestClassSize
    # smallestClassSize = sys.maxint;
    # for event in ['FL','FI','AR','CH','SS','SG']:
    #  smallestClassSize = min(smallestClassSize,len([E for E in some_events if pt.parseEventType(E,headers) == event]))
    #
    # balancedEvents = []
    # for event in ['FL','FI','AR','CH','SS','SG']:
    #  classEvents = [E for E in some_events if pt.parseEventType(E,headers) == event]
    #  reducedClassEvents = random.sample(classEvents,smallestClassSize)
    #  balancedEvents.extend(reducedClassEvents)
    #  some_events = balancedEvents
    #######################################################

    pairs = SolarCBIRTools.generate_event_im_pairs([headers] + some_events, [],
                                          l)  # this attaches the event to the closest image we have,
    # we need the image and associated label for every event report
    pairsWeWant = [pair for pair in pairs if
                   (pair[1][0] != 'derp')]  # grab the wave's events and the associated imagename
    ###################################################
    # We now have one image for every event in our list
    ###################################################
    return headers, pairsWeWant


def event_image_matches(dataset='1MONTH', waves=None):
    if not waves:
        waves = []
    headers, pairs_we_want = simple_pairs(dataset=dataset, waves=waves)
    print 'calculating event-image matches'
    pruned_images = set([pair[1] for pair in pairs_we_want])
    count = 0
    for pair in pairs_we_want:
        count += 1
        event = pair[0]
        for image in pruned_images:
            image_time = image[1]
            if parseEventData.parseStartTime(event, headers) <= image_time <= parseEventData.parseEndTime(event, headers) and image not in pair:
                pair.append(image)
    return headers, pairs_we_want


def image_event_matches(eventTypes=['FL', 'FI', 'AR', 'CH', 'SS', 'SG'], dataset='1MONTH', waves=[]):
    headers, pairs_we_want = event_image_matches(dataset=dataset, waves=waves)
    print 'calculating image-event matches'
    pairs_we_want = [pair for pair in pairs_we_want if parseEventData.parseEventType(pair[0], headers) in eventTypes]
    reverse_matches = dict()
    for pair in pairs_we_want:
        for filename in pair[1:]:
            if filename in reverse_matches:
                reverse_matches[filename].append(pair[0])
            else:
                reverse_matches[filename] = [pair[0]]
    return headers, reverse_matches


def writeList():
    headers, pairsWeWant = event_image_matches()
    with open('SOLAR1MONTH_image_list.txt', 'w') as f:
        for pair in pairsWeWant:
            f.write(pair[1][0] + '\n')  # this is ignoring the other images added to the pair
            y = parseEventData.parseChainCode(pair[0], headers)
            if y == "NA":
                y = parseEventData.parseBoundingBox(pair[0], headers)
            X = SolarCBIRTools.find_grid_cells(y)
            for i in range(64):
                for j in range(64):
                    if X[i, j]:
                        f.write(str(i) + " " + str(j) + "\t")
            f.write("\n")
            f.write(parseEventData.parseEventType(pair[0], headers) + "\n")
