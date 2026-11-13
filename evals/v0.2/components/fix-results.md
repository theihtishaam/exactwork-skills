# Context selector mechanical fix results

Date: 2026-11-12. Scope: authored selector only; no held-out, benchmark-private, run-directory, network, browser, credential, or model access.

## Changes

- Count LF-delimited source lines directly in the bounded byte buffer before decoding/splitting. This preserves the existing LF/CRLF line semantics and rejects excessive line counts before per-line allocations.
- Calculate omitted matches by membership over selected identities, avoiding copies of the entire match set.
- During truncation, maintain the current serialized-byte total and encode only the changed excerpt for prefix probes. Account for numeric counter widths, omitted-character fields, and false-to-true completeness flags. Retain the final full JSON encoding and hard byte-budget check.
- Mirrored the candidate script to `context_candidate/scripts/context_slice.py`.

The two script copies have identical SHA-256:
`EF71289F3F6EB8F53FE58F6D31562CFD184E408C3F8DFA5D71DE77ECB9F0B923`.

## Verification

- All 24 unit tests passed: the original 20 plus four regressions covering rejection before line splitting, exact line-limit boundaries, bounded whole-result encoding work, and Unicode/escaping/counter-boundary budget accounting.
- 150 seeded accepted-input comparisons against the saved pre-fix script produced identical complete JSON objects. These include literal, default-pattern, and explicit-range selections with variable context, line caps, and byte budgets.
- Source identity, exact prefixes, omitted characters, selected ranges, coverage counters, unknown source process status, and the final byte cap remain intact in those checks.

## Measurements

All measurements are local synthetic Python/helper measurements on this machine. They do not measure model tokens, model quality, or end-to-end agent performance. Timings are single-run observations subject to machine load, and peak working set includes the interpreter, test code, and fixture construction. They are not a general memory bound.

| Case | Before | After | Preserved result |
| --- | --- | --- | --- |
| 800 lines, exactly 2,000 source bytes per line, context 0, max-lines 800, max-bytes 400,000 | 23.699 s; peak working set 39,383,040 bytes | 0.095 s; peak working set 39,038,976 bytes | Exactly 400,000 output bytes; 800 selected, 0 omitted matches, 800 truncated |
| 6,900,000 short lines (`xy\n`), 20,700,000 source bytes, ordinary defaults | 1.244 s; peak working set 657,055,744 bytes | 0.033 s; peak working set 39,645,184 bytes | Explicit `Source exceeds 1000000 lines` rejection |
| 10,000 lines, exactly 2,000 source bytes per line, context 0, max-lines 10,000, max-bytes 1,048,576 | Not rerun before fix | 1.017 s; peak working set 131,104,768 bytes | Exactly 1,048,576 output bytes; 10,000 selected, 0 omitted matches, 10,000 truncated |

The initial independent-review 800-line measurement was 19.085 s before and 0.098 s after. The table uses the subsequent paired run, which also collected valid working-set counters for both versions. Initial resource-worker attempts returned zero memory values due to an incorrect Windows ctypes handle signature; those invalid zero values are excluded.

The 20 MiB source cap is not a promise that process memory stays below 20 MiB. Valid large sources still require decoded text, line objects, match metadata, and output buffers. The focused fix prevents the demonstrated excessive-line rejection allocation and repeated full-output serialization.

## Reproduction

Run from this scratch directory with bytecode writes disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python run_tests.py
python differential.py
python resource_worker_before.py 800 2000 800 400000
python resource_worker.py 800 2000 800 400000
python resource_worker.py 10000 2000 10000 1048576
python memory_case.py
```

`context_slice_before.py` is the saved original for local differential and timing checks. `resource_worker_before.py` uses it; the ordinary worker uses the candidate. `memory_case.py` currently measures the fixed candidate; its before numbers were captured during the independent review before the edit.

No candidate source files were altered before authorization. Initial review imports may have generated incidental `__pycache__` files next to imported modules before bytecode writing was disabled; the original source was unchanged at that time.
