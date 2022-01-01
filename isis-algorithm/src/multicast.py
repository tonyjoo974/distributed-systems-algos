class Multicast:
    def __init__(self, clientNodeConnections):
        self.clientNodeConnections = clientNodeConnections
        
    def send(self, msg):
        for clientNodeConnection in self.clientNodeConnections:
            clientNodeConnection.sendall(msg.encode())
