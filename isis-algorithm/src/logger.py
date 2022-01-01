import collections
import socket
import _thread
import time
import sys
import datetime
import json

HOST = '0.0.0.0'
PORT = sys.argv[1]
/Users/jdh0312/Code/CS425/mp1/mp1_node.py
threadCount = 0
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, int(PORT)))
s.listen(10)
graph = []
delay_dict = collections.defaultdict(list)
bandwidth_dict = collections.defaultdict(list)

def postProcess(graph):
    graph.sort()
    normalTime = graph[0][0]
    processed_graph = [(int(item[0]-normalTime), item[1]*1000, item[2]) for item in graph]
    for item in processed_graph:
        delay_dict[item[0]].append(item[1])
        bandwidth_dict[item[0]].append(item[2])

    with open('delay_dict.txt', 'w') as delay_file:
        delay_file.write(json.dumps(delay_dict))        

    with open('bandwidth_dict.txt', 'w') as bandwidth_file:
        bandwidth_file.write(json.dumps(bandwidth_dict))        

    # print(delay_dict)
    # print(bandwidth_dict)
    # {0: [0.0013091564178466797], 5: [0.00021600723266601562], 10: [0.00015020370483398438], 11: [0.0002579689025878906, 0.000225067138671875]}
    # {0: [88], 5: [88], 10: [87], 11: [88, 88]}




def connectionHandler(clientsocket, address, timeStamp):
    nodeName = ""
    try:
        printOnce = True
        while True:
            msg = clientsocket.recv(128).decode()
            if len(msg) == 0:
                break
            parsed = msg.split(" ")
            if printOnce:   
                nodeName = parsed[2]
                print(f'{timeStamp} - {nodeName} connected')
                printOnce = False
            currTime = time.time()
            graph.append((currTime, currTime-float(parsed[0]), len(msg.encode('utf-8'))))
            print(f'{parsed[0]} {parsed[2]} {parsed[1]}')

    finally:
        clientsocket.close()
        print(f'{time.time()} - {nodeName} disconnected')

try:
    while True:
        client, addr = s.accept()
        timeStamp = time.time()
        _thread.start_new_thread(connectionHandler,(client, addr, timeStamp))
        threadCount += 1

finally:
    s.close()
    postProcess(graph)


