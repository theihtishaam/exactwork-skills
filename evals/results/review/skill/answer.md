# Review

- **`discount.py:7`: Discount range validation never rejects ordinary numeric inputs.** `percent < 0 and percent > 100` cannot be true, violating the documented 0–100 constraint. A local check confirmed `discounted_cents(1000, -10)` returns `1100` (an unintended surcharge), while `discounted_cents(1000, 110)` returns `-100` (a negative price), instead of raising the intended `ValueError`. Change `and` to `or` to reject either out-of-range condition.

Verification also confirmed the 0% and 100% endpoints return 1000 and 0 cents respectively, and negative cents raise `ValueError`. The implementation was not edited. Rounding and accepted input types are not fully specified by the docstring, so no additional requirements were assumed.
