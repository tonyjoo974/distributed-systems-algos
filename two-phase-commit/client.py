# ./client clientID1 config.txt

import socket
import sys
import struct

CLIENT_ID = sys.argv[1]
CONFIG_FILE = sys.argv[2]


def packMessage(msg):
    msgSize = struct.pack('>I', len(msg))
    packedMessage = b'' + msgSize + msg.encode()
    return packedMessage

# in our code we assume that the first line of the config file is the coordinator
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    lines = []
    with open(CONFIG_FILE, 'r') as config_file:
        lines = config_file.readlines()
        for line in lines:
            line = line.rstrip('\n')    
            elems = line.split(" ") # branch name, address, port
            s.connect((elems[1], int(elems[2])))
            break
    try:
        while(True):
            line = input()
            msg = line.rstrip('\n')
            #print(msg)
            s.sendall(packMessage(msg))
            sizeRawBytes = s.recv(4) 
            while len(sizeRawBytes) != 4:
                nextByte = s.recv(1) # First 4 bytes will be the proto size   
                sizeRawBytes += nextByte
            msgSize = struct.unpack('>I', sizeRawBytes)[0]
            rawMsg = b""
            remainingDataSize = msgSize
            while remainingDataSize != 0:
                recoveredData = s.recv(remainingDataSize)
                rawMsg += recoveredData
                remainingDataSize = msgSize - len(rawMsg)
            msg = rawMsg.decode()
            if msg != "NO_OP":
                print(f"{msg}")
    except EOFError:
        pass
        #print("------- End Of File Reached --------")
