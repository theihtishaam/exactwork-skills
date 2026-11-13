# Exactwork upgrade: evidence before claims

Checked 2026-11-12. Research-only recommendation; no claimed improvement results. Existing 0.1 release and its evidence were inspected. Current primary sources below were opened during this research.

## Main recommendation

Do not add another general checklist and assume it improves a capable model. Test two separable changes: (1) remove redundant instruction overhead while retaining task outcomes, and (2) add one narrowly scoped, executable context-selection helper only if it beats an ordinary competent workflow on measured criteria. Preserve 0.1 as a frozen comparator. Keep all outcomes, including ties, failures, and cases where the helper is counterproductive.

The strongest feasible evidence in this session is **an exact component measurement plus a controlled behavioral study**. For example, count the full source and selected excerpt with a named tokenizer, mechanically verify that the selected excerpts preserve the task's required evidence, then test whether agents reach the correct diagnosis. That proves a bounded result about the tested text and tasks. It does not by itself prove lower total billed agent tokens, model accuracy across domains, or universal superiority.

## What the primary evidence supports

| Evidence inspected | What it supports | Limit for this project |
|---|---|---|
| [Anthropic, Writing effective tools, 2025-09-11](https://www.anthropic.com/research/writing-tools-for-agents) | Targeted ranges, filtering, pagination, meaningful result fields, actionable errors, and evaluators based on realistic task outcomes | A compact response can omit identifiers needed later; evaluate retrieval cost and correctness, not just the first response length |
| [Anthropic, Code execution with MCP, 2025-11-04](https://www.anthropic.com/research/code-execution-with-mcp) | Filtering or transforming data in code before returning it can reduce model-mediated data movement | This is an executable mechanism. Markdown cannot create the execution environment, enforce tool choice, or guarantee the reported example's savings elsewhere |
| [Agent Skills, Using scripts](https://agentskills.io/skill-creation/using-scripts) | Bundle reusable complex operations when an existing short command is insufficient; name prerequisites and pin dependencies | Do not reinvent an existing reliable command without an advantage. Python becomes a prerequisite for that optional helper |
| [Anthropic, Demystifying evals, 2026-01-09](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Distinguish tasks, repeated trials, graders, final state, and traces; use harder capability cases alongside saturated regressions | A passing filename or final message is not evidence of the environment outcome. One trial does not establish reliability |
| [Agent Skills, Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills) | Clean skill/no-skill comparisons, actual artifact grading, meaningful assertions, and separate performance measurements | Skill authors selecting on the same tests can overfit; preserve a fresh final set |
| [SkillReducer v2, 2026-06-24](https://arxiv.org/html/2603.29919v2) | Structure-aware compression with routing and task checks can reduce instruction footprint | Its optimization criterion doubles as an evaluation signal; the paper identifies that limitation. Its authors' reported gains do not transfer to Exactwork without tests |
| [SWE-Skills-Bench v2, 2026-10-27](https://arxiv.org/abs/2603.15401v2) | Use repository-specific executable requirements and paired comparisons. Helpful procedures must supply something the agent otherwise omits | The paper reports most tested skills lack significant effects. It argues against promising generic accuracy gains from general advice |
| [SkillsBench v4, 2026-06-14](https://arxiv.org/abs/2602.12670v4) | Curated procedures can improve expertise-heavy tasks across multiple model/host setups | Its tasks and curated expertise differ from Exactwork's general workflow. The contrast with SWE-Skills-Bench reinforces task-specific measurement |

These sources justify an engineering direction and measurement method. They do not constitute experimental evidence for this upgrade.

## Why the 0.1 evidence does not answer the user's question

1. The latency, evidence, and handoff tasks were close to ceiling: both arms succeeded. They are useful regression tests, not proof of a quality advantage.
2. Only one trial per condition was run. Model nondeterminism makes a single win, loss, or tie weak evidence of a stable difference.
3. The precision defect was discovered after observing the baseline. The new criterion and the subsequent skill revision were tested on the same example. That is development, not held-out validation.
4. Run order was not randomized and grading was not blinded. Author expectations could influence subjective judgments.
5. Exact model identity, provider usage, cost, elapsed time, and tool-call totals were unavailable. Bytes and output words cannot fill those gaps.
6. The 37 software tests covered package tools and metadata. They do not measure whether the skills improve agent behavior.
7. Explicit reading of a skill file does not exercise native discovery or automatic triggering.
8. No Ponytail behavioral comparison was performed. A comparison table and published Ponytail numbers cannot support superiority.

## A concrete helper worth testing, not assuming

Test a read-only selector for a **specified local text file**, with caller-specified literal terms or ranges and a bounded context window. It should return exact excerpts plus source identity and explicit coverage. It must not recursively search the user's disk, fetch data, execute embedded text, or infer access to credentials.

Recommended observable contract:

- Input path, file hash, byte/line counts, match counts, selected line ranges, omitted coverage, and the command needed to expand a range.
- Exact source excerpts, preserving order and line numbers; combine overlapping windows rather than repeating them.
- Explicit incomplete status when requested matches do not fit the budget. An empty result means no match for those terms, not success or absence of defects.
- No silent decoding replacement. Handle Unicode, CRLF/LF, absent final newline, empty files, long single lines, and malformed input with explicit behavior.
- No claim to know process exit status from a text file. If used with a runner later, producer failure must remain failure even if summarization succeeds; that is a separate, carefully tested feature.
- No generic guarantee that lexical matching preserves the cause. The skill must expand beyond the snippet when meaning depends on surrounding stages, timestamps, stack frames, or relationships.

This is useful only if it improves consistency, provenance, portability, or measured task performance over existing tools. `rg -n -C` with a bounded read is a competent comparator. A naive last-20-lines baseline alone would manufacture a weak opponent. Do not claim a selection algorithm is a security boundary or injection defense.

Avoid adding a broad command wrapper, a multi-agent orchestrator, automatic context deletion, prompt caching controls, or persistent memory merely to expand the feature list. Those enlarge portability and safety scope without a demonstrated need.

## Suggested experiment, frozen before final runs

Use a development set to find real failures and tune once. Ask an independent author to create fresh test fixtures and outcome verifiers without showing the candidate text or desired winning answer. Freeze candidate hashes, fixtures, prompts, rubrics, baseline conditions, trial counts, and stop rules before opening final outputs. If the candidate changes after seeing a held-out failure, that set becomes development; label the next validation honestly.

**Arms:** no Exactwork, frozen 0.1, candidate 0.2. For a helper-only experiment, also compare the same task using ordinary targeted search. Keep initial context, tools, task, model/settings, and permissions matched. Agents receive the user task and inputs, not hidden rubrics. Use isolated workspaces and fresh contexts. Balance or randomize condition order with a recorded seed. Repeat representative cases, ideally at least three trials each; small samples support bounded observations, not general statistical assurance.

**Tasks should reveal a possible difference:** multiple independent errors across a long log; a causal clue outside the last block; contradictory stage results; a large one-line record; repeated noise; a zero-result query requiring expansion; a multi-file contract change with an unchanged caller; a multi-deliverable task where one requirement is easily lost. Keep the old easy cases as regressions. At least one task should be small enough that the helper is unnecessary, so extra ceremony is penalized.

**Primary endpoint:** all user-critical requirements satisfied in actual artifacts, with meaningful scope preservation. Report per-case counts and all failures. For review, record true defects found and unsupported findings separately instead of rewarding a longer list.

**Efficiency endpoints:** exact named-tokenizer counts for the source/excerpt and loaded instruction files; actual observable file-read volume if instrumented; tool calls, latency, and provider usage only where genuinely captured. Report helper instructions and any follow-up reads, not just the compact first excerpt. Agent wall time in concurrent runs is confounded by scheduling, so do not claim speed gains from a few uncontrolled concurrent timings.

**Grading:** deterministic verifiers for code behavior, source-span fidelity, coverage, and forbidden changes; a separate blind reviewer for semantic diagnoses and plans. Strip arm labels and randomize A/B presentation. Review disagreements and valid alternative solutions. Do not change a rubric to favor the candidate after observing results.

## Release decisions and permissible claims

- A mechanically verified reduction in excerpt tokens can be published as **selected-input reduction on these fixtures**, with the tokenizer and coverage requirements stated. It is not total agent token savings.
- If repeated final tasks tie while a shorter skill has a smaller measured footprint, publish **lower instruction overhead with no regression observed in this set**. Do not call a small sample statistical noninferiority.
- If the candidate has consistent task wins and no important regressions, publish those exact counts and conditions. Do not extrapolate to every client or model.
- If results tie or regress, remove the ineffective rule/helper or keep it experimental. An honest no-improvement finding is useful and must not be hidden by more research prose.
- Without provider telemetry, leave billed usage and cost unknown. Do not inspect credentials, browser/session stores, or private application logs to obtain them. Existing authorized clients may expose usage normally; account/login details are not needed for a claim.

The appropriate outcome is a narrower, demonstrably improved mechanism and a reproducible evidence package—not an unsupported “best skill” label.
