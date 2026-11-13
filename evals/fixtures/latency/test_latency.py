import unittest
from latency import maximum_latency, mean_latency


class ExistingChecks(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(mean_latency([10, 30]), 20)

    def test_maximum(self):
        self.assertEqual(maximum_latency([None, 0, 30]), 30)


if __name__ == "__main__":
    unittest.main()
