from decimal import Decimal, InvalidOperation


def summarize(rows):
    totals = {}
    seen = {}
    for row in rows:
        status = row['status']
        if status not in ('posted', 'pending'):
            raise ValueError('invalid status')
        if status == 'pending':
            continue

        direction = row['direction']
        if direction not in ('credit', 'debit'):
            raise ValueError('invalid direction')
        try:
            amount = Decimal(row['amount'])
        except (InvalidOperation, ValueError):
            raise ValueError('invalid amount') from None
        if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValueError('invalid amount')

        identity = (row['currency'], row['id'])
        fingerprint = (direction, row['amount'], status)
        if identity in seen:
            if seen[identity] != fingerprint:
                raise ValueError('conflicting transaction')
            continue
        seen[identity] = fingerprint

        amount = int(amount * 100)
        bucket = totals.setdefault(row['currency'], {'credits_cents': 0, 'debits_cents': 0, 'net_cents': 0})
        key = 'credits_cents' if direction == 'credit' else 'debits_cents'
        bucket[key] += amount
        bucket['net_cents'] = bucket['credits_cents'] - bucket['debits_cents']
    return totals
