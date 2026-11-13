Repaired `summarize` to use exact decimal cents, currency-scoped retry detection,
conflict validation, and contract-valid statuses and directions without modifying
source records. Added and ran a focused regression test covering retries across
currencies, a legitimate opposing transaction, exact cents, and input preservation.
