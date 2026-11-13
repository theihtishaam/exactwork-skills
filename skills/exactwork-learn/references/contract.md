# Record contract, version 1

The helper reads only explicitly supplied regular files under the selected project's `.exactwork/`; each file is limited to 2 MiB. Paths use forward slashes. Traversal, symlinks, Windows reparse points, absolute references, and alternate data streams are rejected. This is a cooperative local workflow, not a hostile filesystem sandbox. Do not place secrets or unrelated personal information in its inputs.

JSON must be UTF-8, without duplicate or unknown keys, NaN, Infinity, or implicit type conversion. SHA256 values are lowercase 64-character hexadecimal strings. A **reference** always has exactly `path` and `sha256`, identifying the exact file bytes. Source records establish provenance only to the extent their contents are accurate.

## Required records

| File | Exact fields |
|---|---|
| Proposal | `schema_version: 1`, nonempty `id`, `candidate` reference to UTF-8 Markdown, `base_sha256` (null if procedure absent), nonempty `hypothesis` and `scope`, `source` reference to the verified failure or explicit correction, `policy` reference, `manifest` reference |
| Policy | `schema_version: 1`, integer `min_trials >= 2`, integer `min_heldout_tasks >= 2`, Boolean `allow_efficiency` |
| Manifest | `schema_version: 1`, nonempty `setup_id`, `grader` reference, `tasks` array |
| Manifest task | Unique nonempty `id`, `split` in `repair`, `transfer`, `regression`, `heldout`, integer `trials` from policy minimum to 100 |
| Evidence | `schema_version: 1`, `proposal_sha256`, `grader_sha256`, `cases` array |
| Evidence case | `task_id`, one-based integer `trial`, `baseline` run, `candidate` run |
| Run | `setup_id`, Boolean `correct`, Boolean `scope`, `artifact` reference, `origin` (`observed` or `manual`), `usage`, `duration` |
| Usage | Null when unavailable; otherwise exactly `kind: "actual"`, nonempty `measurement_id`, nonnegative integer `input_tokens`, nonnegative integer `output_tokens` |
| Duration | Null when unavailable; otherwise exactly nonempty `measurement_id`, finite nonnegative numeric `milliseconds` |

All four splits are required. Declare at least two held-out tasks and at least two trials for every task; these are small minimum coverage checks, not a statistically sufficient sample. Supply every declared task/trial pair exactly once. `setup_id` must agree across manifest and both arms, and should identify model version, harness, settings, tools, budgets, and run protocol. Reference the frozen grader whose checks produced the labels. Manually graded work remains labeled manual.

The gate requires every candidate correctness and scope label to pass, preventing any observed criterion regression, plus either a criterion improved from false to true or an allowed decrease in actual input-plus-output tokens across matched successful pairs. Missing or incompatible measurements cannot establish efficiency. Measurement IDs must identify the same collection method and boundary; use full trial usage including retries/delegation when available. The helper trusts this declaration and does not retrieve provider telemetry.

Totals cover supplied trial measurements. Learning, candidate drafting, and evaluation overhead are not automatically measured; report them separately before any end-to-end savings claim. Time is reported only for complete comparable sets and cannot alone qualify a promotion. Task repair, transfer, regression, and held-out results remain separately inspectable through the task manifest and evidence.

## Commands

Run from the skill directory; project paths are explicit. No model call or command is executed by the helper.

```text
python scripts/learn.py evaluate --project PROJECT --proposal .exactwork/proposal.json --evidence .exactwork/evidence.json
python scripts/learn.py promote --project PROJECT --proposal .exactwork/proposal.json --evidence .exactwork/evidence.json --target .exactwork/procedure.md --expected-base-sha256 HASH
python scripts/learn.py rollback --project PROJECT --version VERSION --expected-current-sha256 HASH
```

Promotion and rollback preview by default; append `--apply` for an already authorized write. Use literal `absent` for an expected absent file. Promotion reevaluates inputs after acquiring a cooperative lock, retains an exact backup and hashed version record, then atomically replaces the procedure. It never changes global skills, model weights, user profiles, graders, tests, or application code. Only the procedure and local transaction records are mutable.

Exit 0 means valid evaluation or completed requested action; exit 1 means a valid but ineligible candidate; exit 2 means malformed, stale, conflicting, or unreadable input. Stdout is JSON. Exit 0 never proves the agent's underlying task succeeded.

On interruption, preserve `.exactwork/pending.json` and the referenced version. Rollback can recover a prepared transaction using the actual expected base hash if replacement never occurred, or candidate hash if it did. If a rollback stopped after restoring bytes, retry using the restored hash. Never remove an unexplained stale lock automatically or overwrite intervening user edits. Multi-file records are recoverable bookkeeping, not a guarantee against arbitrary power loss or concurrent noncooperating writers.

## Synthetic example and verification

From this skill directory, `python tests/test_learn.py --example NEW_DIRECTORY` generates valid synthetic records in a new directory and prints their paths and base hash. The regular commands above can evaluate, preview, promote, and roll back that example. Its labels and token values are invented test inputs, **not measured agent gains**.

`python -m unittest discover -s tests -v` generates independent temporary fixtures and verifies the actual evaluate/promote/rollback round trip, exact backup restoration, malformed evidence rejection, and recovery paths. The filesystem reparse tests simulate both symlink and Windows junction attributes; they are not cross-platform live filesystem certification.
