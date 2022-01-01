import socket
import sys

HOST = sys.argv[2]
NODE_NAME = sys.argv[1]
PORT = sys.argv[3]


with socket.socket(/Users/jdh0312/Code/CS425/mp1/logger.pysocket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    for line in sys.stdin:
        encodedString = (line.rstrip()+" "+NODE_NAME).encode()
        #s.sendall(encodedString)  # sends the message to the server
        # data = s.recv(1024)  # receives the server's message
