import unittest
from report import summarize

class ExistingTests(unittest.TestCase):
    def test_simple(self):
        rows=[dict(id='a',currency='USD',direction='credit',amount='10.00',status='posted')]
        self.assertEqual(summarize(rows)['USD']['net_cents'],1000)

if __name__ == '__main__': unittest.main()
