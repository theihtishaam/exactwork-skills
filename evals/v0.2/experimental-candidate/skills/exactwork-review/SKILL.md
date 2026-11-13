---
name: exactwork-review
description: Review an artifact against its stated contracts and report reproducible defects or coverage gaps. Use for audits or verification; do not edit unless fixes are authorized.
license: MIT
---

# Exactwork Review

Review the current artifact and requested scope. Inspection does not authorize editing.

1. Map the stated contracts to code paths, data transformations, or deliverables. Inspect connected context before deciding an apparent defect is real.
2. Check each contract, not just the first suspicious line. Include representative valid boundaries, invalid inputs that must be rejected, representation changes, and behavior required to remain unchanged. For numeric claims, check units, denominators, and coverage.
3. Follow each suspected failure to a realistic trigger and consequence. Reproduce with a focused check when possible. Distinguish verified defects, unresolved questions, and environment failures. Do not invent severity or findings to fill a quota.
4. Inspect actual artifacts and evidence tied to the current revision. A passing check proves only what it exercises; delegated completion text and prepared files are not live verification. Reuse valid checks and rerun those invalidated by changes.

Report actionable findings with location, trigger, consequence, and smallest useful correction, ordered by impact. Omit personal style preferences unless they violate a requirement or cause a concrete problem. If no defect is supported, say so and name material coverage limits. Authorized fixes remain within scope and require relevant verification.
