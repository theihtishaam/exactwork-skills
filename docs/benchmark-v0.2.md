# Exactwork 0.2: measured results and limits

**Result:** the frozen compact procedures used **13.8% fewer aggregate reported input + output tokens than no skill**, and **7.5% fewer than 0.1**, over two held-out tasks with three trials each. All three conditions passed **6/6 public-task outcomes after a condition-blind grader audit**. This is a small local observation; it does not establish general accuracy improvement, statistical noninferiority, dollar savings, or consistent speed gains.

The compact condition used fewer tokens than no skill in only **3/6 paired trials**. Its log-task aggregate was higher; review-task savings drove the overall difference. The six trials represent only **two unique tasks**, not six independent domains. The released core, research, and review instructions match the frozen candidate; handoff is unchanged. The context helper is optional. The separately tested learning module was not part of this model experiment.

## Held-out results

| Condition | Task passes | Total reported tokens | Per-run median (range) | Visible tool-call items |
|---|---:|---:|---:|---:|
| No skill | 6/6 | 817,122 | 130,186.0 (89,197–207,983) | 29 |
| Exactwork 0.1 | 6/6 | 761,789 | 114,674.0 (111,233–160,257) | 24 |
| Compact 0.2 | 6/6 | 704,714 | 115,122.5 (91,049–147,744) | 27 |

Token totals include every scheduled run, including the originally strict-graded failure. No failed attempt was discarded to improve efficiency. All runs completed and all supplied task inputs were preserved where required.

| Held-out task | No skill total | 0.1 total | Compact 0.2 total | Interpretation |
|---|---:|---:|---:|---|
| h01: long-log diagnosis | 373,328 | 378,861 | 394,031 | 0.2 used 5.5% more than no skill; compact core plus context helper were loaded. |
| h02: queue correctness review | 443,794 | 382,928 | 310,683 | 0.2 used 30.0% less than no skill; all reviews found both verified defects. |

All individual paired token totals are in [final-results.csv](../evals/v0.2/final-results.csv). One h01 pair differs by only 11 tokens. The no-skill h02 runs vary from 89,197 to 207,983 tokens; this variation materially affects aggregate savings. No confidence or universal reliability claim follows from three repeats.

## Original scores and audited corrections

The candidate was frozen before holdout access. **No candidate instructions changed after seeing these outputs.** A separate evaluator reviewed anonymized artifacts without the condition mapping. It knew the benchmark oracle because it authored the fixtures; this is one blinded AI reviewer, not independent human consensus.

Two checks proved narrower than the public task:

1. **d03 citations:** all three answers used exact full section headings, such as `A — Baseline run`, while the original grader required bare letters. The public prompt allowed source sections without prescribing that representation. The first corrected grader accepts exact section IDs or exact complete headings, applied equally to all three conditions.
2. **h01 causal citation:** one compact answer cited line 11003, which records expected/actual row counts and rejection, instead of line 11004, which explains a lost record between decoded input and aggregation. Blind review found the answer's explanation and next investigation valid under the public task. The second corrected grader accepts either of these two lines, while retaining semantic checks; it does not accept arbitrary error lines. All nine h01 answers were regraded.

The original `grade.py`, first `grade_corrected.py`, final `grade_contract_corrected.py`, frozen manifest, original grades, and audit receipts are all preserved. Corrections are evaluator fixes, **not improvements made by the skill**. [Grader correction audit](../evals/v0.2/benchmark/evaluator/CONTRACT-GRADER-CORRECTION.json) · [Blind semantic report](../evals/v0.2/blind-review/semantic-grades.json).

| Held-out scoring view | No skill | 0.1 | Compact 0.2 |
|---|---:|---:|---:|
| Original deterministic grader | 6/6 | 6/6 | 5/6 |
| Public-task contract + blind semantic audit | 6/6 | 6/6 | 6/6 |
| Literal original private-rule sensitivity | 5/6 | 6/6 | 5/6 |

The sensitivity row additionally applies the private rubric's cause-only next-check wording. One no-skill diagnosis instead asked for later outcome records, useful for incomplete capture but less direct than examining the encoding. Its public-task answer remains acceptable. Passing answers are therefore not claimed equally useful. Reporting both interpretations prevents silently improving one arm's score by changing standards.

The development 0.1 log diagnosis had a **real** failure: it denied available causal evidence even though the input contained a peer connection reset and a link to the timeout. That failure remains failed under every interpretation.

## Development observations

Four tasks, one trial per condition. These are development results, not a substitute for held-out validation.

| Condition | Task passes | Total reported tokens | Per-run median (range) | Visible tool-call items |
|---|---:|---:|---:|---:|
| No skill | 4/4 | 425,168 | 104,968.0 (34,160–181,072) | 13 |
| Exactwork 0.1 | 3/4 | 345,016 | 92,978.5 (35,662–123,397) | 10 |
| Compact 0.2 | 4/4 | 348,525 | 77,474.5 (35,257–158,319) | 13 |

Tasks covered log diagnosis, contract-preserving transaction-summary repair with executable checks, evidence interpretation with unequal task mixes, and a one-label edit requiring exact preservation elsewhere. All conditions solved the tiny edit; compact 0.2 used 35,257 tokens versus no skill's 34,160. Extra procedure is not automatically useful on simple work.

The lower 0.1 development total includes its failed diagnosis. It must not be presented as a better cost per successful task. No instruction revision was made in response to development outputs. Independent mechanical fixes to the context selector were completed before its first scored candidate log run.

## Limited Ponytail comparison

Five supplementary runs used Ponytail 5.3.3's pinned **core SKILL.md only**: one repair, one exact label edit, and three queue reviews. They were run after the main schedules, with one worker, rather than randomized together with all arms. This adds time/cache/scheduling confounds. It does not reproduce Ponytail's published benchmark or test its complete runtime, hooks, codebase map, or review-specific skill.

The corresponding same-task subset is:

| Condition | Task passes | Total reported tokens | Per-run median (range) | Visible tool-call items |
|---|---:|---:|---:|---:|
| No skill | 5/5 | 612,815 | 134,861.0 (34,160–207,983) | 26 |
| Exactwork 0.1 | 5/5 | 541,987 | 111,438.0 (35,662–160,257) | 19 |
| Compact 0.2 | 5/5 | 444,117 | 98,177.0 (35,257–110,239) | 19 |
| Ponytail core | 5/5 | 493,995 | 112,766.0 (35,719–132,874) | 18 |

Compact 0.2's aggregate is 10.1% below Ponytail's in this subset, with all conditions passing 5/5. On the three repeated review runs alone, totals are 310,683 versus 338,380 (8.2% lower), but compact 0.2 uses more tokens in one of those three comparisons. This is insufficient to rank the projects generally. Ponytail's own broader author-run evidence is discussed separately in [the source-based comparison](comparison.md).

## Method and measurement boundaries

- **35 scored fresh processes:** 12 development + 18 held-out + 5 supplementary Ponytail. Two earlier infrastructure calibration attempts are documented and excluded; they were not skill-performance trials.
- **Frozen inputs:** independent synthetic task author, original manifest hash `7f6b372cf6f8250e33b2a89cbf7feffb92959f7511dc7c0dffdc0cde93035e1e`; candidate-freeze hash `5a2829b8b9d7b965cda9d8329960bbe6524ce03129ce97029e0124d88389bedb`. Every trial got a fresh fixture. Held-out order used three rotated arm orders and shuffle seed 20261112.
- **Host:** Windows, Codex CLI 0.145.0, workspace-write with the supported `windows.sandbox="unelevated"` setting, explicit instruction injection. The shared prompt disclosed fixture/environment facts equally. No browser, credentials, profiles, or prior conversation stores were inspected.
- **Unknown model identity:** fresh JSONL did not expose the exact inherited model/version. The same known CLI settings were used, but an identical hidden backend and empty inherited skill catalog were not established. This limits causal attribution and external reproducibility.
- **Actual usage:** the latest cumulative fresh-process `turn.completed.usage`, as implemented in [Codex's JSONL processor](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L117) and [usage conversion](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/codex-api/src/sse/responses.rs#L122). Total = input + output. Cached input and reasoning output are already included in their parent categories and are never added again. Cache state was uncontrolled; prices and dollar cost were not collected.
- **Timing:** main phases ran with two concurrent workers; scheduling and service variability confound wall time. No end-to-end agent speed claim is made. [Helper-only timing](component-evidence.md) is a separate experiment.
- **Scope:** no native discovery test across Claude, Harness, OpenCode, or other clients; no longitudinal self-learning trial; no proof of universal quality improvement. Research, construction, and evaluation costs are not included in per-task usage, so this is not a net-savings calculation for the entire project.

## Release decision and audit trail

Release the compact procedures as a measured but limited update: smaller instruction footprints, equal public-task success on this small held-out set, and lower aggregate reported usage with significant per-task variation. Keep optional helpers opt-in. Do not claim stronger accuracy, automatic ongoing improvement, broad superiority, or guaranteed savings.

The learning helper has its own 38 author/independent software tests for evidence gates and transactions. Its truth assumptions and lack of longitudinal evidence remain explicit. It did not run or approve this earlier study.

[Final machine-readable results](../evals/v0.2/final-results.json) · [Sanitized observable traces and original grades](../evals/v0.2/evidence/analysis.json) · [Reproduction guide](../evals/v0.2/public_eval_tools/REPRODUCE.md) · [Frozen study plan](../evals/v0.2/study-plan.md).

Public traces omit internal reasoning text, session identifiers, raw stderr, and personal absolute paths. Source and sanitized hashes are distinguished. Full fresh raw records remain local; original prompts can be reconstructed from licensed frozen inputs, with helper-path substitutions disclosed. No hidden reasoning is required to audit outcomes or usage.
