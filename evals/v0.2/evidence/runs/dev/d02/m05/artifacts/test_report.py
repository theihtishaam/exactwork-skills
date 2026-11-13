import copy
import unittest

from report import summarize


class ExistingTests(unittest.TestCase):
    def test_simple(self):
        rows = [dict(id='a', currency='USD', direction='credit', amount='10.00', status='posted')]
        self.assertEqual(summarize(rows)['USD']['net_cents'], 1000)

    def test_currency_scoped_retries_and_opposing_transaction(self):
        rows = [
            dict(id='a', currency='USD', direction='credit', amount='0.29', status='posted'),
            dict(id='a', currency='USD', direction='credit', amount='0.29', status='posted'),
            dict(id='a', currency='EUR', direction='credit', amount='3.00', status='posted'),
            dict(id='b', currency='USD', direction='debit', amount='0.29', status='posted'),
        ]
        original = copy.deepcopy(rows)

        self.assertEqual(
            summarize(rows),
            {
                'USD': {'credits_cents': 29, 'debits_cents': 29, 'net_cents': 0},
                'EUR': {'credits_cents': 300, 'debits_cents': 0, 'net_cents': 300},
            },
        )
        self.assertEqual(rows, original)


if __name__ == '__main__':
    unittest.main()
