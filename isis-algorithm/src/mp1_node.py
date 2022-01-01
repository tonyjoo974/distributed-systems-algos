# kill -9 $(lsof -ti:1000,2000,3000)
# python3 -u gentx.py 5 | python3 mp1_node.py node1 1000 config_1.txt
# python3 -u gentx.py 5 | ./mp1_node node1 1000 config_1.txt
# python3 -u gentx.py | python3 mp1_node.py node1 1000 config_1.txt
# python3 -u gentx.py 5 | python3 mp1_node.py node2 2000 config_2.txt
# python3 -u gentx.py | python3 mp1_node.py node2 2000 config_2.txt
# python3 -u gentx.py 5 | python3 mp1_node.py node3 3000 config_3.txt
# python3 -u gentx.py 5 | python3 mp1_node_failed.py node3 3000 config_3.txt
# python3 -u gentx.py 5 | ./mp1_node node1 1000 config_1.txt
# python3 -u gentx.py 5 | ./mp1_node node2 2000 config_2.txt
# python3 -u gentx.py 5 | ./mp1_node node3 3000 config_3.txt

from collections import defaultdict
import sys
import socket
import threading
import time
from google import protobuf
import logging

from google.protobuf import message
import ncast as nc
import isis_pb2 as isismsg
import hashlib
import heapq
import atomiccounter 
import struct

HOST = '0.0.0.0'
NODE_NAME = sys.argv[1]
PORT = sys.argv[2]
CONFIG_FILE = sys.argv[3]
NODE_INFOS = [] # tuple of (nodeName, nodeIP, nodePort)

BANK_ACCOUNTS = defaultdict(int) #{ a : 0, b: 500}
CLIENT_NODE_CONNECTIONS_MAP = {}

MY_PROPOSED_GLOBAL_SEQUENCE = atomiccounter.AtomicCounter(initial = 0)
PROPOSED_PRIORITY_QUEUE = []
MAP_MESSAGE_ID_TO_MSG = {}
MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID = defaultdict(list)
PQ_LOCK = threading.Lock()
MESSAGE_ID_CTR = atomiccounter.AtomicCounter(initial = 0)
IS_READY_COUNTER = atomiccounter.AtomicCounter(initial = 0)


def setupLoggger(name, fileName, level=logging.INFO):
    """To setup as many loggers as you want"""
    with open(fileName, 'w') as config_file:
        pass

    handler = logging.FileHandler(fileName)        
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


#fileName = NODE_NAME + "_delivered_output.txt"
deliveredOrder = open(f'{NODE_NAME}_delivered_output.txt', 'w')
#debugFile = open(f'{NODE_NAME}_debug.txt', 'w')
debugMessageOrder = open(f'{NODE_NAME}_debug_message_order.txt', 'w')
delayLogger = setupLoggger("delay", f'{NODE_NAME}_delay_data.txt')
initiationTimeLogger = setupLoggger("initiation", f'{NODE_NAME}_initiation_data.txt')
bandwidthLogger = setupLoggger("bandwidth", f'{NODE_NAME}_bandwidth_data.txt')
debugLogger = setupLoggger("debug", f'{NODE_NAME}_debug.txt')


def cprint(strz):
    pass
    #print(strz)

def aprint(strz):
    pass
    #print(strz)

def dprint(strz):
    debugLogger.info(f"{strz}\n")
    # debugFile.flush()

NCAST = nc.NCast(CLIENT_NODE_CONNECTIONS_MAP, bandwidthLogger, debugLogger) #for multicast and unicast


def debugState():
    pass
    # dprint("----------------------------START DEBUG STATE--------------------------------------\n")
    # dprint(f"Proposed Priority Queue: Size: {len(PROPOSED_PRIORITY_QUEUE)} \n {PROPOSED_PRIORITY_QUEUE}")
    # dprint(f"Map Of Proposed Prioirty Queue: Size: {len(MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID)} \n {MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID}")
    # #dprint(f"MY_PROPOSED_GLOBAL_SEQUENCE: {MY_PROPOSED_GLOBAL_SEQUENCE}")
    # dprint("------------------------------END DEBUG STATE------------------------------------\n")


#protoTemp = isismsg.isis()
#protoTemp.ParseFromString(temp.SerializeToString())
#print(protoTemp)

# example = DEPOSIT g 57

# https://www.tutorialspoint.com/python/python_multithreading.htm
class ServerThread(threading.Thread):
   def __init__(self, name, serverSocket):
      threading.Thread.__init__(self)
      self.name = name
      self.serverSocket = serverSocket
   def run(self):
        cprint("Starting Server")
        server = self.serverSocket
        try:
            while True:
                client, addr = server.accept()
                connThread = ServerConnectionHandlerThread("conn", client, addr)
                connThread.start()
        finally:
            server.close()
            cprint("close server")

#rawMessage = protoMsg.message
#if False: 
#    processTransaction(rawMessage)
def processTransaction(protoMsg):
    rawMessage = protoMsg.message    
    splittedMessage = rawMessage.split(' ')
    cprint(f"Delivered: {protoMsg.message_id} ")
    dprint(f"Delivered: {protoMsg.message_id} proposedSequence: {protoMsg.proposed_sequence} proposedSequenceProcessId: {protoMsg.proposed_sequence_process_id} \n")

    if(splittedMessage[0] == "DEPOSIT"): #DEPOSIT e 23
        depositAccount = str(splittedMessage[1])
        depositAmount = int(str(splittedMessage[2]))
        BANK_ACCOUNTS[depositAccount] += depositAmount
    elif(splittedMessage[0] == "TRANSFER"): #TRANSFER f -> j 24
        transferAmount = int(str(splittedMessage[4]))
        transferFrom = str(splittedMessage[1])
        transferTo = str(splittedMessage[3])
        if (BANK_ACCOUNTS[transferFrom] - transferAmount) >= 0:
            BANK_ACCOUNTS[transferFrom] -= transferAmount
            BANK_ACCOUNTS[transferTo] += transferAmount
    sorted_accounts = dict(sorted(BANK_ACCOUNTS.items()))
    print(f'BALANCES {"".join(f"{key}:{value} " for key, value in sorted_accounts.items())}\n')
    #deliveredOrder.write(f'BALANCES {"".join(f"{key}:{value} " for key, value in sorted_accounts.items())}\n')
    #deliveredOrder.flush()
    delayLogger.info(f'{time.time()} {protoMsg.message_id}')

def deliverAttempt():
    #print(f"Deliver Attempt Agreed Priority Queue: {AGREED_PRIORITY_QUEUE}, Proposed Queue: {PROPOSED_PRIORITY_QUEUE}")
    #if len(AGREED_PRIORITY_QUEUE) > 0 and len(PROPOSED_PRIORITY_QUEUE) > 0:
        #dprint(f"Deliver Attempt Agreed Priority Queue[0]: {AGREED_PRIORITY_QUEUE[0]}, Proposed Queue[0]: {PROPOSED_PRIORITY_QUEUE[0]}")
    while len(PROPOSED_PRIORITY_QUEUE) > 0 and PROPOSED_PRIORITY_QUEUE[0][2].is_agreed:
        poppedMsg = heapq.heappop(PROPOSED_PRIORITY_QUEUE)[2] #TODO handle failures
        debugState()
        #R-multicast for messages that we have the agreed sequence
        if(poppedMsg.message_owner_process_id != NODE_NAME):
           NCAST.multicast(poppedMsg.SerializeToString())
        # Deliver
        processTransaction(poppedMsg)

def handleFailureForMessageOwner(nodeNameFailed):
    """
    Minimum for R-multicast is 2 x OWD, 1 OWD for waiting for the message to arrive from the dead node
    to another alive node. another 1x OWD for waiting the rebroadcast to arrive at our node
    (minimum is 10 seconds, we add 5 additional seconds for processing delay
    """
    time.sleep(15) 
    with PQ_LOCK:
        del CLIENT_NODE_CONNECTIONS_MAP[nodeNameFailed]
        for elem in PROPOSED_PRIORITY_QUEUE:
            if elem[2].message_owner_process_id == nodeNameFailed:
                PROPOSED_PRIORITY_QUEUE.remove(elem)
        for elem in PROPOSED_PRIORITY_QUEUE:
            protoMsg = elem[2]
            if (len(MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[protoMsg.message_id]) == (len(CLIENT_NODE_CONNECTIONS_MAP)+1)):
                maxTuple = max(MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[protoMsg.message_id])
                MY_PROPOSED_GLOBAL_SEQUENCE.max(maxTuple[0])
                protoMsg.proposed_sequence = maxTuple[0]
                protoMsg.proposed_sequence_process_id = maxTuple[1]
                protoMsg.sender_process_id = NODE_NAME
                protoMsg.is_agreed = True
                for elem2 in PROPOSED_PRIORITY_QUEUE:
                    if elem2[2].message_id == protoMsg.message_id:
                        PROPOSED_PRIORITY_QUEUE.remove(elem2)
                        heapq.heappush(PROPOSED_PRIORITY_QUEUE, (protoMsg.proposed_sequence, protoMsg.proposed_sequence_process_id, protoMsg))      
                        break

                result = NCAST.multicast(protoMsg.SerializeToString())
                #if len(result) > 0:
                #    handleFailureForMessageOwner(nodeNameFailed)
                del(MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[protoMsg.message_id])
        heapq.heapify(PROPOSED_PRIORITY_QUEUE)                      
        deliverAttempt()


def connectionHandler(clientsocket, address):
    try:
        # wait until we have connections to all the other nodes before starting to listen so
        # that multicast will not fail
        while True:
            if len(NODE_INFOS) == len(CLIENT_NODE_CONNECTIONS_MAP):
                break
            else:
                time.sleep(0.1)          

        #ready = False
        while True:
            try:
                # parsing END-------- TODO move this to another function
                sizeRawBytes = clientsocket.recv(4) 
                #print(f"Received Size Bytes {sizeRawBytes}")
                while len(sizeRawBytes) != 4:
                    nextByte = clientsocket.recv(1) # First 4 bytes will be the proto size   
                    sizeRawBytes += nextByte
                    if len(nextByte) == 0:
                        cprint(f'Size Byte broken')
                        break
                protobufDataSize = struct.unpack('>I', sizeRawBytes)[0]
                protoBufRawMsg = b""
                remainingDataSize = protobufDataSize
                while remainingDataSize != 0:
                    recoveredData = clientsocket.recv(remainingDataSize)
                    protoBufRawMsg += recoveredData
                    remainingDataSize = protobufDataSize - len(protoBufRawMsg)
                    if remainingDataSize != 0:
                        cprint(f" WATCHOUT!!! Remaining Data Size {remainingDataSize} recovered length: {len(recoveredData)} current size: {len(protoBufRawMsg)} expected size: {protobufDataSize} ")
                        cprint(f"WATCHOUT!!! recovered data: {recoveredData}")
                        cprint(f"WATCHOUT!!! raw protomsg: {protoBufRawMsg}")
                        cprint(f"WATCHOUT!!! raw message: {sizeRawBytes} raw message: {len(sizeRawBytes)}")
            except struct.error as e:
                cprint(f"encountered error {e} sizeRawBytes: {sizeRawBytes}")
                if len(clientsocket.recv(0)) == 0:    
                    cprint(f'disconnected from: {address}')
                    break                    
                continue

            bandwidthLogger.info(f"{time.time()} {protobufDataSize+4}") # +4 for size byte integer
            protoMsg = isismsg.isis()
            try:
                parsedSize = protoMsg.ParseFromString(protoBufRawMsg)
                if parsedSize != protobufDataSize:
                    cprint(f"ENCOUNTERED ERROR WHEN PARSING SIZE NOT EQUAL: {protoBufRawMsg} \n parsedSize: {parsedSize} remainingSize: {remainingDataSize} protobufsize: {protobufDataSize} recoveredLength: {protoBufRawMsg}")
                    cprint(f"ERRORS: sizeRawBytes={sizeRawBytes}, sizeRawBytesLength = {len(sizeRawBytes)}")
            except Exception as e:
                cprint(" ENCOUNTERED ERROR WHEN PARSING: ", protoBufRawMsg)
                cprint(f"EXCEPTION: {e}")
                continue
            #print(f"Receive Message ID = {protoMsg.message_id} from =  {protoMsg.sender_process_id} rawProto = {protoBufRawMsg}")
            #dprint(f"Received Proto from {protoMsg.sender_process_id}: \n {protoMsg} -------------------------- \n")
            if(protoMsg.message_owner_process_id == NODE_NAME): # OUR MESSAGE (process reply message)  # MASTER (Message Initator)
                with PQ_LOCK:
                    MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[protoMsg.message_id].append((protoMsg.proposed_sequence, protoMsg.sender_process_id))
                if len(MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[protoMsg.message_id]) == (len(CLIENT_NODE_CONNECTIONS_MAP)+1):
                    # AGREED_PRIORITY_QUEUE = [(2,3)]
                    # PROPOSED_PRIORITY_QUEUE = [(1,1,protobuf_object), (1,3,protobuf_object)]
                    # pop PROPOSED_PRIORITY_QUEUE = [(1,1,protobuf_object)]
                    with PQ_LOCK:
                        maxTuple = max(MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[protoMsg.message_id])
                        MY_PROPOSED_GLOBAL_SEQUENCE.max(maxTuple[0])
                        protoMsg.proposed_sequence = maxTuple[0]
                        protoMsg.proposed_sequence_process_id = maxTuple[1]
                        protoMsg.sender_process_id = NODE_NAME
                        protoMsg.is_agreed = True
                        for elem in PROPOSED_PRIORITY_QUEUE:
                            if elem[2].message_id == protoMsg.message_id:
                                PROPOSED_PRIORITY_QUEUE.remove(elem)
                                heapq.heapify(PROPOSED_PRIORITY_QUEUE)                      
                                heapq.heappush(PROPOSED_PRIORITY_QUEUE, (protoMsg.proposed_sequence, protoMsg.proposed_sequence_process_id, protoMsg))      
                                break
                    debugState()
                    NCAST.multicast(protoMsg.SerializeToString())
                    with PQ_LOCK:
                        deliverAttempt()
                    del(MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[protoMsg.message_id])
            else: # CLIENT (all other processes)
                # not owner of the message, send back to owner with MY_PROPOSED_GLOBAL_SEQUENCE + 1
                if not protoMsg.is_agreed:
                    with PQ_LOCK:
                        destinationProcessId = protoMsg.sender_process_id
                        protoMsg.sender_process_id = NODE_NAME
                        protoMsg.proposed_sequence = MY_PROPOSED_GLOBAL_SEQUENCE.increment()
                        protoMsg.proposed_sequence_process_id = NODE_NAME
                        heapq.heappush(PROPOSED_PRIORITY_QUEUE, (protoMsg.proposed_sequence, NODE_NAME, protoMsg)) # (proposed_sequence, process_id, protobuf_object)
                    debugState()
                    #dprint(f"Sending Proto To {destinationProcessId}: \n {protoMsg} -------------------------- \n")
                    result = NCAST.unicast(protoMsg.SerializeToString(), destinationProcessId)
                    # with PQ_LOCK:
                    #     # Handle Failure
                    #     if not result:
                    #         for elem in PROPOSED_PRIORITY_QUEUE:
                    #             if elem[2].message_owner_process_id == destinationProcessId:
                    #                 PROPOSED_PRIORITY_QUEUE.remove(elem)
                    #         print(f"process reply failed to {destinationProcessId}")
                    #         heapq.heapify(PROPOSED_PRIORITY_QUEUE)
                    #         if destinationProcessId in CLIENT_NODE_CONNECTIONS_MAP: # might be deleted by function 120 first
                    #             del CLIENT_NODE_CONNECTIONS_MAP[destinationProcessId]
                            #NCAST.multicast(protoMsg)
                else:   
                    # Message Order has been finalized, update the sequences in our queue and push that proto that was agreed to our PQ
                    with PQ_LOCK:   
                        MY_PROPOSED_GLOBAL_SEQUENCE.max(protoMsg.proposed_sequence)
                        for elem in PROPOSED_PRIORITY_QUEUE:
                            if elem[2].message_id == protoMsg.message_id:
                                PROPOSED_PRIORITY_QUEUE.remove(elem)
                                heapq.heapify(PROPOSED_PRIORITY_QUEUE)
                                heapq.heappush(PROPOSED_PRIORITY_QUEUE, (protoMsg.proposed_sequence, protoMsg.proposed_sequence_process_id, protoMsg))                            
                                break
                        deliverAttempt()
                    debugState()                    
            #cprint(f'Length {len(msg)} Server Received: {protoMsg}')
    finally:
        clientsocket.close()
        cprint('disconnected')


class ServerConnectionHandlerThread(threading.Thread):
   def __init__(self, name, client, addr):
      threading.Thread.__init__(self)
      self.name = name
      self.client = client
      self.addr = addr
   def run(self):
       connectionHandler(self.client, self.addr)

def createClientConnections():
    for (nodeName, nodeIp, nodePort) in NODE_INFOS:
        cprint("Trying to connect to: " + nodeName)
        while True:
            try:
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientSocket.connect((nodeIp, int(nodePort))) #maybe move this to another thread
                cprint(f"Connection to {nodeName} success")
                CLIENT_NODE_CONNECTIONS_MAP[nodeName] = clientSocket
                break
            except socket.error as ex:
                cprint(f"Couldn't connect to {nodeName}!!!!! {nodeIp} {nodePort} retrying....")
                cprint(ex)
                time.sleep(0.3)

# parse config file
lines = []
with open(CONFIG_FILE, 'r') as config_file:
    lines = config_file.readlines()
numberOfNodes = int(lines[0].rstrip('\n'))
for line in lines[1:]:
    line = line.rstrip('\n')    
    elems = line.split(" ")
    NODE_INFOS.append((elems[0], elems[1], elems[2]))

# Create new server thread and client threads and initialize connections
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, int(PORT)))
serverSocket.listen(10)
thread1 = ServerThread("Server", serverSocket)
thread1.start()
createClientConnections()

# multicast STDIN + ISIS

# heapq.heappush(PROPOSED_PRIORITY_QUEUE, (1,1))
# [(1,1), (2,1), (2,2)]

# send multicast for initial ACK for readiness

#NCAST.multicast(NODE_NAME.encode())
#while True:
#    if IS_READY_COUNTER.value == len(CLIENT_NODE_CONNECTIONS_MAP):
#       break
#    else:
#       time.sleep(0.1)          

for line in sys.stdin:
    temp = isismsg.isis()
    temp.proposed_sequence_process_id = NODE_NAME
    temp.message_owner_process_id = NODE_NAME
    temp.sender_process_id = NODE_NAME
    temp.message_id = hashlib.md5(line.encode()).hexdigest()
    temp.message_id = str(NODE_NAME) + ":" + str(MESSAGE_ID_CTR.increment())
    temp.message = line
    temp.is_agreed = False
    cprint(f"Sending Message ID = {temp.message_id}")

    MAP_MESSAGE_ID_TO_MSG[temp.message_id] = temp
    with PQ_LOCK:
        temp.proposed_sequence = MY_PROPOSED_GLOBAL_SEQUENCE.increment()
        MAP_OF_PROPOSED_SEQUENCES_FOR_MESSAGE_ID[temp.message_id].append((temp.proposed_sequence, temp.proposed_sequence_process_id))
        heapq.heappush(PROPOSED_PRIORITY_QUEUE, (temp.proposed_sequence, temp.proposed_sequence_process_id, temp)) # (proposed_sequence, process_id, protobuf_object)
    debugState()
    rawBytes = temp.SerializeToString()
    temp3 = isismsg.isis()
    temp3bytes = temp3.ParseFromString(rawBytes)
    if temp3bytes != len(rawBytes):
        cprint("EMERGENCY ERROR!!! SERIALIZING WRONG")
    initiationTimeLogger.info(f"{time.time()} {temp.message_id}")
    result = NCAST.multicast(rawBytes)
    if len(result) > 0:
        for nodeNameFailed in result:
            handleFailureForMessageOwner(nodeNameFailed)
    
deliveredOrder.close()
