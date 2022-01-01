import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import math
import sys

#bandWidthFile = "node_bandwidth_data_copy.txt"
#delayFile = "node2_delay_data.txt"
HOST_COUNT = int(sys.argv[1])
# DIRECTORY = sys.argv[2] + "/"
DIRECTORY = ""


bandwidthGraphOffset = 30
bandwidthGraphEndTrim = 40
delayGraphOffset = 100
delayGraphTrim = 0

totalBandwidthDict = defaultdict(list)
colors = ["tomato", "mediumorchid", "lightsalmon", "indigo", "lime", "seagreen", "blue", "red"]
for i in range(1, int(HOST_COUNT) + 1):
    bandWidthArray = []
    bandwidthDict = defaultdict(list)
    bandWidthFile = DIRECTORY + f"node{i}_bandwidth_data.txt"
    with open(bandWidthFile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            elems = line.split(" ")
            bandWidthArray.append((math.floor(float(elems[0])), int(elems[1].strip("\n"))))
        sortedBandwidth = sorted(bandWidthArray)
        normalizedBandwidth = []
        smallest = min(sortedBandwidth)
        for time, size in sortedBandwidth:
            key = int(time-smallest[0])
            bandwidthDict[key].append(size)
            totalBandwidthDict[key].append(size)
        #sortedNormalizedBandwidth = sorted(normalizedBandwidth)
        #print(sortedNormalizedBandwidth)
        plotArray = []
        for time, sizeList in bandwidthDict.items():
            plotArray.append(np.sum(sizeList))
    plt.plot(plotArray[bandwidthGraphOffset:len(plotArray)-bandwidthGraphEndTrim], color=colors[i-1], label=f"node{i}")
plt.ylabel("Bytes")
plt.xlabel("Time (seconds)")
plt.legend()
plt.savefig(DIRECTORY + "bandwidth.png")
plt.clf()

totalBandwidthPlotArray = []
for time, sizeList in totalBandwidthDict.items():
    totalBandwidthPlotArray.append(np.sum(sizeList))
    
plt.plot(totalBandwidthPlotArray[bandwidthGraphOffset:len(plotArray)-bandwidthGraphEndTrim], color="blue", label=f"total bandwidth")
plt.ylabel("Bytes")
plt.xlabel("Time (seconds)")
plt.legend()
plt.savefig(DIRECTORY + "total_bandwidth.png")
plt.clf()

#--------------DELAY-------------

initiationDelayMap = defaultdict(float)
for i in range(1, int(HOST_COUNT) + 1):
    initiationFile = DIRECTORY + f"node{i}_initiation_data.txt"
    with open(initiationFile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            elems = line.split(" ")
            msgId = elems[1].strip("\n")
            initiationDelayMap[msgId] = float(elems[0])

delayListArray = defaultdict(list)
indexMap = defaultdict(int)
index = 0
for i in range(1, int(HOST_COUNT) + 1):
    delayFile = DIRECTORY + f"node{i}_delay_data.txt"
    with open(delayFile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            elems = line.split(" ")
            msgId = elems[1].strip("\n")
            indexMap[msgId] = index
            delayListArray[msgId].append(float(elems[0]))
            index += 1
    
minDelayArray = []
maxDelayArray = []
difo = []
indexMap = dict(sorted(indexMap.items(), key=lambda x:x[1]))
for msgId, index in indexMap.items():
    temp = []
    timestampsOfProcessedForMessageId = delayListArray[msgId]
    initiationTimestampForMessageId = initiationDelayMap[msgId]
    for elem in timestampsOfProcessedForMessageId:
        delay = elem - initiationTimestampForMessageId
        temp.append((msgId,delay, elem, initiationTimestampForMessageId))
    minDelay = min(timestampsOfProcessedForMessageId) - initiationTimestampForMessageId
    maxDelay = max(timestampsOfProcessedForMessageId) - initiationTimestampForMessageId
    minDelayArray.append(minDelay)
    maxDelayArray.append(maxDelay)
    difo.append(temp)

#print(difo)
#print(minDelayArray)
#print(maxDelayArray)
plt.plot(maxDelayArray[delayGraphOffset:len(maxDelayArray) - delayGraphTrim], color="tomato", label=f"max")
plt.ylabel("Delay seconds")
plt.xlabel("Message Counter")
plt.legend()
plt.savefig(DIRECTORY + "delay_max.png")
plt.clf()

plt.plot(minDelayArray[delayGraphOffset:len(minDelayArray) - delayGraphTrim], color="blue", label=f"min")
plt.ylabel("Delay seconds")
plt.xlabel("Message Counter")
plt.legend()
plt.savefig(DIRECTORY + "delay_min.png")
plt.clf()

plt.plot(minDelayArray[delayGraphOffset:len(minDelayArray) - delayGraphTrim], color="blue", label=f"min")
plt.plot(maxDelayArray[delayGraphOffset:len(maxDelayArray) - delayGraphTrim], color="tomato", label=f"max")
plt.ylabel("Delay seconds")
plt.xlabel("Message Counter")
plt.legend()
plt.savefig(DIRECTORY + "delay.png")
plt.clf()
