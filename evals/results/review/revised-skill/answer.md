# Review

Two verified correctness defects:

1. **Discount bounds are never enforced — `discount.py:7`.** The condition requires `percent` to be both below 0 and above 100, which is impossible for ordinary numbers. `discounted_cents(1000, -1)` returns `1010`, and `discounted_cents(1000, 101)` returns `-10`, instead of rejecting discounts outside the documented 0–100 range. Replace the condition with a range check such as `if not 0 <= percent <= 100:`.

2. **Floating-point conversion corrupts valid integer amounts — `discount.py:9`.** With no documented upper limit on cents, `discounted_cents(9007199254740993, 0)` must preserve the amount, but returns `9007199254740992`. `discounted_cents(10**309, 0)` raises `OverflowError`. The `/ 100` operation converts the intermediate integer to a float, losing precision or exceeding its range. Perform the calculation and rounding using exact arithmetic appropriate to the supported percentage types.

Evidence: reproduced both defects locally against the unchanged implementation. Also checked zero cents, discounts of 0 and 100, an ordinary 25% discount, and rejection of negative cents; these checks passed. The contract does not specify rounding ties or non-integer percentage types, so those ambiguities are not reported as defects.
