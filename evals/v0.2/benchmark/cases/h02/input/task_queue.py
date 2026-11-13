class TaskQueue:
    def __init__(self, capacity, items=[]):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._items = items

    def put(self, item):
        self._items.append(item)
        if len(self._items) > self.capacity:
            raise OverflowError("queue full")

    def get(self):
        if not self._items:
            raise IndexError("queue empty")
        return self._items.pop(0)

    def __len__(self):
        return len(self._items)
