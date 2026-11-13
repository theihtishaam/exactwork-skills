# Learning from evidence

`exactwork-learn` is an agent procedure plus a deterministic record checker. The agent performs the reasoning and evaluations; the helper checks the submitted evidence structure, referenced file hashes, matching conditions, and local update transaction. Neither changes the model's weights.

## Use it in a project

Install `exactwork-learn` for the client you use. Invoke it when you have a verified recurring failure or an explicit correction worth preserving. Ordinary task execution does not silently create memory or trigger model calls.

1. Identify the exact failure, desired behavior, scope, and exclusions. A preference such as a report format remains a project preference, not a claim of universal quality.
2. Freeze the baseline procedure, evaluation rubric, setup, policy, and task manifest before drafting a candidate. Keep independent holdouts unavailable to the author. Use separate repair, transfer, regression, and held-out cases.
3. Write one small candidate and collect paired outcomes. Keep every declared trial, including failures. Correctness and scope take priority. Token comparisons require actual matching usage, including relevant retries; missing measurements stay unknown.
4. Evaluate and inspect the proposed update. Promotion changes only `.exactwork/procedure.md` in the selected project and records a backup. Rollback checks the current hash so later user edits are preserved.
5. In future sessions, ask the agent to load the project procedure when its scope matches. Revalidate when project requirements, tools, or model behavior change. Exposed holdouts become development data for the next candidate.

The minimum record policy requires two trials per task and at least two held-out tasks. This is a coverage floor, not statistical assurance. Evaluation consumes tokens and time; those costs must be included before claiming net savings.

## Commands

From the installed skill directory, with files prepared according to the [record contract](../skills/exactwork-learn/references/contract.md):

```sh
python scripts/learn.py evaluate --project PROJECT --proposal .exactwork/proposal.json --evidence .exactwork/evidence.json
python scripts/learn.py promote --project PROJECT --proposal .exactwork/proposal.json --evidence .exactwork/evidence.json --target .exactwork/procedure.md --expected-base-sha256 HASH
```

The second command previews the update. Append `--apply` for the authorized write. Use `absent` instead of `HASH` when the procedure does not exist. The returned version and hash identify the exact update.

```sh
python scripts/learn.py rollback --project PROJECT --version VERSION --expected-current-sha256 HASH
```

Rollback also previews by default; append `--apply` to restore the exact prior bytes. If the file changed after promotion, rollback refuses to overwrite it. The contract explains interrupted-transaction recovery.

## Try the mechanism without an AI call

From the repository root:

```sh
python skills/exactwork-learn/tests/test_learn.py --example ./learning-demo
```

This creates a new directory containing **invented test records**, then prints their paths and base hash. Run the commands above against that directory to inspect, promote, and roll back the synthetic update. These numbers and labels are not evidence of agent improvement. The tests exercise rejected regressions, incomplete evidence, stale files, tampering, and recovery.

## What this does and does not establish

The helper can enforce consistency: exact hashes, declared task/trial coverage, paired setup identifiers, all candidate correctness/scope labels passing, and a qualifying gain. It cannot prove honest grading, a meaningful rubric, genuine withheld tasks, or the provenance of a caller-labeled usage value. Inspect those independently. It reports time only when measurements are comparable; time alone cannot qualify a promotion.

The 0.2 study also illustrates why graders need review: a valid alternative citation initially failed an overly narrow check. A condition-blind audit justified a separately versioned correction, while preserving original results and unchanged candidate instructions. The [study report](benchmark-v0.2.md) shows both scores. This was a manual release evaluation, not an experiment run by the new learning helper. The helper's regression-rejection and rollback behavior were tested separately; no longitudinal learning benefit has been established.

There is no autonomous daemon. Global skills, application code, model weights, evaluation graders, and user profiles are outside the helper's writable target. Local versioning assumes cooperating processes, with checked hashes and recovery records; it is not protection against a hostile filesystem writer or arbitrary power loss.
