import unittest
from latency import maximum_latency, mean_latency


class ExistingChecks(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(mean_latency([10, 30]), 20)

    def test_mean_zero_and_missing_values(self):
        cases = [
            ([None, 0, 30], 15),
            ([0, None, 0], 0),
            ([None, None], None),
            ([], None),
        ]
        for values, expected in cases:
            with self.subTest(values=values):
                self.assertEqual(mean_latency(values), expected)

    def test_maximum(self):
        self.assertEqual(maximum_latency([None, 0, 30]), 30)


if __name__ == "__main__":
    unittest.main()
