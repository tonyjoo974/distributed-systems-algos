import time
import struct

class NCast:
    def __init__(self, clientNodeConnections, logger, debugLogger):
        self.clientNodeConnections = clientNodeConnections
        self.logger = logger
        self.debugLogger = debugLogger

    def multicast(self, msg):
        failedNodes = []

        #start = time.process_time()
        for name, clientNodeConnection in self.clientNodeConnections.items():
            sizeBytes = struct.pack('>I', len(msg))
            #print(f"MC sent messageLength: {sizeBytes}")
            #print(f"MC sent message: {msg}")
            try:
                clientNodeConnection.sendall(sizeBytes + msg)
                self.logger.info(f"{time.time()} {len(msg)+4}")
            except Exception as e:
                self.debugLogger.info(f"From Multicast: {name} has died {e}")
                failedNodes.append(name)
        #print(f"Multicast took: {time.process_time() - start}")
        return failedNodes

    def unicast(self, msg, nodeName):
        sizeBytes = struct.pack('>I', len(msg))
        #print(f"MC sent messageLength: {sizeBytes}")
        #print(f"UC sent message: {msg} ")
        try:
            if nodeName in self.clientNodeConnections:
                self.clientNodeConnections[nodeName].sendall(sizeBytes + msg)
                self.logger.info(f"{time.time()} {len(msg)+4}")
                return True
            else:
                return False
        # except BrokenPipeError as e:
        except Exception as e:
            self.debugLogger.info(f"From Unicast: {nodeName} has died {e}")
            return False

    
    def recoverNextRawMessageFromSocket(self, clientSocket):
        msg = clientSocket.recv(4) 
        if len(msg) == 0:
            return ""
        else:
            protobufDataSize = struct.unpack('>I', msg)[0]
            protoBufRawMsg = b""
            remainingDataSize = protobufDataSize
            while(remainingDataSize != 0):
                protoBufRawMsg += clientSocket.recv(remainingDataSize)
                remainingDataSize = protobufDataSize - len(protoBufRawMsg)
            return protoBufRawMsg

