# Exactwork Learn: evidence-gated local procedure improvement

Design only; checked 2026-11-12. Proposed module: `exactwork-learn`. No implementation or live installation authorized by this document. The user authorized building this capability; using it to alter a particular project requires that project's explicit target and scope.

## What “learning” means

An agent turns a verified task failure or explicit user correction into a narrowly applicable procedure, tests it, and retains a version only when stated gates pass. It changes project files, **not model weights**, and has no automatic global installation, publication, credential access, or permanent user-profile memory. Invocation for this purpose permits a project-local `.exactwork/` record. Ordinary work need not produce learning records.

Start with one optional skill plus one standard-library Python helper. The model proposes changes; the helper checks evidence records and manages versions. It never invokes models, executes commands, invents grades, or treats its own successful exit as proof of improvement.

## Research that changes the design

- [Does Failure Feedback Direct Agent Self-Modification?, v1, 2026-10-10](https://arxiv.org/abs/2610.14662v1) separates target repair, transfer, and held-out change. Targeted repair did not reliably imply held-out improvement. Therefore fixing the example that inspired a rule is necessary evidence about that example, not evidence of general benefit.
- [Who Grades the Grader?, v2, 2026-07-30](https://arxiv.org/abs/2607.12790v2) reports an always-pass evaluator when anchor guards were removed and rubric gaming detected independently. Therefore this minimal module cannot revise its own grader, policy, or held-out cases during a promotion attempt. Changes to those require a separately reviewed experiment.
- [OpenAI evaluation playbook, 2026-05-29](https://openai.com/index/trustworthy-third-party-evaluations-foundations/) requires claims and their validity evidence, and controlled comparisons with fixed tasks, scoring, budgets, and harness. Therefore all results record the tested setup; cross-model or differently budgeted runs cannot silently become matched pairs.
- [Anthropic agent evaluations, 2026-01-09](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) distinguishes task outcomes, trials, graders, and traces. Therefore saved output and observed environment checks outrank an agent saying it succeeded.

These support the design; none proves Exactwork improves a user's model.

## Minimal interface and records

All paths are explicit local project paths. No recursive search, network, profile reads, or auto-discovery of previous chats.

```text
learn.py evaluate --project ROOT --proposal proposal.json --evidence evidence.json
learn.py promote --project ROOT --proposal proposal.json --evidence evidence.json \
  --target .exactwork/procedure.md --expected-base-sha256 HASH --apply
learn.py rollback --project ROOT --version VERSION --expected-current-sha256 HASH --apply
```

`evaluate` is read-only and returns JSON: `eligible`, reason codes, matched outcomes, missing evidence, and the narrow supported claim. Promotion without `--apply` is a dry run. Promotion reruns evaluation; an old “pass” file is insufficient. The explicit target must already be authorized; flags are not proof of user consent.

Proposal fields: schema version, proposal ID, minimal failure/correction quotation or artifact reference, source hash, applicability and exclusions, environment/version guard, expiration/revalidation condition, one causal hypothesis, candidate path/hash, exact target/base hash, and frozen policy/evaluation-manifest hashes. Prefer one short rule that repairs a demonstrated mechanism. A correction records a project preference, not a measured universal quality improvement.

Evidence fields: task/trial IDs, split (`repair`, `transfer`, `regression`, `heldout`), baseline/candidate versions, model/harness/settings/budget IDs, artifact hashes, grader/version, criterion outcomes, origin (`observed` or `manual`), and optional actual usage/time with units and measurement boundary. Missing measurements are `null`, never zero. Exclude credentials and unnecessary conversation/personal data.

## Deterministic promotion gate

1. Validate strict schema, finite metrics, unique paired trial IDs, declared task coverage, provenance references, and every frozen hash. Reject changed artifacts, graders, policy, candidate, base, or incomplete evidence.
2. Require a prespecified evaluation manifest containing the triggering case, related transfer cases, unrelated regression cases, and held-out cases unavailable during candidate drafting. Candidate authoring cannot read final held-out answers. “Held out” is a documented process assertion; hashing alone cannot prove it.
3. Check task correctness **and relevance/scope adherence** against independent artifact or environment criteria. Require all mandatory candidate checks to pass and no observed criterion regression against baseline. Missing outcomes block promotion. Require repair or another prespecified positive result; passing unchanged tests alone is not improvement.
4. For stochastic runs, require the manifest's prespecified repeated trials and report all outcomes. A conservative no-observed-regression gate may reject useful noisy candidates. It does not establish statistical noninferiority; report sample size and uncertainty without inventing a universal safe threshold.
5. Only after quality gates pass, compare efficiency using matched successful pairs with identical measurement definitions and setups. Require actual telemetry for token/time claims; report instructions' byte/token footprint separately. Include failures, retries, delegation, and learning/evaluation overhead in separate all-run totals. Missing metrics block that efficiency claim, not an independently demonstrated quality repair.

Never promote merely because the candidate says it learned. Deterministic checks establish record consistency and declared gate satisfaction, not that supplied grades are truthful or that a rubric covers every real requirement. Manual grading stays visibly manual.

## Versioning, rollback, and stopping

Restrict v1 writes to one authorized Markdown procedure under `.exactwork/`. Stage tests and candidates separately; the module does not edit application code, global skills, AGENTS files, or graders. Resolve paths under the project; reject traversal, symlinks/reparse points and nonregular files. No browser/authentication/credential paths are permitted.

Before replacement, acquire a cooperative lock, recheck target/candidate hashes, save exact original bytes and a pending transaction record, then replace through a same-directory temporary file. Record candidate/evidence/policy/base hashes, time, supported claim and backup reference in an append-only version record. On interruption, stop and reconcile the pending transaction against actual hashes. Rollback restores exact backup bytes only if the current hash still equals that version's promoted hash; otherwise preserve user edits and report conflict. This is not a hostile-concurrency security boundary.

One hypothesis per attempt. Keep rejected results. Once held-out feedback influences another candidate, retire that set from final evaluation and obtain fresh cases. Revalidate when version/scope guards expire. Retire redundant rules only through the same regression gate. Report “local procedure updated; observed results X/Y,” never “the model permanently became smarter.”
