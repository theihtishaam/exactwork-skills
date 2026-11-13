# Review

- **Invalid percentages are accepted (line 7).** `percent < 0 and percent > 100` can never be true for an ordinary number. `discounted_cents(1000, -10)` returns `1100`, and `discounted_cents(1000, 110)` returns `-100`, instead of rejecting percentages outside the documented 0–100 range. The guard needs `or`.
- **Valid large integer amounts lose cents (line 9).** `/ 100` converts the calculation to floating point. `discounted_cents(9007199254740993, 0)` returns `9007199254740992`, although a 0% discount must preserve the original amount. No maximum integer amount is documented; use exact arithmetic to avoid this loss.

Verified all three examples with Python. The implementation was not edited.
