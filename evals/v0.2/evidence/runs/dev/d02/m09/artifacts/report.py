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

        retry_key = (row['currency'], row['id'])
        previous = seen.get(retry_key)
        if previous is not None:
            if row != previous:
                raise ValueError('conflicting posted rows')
            continue
        seen[retry_key] = row.copy()

        try:
            decimal_amount = Decimal(row['amount'])
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError('invalid amount') from None
        if not decimal_amount.is_finite() or decimal_amount < 0:
            raise ValueError('invalid amount')
        if decimal_amount.as_tuple().exponent < -2:
            raise ValueError('amount has more than two fractional digits')
        parts = decimal_amount.as_tuple()
        coefficient = int(''.join(map(str, parts.digits)))
        amount = coefficient * (10 ** (parts.exponent + 2))

        bucket = totals.setdefault(row['currency'], {'credits_cents': 0, 'debits_cents': 0, 'net_cents': 0})
        key = 'credits_cents' if direction == 'credit' else 'debits_cents'
        bucket[key] += amount
        bucket['net_cents'] = bucket['credits_cents'] - bucket['debits_cents']
    return totals


