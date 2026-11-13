Fixed `mean_latency` to exclude only `None`, count zero measurements, and return `None` when no valid measurements exist. `maximum_latency` is unchanged.

Added regression checks for mixed zero/missing values, zero-only valid measurements, and empty/all-missing inputs. Verification: `python -m unittest -v` passed all 4 tests.
