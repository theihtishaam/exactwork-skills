from decimal import Decimal


def summarize(rows):
    totals = {}
    seen = set()
    for row in rows:
        if row['status'] != 'posted':
            continue
        if row['id'] in seen:
            continue
        seen.add(row['id'])
        amount = int(float(row['amount']) * 100)
        bucket = totals.setdefault(row['currency'], {'credits_cents': 0, 'debits_cents': 0, 'net_cents': 0})
        key = 'credits_cents' if row['direction'] == 'credit' else 'debits_cents'
        bucket[key] += amount
        bucket['net_cents'] = bucket['credits_cents'] - bucket['debits_cents']
    return totals
