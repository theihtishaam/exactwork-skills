from decimal import Decimal, InvalidOperation


def _cents(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("amount must be a decimal string") from None

    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise ValueError("amount must be nonnegative with at most two decimal places")
    return int(amount * 100)


def summarize(rows):
    totals = {}
    seen = {}

    for row in rows:
        status = row['status']
        if status not in ('posted', 'pending'):
            raise ValueError("status must be posted or pending")
        if status == 'pending':
            continue

        direction = row['direction']
        if direction not in ('credit', 'debit'):
            raise ValueError("direction must be credit or debit")

        identity = (row['currency'], row['id'])
        record = (
            row['id'], row['currency'], direction, row['amount'], status,
        )
        if identity in seen:
            if seen[identity] != record:
                raise ValueError("conflicting posted rows share currency and id")
            continue

        amount = _cents(row['amount'])
        seen[identity] = record
        bucket = totals.setdefault(
            row['currency'],
            {'credits_cents': 0, 'debits_cents': 0, 'net_cents': 0},
        )
        key = 'credits_cents' if direction == 'credit' else 'debits_cents'
        bucket[key] += amount
        bucket['net_cents'] = bucket['credits_cents'] - bucket['debits_cents']

    return totals
