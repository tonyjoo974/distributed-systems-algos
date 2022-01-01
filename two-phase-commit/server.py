# ./server A config.txt 2000
# ./server B config.txt 3000
# ./server C config.txt 4000
# pgrep -f "server" | xargs kill
# ./client clientID1 config.txt
# ps -fA | grep python

import sys
import socket
import threading
import time
import logging
from collections import defaultdict
import struct

BRANCH_ID = sys.argv[1]
CONFIG_FILE = sys.argv[2]
PORT = None #TODO change to reading from file

NODE_INFOS = [] # (branch,address,port)

PARTICIPANT_TO_COORDINATOR_CONNECTION = None               # participant ---> coordinator connection 
COORDINATOR_TO_PARTICIPANT_MAP_CONN = defaultdict(None) # coordinator ---> participants connection

QUEUE_COMMIT = []

BANK_DEPOSITS = defaultdict(int)
SHADOW_BANK_DEPOSITS = defaultdict(int)

TRANSACTION_STATE = "ABORTED" # BEGIN, ABORTED

def cprint(txt):
    print(txt)

def parseConfigFile():
    global PORT
    lines = []
    with open(CONFIG_FILE, 'r') as config_file:
        lines = config_file.readlines()
        for line in lines:
            line = line.rstrip('\n')    
            elems = line.split(" ")
            NODE_INFOS.append((elems[0], elems[1], elems[2]))
            if elems[0] == BRANCH_ID:
                PORT = int(elems[2])

def isCoordinator():
    return BRANCH_ID == NODE_INFOS[0][0]

def sendToCoordinator(msg):
    PARTICIPANT_TO_COORDINATOR_CONNECTION.sendall(msg)

def isClientMessage(msg):
    return msg.startswith("BEGIN") or msg.startswith("COMMIT") or msg.startswith("ABORT") or msg.startswith("DEPOSIT") or msg.startswith("WITHDRAW") or msg.startswith("BALANCE")

def packMessage(msg):
    msgSize = struct.pack('>I', len(msg))
    packedMessage = b'' + msgSize + msg.encode()
    return packedMessage

# ------------------------ PARTICIPANT CODE ----------------------------
def createConnectionToCoordinator():
    (branch, address, port) = NODE_INFOS[0]
    while True:
        try:
            PARTICIPANT_TO_COORDINATOR_CONNECTION = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            PARTICIPANT_TO_COORDINATOR_CONNECTION.connect((address, int(port))) #maybe move this to another thread
            cprint(f"Connection to branch {branch} {address} {port} success")
            break
        except socket.error as ex:
            cprint(f"Couldn't connect to {branch}!!!!! {address} {port} retrying....")
            cprint(ex)
            time.sleep(0.3)


# ------------------------ COORDINATOR CODE ----------------------------


def coordinatorCreateParticipantsConnection():
    global BRANCH_ID
    cprint("Connecting to NODE_INFOS as coordinator")
    for (branch, address, port) in NODE_INFOS:
        cprint("Trying to connect to: " + branch)
        while True:
            #if branch == BRANCH_ID:
                #cprint(f"skipping creating branch for {BRANCH_ID}")
                #break
            try:
                if branch == BRANCH_ID:
                    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    clientSocket.connect(("0.0.0.0", int(port))) #maybe move this to another thread
                    COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch] = clientSocket
                    cprint(f"Local connection to my own branch 0.0.0.0 {port} success")
                    break
                else:
                    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    clientSocket.connect((address, int(port))) #maybe move this to another thread
                    COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch] = clientSocket
                    cprint(f"Connection to {branch} {address} {port} success")
                    break
            except socket.error as ex:
                cprint(f"Couldn't connect to {branch}!!!!! {address} {port} retrying....")
                cprint(ex)
                time.sleep(0.3)
                
# ------------------------ SERVER CODE ----------------------------

# Coordinator only handles messages from client.py in this while loop
# Partipants only handles messages from client.py in this while loop
def connectionHandler(clientsocket, address):
    cprint(f"start connection handler")
    try:
        while True:
            sizeRawBytes = clientsocket.recv(4) 
            while len(sizeRawBytes) != 4:
                nextByte = clientsocket.recv(1) # First 4 bytes will be the proto size   
                sizeRawBytes += nextByte
                # // TODO investigate non blocking recv
                #if len(nextByte) == 0:
                #    cprint(f'Size Byte broken')
                #    break
            msgSize = struct.unpack('>I', sizeRawBytes)[0]
            rawMsg = b""
            remainingDataSize = msgSize
            while remainingDataSize != 0:
                recoveredData = clientsocket.recv(remainingDataSize)
                rawMsg += recoveredData
                remainingDataSize = msgSize - len(rawMsg)
            msg = rawMsg.decode()
            cprint(f"received {msg}")
            if isClientMessage(msg):
                coordinatorProcessMsg(msg, clientsocket)
            else:
                participantProcessMsg(msg, clientsocket)
    finally:
        clientsocket.close()
        cprint("------------disconnected-------------")
        raise RuntimeError("Socket Closed")

class ServerConnectionHandlerThread(threading.Thread):
   def __init__(self, name, client, addr):
      threading.Thread.__init__(self)
      self.name = name
      self.client = client
      self.addr = addr
   def run(self):
       connectionHandler(self.client, self.addr)

class ServerThread(threading.Thread):
   def __init__(self, name, serverSocket):
      threading.Thread.__init__(self)
      self.name = name
      self.serverSocket = serverSocket
   def run(self):
        cprint("Starting Server.... Waiting for connections....")
        server = self.serverSocket
        try:
            while True:
                client, addr = server.accept()
                cprint(f"Got Connection from {client} {addr}")
                connThread = ServerConnectionHandlerThread("conn", client, addr)
                connThread.start()
        finally:
            server.close()
            cprint("close server")


def setupServer():
    # starting server.........
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', int(PORT)))
    serverSocket.listen(5) # client py
    serverThread = ServerThread("Server" + BRANCH_ID, serverSocket)
    serverThread.start()


def setupCoordinator():
    coordinatorCreateParticipantsConnection()

def setupParticipant():
    createConnectionToCoordinator()

def main():
    parseConfigFile()
    cprint(f"{NODE_INFOS} COORDINATOR: {isCoordinator()}")

    setupServer()
    # connect to other servers if we are the coordinator......
    # assume that the coordinator if 
    if isCoordinator():
        setupCoordinator()
    else:
        setupParticipant()

#-------------- COORDINATOR PROCESS MSG -------------------------------- #

def blockAndRecvNextMessage(socket):
    sizeRawBytes = socket.recv(4) 
    while len(sizeRawBytes) != 4:
        nextByte = socket.recv(1) # First 4 bytes will be the proto size   
        sizeRawBytes += nextByte
        # // TODO investigate non blocking recv
        #if len(nextByte) == 0:
        #    cprint(f'Size Byte broken')
        #    break
    msgSize = struct.unpack('>I', sizeRawBytes)[0]
    rawMsg = b""
    remainingDataSize = msgSize
    while remainingDataSize != 0:
        recoveredData = socket.recv(remainingDataSize)
        rawMsg += recoveredData
        remainingDataSize = msgSize - len(rawMsg)
    return rawMsg.decode()

def multicastAndWaitForResponses(msg):
    # responsesMap = defaultdict(None)
    for branch, conn in COORDINATOR_TO_PARTICIPANT_MAP_CONN.items():
        #TODO make seperate thread
        conn.sendall(msg)
        result = blockAndRecvNextMessage(conn)
        if result.startswith("PART_ABORT"):
            return False
        # responsesMap[branch] = result
    return True


def coordinatorProcessMsg(msg, clientSocket):
    global TRANSACTION_STATE,COORDINATOR_TO_PARTICIPANT_MAP_CONN
    msg = msg.strip("\n")
    if msg.startswith("BEGIN"):
        # TODO for isolation keep track of TransactionID and clientSocket maps
        TRANSACTION_STATE = "BEGIN"
        multicastAndWaitForResponses(packMessage("COORD_BEGIN"))
        clientSocket.sendall(packMessage("OK"))
        return
    elif TRANSACTION_STATE == "ABORTED":
        # SKIP IF ALL MESSAGES IF TRANSACTION STATE IS ABORTED OR NOT YET BEGIN
        clientSocket.sendall(packMessage("NO_OP"))
        return
    elif msg.startswith("DEPOSIT"): #DEPOSIT B.bar 20
        params = msg.split(" ")
        branchDetail = params[1].split(".")
        branch = branchDetail[0]
        COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch].sendall(packMessage("COORD_"+msg))
        msg = blockAndRecvNextMessage(COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch])
        clientSocket.sendall(packMessage("OK"))
    elif msg.startswith("BALANCE"): #BALANCE A.foo
        params = msg.split(" ")
        branchDetail = params[1].split(".")
        branch = branchDetail[0]
        COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch].sendall(packMessage("COORD_"+msg))
        msg = blockAndRecvNextMessage(COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch])
        if msg == "NOT_FOUND":
            TRANSACTION_STATE = "ABORTED"
            multicastAndWaitForResponses(packMessage("COORD_DO_ABORT"))
            clientSocket.sendall(packMessage("NOT FOUND, ABORTED"))
        else:
            clientSocket.sendall(packMessage(msg))
        return
    elif msg.startswith("WITHDRAW"): #WITHDRAW B.bar 30
        params = msg.split(" ")
        branchDetail = params[1].split(".")
        branch = branchDetail[0]
        COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch].sendall(packMessage("COORD_"+msg))
        msg = blockAndRecvNextMessage(COORDINATOR_TO_PARTICIPANT_MAP_CONN[branch])
        if msg.startswith("NOT_FOUND"):
            TRANSACTION_STATE = "ABORTED"
            multicastAndWaitForResponses(packMessage("COORD_DO_ABORT"))            
            clientSocket.sendall(packMessage("NOT FOUND, ABORTED"))
        else:
            clientSocket.sendall(packMessage(msg))
        return
    elif msg.startswith("COMMIT"):
        # multicast to all branches and wait for all branches to response
        result = multicastAndWaitForResponses(packMessage("COORD_CAN_COMMIT"))
        if result:
            TRANSACTION_STATE = "ABORTED" #Commited
            multicastAndWaitForResponses(packMessage("COORD_DO_COMMIT"))
            clientSocket.sendall(packMessage("COMMIT OK"))
        else:
            TRANSACTION_STATE = "ABORTED"
            multicastAndWaitForResponses(packMessage("COORD_DO_ABORT"))
            clientSocket.sendall(packMessage("ABORTED"))
        return
    elif msg.startswith("ABORT"):
        TRANSACTION_STATE = "ABORTED"
        multicastAndWaitForResponses(packMessage("COORD_DO_ABORT"))
        clientSocket.sendall(packMessage("ABORTED"))
    else:
        cprint("UNKNOWN MESSAGE")
        clientSocket.sendall(packMessage(("UNKNOWN MESSAGE")))
        return

# --------------- PARTICIPANT PROCESS MSG ------------------------------ #


def participantProcessMsg(msg, coordinatorSocket):
    global SHADOW_BANK_DEPOSITS,BANK_DEPOSITS
    msg = msg.strip("\n")
    if msg.startswith("COORD_BEGIN"):
        SHADOW_BANK_DEPOSITS = BANK_DEPOSITS.copy()
        coordinatorSocket.sendall(packMessage("OK"))
        pass
    elif msg.startswith("COORD_CAN_COMMIT"):
        for val in SHADOW_BANK_DEPOSITS.values():
            if val < 0:
                coordinatorSocket.sendall(packMessage("PART_ABORT"))
                return
        coordinatorSocket.sendall(packMessage("OK"))
        return
    elif msg.startswith("COORD_DO_COMMIT"):
        BANK_DEPOSITS = SHADOW_BANK_DEPOSITS.copy()
        coordinatorSocket.sendall(packMessage("HAVE_COMMITED"))
        return    
    elif msg.startswith("COORD_DO_ABORT"):
        SHADOW_BANK_DEPOSITS = BANK_DEPOSITS.copy()
        coordinatorSocket.sendall(packMessage("HAVE_ABORTED"))
        return
    elif msg.startswith("COORD_DEPOSIT"):
        params = msg.split(" ")
        branchDetail = params[1].split(".")
        branch = branchDetail[0]
        account = branchDetail[1]
        amount = int(params[2])
        SHADOW_BANK_DEPOSITS[account] += amount
        coordinatorSocket.sendall(packMessage("OK"))
        return
    elif msg.startswith("COORD_WITHDRAW"):
        params = msg.split(" ")
        branchDetail = params[1].split(".")
        branch = branchDetail[0]
        account = branchDetail[1]
        amount = int(params[2])
        if account in SHADOW_BANK_DEPOSITS.keys():
            SHADOW_BANK_DEPOSITS[account] -= amount
            coordinatorSocket.sendall(packMessage("OK"))
        else:
            coordinatorSocket.sendall(packMessage("NOT_FOUND"))
        return
    elif msg.startswith("COORD_BALANCE"):
        params = msg.split(" ")
        branchDetail = params[1].split(".")
        branch = branchDetail[0]
        account = branchDetail[1]
        if account in SHADOW_BANK_DEPOSITS.keys():
            coordinatorSocket.sendall(packMessage(f"{branch}.{account} = {SHADOW_BANK_DEPOSITS[account]}"))
        else:
            coordinatorSocket.sendall(packMessage("NOT_FOUND"))
        return
    else:
        cprint(f"unknown msg{msg}")
                

if __name__ == '__main__':
    main()

