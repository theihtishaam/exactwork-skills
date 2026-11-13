Fixed `mean_latency` to exclude only `None`, count valid zero measurements, and return `None` when no valid measurements remain. `maximum_latency` is unchanged.

Added regression coverage for mixed zero/missing values, all-zero measurements, all-missing values, and empty input. The zero cases failed before the fix; `python -m unittest -v` now passes all 3 tests. No external dependencies were added.
