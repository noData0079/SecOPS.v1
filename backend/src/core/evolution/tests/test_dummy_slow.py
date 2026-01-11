
import unittest
from backend.src.core.evolution.dummy_slow import slow_sum

class TestDummySlow(unittest.TestCase):
    def test_slow_sum(self):
        # sum of 0..4 is 0+1+2+3+4 = 10
        self.assertEqual(slow_sum(5), 10)
        self.assertEqual(slow_sum(10), 45)
        self.assertEqual(slow_sum(1), 0)
        self.assertEqual(slow_sum(0), 0)

if __name__ == '__main__':
    unittest.main()
