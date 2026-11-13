# What the component evidence shows

The context helper performs explicit, bounded extraction from one UTF-8 text file. It labels every selected line, provides a source SHA256, merges overlapping windows, and reports omitted matches or truncated text. It does not infer job success or guarantee that lexical matches contain every cause.

## Implementation speed

Independent review found quadratic serialization work in an early draft. Incremental byte accounting removed repeated full-output serialization; a final check still enforces the complete JSON byte budget. A separate fix counts newlines before splitting oversized-line-count inputs into millions of strings.

Three alternating-order pairs used fresh Python subprocesses on one Windows machine. The synthetic source had 800 lines of 2,000 bytes each; the output budget was 400,000 bytes. Every pair produced byte-identical JSON. Source lines were truncated with explicit counters in both versions.

| Measurement | Early draft median (range) | Released helper median (range) |
|---|---:|---:|
| Timed wall seconds | 18.472 (17.169–19.577) | 0.104 (0.074–0.174) |
| Process CPU seconds | 17.797 (16.875–18.266) | 0.094 (0.078–0.141) |

These measurements exclude import, process startup, fixture creation, and report writes. Concurrent local evaluation could add scheduling noise. This is a measured improvement over **our own unreleased draft**, not over Ponytail, ordinary search tools, or an AI agent. It establishes neither general agent speed nor accuracy. [All observations and reproduction scripts](../evals/v0.2/components/README.md).

A separate single memory probe of a rejected 20.7 MB input with millions of short lines fell from 657.1 MB to 39.6 MB observed peak. That includes interpreter/test data and is exploratory, not a general memory bound. The independent review record preserves the method and limits.

## Instruction and excerpt footprint

The compact core measured 391 `o200k_base` tokens versus 554 for the prior core; research measured 334 versus 462; review 290 versus 415. These are instruction counts, not total agent tokens. The optional context instructions add another 321 tokens. The released procedures match the frozen candidate; the historical `experimental-candidate` archive preserves the exact study inputs.

One development log measured 695,861 tokens in full; the first bounded selector response measured 1,552. That response is an excerpt, not a substitute for all required evidence. Follow-up reads and helper overhead must be counted in actual task usage. The [behavioral study](benchmark-v0.2.md) measures those task-level outcomes separately and shows why excerpt compression alone cannot justify a performance claim.

## Mechanical verification

The 24 context tests cover exact source lines and hashes, literal query matching, overlaps, strict decoding, empty files, CRLF/LF, absent final newline, long lines, budget enforcement, omission status, and input limits. A seeded 150-case differential comparison preserved complete JSON output between the old and optimized implementation. No output-equality test can establish whether an agent makes the correct diagnosis; that needs task-level evaluation.
