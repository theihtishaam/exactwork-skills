import unittest
from task_queue import TaskQueue

class ExistingTests(unittest.TestCase):
    def test_fifo(self):
        q=TaskQueue(2)
        q.put('a')
        q.put('b')
        self.assertEqual(q.get(),'a')
        self.assertEqual(q.get(),'b')

if __name__ == '__main__': unittest.main()
