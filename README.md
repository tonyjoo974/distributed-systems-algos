Distributed Systems Algorithms
-----

**ISIS algorithm**
* In an asynchronous system that keeps track of accounts, we use ISIS algorithm to ensure total ordering for handling trasactions. We handle failures via R-multicast and proper timeouts of a node. We test failure scenarios where arbitrary number of nodes may fail

**Raft Consensus**
* Implements the leader election and logging components of <a href="https://raft.github.io/raft.pdf/" target="_blank">Raft</a>

**Two Phase Commit (2PC) Protocol**
* Implements atomicity and consistency support for all objects managed by multiple servers in a distributed transaction system