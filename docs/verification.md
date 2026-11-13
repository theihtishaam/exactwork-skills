# Release verification — 0.2.0

Checked 2026-11-12 on Windows with Python 3.11.9. Local software verification and agent-behavior evidence are separate.

## Software checks

| Suite | Result |
|---|---|
| Installer and metadata | 37 tests: 33 passed, 4 skipped because symbolic-link creation privileges were unavailable; actual Windows junction checks passed |
| Context extraction | 24/24 passed |
| Learning and independent review | 38/38 passed: 32 author tests plus 6 independent tests |
| Public evidence export/parser | 5/5 passed |
| Offline auditor control/mutation checks | 11/11 passed |

Together these cover 115 distinct tests: 111 passed and 4 skipped. The learning suite was rerun against the actual packaged files after the reviewed fixes. These are software tests, not AI task-success percentages. [Independent learning review](../evals/v0.2/learn-review/review-results.md).

The context review found and fixed excessive repeated JSON serialization and high allocation before line-limit rejection. The learner review reproduced and fixed three defects: interrupted rollback cleanup could not resume, falsey pending records escaped validation, and finite durations could overflow aggregate JSON values. Exact regression reproductions now pass. Supplied grades/telemetry still require trustworthy provenance; the helper does not validate their truth.

## Distribution checks

- All six skill folders passed frontmatter, name, size-budget, and standalone-link validation.
- All six actual bundles were copied into disposable projects for each of nine installer targets, then compared byte-for-byte and checked for unchanged repeat installation. This proves installer path/copy behavior; it does not prove native discovery or model behavior in those clients.
- Released benchmarked files match the frozen candidate hashes. The reviewed learner script hash is `b01fc19d420013af86bf55063a2c09af88c4e409de624538cf61fb2d3fbc7fe7`.
- Main documentation links and all three SVGs passed structural checks. PNG previews of the authored diagrams were inspected for legibility and clipping. The previously generated cover retains its [provenance](../assets/PROVENANCE.md).
- Generated public deliverables were checked for personal workspace strings. Exported fresh traces omit internal reasoning, session identifiers, raw stderr and personal paths; originals remain local, with separate original/public hashes.
- Windows/Linux Python 3.10/3.12 CI configuration is included with pinned actions. Remote CI was not run; local results do not certify every matrix environment.

No live agent configuration, user profile, global skill installation, or GitHub repository was changed. [Machine-readable package checks](../evals/v0.2/release-checks.json).

## Model study

There were 35 scored fresh CLI runs: 12 development, 18 held-out and 5 supplementary Ponytail. The [benchmark report](benchmark-v0.2.md) includes actual usage, all runs, original grades, arm-blind semantic review, and separately versioned contract corrections. A second reviewer independently checked the joins, all aggregate arithmetic, corrected graders, published percentages, and frozen release hashes. [Independent analysis audit](../evals/v0.2/independent-analysis-audit.md).

The compact condition had 13.8% lower aggregate reported tokens than no skill on two held-out tasks repeated three times, with 6/6 public-task passes in each condition after audit. Savings occurred in only 3/6 pairs and did not extend to the log-task aggregate. This supports a bounded observation, not a general accuracy or speed claim. The exact inherited model was not exposed; native multi-client activation and longitudinal learning remain unverified.

The learning module was not part of those model trials. Its tests establish record/transaction behavior, not future performance improvement.

## Reproduce local checks

From the repository root:

```sh
python -B -m unittest discover -s tests -v
python -B -m unittest discover -s skills/exactwork-context/tests -v
python -B evals/v0.2/learn-review/test_independent_review.py
python -B -m unittest discover -s evals/v0.2/public_eval_tools -p test_public_tools.py -v
python -B evals/v0.2/audit_results.py
python -B evals/v0.2/test_audit_results.py evals/v0.2
python -B tools/validate.py
python -B tools/measure.py
```

The offline auditor checks 35 runs, 219 public file hashes, 27 semantic receipts, 12 corrected-grade receipts, and all summary arithmetic. Its mutation tests reject missing/duplicate trials, altered usage or percentages, semantic attribution errors, unapproved grade changes, and byte tampering. These commands make no model calls. See the [study reproduction guide](../evals/v0.2/public_eval_tools/REPRODUCE.md) for explicitly launching new trials with the frozen files, and [component measurements](component-evidence.md) for the helper-only speed experiment. Preserve published results; write any new measurements separately.

The [0.1 verification report](verification-v0.1.md) and exploratory outputs remain historical evidence.
