---
name: exactwork-review
description: Review a change or deliverable for concrete correctness, coverage, and evidence gaps. Use for an audit, final verification, or requested review; do not edit unless a fix is authorized.
license: MIT
---

# Exactwork Review

Assess the requested artifact against its actual requirements. Review is read-only unless the user also authorizes fixes. Host and user instructions govern scope.

- Establish the relevant revision, inputs, acceptance criteria, and surrounding contracts. Read connected context when needed to understand an apparent defect. An isolated snippet may omit the guarantee that makes it correct.
- Prioritize failures that change results or harm users: incorrect behavior, omitted requirements, unsafe data handling, broken integrations, unsupported claims, or inaccessible output. Style preferences are findings only when they violate a requirement or create a concrete problem.
- Follow a suspect path to a realistic trigger and observable consequence. For code, inspect callers and boundary cases; for data, reconcile units, coverage, duplicates, and totals; for research, check source support and comparability; for visual work, inspect the rendered artifact.
- Use a focused reproduction or check when available. Distinguish verified defects from unresolved questions. A failed test can be an environment failure; a passing test covers only what it exercises. Inspect delegated artifacts instead of accepting a completion claim alone.
- Check that evidence belongs to the current artifact. Reuse still-valid checks; rerun those invalidated by changes. Never imply an unperformed live or integration check succeeded.
- Return actionable findings with location, trigger, impact, evidence, and the smallest useful correction. Order by consequence. Do not invent a minimum number of findings or inflate severity to appear thorough.

If no actionable defect is supported, say so and identify material coverage limits. If fixing is authorized, make the scoped correction and verify its consequence; do not use the review as permission for an unrelated rewrite.
