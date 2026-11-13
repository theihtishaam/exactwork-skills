import unittest
from latency import maximum_latency, mean_latency


class ExistingChecks(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(mean_latency([10, 30]), 20)

    def test_mean_counts_zero_and_ignores_missing_values(self):
        self.assertEqual(mean_latency([None, 0, 10]), 5)
        self.assertEqual(mean_latency([None, 0]), 0)

    def test_mean_without_valid_measurements(self):
        for values in ([], [None, None]):
            with self.subTest(values=values):
                self.assertIsNone(mean_latency(values))

    def test_maximum(self):
        self.assertEqual(maximum_latency([None, 0, 30]), 30)


if __name__ == "__main__":
    unittest.main()
