from __future__ import division
from subprocess import call
import csv
import ast

#for wave in ['0193','0171','0094']:
for wave in ['0193']:
#  call("cat results/*_rooktemp_3DAYDEMO_"+wave+"_c_0=*_balance=Mirror_alphaS=*_alphaT=*_theta=0.7.results > res.txt", shell = True)
  call("cat results/*_rook_1DAY_"+wave+"_c_0=*_balance=Mirror_alpha=*theta=0.7.results > res.txt", shell = True)
  # shell = TRUE is UNSAFE for general user input (subject to script injection)
  # also, there may be a cleaner way to do this
  
  with open("res.txt") as f:
    data = [l for l in f.readlines()]
  # write simple data
  
  parsedData = []
  x = []
  for line in data:
    line = line[:-1] # ignore newline
    split = line.split(":")
    if split[0] == 'TP' or \
       split[0] == 'FP' or \
       split[0] == 'TN' or \
       split[0] == 'FN' or \
       split[0] == ' ' or  \
       split[0] == '' :
      pass
    else:
      datum = split[1]
      datum = datum.strip(" ")
      x.append(datum)
    if len(x) == 10:
      parsedData.append(x)
      x = []

  ##SIMPLE DISPLAY OF ALL DATA
  #csv_data.append(["event","neighborhood","dataset","alpha_s","alpha_t","balance","c_0","theta","accuracy","precision","recall"])
  #for element in parsedData:
  #  csv_data.append([str(x) for x in element])
  #break  
  
  for resultsTypeIterator in range(5):
    csv_data = []
    for event in ['AR','CH','FL','SG']:
      print event,wave
      blah =  [str(x/10) for x in range(11)] # build headers (alpha_s vals)
      blah.reverse()
      header = [event]+[str(x/10) for x in range(11)]
      csv_data.append(header)
      eventData = [x for x in parsedData if x[0] == event and x]
      derp = [['' for i in range(11)] for j in range(11)]
      for eventDatum in eventData:
        alpha = ast.literal_eval(eventDatum[3])
        alpha_s = alpha[0]
        alpha_t = alpha[1]
        accuracy = eventDatum[7]
        precision = eventDatum[8]
        recall = eventDatum[9]
        if resultsTypeIterator == 0:
          derp[int(float(alpha_s)*10)][int(float(alpha_t)*10)] = str(precision)+'/'+str(recall)
        elif resultsTypeIterator == 1:
          derp[int(float(alpha_s)*10)][int(float(alpha_t)*10)] = str(precision).strip('%')
        elif resultsTypeIterator == 2:
          derp[int(float(alpha_s)*10)][int(float(alpha_t)*10)] = str(recall).strip('%')
        elif resultsTypeIterator == 3:
          derp[int(float(alpha_s)*10)][int(float(alpha_t)*10)] = str(accuracy).strip('%')
        elif resultsTypeIterator == 4:
          pre = float(precision.strip('%'))
          rec = float(recall.strip('%'))
          F1 = 0 if pre+rec == 0 else (2*pre*rec)/(pre+rec)
          derp[int(float(alpha_s)*10)][int(float(alpha_t)*10)] = F1
  
      for x in derp:
        csv_data.append([blah.pop()]+x)
      csv_data.append([])
    if resultsTypeIterator == 0:
  # 'long' vs 'short' here is the temporal neighborhood size
  #    filename = "resultsPrecisionRecall"+wave+"long.csv"
      filename = "resultsPrecisionRecall"+wave+"short.csv"
    elif resultsTypeIterator == 1:
  #    filename = "resultsPrecision"+wave+"long.csv"
      filename = "resultsPrecision"+wave+"short.csv"
    elif resultsTypeIterator == 2:
  #    filename = "resultsRecall"+wave+"long.csv"
      filename = "resultsRecall"+wave+"short.csv"
    elif resultsTypeIterator == 3:
  #    filename = "resultsAccuracy"+wave+"long.csv"
      filename = "resultsAccuracy"+wave+"short.csv"
    elif resultsTypeIterator == 4:
  #    filename = "resultsF1"+wave+"long.csv"
      filename = "resultsF1"+wave+"short.csv"
  
    with open(filename,'w') as f:
      w = csv.writer(f)
      w.writerows(csv_data)
