import time

def parseAIADate(s):
    time.timezone = 0
    time.altzone = 0
    time.daylight = 0
    year = int(s[0:4])
    month = int(s[4:6])
    day = int(s[6:8])
    hour = int(s[9:11])
    minute = int(s[11:13])
    second = int(s[13:15])
    return time.mktime((year,month,day,hour,minute,second,0,0,0))


def parseStartTimeReadable(event,headers):
    s = event[headers.index('starttime')]
    time.timezone = 0
    time.altzone = 0
    time.daylight = 0
    year = int(s[0:4])
    month = int(s[5:7])
    day = int(s[8:10])
    hour = int(s[11:13])
    minute = int(s[14:16])
    second = int(s[17:19])
    return year,month,day,hour,minute,second

def parseStartTime(event,headers):
    s = event[headers.index('starttime')]
    time.timezone = 0
    time.altzone = 0
    time.daylight = 0
    year = int(s[0:4])
    month = int(s[5:7])
    day = int(s[8:10])
    hour = int(s[11:13])
    minute = int(s[14:16])
    second = int(s[17:19])
    return time.mktime((year,month,day,hour,minute,second,0,0,0))

def parseEndTime(event,headers):
    s = event[headers.index('endtime')]
    time.timezone = 0
    time.altzone = 0
    time.daylight = 0
    year = int(s[0:4])
    month = int(s[5:7])
    day = int(s[8:10])
    hour = int(s[11:13])
    minute = int(s[14:16])
    second = int(s[17:19])
    return time.mktime((year,month,day,hour,minute,second,0,0,0))

def parseEndTimeReadable(event,headers):
    s = event[headers.index('endtime')]
    time.timezone = 0
    time.altzone = 0
    time.daylight = 0
    year = int(s[0:4])
    month = int(s[5:7])
    day = int(s[8:10])
    hour = int(s[11:13])
    minute = int(s[14:16])
    second = int(s[17:19])
    return year,month,day,hour,minute,second

def parseMidTime(event,headers):
    a = parseStartTime(event,headers)
    b = parseEndTime(event,headers)
    return (a+b)/2# a and b are floats here, I'm pretty sure

def parseEventType(event,headers):
    s = event[headers.index('eventtype')]
    return s

def parseWave(event,headers):
    s = event[headers.index('channel')]
#    if s == ' AIA 193':#space is important
#        return '193'
#    elif s == 'HMI':
#        return '171'
#    elif s == 'H-alpha': # filaments
#        return '304'
#    else:
#        return '131'
    return s

def parseCenter(event,headers):
    s = event[headers.index('center')]
    s = s.strip('POINT()')
    nums = s.split(' ')
    return [int(nums[0]),int(nums[1])]

def parseBoundingBox(event,headers):
    s = event[headers.index('bbox')]
    s = s.strip('POLYGON()')
    points = [[int(s_num) for s_num in s_point.split(' ')] for s_point in s.split(',')]
    return points

def parseChainCode(event,headers):
    s = event[headers.index('ccode')]
    if s == 'NA' or s == '':
        return 'NA'
    else:
        s = s.strip('POLYGON()')
        points = [[int(s_num) for s_num in s_point.split(' ')] for s_point in s.split(',')]
        return points
    
