# Independent learner review

Status: all three reproduced defects were fixed by the author and independently verified. Final combined suite: 38 tests passed in 5.707 seconds (32 candidate tests plus 6 independent tests).

Scope: `work/v02/learn_candidate` only. The main experimental candidate remains frozen and was not edited. Review fixtures are synthetic and local, under `work/v02/learn-review`; no model calls, held-out data, credentials, or browser data were accessed.

Initial run: all 29 original tests passed. Two additional safety checks passed. Three additional regression checks failed, reproducing the findings below.

## Findings sent to the author

1. **Rollback recovery becomes stuck after pending cleanup fails.** Inject a failed promotion commit, then let rollback restore the base and write `rolled-back.json`, but fail deletion of `.exactwork/pending.json`. The restored content is correct, yet retry rejects `version already rolled back`, and new promotion rejects the remaining pending transaction. This violates the documented interrupted-operation recovery path. Minimal fix: recognize a valid completed rollback with matching pending state, verify the restored hash and unchanged user content, and permit cleanup retry without another overwrite.
2. **Falsey pending records bypass validation.** After ordinary promotion, set `.exactwork/pending.json` to `{}`. Rollback treats the parsed object as absent, changes the procedure, and leaves the malformed pending blocker. Minimal fix: distinguish a missing path from an existing falsey JSON value and validate every existing pending record before mutation.
3. **Finite duration inputs can overflow the reported total.** Set all supplied duration values to `1e308`. Each passes the finite-value check, but summation produces infinity; CLI JSON encoding raises an uncaught ValueError and exits 1 with a traceback and empty stdout. Minimal fix: validate aggregate totals before returning or persisting them, producing the documented structured exit-2 error.

The author was notified with the exact reproducible test names in `test_independent_review.py` and acknowledged ownership of implementation fixes.

## Safety checks observed

- Real `promote --apply` separately rejected failed correctness and scope labels despite declared token savings; exit 1 reported `eligible: false`, with the project file snapshot unchanged.
- Real `promote --apply` rejected a stale baseline after a user edit; exit 2 preserved the exact edited bytes.
- Existing tests exercise correctness failures, duplicate/missing/undeclared task/trial pairs, mismatched setup/grader, altered referenced artifacts, rollback user edits, preview immutability, and interruption before/after replacement.
- An extra independent test now checks that a user edit made after restore but before a pending-cleanup retry remains untouched.

The supplied labels and declared telemetry are trusted input by design. The schema does not authenticate provider usage or execute a grader. Accepted synthetic labels are therefore not proof of measured improvement. This limitation is explicit in the skill and contract and is not reported here as an implementation bypass. Noncooperating filesystem races are outside the documented cooperative transaction model; this review does not claim hostile-writer or power-loss safety.

## Final fix verification

- Completed rollback with a matching remaining pending transaction permits a cleanup-only retry using the restored expected hash. It verifies the completion marker and backup, and does not rewrite the procedure. A new intervening user edit is still rejected and preserved.
- Every existing pending JSON record is validated, including falsey values. The candidate regression covers `{}`, `null`, `[]`, `false`, `0`, and an empty JSON string.
- Nonfinite aggregate telemetry is rejected before returning or persisting an evaluation; the real CLI now returns structured JSON with exit 2 for the reproduced overflow.
- The original 29 tests, three author-added regressions, and all six independent review tests passed together. The independent CLI gate test contains separate correctness and scope subcases; the recovery edit test checks both claimed restored and edited hashes.
- Final reviewed script SHA-256: `b01fc19d420013af86bf55063a2c09af88c4e409de624538cf61fb2d3fbc7fe7`.
- Candidate MIT frontmatter and the existing MIT LICENSE were added as requested. Main benchmark candidate source was not modified.

Reproduce with `python evals/v0.2/learn-review/test_independent_review.py` from the workspace. The harness places all temporary fixtures beneath `learn-review` and disables Python bytecode writes. `verification.json` records the observed test result and final source identity. This is local implementation verification, not evidence that the learner improves model performance.
