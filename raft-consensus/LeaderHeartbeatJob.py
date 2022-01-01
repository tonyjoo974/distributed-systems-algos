import random
import sys
import threading
import queue
import time

class LeaderHeartbeatJob(threading.Thread):
    def __init__(self, broadcastHeartbeat=None):
        threading.Thread.__init__(self)
        self.blockingTaskQueue = queue.Queue()
        self.broadcastHeartbeat = broadcastHeartbeat
        self.running = False

    def heartbeatbg(self):
        while True:
            try:
                self.running = True               
                result = self.blockingTaskQueue.get(timeout = 0.15)
                if (result == "stop"):
                    self.running = False
                    break
            except queue.Empty:
                if self.broadcastHeartbeat is not None:
                    self.broadcastHeartbeat()
                pass

    def run(self):
        self.heartbeatbg()

    def stop(self):
        self.blockingTaskQueue.put("stop")

    def restart(self):
        self.blockingTaskQueue.put("continue")
        
    def overrideBroadcast(self, broadcastHeartbeat):
        self.broadcastHeartbeat = broadcastHeartbeat