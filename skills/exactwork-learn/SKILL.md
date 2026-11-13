---
name: exactwork-learn
description: Improve an explicitly scoped project procedure from verified failures or user corrections, with paired evidence checks, local versioning, and rollback. Use when the user requests project-specific learning or procedure improvement.
license: MIT
---

Use existing authorization for this project. This updates a local procedure, not model weights or global memory. Python 3.10+ is required for the optional helper.

1. Record only a verified failure or explicit correction and the smallest applicable rule. Keep relevance, exclusions, and revalidation conditions in the candidate. Never read browser, authentication, credential, or unrelated profile data.
2. Before drafting, freeze the baseline, rubric, setup, policy, and evaluation manifest. Separate repair, transfer, regression, and independently withheld cases. Do not optimize against final held-out answers or let a candidate change its grader. Retire exposed holdouts before another attempt.
3. Read [the record contract](references/contract.md). Stage minimal records under this project's `.exactwork/`. Evaluate correctness and scope first; use actual comparable telemetry for efficiency. Preserve failures and unknown measurements.
4. Run `scripts/learn.py evaluate`; inspect the supplied evidence and proposed change. Only promote the explicitly authorized `.exactwork/procedure.md`, using the expected base hash and `--apply`. Preview is the default. Preserve backups; rollback rejects changed user content.

Load learned procedures only for their stated scope. Report observed case counts and limits. The checker validates records and hashes; it cannot prove honest grading, hidden holdouts, statistical reliability, or universal improvement.
