# Release verification

Checked **2026-11-12**, release **0.1.0**. This report distinguishes packaging, observed agent behavior, and performance that has not been measured.

## Distribution and structural checks

On Windows with Python 3.11.9:

- **37 unit tests ran: 33 passed, 4 skipped.** Skipped cases require symbolic-link creation privileges unavailable in this account. Three actual Windows junction checks passed.
- All four skill folders passed the package validator: frontmatter, directory/name agreement, size limits, and standalone local references.
- The installer was exercised in temporary projects, including every client destination, preview without writes, exact repeat installation, conflicting existing files, complete preflight before mutation, spaces, nested resources, and path/link rejection.
- Independent review reproduced a malformed-YAML acceptance defect. The validator was corrected and regression cases now pass. It intentionally validates this package's limited single-line frontmatter subset, not arbitrary YAML.
- Local documentation links and SVG XML were checked. Both diagrams were rendered and inspected for legibility and clipping. The actual saved AI cover was opened and inspected; its title and tagline are correct.
- The GitHub Actions workflow covers Windows/Linux and Python 3.10/3.12, using verified pinned action revisions. **Remote CI has not run.** Local Windows success does not prove all matrix environments pass.

No actual agent installation, application profile, or remote repository was changed. The installer was tested only in isolated temporary destinations.

## Agent task observations

Eight fresh-context runs compared each skill with a no-Exactwork baseline; a ninth run retested the revised review skill. The same inherited session model and tool environment were used, but the runtime receipt did not expose an exact model/version or usage totals. Skills were supplied by explicit file reading, not native discovery. Run order was not randomized and grading was not blinded.

| Synthetic task | No-skill baseline | First with-skill run | Follow-up |
|---|---|---|---|
| Zero/missing latency bug | Correct fix; regression checks pass | Correct fix; regression checks pass | Root independently checked zero, missing, empty, normal input and unchanged maximum function |
| Conflicting QuillCache evidence | Correct source interpretation; speedup not established | Correct source interpretation; speedup not established | Both fit the word limit and preserve the supplied source |
| Read-only discount review | Found range guard and integer precision defects | Found range guard; missed integer precision | Revised skill found both in a new run; implementation stayed unchanged |
| Migration handoff after correction | Preserved current scope and unrun integration state | Preserved current scope and unrun integration state | Both retained draft-only/no-deployment boundaries and left inputs unchanged |

The initial review rubric tested the range defect; the baseline revealed the additional precision issue. That criterion was added after observation. The revision adds contract-wide boundary and representation checks. This is a useful development correction, **not** an independently held-out improvement result. The original review skill and all nine output sets are preserved in [results](../evals/results).

The [machine-readable record](../evals/results/local-smoke.json) includes artifact paths, hashes, review findings, and explicit `null` usage fields. Full execution transcripts are not bundled. Checks concern observable artifacts and available completion evidence; they are not a sandbox or a proof of every possible side effect.

These tasks caught a real weakness and exercised the requested behaviors. They do not demonstrate universal accuracy, robust superiority, native activation across clients, or statistical reliability. Most observed outcomes tied the baseline.

## Static instruction footprint

Measurements include the entire UTF-8 `SKILL.md`, including frontmatter. The word count is whitespace-based. Reproduce with `python tools/measure.py`; hashes are in [static-footprint.json](../evals/results/static-footprint.json).

| Skill | Bytes | Words |
|---|---:|---:|
| exactwork | 3,049 | 444 |
| exactwork-research | 2,553 | 358 |
| exactwork-review, revised | 2,306 | 333 |
| exactwork-handoff | 1,575 | 218 |

For context, Ponytail's pinned full skill is 3,496 bytes and its alternative compact `AGENTS.md` rules are 2,721 bytes. Exactwork's core falls between them. These are different instruction sets and entry modes; do not sum Ponytail's alternatives or treat these values as equivalent loaded contexts. [Pinned baseline and hashes](../evals/results/baseline-manifest.json)

No tokenizer or provider usage was substituted for these byte counts. Total-token savings, cost savings, reasoning-token effects, and quality gains are **not established**. The skills add context when loaded and can cost more on tasks that do not need them.

## Remaining validation

Before making cross-client claims, test native discovery and actual task completion in the intended client versions. Before publishing efficiency claims, use repeated matched runs, full usage accounting including delegation, representative private/held-out tasks, and blind quality review where useful. Follow the [evaluation protocol](../evals/README.md).
