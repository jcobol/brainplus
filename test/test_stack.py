
import sys, os

sys.path.insert(0, "%s/../lib" % os.path.dirname(__file__))

import unittest
from brainplus import Stack

class TestStack(unittest.TestCase):
    
    def test_stack(self):
        s = Stack()
        s.push(12)
        self.assertEqual(len(s.stack), 1)
        self.assertEqual(s.stack[0], 12)
        val = s.pop()
        self.assertEqual(val, 12)
        self.assertEqual(s.is_empty(), True)

if __name__ == '__main__':
    unittest.main()
