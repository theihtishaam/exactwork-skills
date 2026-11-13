# Comparing Exactwork with other skill projects

Reviewed 2026-11-13. This is a source-backed guide to ten projects, including Exactwork. It compares their documented scope and intended use, not intelligence scores or a quality leaderboard. The collection includes skill libraries, development methodologies, specification frameworks and runtime toolkits: they are not interchangeable benchmark units.

## Choose by the job

| Project | Documented focus | When its approach fits |
|---|---|---|
| [Exactwork](https://github.com/theihtishaam/exactwork-skills/blob/4ae7fc0b16a955935b9d54d4b23c80f5efd3b282/README.md) | Focused tasks and evidence. Six procedures; traceable excerpts; local learning with rollback. | Choose a compact procedure for a task, then inspect its evidence and results. |
| [Ponytail](https://github.com/DietrichGebert/ponytail/blob/96608e078b2d5ea607c5c3b8b5a54d1c1fba6846/README.md) | Coding workflow and runtime. Coding instructions with host integrations and review workflows. | Choose its coding workflow and host-specific runtime when those integrations fit. |
| [Superpowers](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/README.md) | Software development method. Design, implementation plans, test-driven work and reviews. | Choose a coordinated development method with design approval and review steps. |
| [GSD Core](https://github.com/open-gsd/gsd-core/blob/0f49a38f1415e7d073b8bddb05d18c01c63d6b05/README.md) | Context and spec-driven work. Meta-prompting and context engineering across coding agents. | Explore its development and context workflow for longer coding projects. |
| [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD/blob/e435a22574fe55722841086e5566420178b98df3/README.md) | Agile delivery workflow. Clarify, plan, build, verify and adjust; modular tooling. | Choose its broader delivery process and planning artifacts. The reviewed main branch describes v7 preview and a separate v6.12 stable route. |
| [Spec Kit](https://github.com/github/spec-kit/blob/2ee2b1e8005905db05f5717300a469b3068b908f/README.md) | Specifications and processes. Reusable templates, workflows, integrations and extensions. | Choose configurable processes for specification, bug fixing or idea assessment. |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/d12c2817776779e06891d68230773b3bb673b106/README.md) | Change proposals and specs. Propose, implement and archive changes with requirements. | Choose a change-centered specification workflow that retains design and task artifacts. |
| [ECC](https://github.com/affaan-m/ECC/blob/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b/README.md) | Agent configuration ecosystem. Skills, rules, hooks, memory and continuous-learning features. | Choose a broader configurable toolkit; its minimal path can omit runtime hooks. |
| [Anthropic Skills](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/README.md) | Specialized task skills. Document, creative, technical and business skill examples. | Choose domain-specific instructions and implementations for the artifact you need. |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/README.md) | Web and platform expertise. React, web interface, writing and Vercel optimization guidance. | Choose specialist guidance for web applications, interfaces and the Vercel platform. |

The descriptions summarize the linked README snapshots. They are not exhaustive feature audits; an omitted capability is not a claim that a project lacks it. GSD's former repository redirects to GSD Core. BMad's reviewed main branch is preview documentation. Ponytail uses the pinned version from the original comparison rather than claiming to describe a newer release.

## Where Exactwork is a useful fit

Exactwork combines six small entry procedures with a source-preserving context helper and explicit project-local learning. Its core entry file is 2,167 UTF-8 bytes. The optional learning helper validates supplied records before promotion and retains rollback; it does not establish that the supplied grades are true. No separate runtime service is required. These properties can be inspected in the [skills](../skills), [learning guide](learning.md), and [instruction-size chart](../assets/instruction-footprint.svg).

Those are reasons to try Exactwork for scoped, inspectable work. They are not proof that it replaces specialized expertise, that other projects lack equivalent capabilities, or that smaller files improve every task. Libraries with domain-specific instructions can complement a working procedure.

## What we can compare numerically

Only Ponytail core has been tested alongside Exactwork in this release. The matched five-run coding subset contains three unique synthetic tasks. No skill, Exactwork 0.1, Exactwork 0.2 and Ponytail core each passed 5/5. Compact Exactwork used 444,117 aggregate reported input+output tokens and Ponytail 493,995: a 10.1% difference within that subset. Ponytail ran later rather than interleaved; its full runtime and review skill were excluded. Model identity and cache state were uncontrolled. This establishes no accuracy lead or general ranking. [Study and raw results](benchmark-v0.2.md).

The other eight external projects in this guide were inspected through documentation, not executed in matched model trials. Their quality, intelligence, token usage, speed and reliability relative to Exactwork are **not measured here**. They must not be plotted as zero or given invented scores.

## Intelligence and work quality

A skill changes the instructions a model receives; this release does not measure a model's general intelligence. Task correctness is one observable quality measure. Useful future comparisons should also measure instruction compliance, regression avoidance, evidence accuracy and review usefulness with independently graded tasks. A longer answer, a larger skill catalog or a lower token count alone is not a quality score.

Before claiming a lead across projects or models, freeze representative tasks and rubrics; pin each selected skill, host and exact model; compare the same tool access and budgets; interleave conditions with repeated trials; use graders independent of the candidate; retain failures and uncertainty. Test the relevant workflow or skill from each collection rather than comparing an entire library with a single prompt. This is an evaluation requirement, not a completed experiment.
