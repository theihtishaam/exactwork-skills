# Exactwork 0.2 study plan — before trials

Date: 2026-11-12. Goal: identify a measured improvement, not presume one.

## Research decision

Prior smoke tests were saturated and lacked usage telemetry. Keep 0.1 frozen. Evaluate a shorter execution/research/review procedure and an optional deterministic context selector. Keep handoff unchanged because no evidence currently justifies changing it.

The selector must be read-only, preserve source ranges/identity, expose omitted coverage, and never confuse successful extraction with successful execution. Compare against an agent that can use ordinary competent search, not a deliberately weak tail-only baseline. Candidate helper remains experimental unless evidence supports adoption.

## Conditions and cases

Three conditions: no Exactwork instructions, frozen 0.1, candidate 0.2. Add Ponytail's pinned core on applicable coding cases after the main comparison if feasible; report it separately rather than mixing its published results with this experiment.

An independent designer authors six cases and graders without reading the candidate. Four development cases: log diagnosis, multi-requirement code/data repair, numerical-evidence comparison, and a trivial scope-control task. Two holdouts stay hidden from the author until candidate content and hashes are frozen: a different log diagnosis and a multi-defect review.

Each trial receives a fresh fixture copy, the identical task prompt, and only its condition's procedure text. Explicit instruction loading is tested; native discovery is not. Agents can use ordinary available shell/read tools. No external browsing, credential/profile access, production effects, or unrelated skills. Initial output artifacts and grader code are withheld from agents.

Start with one run per condition on four dev cases (12 runs). Use development failures to make at most one justified revision, record both versions, then freeze the final candidate. Run three trials per condition on each of two holdouts (18 runs), with seeded balanced order. Do not tune on holdout results and call them unseen afterward. Any additional run must be separately labeled with its reason; keep failed runs.

## Measurements

Primary: all mandatory outcome requirements met, judged by predeclared deterministic checks plus blinded semantic judgment where needed. Preserve every failure and tie. Scope violations and false claims cannot be offset by attractive formatting or fewer tokens.

Secondary: fresh Codex CLI `turn.completed.usage` input/output/cache/reasoning fields, command counts, and elapsed time. Use one new ephemeral process per trial; the usage object is cumulative. All-zero/missing usage is unavailable. Cache is not added a second time to inclusive input totals. Do not quote billed dollars without billing evidence or speed gains from concurrent wall time.

CLI 0.145.0 uses normal host-managed authentication; no authentication files or old sessions are inspected. `--ignore-user-config` does not guarantee an empty instruction environment. Report the remaining host context and default model identity as unknown unless the fresh run exposes it reliably.

Supplementary: exact byte/word/tokenizer counts of instructions and source/excerpts with named tokenizer. These are component measurements, not substitutions for provider usage. Include helper instructions, executions, and follow-up reads in agent usage.

## Release rules

Publish counts and paired differences only for this setup. No universal model/client superiority. A smaller prompt with tied successful outcomes supports a limited overhead result, not higher accuracy. A context selector must preserve required evidence on tests and avoid important task regressions. If the full candidate does not improve, keep only the proven component or release it as experimental with failures visible. Do not spend indefinitely chasing a win.

Raw new task events, artifacts, hashes, grader results, and analysis code will be retained for reproducibility. Do not include private machine paths or account information in public exports.
