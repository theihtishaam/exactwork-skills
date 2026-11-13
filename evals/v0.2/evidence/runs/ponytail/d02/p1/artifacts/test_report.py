import unittest
from copy import deepcopy
from report import summarize

class ExistingTests(unittest.TestCase):
    def test_simple(self):
        rows=[dict(id='a',currency='USD',direction='credit',amount='10.00',status='posted')]
        self.assertEqual(summarize(rows)['USD']['net_cents'],1000)

    def test_contract_regression(self):
        rows = [
            dict(id='a', currency='USD', direction='credit', amount='0.29', status='posted'),
            dict(id='a', currency='EUR', direction='credit', amount='3.00', status='posted'),
            dict(id='b', currency='USD', direction='debit', amount='0.29', status='posted'),
            dict(id='a', currency='USD', direction='credit', amount='0.29', status='posted'),
            dict(id='p', currency='USD', direction='credit', amount='not parsed', status='pending'),
        ]
        original = deepcopy(rows)

        self.assertEqual(summarize(rows), {
            'USD': {'credits_cents': 29, 'debits_cents': 29, 'net_cents': 0},
            'EUR': {'credits_cents': 300, 'debits_cents': 0, 'net_cents': 300},
        })
        self.assertEqual(rows, original)
        with self.assertRaises(ValueError):
            summarize([dict(id='a', currency='USD', direction='credit', amount='0.291', status='posted')])
        with self.assertRaises(ValueError):
            summarize(rows[:1] + [dict(id='a', currency='USD', direction='debit', amount='0.29', status='posted')])

if __name__ == '__main__': unittest.main()
