import random
import sys
import threading
import queue
import time

class LeaderElectionTimeout(threading.Thread):
    def __init__(self, timeoutCallback):
        threading.Thread.__init__(self)
        self.blockingTaskQueue = queue.Queue()
        self.timeoutCallback = timeoutCallback
        self.running = False

    def heartbeatbg(self):
        while True:
            try:
                #print("Heartbeat Waiting...", flush=True, file=sys.stderr)
                result = self.blockingTaskQueue.get(timeout = random.uniform(0.55, 0.85))
                if (result == "stop"):
                    self.running = False
                    break
            except queue.Empty:
                self.timeoutCallback()
                pass


    def run(self):
        self.running = True
        self.heartbeatbg()

    def stop(self):
        self.running = False
        self.blockingTaskQueue.put("stop")

    def restart(self):
        self.blockingTaskQueue.put("continue")

    def isStopped(self):
        return self.running == False
