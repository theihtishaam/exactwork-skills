# Current measured study

Start with the [0.2 report](../docs/benchmark-v0.2.md), [final results](v0.2/final-results.json), and [reproduction guide](v0.2/public_eval_tools/REPRODUCE.md). It includes 35 scored runs with actual CLI usage, original and corrected grades, a blind semantic audit, and a small Ponytail comparison. The learning module has separate software tests; no longitudinal learning effect is claimed.

The material below is the original 0.1 exploratory protocol and remains historical context.

# Evaluate outcomes, then overhead

The four [cases](cases.json) cover a real code change, conflicting supplied evidence, read-only defect review, and a corrected task handoff. Fixtures are synthetic and contain no real credentials or business records. The adversarial text in the evidence fixture is data to be rejected, not an instruction to execute.

## Repeatable manual protocol

1. Copy one case's fixture to two clean, isolated workspaces. Keep the same prompt, tool availability, host/model version, settings, and output request.
2. Start a fresh agent context for each run. Give one the relevant `SKILL.md` and the other no Exactwork instructions. Do not give either the rubric, expected answer, previous outputs, or development discussion.
3. Run the task. Preserve actual output files and execution evidence. Do not collect browser profiles, private credentials, or unrelated user data. Use exported task usage only when the host provides it without exposing private authentication data.
4. Grade the listed checks against actual artifacts. Prefer executable checks for code, counts, and unchanged files; use independent judgment for evidence fidelity. Give paired outputs neutral A/B labels and randomize order for subjective comparison. Allow ties.
5. Report every run, including errors and missing measurements. Repeat cases in both orders before making performance claims. Test native discovery separately from explicit file loading.

The released cases are public development tests. After tuning, use a separate untouched set for final claims. More repetitions on the same tuned examples do not create a held-out evaluation.

## Metrics that must stay separate

- **Success:** all mandatory requirements met; an attractive answer cannot offset a correctness failure.
- **Scope:** unauthorized edits, omitted deliverables, unnecessary expansion, and clarification behavior.
- **Usage:** provider-reported input, output, cache-read, cache-write, reasoning, and total usage where available. Record the provider's definitions; some fields overlap and must not be blindly added.
- **Cost and time:** actual billed cost and observed duration, including retries and delegated work where available. Cached tokens still have provider-dependent costs.
- **Footprint:** bytes, characters, words, or explicitly named tokenizer counts. These describe instructions; they are not API usage.

Unknown values are `null`. Do not substitute answer length for tokens, zero for missing timing, or a plausible estimate for a measurement. Use a per-task record shaped like [run-template.json](run-template.json); do not publish the template as a completed result.

Compare cost and success jointly. A cheap failed attempt is not a successful efficiency improvement. Aggregate only compatible fields from matched runs, disclose missing coverage, and include uncertainty for repeated measurements. A one-off smoke test supports only that observed run.

## Run the package checks

From the repository directory:

```sh
python -m unittest discover -s tests -v
python tools/validate.py
python tools/measure.py
```

These validate distribution tooling and static structure. They do not run paid models or establish behavioral improvement. [Release verification](../docs/verification.md) records which behavioral tasks were actually exercised.
