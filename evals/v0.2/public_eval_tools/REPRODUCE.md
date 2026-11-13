# Reproduce or audit this local study

These Python standard-library tools separate launching a new model trial from exporting existing evidence. Importing them and running their tests makes no model calls. No tool reads credentials, configuration files, browser stores, or historical sessions. Model requests use only the CLI client's normal managed login; do not paste credentials into commands or prompts.

`../evidence/analysis.json` and `analysis.csv` contain all 35 scheduled runs: 12 development, 18 holdout, and 5 supplementary Ponytail comparisons. Each run links to its sanitized observable trace, final message, deterministic grade, original record metadata, and changed/new textual artifacts. Calibration attempts are excluded from scored schedules, not silently counted as skill failures. A required semantic review is indicated separately and is not satisfied by a passing deterministic grade. The publication's final analysis owns any subsequently added blinded semantic judgment.

## Audit the evidence without making model calls

The export checks the original stdout, prompt, and final-answer hashes against the original collector record. It reparses usage and activity counts from the fresh stdout and refuses mismatches. It retains the original source hashes, but gives each sanitized public file a separate hash. Redaction changes bytes: a public trace is not expected to match its original raw hash. The raw logs stay local.

`trace.jsonl` retains allowlisted completed commands and their exported results, file changes, visible agent messages, and turn completion/failure events. It removes reasoning items, thread/turn/session identifiers, raw stderr, and known personal paths. Unknown item types are omitted and counted. Unmapped personal home paths fail the export. Replacements identify only paths already known from the task; the script does not inspect those locations. Full prompts are deliberately not redistributed, including Ponytail's instructions. Their original hashes are retained.

```sh
python -m unittest discover -s public_eval_tools -p test_public_tools.py -v
python public_eval_tools/export_study.py --study-root ./study --output-dir ./public-evidence
```

For a local export containing other known personal path prefixes, append `--redact-prefix 'EXACT_PATH=<PLACEHOLDER>'`. The explicit study root maps to `<STUDY_ROOT>`, and an absolute CLI executable/wrapper found in the recorded invocation maps to `<CODEX_CLI>`. The supplied study export also maps its known task workspace and user-home prefix to generic placeholders. The script has no hardcoded personal path. It can be rerun as trials finish; incomplete rows remain explicit, and `complete` becomes true only after all 35 scheduled rows export. Do not reuse an output directory for a different study.

## Prepare frozen inputs

Use the published frozen benchmark generator, task prompts, and graders; frozen version 0.1 procedures; and the experimental compact candidate, rather than substituting the final release's default skills. The experiment tested these snapshots by explicit loading. It did not test native skill discovery. Keep their original files and hash manifests unchanged. `candidate-freeze.json` and the original schedules are included under `evidence/inputs`.

Ponytail comparisons require the exact pinned upstream snapshot identified by the publication, with its MIT license and attribution preserved. Obtain that snapshot before reproducing Ponytail runs; do not substitute the moving default branch. The full third-party instructions are not included in these exported prompts. The new-run prompt composer reads only the explicitly supplied local licensed file.

Create a fresh fixture using the frozen benchmark's `prepare.py CASE RUN_DIR`. Keep graders, condition instructions, the optional context helper, and logs outside the fixture. Supply only the task data the case permits. The holdout schedule preserves the original case/condition/repetition ordering. The original study used two concurrent workers; running serially may change cache behavior and timing. Retain the original schedule and document any deviation.

Procedure routing in the original study:

| Cases | Procedure |
| --- | --- |
| d01, d02, d04, h01 | exactwork |
| d03 | exactwork-research |
| h02 | exactwork-review |
| candidate d01 and h01 only | exactwork plus exactwork-context and its explicitly named helper |
| no-skill condition | no procedure file |
| Ponytail condition | pinned Ponytail core file; only d02, d04, h02 were scheduled |

The included `common-prompt.txt` is the exact shared prompt used by the original scheduler. Compose a local prompt from the frozen case and procedure:

```sh
python public_eval_tools/compose_prompt.py --study-root ./study --common-prompt ./study/common-prompt.txt --case-prompt ./study/benchmark/cases/d02/prompt.txt --procedure-file ./study/baseline-v01/skills/exactwork/SKILL.md --output ./study/prompts/new-trial.txt
```

Repeat `--procedure-file` for the candidate context skill, then pass `--helper` with its frozen `context_slice.py`. Omit procedure/helper arguments for no-skill. Optionally pass `--procedure-output` to save the exact assembled procedure, then give that file to the runner's `--skill-file` for its separate hash. The original prompt included an absolute helper path: moving it necessarily changes that trial's prompt hash. Record the new prompt hash, preserve the original hash, and disclose the path substitution. The composer recreates ordering and separators but does not promise byte identity after a path or platform newline change. The common-prompt manifest identifies both original source and shared-text hashes.

## Launch an explicitly requested new trial

Check the public CLI version/help before a new study. The historical version was Codex CLI 0.145.0. `portable_runner.py` accepts an explicit executable argument array and explicit study root; it never invokes a shell around that command. Use a direct executable, or Node plus a public Codex JavaScript launcher. A CLI update or different model is a new configuration, not an exact replication.

```sh
python public_eval_tools/portable_runner.py --study-root ./study --run-dir ./study/runs/new-trial --prompt-file ./study/prompts/new-trial.txt --cli-argv-json '["codex"]' --cli-version 0.145.0 --timeout 300
```

On the original Windows setup, add `--windows-sandbox unelevated`. Version 0.145.0 otherwise downgrades workspace-write to read-only if its Windows sandbox is disabled and user config is ignored. This setting enables the restricted-token sandbox; it does not bypass rules or approval policy. Its network isolation is weaker than the elevated implementation. Do not change managed requirements, provision administrator setup, or use bypass flags to force a reproduction to run. If infrastructure cannot execute the fixture, preserve the attempt and classify it separately. Normal workspace-write temporary-directory behavior is retained; the task prompt restricts actual file changes to its required fixture outputs.

The collector writes a new sibling `RUN_DIR-telemetry` directory, never logs inside the fixture and never overwrites an old trial. It records fresh stdout/stderr, answer, hashes, status, and usage. Run the frozen case grader against the fixture afterward; retain every failed or incomplete trial. Use the original grading/semantic-review protocol. The runner deliberately does not schedule, tune, or select winning trials.

## Interpret usage conservatively

One fresh process is used per trial. `turn.completed.usage` is a cumulative thread report; the parser takes the latest report and never sums reports. Total reported tokens are `input_tokens + output_tokens`. Cached and cache-write input are input details; reasoning output is an output detail, so none is added again. Missing/invalid/all-zero primary usage is unavailable, not a zero-cost trial. Output tokens include reasoning and other generated structure; final-answer text length is not a substitute.

The schema comes from [Codex 0.145.0's JSONL processor](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L117) and [Responses usage conversion](https://github.com/openai/codex/blob/rust-v0.145.0/codex-rs/codex-api/src/sse/responses.rs#L122). Command-output counts measure Unicode code points in exported command-output strings, not tokens or every tool's output. Missing command outputs produce a null total with a partial observed sum. Visible activity-item counts are not claimed to count every internal API call.

The exact inherited model was not exposed by the collector and remains unknown. Ignoring user config did not prove an empty inherited instruction/skill catalog. Cache state was not controlled. Concurrent wall times include startup, scheduling, and service variability, so they do not support speed claims. No dollar-cost or universal model/client superiority claim follows from this study. The original strict citation failure remains in the exported deterministic grades. Separate blinded contract auditing accepted that alternative citation; see the final report and corrected grades. The released compact instruction files match the frozen candidate. Context extraction and self-learning remain optional. Self-learning was not evaluated in this model benchmark.

## Paths in the published repository

This guide's `./study` is a generic task-owned study directory. In the release, its frozen sources are under `evals/v0.2/`: `benchmark/`, `baseline-v0.1/`, `experimental-candidate/`, and `ponytail-baseline/`. The latter contains the licensed pinned upstream files. `public_eval_tools/` contains these tools and the common prompt; `evidence/` is its sibling, not child. `final-results.json` joins original outcomes with the separately archived semantic audit and corrected grades. The historical folder name `experimental-candidate` does not mean a different post-study revision.

## Audit the published final results

From the repository root, run `python -B evals/v0.2/audit_results.py`. It verifies public evidence hashes, all 35 scheduled runs, exact usage, blinded-answer attribution, original/corrected grades, CSV consistency, and reported aggregates. Run `python -B evals/v0.2/test_audit_results.py evals/v0.2` for eleven control/mutation checks in a disposable copy. These checks require no model or network. They establish internal consistency; they do not authenticate omitted original logs or independently judge the semantic rubric.
