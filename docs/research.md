> Version 0.2 adds [targeted upgrade research](upgrade-research.md), [learning research](learning-research.md), and an [actual measured study](benchmark-v0.2.md). The original research below informed 0.1 and remains background, not independent evidence for 0.2 performance.

# Research behind Exactwork

**Research date: 2026-11-12.** This document records the evidence and decisions used before implementation. Exactwork is designed to reduce avoidable context, preserve user intent, and improve verification. It is not yet proven to reduce total tokens or outperform Ponytail across models and tools.

The research combined a pinned Ponytail source audit, current client documentation, empirical studies, and concrete skill examples. Source inspection establishes what a project contains; published results establish what its authors report under their conditions. Neither substitutes for a controlled evaluation of Exactwork.

## 1. Define the outcome before optimizing

The objective is **less total work per correctly completed task**, with the user's scope, requested detail, and acceptance criteria preserved. Shorter answers, smaller diffs, fewer tool calls, and smaller instruction files can all be useful. They can also conceal unfinished work. None is an adequate success metric alone.

This leads to four intended capabilities: a compact execution core, evidence-driven research, bounded review, and a handoff that preserves decisions and unresolved work. They are independent skills, not mandatory stages in every task. A simple correction should remain simple; a complex investigation should receive the evidence and explanation it needs.

## 2. What Ponytail already gets right

The inspected baseline is **Ponytail 5.3.3**, commit [`96608e078b2d5ea607c5c3b8b5a54d1c1fba6846`](https://github.com/DietrichGebert/ponytail/tree/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846). Its core goes beyond brevity: it asks agents to trace affected code and dependencies, preserve architecture, reuse existing capabilities, protect important validation and error handling, and complete dependent changes. It scales checks to the edit instead of requiring tests for every trivial change. Exactwork adopts the principle that minimal work must still be complete. [Main skill](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/skills/ponytail/SKILL.md)

Ponytail also supplies runtime features: session intensity modes, host adapters, activation and compaction handling, a bounded codebase map, and optional status visibility. Its instruction builder already filters content by active intensity. These are real capabilities, not merely overhead. Exactwork chooses portable Markdown without runtime hooks, trading away automatic reinforcement and telemetry for simpler distribution and inspection. [Instruction builder](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/hooks/ponytail-instructions.js), [runtime adapter](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/hooks/ponytail-runtime.js), [codebase map](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/hooks/ponytail-map.js)

Its published 2026-10-07 benchmark reports 39 tasks, three arms, five repetitions each: 585 headless Claude Code sessions. The author reports 45% fewer **output** tokens and 26% lower cost versus no skill in the stated setup. Those are Ponytail's reported results, not Exactwork measurements or independent replication. Bash was disabled, so the experiment does not represent a full edit-run-debug loop. Deterministic correctness checks covered 18 tasks; reported correctness was essentially level, and the response-quality comparison against no skill was not statistically significant. This is a substantive benchmark with limitations, not evidence that Ponytail lacks evaluation. [Dated results](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/benchmarks/results/2026-10-07-agentic.md), [method](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/benchmarks/agentic/README.md)

The proposed improvement is therefore a different emphasis: preserve deliverables and constraints across domains, distinguish facts from inference, avoid repeated exploration, and report verification accurately. Whether those choices improve real outcomes must be tested.

## 3. Evidence is mixed: skills need a reason to exist

**SkillsBench v4** reports 87 tasks across eight domains and 18 matched model-harness configurations, with average pass rates of 33.9% without skills and 50.5% with curated skills. Focused expertise can help on the benchmark's tasks. That does not establish that a general productivity skill improves every task. [Li et al., v4, 2026-06-14](https://arxiv.org/abs/2602.12670v4)

**SWE-Skills-Bench v2** reports 92 of 98 tested public skills without statistically significant effects across its four agent-model configurations; average pass ratios were 76.6% and 76.9%. The authors identify useful missing procedures, but also harmful anchoring on templates and conflicts with user instructions. Exactwork must preserve explicit task requirements rather than replace them with its own workflow. [Han et al., v2, 2026-10-27](https://arxiv.org/abs/2603.15401v2)

The **AGENTS.md study v3** reports no general task-success improvement and more than 20% average inference-cost growth in its tested coding conditions. It studies repository context files, not every possible skill. Its relevant warning is narrower: extra instructions can cause extra work without sufficient benefit. [Gloaguen et al., v3, 2026-09-29](https://arxiv.org/abs/2602.11988v3)

A small recent study of three stale-instruction situations also found wasted operations despite successful final outcomes. Its scale does not justify a universal failure rate. It does justify checking current source and commands before obeying old instructions mechanically. [Mehtiyev et al., v1, 2026-11-06](https://arxiv.org/abs/2611.09802v1)

Together these findings support a conditional hypothesis: instructions are worthwhile when they correct a demonstrated gap and cost less than the mistakes they prevent. They do not support promises of “more intelligence,” guaranteed savings, or a universal best skill.

## 4. Mechanisms worth using

**Load relevant knowledge when needed.** The Agent Skills format separates discovery metadata, selected instructions, and supporting resources. Exactwork uses short descriptions and standalone companions so the research or handoff procedure need not accompany every coding edit. Installed metadata still costs context, and selecting every companion defeats this design. [Agent Skills specification](https://agentskills.io/specification)

**Curate context without discarding evidence.** Anthropic's context guidance favors a small, useful context and targeted retrieval while warning that compaction can lose important details. Exactwork should retain exact constraints, consequential decisions, unresolved questions, and evidence locations. It should widen an excerpt when missing context could change the conclusion. A summary is a navigation aid, not replacement evidence for a contested claim. [Effective context engineering, 2025-09-29](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

**Reduce data movement at the tool boundary.** Filtering, ranges, pagination, and deterministic aggregation can avoid large model-visible dumps. Any reduction must preserve failure status, relevant diagnostics, and a way to retrieve omitted material. An empty preview must never be described as a complete absence of matches. These are tool-use decisions; Markdown alone cannot implement a new execution engine. [Writing effective tools, 2025-09-11](https://www.anthropic.com/research/writing-tools-for-agents), [Code execution with MCP, 2025-11-04](https://www.anthropic.com/research/code-execution-with-mcp)

**Scale orchestration to expected benefit.** Independent research can run in parallel; a tiny edit does not need several reviewers. Count delegated work in the total cost and require concrete findings from it. The simplest workflow that meets the task is a sensible starting point, with complexity added for a demonstrated need. [Building effective agents, 2024-12-19](https://www.anthropic.com/research/building-effective-agents)

**Keep caching separate from shortening.** Caching depends on provider and harness behavior, eligible prefixes, and reported usage. A skill cannot guarantee a cache hit or lower bills. Changing instructions may alter cache reuse. Evaluate actual input, output, and cache fields instead of calling all omitted or cached text “saved tokens.” [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)

## 5. Concrete examples: adopt selectively

| Source inspected | Useful pattern | Exactwork decision |
|---|---|---|
| Ponytail | Complete minimal changes; proportional checks; explicit measurement boundaries | Keep completeness and restraint; omit session runtime and mandatory modes |
| Anthropic skill-creator | Separate activation tests from output evaluation; inspect artifacts; compare against no skill | Adopt paired evaluation and evidence-based grading; avoid assuming its Claude runner is universal |
| OpenAI current examples | Deterministic scaffolding; checks tied to rendered outcomes | Validate mechanical work in code; keep product-specific APIs outside shared skills |
| Vercel Agent Skills | Prioritized specialist rules and explicit applicability | Coexist with domain expertise; load only relevant rules |
| Superpowers | Intent clarification, causal debugging, evidence before completion claims | Keep the principles; make process proportional to ambiguity and risk |

**Anthropic.** At commit [`2c5958ecac7cee2b583967a2c4981d0f4a75c579`](https://github.com/anthropics/skills/tree/2c5958ecac7cee2b583967a2c4981d0f4a75c579), the skill-creator separates triggering from task-output evaluation and recommends realistic near-miss queries. Its grader inspects actual outputs rather than accepting completion claims. Its comparator hides which variant produced an answer. These are useful evaluation patterns; Exactwork additionally requires explicit ties, task-specific correctness gates, and clear missing telemetry. [Skill creator](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/SKILL.md), [grader](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/agents/grader.md), [comparator](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/agents/comparator.md)

The inspected aggregator can fall back from missing token telemetry to character counts under a token label. Exactwork must distinguish those units and retain unavailable values as missing. The iterative optimizer selects by its test split; publication-quality claims should reserve an additional untouched final set. These are methodological design decisions, not claims that the upstream suite is useless. [Aggregator](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/scripts/aggregate_benchmark.py#L136-L153), [optimization loop](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/scripts/run_loop.py#L194-L218)

**OpenAI.** The `openai/skills` repository now redirects current examples to `openai/plugins`. The inspected `plugin-creator` separates a scaffolding script from schema references; `frontend-testing-debugging` defines a concrete interaction and checks rendered behavior. Exactwork adopts deterministic validation and outcome-specific evidence, not their plugin manifests, browser APIs, or fixed report format. [Deprecation notice](https://github.com/openai/skills/blob/main/README.md), [plugin creator](https://github.com/openai/plugins/blob/main/.agents/skills/plugin-creator/SKILL.md), [frontend testing](https://github.com/openai/plugins/blob/main/plugins/build-web-apps/skills/frontend-testing-debugging/SKILL.md)

**Vercel.** At commit [`1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62`](https://github.com/vercel-labs/agent-skills/tree/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62), React guidance uses a priority index and individual rules; composition guidance bounds advice by framework version. A short web-design entrypoint fetches external rules, illustrating why entrypoint size is not total context cost or offline reproducibility. Exactwork should complement these specialist skills and keep its own basic instructions self-contained. [React](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/react-best-practices/SKILL.md), [composition](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/composition-patterns/SKILL.md), [web design](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/web-design-guidelines/SKILL.md)

**Superpowers.** At commit [`22f0b463e7a5e579904dd6211a520321035526f7`](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7), brainstorming preserves settled choices and permits a quick-task escape or explicit request to proceed. Its broader design workflow can still introduce approval and planning stages; its bootstrap has a very broad skill-applicability threshold. Exactwork omits a universal design gate and prefers specific descriptions. [Brainstorming](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/brainstorming/SKILL.md), [bootstrap](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/using-superpowers/SKILL.md)

Its debugging and verification procedures emphasize reproducing faults, testing hypotheses, and observing success. Exactwork keeps those principles, while binding reusable evidence to a revision and environment instead of rerunning unchanged checks as a ritual. Relevant changes invalidate earlier evidence. [Systematic debugging](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/systematic-debugging/SKILL.md), [verification](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/verification-before-completion/SKILL.md)

## 6. Portability shapes the design

The shared core uses standard names, descriptions, Markdown, and relative resources. It cannot grant tools, permissions, browsing, or permanent session enforcement. The same model inside different harnesses may have different discovery and execution behavior.

Current documentation supports `.agents/skills` in Codex, OpenCode, DeepSeek Harness, Gemini CLI, and Cursor. Other clients have distinct native roots. Duplicate definitions, cloud deployment, and invocation syntax differ. Harness's direct-folder discovery was additionally corroborated in installed public package code version 0.2.2-rc.1. These are documented or source-inspected capabilities, not a claim that Exactwork has passed live tests in every client. The [compatibility guide](compatibility.md) provides the client-specific evidence and commands.

Therefore installation is explicit, project-scoped, and preview-first. Only the core is the default selection. Human documentation and artwork stay outside the skill folders; optional companions are not silently loaded. A manual instruction fallback helps unsupported tools but is labeled separately from native integration.

## 7. What would prove improvement?

Compare no-skill and Exactwork runs on identical fixtures, with the same model, harness, settings, tools, and starting context. Include Ponytail only on overlapping tasks using its supported invocation. Reset workspace state, alternate or randomize run order, repeat stochastic trials, and preserve all failures. Test natural activation separately from explicit invocation. [Agent Skills evaluation guidance](https://agentskills.io/skill-creation/evaluating-skills)

The suite must include positive and negative cases: when research is necessary and when it is wasteful; when clarification prevents a damaging assumption and when a safe default suffices; real defects and clean reviews; incomplete integration tests; changing user constraints; and resumption from a handoff. Deterministic checks should examine actual artifacts. Subjective quality needs blinded review, not flattering self-assessment. [Demystifying agent evaluations, 2026-01-09](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)

Record task success, scope adherence, input/output/cache usage, tool calls, elapsed time, and cost when available. Include subagents. Missing usage is unavailable, not zero; character counts and tokenizer estimates have separate labels. Preserve a held-out set after tuning. Report success and cost together so a cheap failed task cannot look like an improvement.

## 8. Confidence gate before implementation

The research gate passed for a **small, testable first release**: the format is documented; named clients have sourced installation paths; prior art supplies useful patterns and known tradeoffs; and the proposed behavior has falsifiable evaluation criteria. This supports building the package, not publishing a superiority claim.

Known costs remain: every discovered skill adds metadata, every activated skill adds instructions, extra verification can increase latency, and generic guidance may duplicate a capable agent's existing behavior. Too much compression can hide evidence. Too many companions can cause redundant activation. These risks justify narrow descriptions, proportional checks, and explicit measurement.

The release should state separately what was structurally validated, what installer behavior was tested, what isolated agent behavior was observed, and what remains unmeasured. Broader accuracy gains, total-token reductions, and superiority to Ponytail remain hypotheses until matched task results support them. That boundary is part of Exactwork's quality standard.
