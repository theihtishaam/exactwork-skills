# Why Exactwork is built this way

The objective is less avoidable work **per correctly completed task**. Short prompts and short replies are secondary measurements. A tiny answer that omits a requirement fails the objective.

Research preceded implementation. We inspected Ponytail and other established collections, official client documentation, and studies with conflicting findings. The [research record](research.md) explains what the sources support and what remains a design hypothesis.

## Six independent bundles

`exactwork` handles scoped execution. `exactwork-research` handles evidence synthesis. `exactwork-review` assesses an artifact without assuming permission to edit it. `exactwork-handoff` preserves continuation state without creating automatic permanent memory.

The four instruction procedures remain small. Optional `exactwork-context` bundles a bounded extraction script; `exactwork-learn` bundles a local procedure versioning helper and its record contract. There are no forced cross-skill loads. Install only the core to start; add companions when their procedures fit your work. More installed skills still add discovery metadata.

## Decisions and tradeoffs

| Decision | Intended benefit | Cost or limitation |
|---|---|---|
| Task-sized planning | Avoid ceremony for clear work | The model must judge task complexity |
| Selective context, expandable when needed | Avoid broad dumps and repeated reads | Too narrow a read can miss context; explicit widening is required |
| Evidence tied to artifact state | Reuse valid checks without claiming stale success | No hook automatically tracks revisions |
| No global persistent mode or runtime hooks | Easier inspection and portability | Project learning is explicit; it does not create a background service or global memory |
| User intent takes priority over brevity | Preserve requested depth and full deliverables | Sometimes correct work costs more tokens |
| Optional domain skills remain authoritative | Reuse real expertise | Exactwork does not replace technical knowledge |
| Plain files, preview-first installer | No secrets, services, or app configuration needed | Users still need client-supported discovery and suitable permissions |
| Missing metrics remain missing | Avoid false efficiency claims | Observed local usage is reported separately from missing model identity, prices, and uncontrolled cache |

## A working method, not an enforcement layer

The instructions encourage precise scope, bounded searches, failure-aware retries, and checks matched to risk. They cannot add tools, grant authorization, prevent every injection, fix a model's reasoning, or guarantee obedience. Existing user and host instructions still govern the work.

Simple tasks should remain simple. A correction to a label does not need a research report. A multi-file behavior change may require caller inspection and regression tests. A deep-research request warrants substantial investigation before implementation. An explicit request for detailed explanation must not be compressed into an unhelpful slogan.

## When to keep or remove a rule

Keep a rule when a realistic failure or observed improvement justifies its context cost. Test it against a baseline and difficult near-misses. Remove rules that duplicate existing guidance without changing outcomes. Do not grow a universal checklist to compensate for every unrelated incident.

See the [evaluation protocol](../evals/README.md) and [release evidence](verification.md). Behavioral observations are separate from installer correctness and file-size measurements.

## Upgrade evidence

The [0.2 study](benchmark-v0.2.md) compares frozen instructions with no-skill and 0.1 baselines, preserves original grades, and documents arm-blind corrections to overly narrow checks. Measured aggregate savings coexist with regressions in token usage on some tasks. The [learning helper](learning.md) can reject supplied evidence that violates required correctness/scope, but longitudinal learning benefits remain unmeasured.
