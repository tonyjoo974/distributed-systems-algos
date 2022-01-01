
class clientThread(threading.Thread):
    def __init__(self, name):
      threading.Thread.__init__(self)
      self.name = name
    def run(self):
        for (nodeName, nodeIp, nodePort) in NODE_INFOS:
            cprint("Trying to connect to: " + nodeName)
            thread = clientThreadWorker("client1", nodeName, nodeIp, nodePort)
            thread.start()
        #cprint(CLIENT_NODE_CONNECTIONS)

class clientThreadWorker(threading.Thread):
    def __init__(self, name, nodeName, nodeIp, nodePort):
      threading.Thread.__init__(self)
      self.name = name
      self.nodeName = nodeName
      self.nodeIp = nodeIp
      self.nodePort = nodePort
    def run(self):
        clientSocket = 0
        while True:
            try:
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientSocket.connect((self.nodeIp, int(self.nodePort))) #maybe move this to another thread
                cprint(f"Connection to {self.nodeName} success")
                CLIENT_NODE_CONNECTIONS.append(clientSocket)
                break
            except socket.error as ex:
                print(f"Couldn't connect to {self.nodeName}!!!!!")
                cprint(ex)
            finally:
                time.sleep(3)
        while True:
            time.sleep(1)
            clientSocket.sendall("test message".encode())
