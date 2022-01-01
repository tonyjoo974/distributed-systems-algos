import threading

# ref https://gist.github.com/benhoyt/8c8a8d62debe8e5aa5340373f9c509c7
class AtomicCounter:
    
    def __init__(self, initial=0):
        """Initialize a new atomic counter to given initial value (default 0)."""
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        """Atomically increment the counter by num (default 1) and return the
        new value.
        """
        with self._lock:
            self.value += num
            return self.value

    def max(self, num1):
        with self._lock:
            self.value = max(num1, self.value)
            return self.value



            