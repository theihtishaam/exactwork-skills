# Posted transaction summary
summarize(rows) returns a dictionary keyed by currency; each value has integer
`credits_cents`, `debits_cents`, and `net_cents` fields. A posted row has fields
id, currency, direction (credit/debit), amount (nonnegative decimal string), status.
Pending rows are ignored. Each currency has two decimal places. Amounts with
more than two fractional digits or nonfinite/negative values must raise ValueError.
The same id may occur in different currencies. An identical posted row repeated
with the same (currency,id) is a retry and is counted once. Conflicting posted rows
with the same (currency,id) must raise ValueError. Currency, direction, and status
must not be normalized or rewritten. Input records must remain unchanged.
Gross credits and debits are both retained; net = credits - debits. A legitimate
opposing transaction with a different id is not a duplicate. Do not call credits revenue.
Only posted and pending statuses are valid. A pending row's amount need not be parsed.
