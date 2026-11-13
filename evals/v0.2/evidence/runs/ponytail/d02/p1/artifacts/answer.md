Fixed `summarize` to use exact decimal cents, deduplicate by `(currency, id)`, reject conflicting retries and invalid posted values/statuses, preserve gross totals, and leave input rows unchanged.

Added a focused contract regression test covering cross-currency IDs, exact cents, retries, pending rows, conflicts, excess precision, and source preservation. `python -m unittest -v` passes 2 tests.

Skipped dependencies and unrelated files. Remaining risk: validation is scoped to the transaction fields and rules stated in `CONTRACT.md`.
