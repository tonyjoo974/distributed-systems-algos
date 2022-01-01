# apython --serve :8889 -m example.echo 8888
# apython framework.py 2 ./raft
# python3.10 framework.py 3 ./raft
# python3.10 raft_partition_test.py 20
# python3.10 raft_election_test.py 20
# python3.10 raft_election_failure_test.py 9
# ------------ LOGGING TEST --------
# python3.10 raft_simple_log_test.py 9
# python3.10 raft_log5_test.py 9
# python3.10 raft_simple_log_test.py -d 3
# python3.10 raft_log_follower_failure_test.py 20
# python3.10 raft_log_follower_failure_test.py -d 
# python3.10 raft_log_follower_failure_test.py -d 3
# python3.10 raft_log_leader_failure_test.py 20
# python3.10 raft_log_partition_test.py 20
# pgrep -f "raft.py" | xargs kill                                                         
import sys
import asyncio
import threading
import time
from typing import Tuple
from LeaderElectionTimeout import LeaderElectionTimeout
from LeaderHeartbeatJob import LeaderHeartbeatJob
from datetime import datetime

class Raft:
    def __init__(self):
        self.nodeID = int(sys.argv[1])
        self.number_of_nodes = int(sys.argv[2].replace('add',''))
        #self.debug_file = open(f'{self.nodeID}_debug.txt', 'w')
        self.currentTerm = 1
        self.current_leader_node = None
        self.votedFor = None
        self.state = "Follower"
        self.leaderElectionTask = None
        self.updateLock = threading.Lock()

        # for log replication
        self.commitIndex = 0 # index of highest log entry known to be committed (initialized to 0, increases monotonically)
        # self.lastApplied = 0 # index of highest log entry applied to state machine (initialized to 0, increases monotonically)
        
        self.termAndEntries = [] # tuple (term, message) log entries; each entry contains command for state machine, and term when entry was received by leader (first index is 1)
        
        # leader's log replication (reinitialize when a node becomes a leader)
        self.nextIndex = [] # for each server, index of the next log entry to send to that server (initialized to leaderlast log index + 1)
        self.matchIndex = [] # for each server, index of highest log entryknown to be replicated on server(initialized to 0, increases monotonically)
        self.numAppendEntriesAgreed = []
        self.appendEntriesHeartbeat = None


    def dprint(self, msg, flush=True):
        #self.debug_file.write(msg + "\n")
        #self.debug_file.flush()
        if "log" in msg or "commit" in msg:
            self.debugPrint(msg)
        try:
            print(msg, flush=True)
        except BrokenPipeError:
            pass

    def debugPrint(self, msg, flush=True):
        pass
        #self.debug_file.write(msg + "\n")
        #self.debug_file.flush()
        #print(msg, file=sys.stderr, flush=True)

    def requestVote(self, destination, term):
        prevLogIndex = len(self.termAndEntries)-1
        prevLogTerm = -1
        if(prevLogIndex >= 0):
            prevLogTerm = self.termAndEntries[prevLogIndex][0]
        self.dprint(f"SEND {destination} RequestVote {term} {prevLogIndex} {prevLogTerm}", flush=True)

    def replyVote(self, destination, term, agreed):
        self.dprint(f"SEND {destination} RequestVotesResponse {term} {agreed}", flush=True)

    # For heartbeat
    def broadcastAppendEntries(self):
        for pid in range(self.number_of_nodes):
            if pid != self.nodeID:
                #self.sendAppendEntries(pid, self.currentTerm, self.commitIndex, None)
                if self.nextIndex[pid] == (len(self.termAndEntries)-1):
                    self.sendAppendEntries(pid, self.currentTerm, self.commitIndex, None)
                else:
                    prevLogIndex = self.nextIndex[pid]
                    content = None
                    termOfEntry = -1
                    # send the next term if we are ahead
                    if prevLogIndex+1 <= (len(self.termAndEntries)-1) and prevLogIndex+1 >= 0:
                        entry = self.termAndEntries[prevLogIndex+1]
                        content = entry[1]
                        termOfEntry = entry[0]
                    self.sendAppendEntries(pid, self.currentTerm, self.commitIndex, content, termOfEntry)

    # for new entries only
    def broadcastAppendEntriesWithEntry(self, entry):
        for pid in range(self.number_of_nodes):
            if pid != self.nodeID:
                self.sendAppendEntries(pid, self.currentTerm, self.commitIndex, entry, self.currentTerm)

    def sendAppendEntries(self, destination, term, commitIndex, entry, entryTerm=-1):
        prevLogIndex = self.nextIndex[destination] # len(self.termAndEntries)-1
        prevLogTerm = -1 
        if prevLogIndex > -1:
            prevLogTerm = self.termAndEntries[prevLogIndex][0]
        if entry is None: 
            self.debugPrint(f"HEARTBEAT to {destination} prevLogIndex {prevLogIndex} prevLogterm {prevLogTerm} currentTerm {self.currentTerm} {entryTerm}")
            self.dprint(f"SEND {destination} AppendEntries {term} {commitIndex} [] {prevLogIndex} {prevLogTerm} {entryTerm}", flush=True)
        else:
            self.debugPrint(f"sending to {destination} prevLogIndex {prevLogIndex} prevterm {prevLogTerm} entry {entry} commitIndex {self.commitIndex} {entryTerm}")
            self.dprint(f"SEND {destination} AppendEntries {term} {commitIndex} [{entry}] {prevLogIndex} {prevLogTerm} {entryTerm}", flush=True)

    def replyAppendEntries(self, destination, term, agreed, prevLogIndex):
        senderID = self.nodeID
        self.dprint(f"SEND {destination} AppendEntriesResponse {term} {agreed} {prevLogIndex} {senderID}", flush=True)

    def printLogStateOnly(self):
        if len(self.termAndEntries) >= 1:
            tupleLog = self.termAndEntries[-1]
            self.dprint(f"STATE log[{int(len(self.termAndEntries))}]=[{tupleLog[0]},\"{tupleLog[1]}\"]", flush=True)
            self.dprint(f"STATE commitIndex={self.commitIndex}", flush=True)

    def printState(self):
        self.dprint(f"STATE term={self.currentTerm}", flush=True)
        self.debugPrint(f"STATE term={self.currentTerm}", flush=True)
        self.dprint(f"STATE state=\"{self.state}\"", flush=True)
        self.debugPrint(f"STATE state=\"{self.state}\"", flush=True)
        if self.current_leader_node is not None:
            self.dprint(f"STATE leader={self.current_leader_node}", flush=True)
            self.debugPrint(f"STATE leader={self.current_leader_node}", flush=True)


    '''
    RECEIVE 0(source) RequestVotes 2(term)
    55218.948902874 0>STATE state=Candidate
    55218.948948452 Got exception <class 'json.decoder.JSONDecodeError'> Expecting value: line 1 column 1 (char 0) while processing line b'STATE state=Candidate\n' on 0
    '''
    def receiver(self):
        # line = RECEIVE 0 RequestVote 1
        for line in sys.stdin:
            #print("Receiver message...." + line, file=sys.stderr, flush=True)
            line = line.strip()
            self.debugPrint(line)
            params = line.split(" ")
            msgType = params[0]
            #print(f"MSGTYPE {msgType}", file=sys.stderr, flush=True)
            if msgType == 'RECEIVE':
                sourceNode = int(params[1])
                commandType = params[2]
                term = int(params[3])
                if commandType == 'RequestVote':
                    prevLogIndex = int(params[4])
                    prevLogTerm = int(params[5])
                    # lock this block
                    with self.updateLock:
                        if prevLogIndex > -1 and len(self.termAndEntries) > 0:
                            if self.termAndEntries[-1][0] > term:
                                self.replyVote(sourceNode, term, False)
                                continue
                            elif self.termAndEntries[-1][0] == term:
                                if prevLogIndex < (len(self.termAndEntries)-1):
                                    self.replyVote(sourceNode, term, False)
                                    continue
                        if self.currentTerm < term or self.votedFor is None:
                            self.votedFor = sourceNode
                            if self.state != "Follower":
                                self.debugPrint(f" ------------------------ I AM FOLLOWER NOW FROM REQUEST VOTE -------------------------")
                            if self.state == "Leader":
                                self.appendEntriesHeartbeat.stop()
                            self.state = "Follower"
                            self.currentTerm = term
                            self.agreedCountForTerm = 0
                            self.current_leader_node = None
                            self.printState()
                            self.replyVote(sourceNode, term, True)
                            self.safeRestartElectionTaskWrapper()  # reset timeout
                        else:
                            self.replyVote(sourceNode, term, False)
                elif commandType == 'RequestVotesResponse':
                    with self.updateLock:
                        agreed = str(params[4]).strip()
                        if agreed == 'True' and self.state == "Candidate" and self.currentTerm == term:
                            self.agreedCountForTerm += 1
                            self.debugPrint(f"Majority Check Leader Current Counter={self.agreedCountForTerm} Target={(self.number_of_nodes+1)//2}")
                            if self.agreedCountForTerm >= ((self.number_of_nodes)//2 +1) and self.state != "Leader": #majority
                                self.state = "Leader"
                                self.debugPrint(f"********** I AM LEADER NOT INITIALIZE ********************************")
                                self.current_leader_node = self.nodeID
                                self.printState()
                                self.initializeLeader()
                                self.broadcastAppendEntries()
                                self.leaderElectionTask.stop()
                                if self.appendEntriesHeartbeat is not None:
                                    self.appendEntriesHeartbeat.stop()
                                self.appendEntriesHeartbeat = LeaderHeartbeatJob(self.broadcastAppendEntries)
                                self.appendEntriesHeartbeat.start()        
                        elif agreed == "False":
                            pass
                elif commandType == 'AppendEntries':
                    term = int(params[3])
                    leaderCommitIndex = int(params[4])
                    entry = str(params[5]).replace('[', '').replace(']', '')
                    prevLogIndex = int(params[6])
                    prevLogTerm = int(params[7])
                    entryTerm = int(params[8])
                    #self.debugPrint(f"{self.nodeID} trying to append entry Entry={entry} prevLogIndex={prevLogIndex} prevLogTerm={prevLogTerm} length={len(self.termAndEntries)} initialAppend={initialAppend} prevEq={previousEntryAndTermEqual} leaderCommitIndex={leaderCommitIndex}")
                    #self.debugPrint(f"RECEIVE APPEND ENTRIES entry {entry} prevLogIndex {prevLogIndex} prevLogTerm {prevLogTerm} myTerm {self.currentTerm} leader term {term}")
                    with self.updateLock:
                        if self.currentTerm <= term:
                            if self.state == 'Leader':
                                self.appendEntriesHeartbeat.stop()
                                self.leaderElectionTask = LeaderElectionTimeout(self.timeoutHeartbeatHandler)
                                self.leaderElectionTask.start()
                            elif self.state == 'Follower':
                                self.leaderElectionTask.restart() # restart election timer

                            self.currentTerm = term
                            if self.state != "Follower":
                                self.debugPrint(f" ------------------------ I AM FOLLOWER NOW FROM APPEND ENTRIES {self.currentTerm} {term} -------------------------")
                            self.state = "Follower"
                            self.current_leader_node = sourceNode
                            self.votedFor = sourceNode
                            self.printState()

                            # drop extra entries
                            if len(self.termAndEntries) > prevLogIndex:
                                self.termAndEntries = self.termAndEntries[0:prevLogIndex+1]

                            initialAppend = (prevLogIndex == -1) and (len(self.termAndEntries) == 0)
                            previousEntryAndTermEqual = (prevLogIndex >= 0) and (prevLogIndex == (len(self.termAndEntries)-1)) and (prevLogTerm == self.termAndEntries[prevLogIndex][0])
                                 
                            self.debugPrint(f"APPENDENTRIES LOGIC CHECK Entry={entry} prevLogIndex={prevLogIndex} prevLogTerm={prevLogTerm} length={len(self.termAndEntries)} initialAppend={initialAppend} prevEq={previousEntryAndTermEqual} leaderCommitIndex={leaderCommitIndex}")
                            if prevLogIndex >= 0 and prevLogIndex <= (len(self.termAndEntries)-1):
                                self.debugPrint(f"My Prevlogterm is {self.termAndEntries[prevLogIndex][0]} length-1 {(len(self.termAndEntries)-1)} vs prevLogIndex {prevLogIndex}")
                            if initialAppend or previousEntryAndTermEqual:
                                self.debugPrint(f"Processing the appendentries request......")
                                if entry != "":
                                    self.termAndEntries.append((entryTerm, entry))
                                    self.debugPrint(f"MY LOGS {self.termAndEntries}")
                                    self.printLogStateOnly()
                                    self.replyAppendEntries(sourceNode, term, True, prevLogIndex)
                            else:
                                self.debugPrint(f"{self.nodeID} REPLIED FALSE TO {sourceNode} Term {term} PrevLogIndex {prevLogIndex}")
                                self.replyAppendEntries(sourceNode, term, False, prevLogIndex)      
                            # TODO maybe move somewhere  (maybe add more logic)                                                    
                            if (initialAppend or previousEntryAndTermEqual) and (leaderCommitIndex > self.commitIndex):
                                self.commitIndex = min(len(self.termAndEntries), leaderCommitIndex)     
                                self.printLogStateOnly()
                elif commandType == 'AppendEntriesResponse':
                    with self.updateLock:
                        agreed = str(params[-3])
                        prevLogIndex = int(params[-2])
                        senderID = int(params[-1])
                        if self.state == 'Leader':
                            if agreed == 'True':
                                self.nextIndex[senderID] = max(self.nextIndex[senderID], prevLogIndex+1) # use max to avoid old entries from coming in
                                self.debugPrint(f"receiving true AppendEntriesResponse from {senderID} prevLogIndex {prevLogIndex} self.nextIndex[senderID] {self.nextIndex[senderID]} numAppendEntriesAgreed {self.numAppendEntriesAgreed}")
                                #if prevLogIndex <= len(self.numAppendEntriesAgreed): # ignore agreed response from heartbeat
                                try:
                                    self.numAppendEntriesAgreed[prevLogIndex+1] += 1
                                except Exception:
                                    self.debugPrint(f"trying to access entry {prevLogIndex+1} numAppendEntriesAgreed {self.numAppendEntriesAgreed}")
                                    raise Exception
                                if self.numAppendEntriesAgreed[prevLogIndex+1] >= ((self.number_of_nodes)//2+1): #majority
                                    self.debugPrint(f" Majority Check comitIndex={self.commitIndex} prevLogIndex+2={prevLogIndex+2} {self.numAppendEntriesAgreed} ")                                    
                                    self.commitIndex = max(self.commitIndex, prevLogIndex+2)
                                    self.printLogStateOnly()
                            else:
                                time.sleep(0.05)
                                if(self.nextIndex[senderID] >= 0):
                                    self.nextIndex[senderID] -= 1
                                self.debugPrint(f"self.nextIndex {self.nextIndex} {self.termAndEntries}")
                                termAndEntryToRetrySend = self.termAndEntries[self.nextIndex[senderID]+1]                                
                                #self.debugPrint(f"retry sending to {senderID} commitIndex {self.commitIndex} term,content {termAndEntryToRetrySend}")
                                self.sendAppendEntries(senderID, termAndEntryToRetrySend[0], self.commitIndex, termAndEntryToRetrySend[1])
            elif msgType == 'LOG':
                if self.state == 'Leader':
                    with self.updateLock:
                        message = str(params[1])
                        self.termAndEntries.append((self.currentTerm, message))
                        self.debugPrint(f"MY LOGS {self.termAndEntries}")
                        self.numAppendEntriesAgreed.append(1)
                        self.printLogStateOnly()              
                        self.broadcastAppendEntriesWithEntry(message)      
            else:
                print("UNKNOWN COMMAND " + commandType, file=sys.stderr, flush=True)
        self.debugPrint("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ I AM OUT $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    def initializeLeader(self):
        self.debugPrint(f" ************************************ I AM LEADER NOW ***************************************")
        self.debugPrint(f" MY LOGS {self.termAndEntries}")
        self.nextIndex = []
        for _ in range(self.number_of_nodes):
            self.nextIndex.append(len(self.termAndEntries)-1)     
        self.numAppendEntriesAgreed = []
        for _ in range(len(self.termAndEntries)):
            self.numAppendEntriesAgreed.append(1)

    def timeoutHeartbeatHandler(self):
        with self.updateLock:
            self.currentTerm += 1
            self.state = "Candidate"
            self.agreedCountForTerm = 1
            self.votedFor = self.nodeID
            self.current_leader_node = None
            self.printState()
            for pid in range(self.number_of_nodes):
                if pid != self.nodeID:
                    self.requestVote(pid, self.currentTerm)
            self.safeRestartElectionTaskWrapper()
    
    def setLeaderElectionTask(self, task):
        self.leaderElectionTask = task

    def safeRestartElectionTaskWrapper(self):
        if self.leaderElectionTask.isStopped():
            self.leaderElectionTask = LeaderElectionTimeout(self.timeoutHeartbeatHandler)
            self.leaderElectionTask.start()
        else:
            self.leaderElectionTask.restart()        

def main():
    #init
    #print(f" sys argv dxh ***** {sys.argv}", flush=True, file=sys.stderr)
    raft = Raft()
    raft.debugPrint(f" ------------------------ I AM FOLLOWER NOW -------------------------")
    receiverThread = threading.Thread(target=raft.receiver)
    electionTimeoutJob = LeaderElectionTimeout(raft.timeoutHeartbeatHandler)
    raft.setLeaderElectionTask(electionTimeoutJob)
    electionTimeoutJob.start()    
    receiverThread.start() # start listening stdin


if __name__ == '__main__':
    main()

