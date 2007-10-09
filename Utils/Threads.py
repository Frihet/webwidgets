import threading

class Counter(object):
    def __init__(self, value = 0):
        self.value = value - 1
        self.lock = threading.Lock()
    
    def __iter__(self):
        return self

    def next(self):
        self.lock.acquire()
        try:
            self.value += 1
            return self.value
        finally:
            self.lock.release()
