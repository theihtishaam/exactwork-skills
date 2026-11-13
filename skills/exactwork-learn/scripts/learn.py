#!/usr/bin/env python3
"""Validate supplied learning records; version one explicitly authorized local procedure.

This checks evidence consistency, not grader truth or general improvement. Python 3.10+.
No commands, network, directory discovery, model calls, or global memory.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import sys
import tempfile
import uuid

LIMIT = 2 * 1024 * 1024
TARGET = ".exactwork/procedure.md"
SPLITS = {"repair", "transfer", "regression", "heldout"}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def schema(value, keys, label):
    require(type(value) is dict and set(value) == set(keys.split()), label + ": unexpected or missing fields")


def string(value, label):
    require(type(value) is str and 0 < len(value.strip()) <= 2000, label + ": expected nonempty string")
    return value


def sha(value, label, nullable=False):
    require((nullable and value is None) or (type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value)), label + ": expected SHA256")


def integer(value, label, minimum=0):
    require(type(value) is int and minimum <= value <= 1000000000000, label + ": expected bounded integer")


def no_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400), "symlink/reparse point rejected: " + str(path))


def project_root(value):
    root = Path(value).absolute()
    for item in [*reversed(root.parents), root]:
        no_link(item)
    require(root.is_dir(), "project must be an existing directory")
    return root.resolve()


def local(root, relative):
    string(relative, "path")
    pieces = relative.split("/")
    require(not PureWindowsPath(relative).is_absolute() and "\\" not in relative and ":" not in relative, "use project-relative forward-slash paths")
    require(pieces[0] == ".exactwork" and all(p not in {"", ".", ".."} for p in pieces), "path must stay inside project .exactwork")
    path = root
    for piece in pieces:
        path = path / piece
        no_link(path)
    require(path.resolve().is_relative_to(root), "path escapes project")
    return path


def read(root, relative):
    path = local(root, relative)
    require(path.is_file(), "expected regular file: " + relative)
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    require(len(data) <= LIMIT, "file exceeds 2 MiB: " + relative)
    return data


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def parse(data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda x: (_ for _ in ()).throw(Invalid("nonfinite JSON number: " + x)))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Invalid("invalid UTF-8 JSON: " + str(error)) from error


def reference(root, ref):
    schema(ref, "path sha256", "reference")
    sha(ref["sha256"], "reference hash")
    data = read(root, ref["path"])
    require(digest(data) == ref["sha256"], "artifact hash changed: " + ref["path"])
    return data


def version1(value):
    require(type(value["schema_version"]) is int and value["schema_version"] == 1, "schema_version must be 1")


def current(root):
    path = local(root, TARGET)
    if not path.exists():
        return None, None
    data = read(root, TARGET)
    return digest(data), data


def run_record(root, run, setup):
    schema(run, "setup_id correct scope artifact origin usage duration", "run")
    require(run["setup_id"] == setup, "unmatched setup_id")
    require(type(run["correct"]) is bool and type(run["scope"]) is bool, "grades must be booleans")
    require(run["origin"] in ("observed", "manual"), "unknown grading origin")
    reference(root, run["artifact"])
    if run["usage"] is not None:
        schema(run["usage"], "kind measurement_id input_tokens output_tokens", "usage")
        require(run["usage"]["kind"] == "actual", "only actual usage is accepted; estimates must stay separate")
        string(run["usage"]["measurement_id"], "usage measurement_id")
        for key in ("input_tokens", "output_tokens"):
            integer(run["usage"][key], key)
    if run["duration"] is not None:
        schema(run["duration"], "measurement_id milliseconds", "duration")
        string(run["duration"]["measurement_id"], "time measurement_id")
        value = run["duration"]["milliseconds"]
        require(type(value) in (int, float) and math.isfinite(value) and value >= 0, "duration must be finite nonnegative number")


def metric_summary(cases, field):
    """Complete matched successful pairs only; all-run totals reported separately."""
    successful = [c for c in cases if all(c[a]["correct"] and c[a]["scope"] for a in ("baseline", "candidate"))]
    def totals(rows):
        values = [c[a][field] for c in rows for a in ("baseline", "candidate")]
        if not values or any(v is None for v in values) or len({v["measurement_id"] for v in values}) != 1:
            return None
        def number(item):
            return item["input_tokens"] + item["output_tokens"] if field == "usage" else item["milliseconds"]
        result = {"measurement_id": values[0]["measurement_id"], "baseline": sum(number(c["baseline"][field]) for c in rows), "candidate": sum(number(c["candidate"][field]) for c in rows)}
        require(all(math.isfinite(result[arm]) for arm in ("baseline", "candidate")), "metric total overflow; all totals must be finite")
        return result
    return {"successful_pairs": len(successful), "matched_successful_totals": totals(successful), "all_run_totals": totals(cases)}


def evaluate(root, proposal_path, evidence_path):
    proposal_bytes, evidence_bytes = read(root, proposal_path), read(root, evidence_path)
    proposal, evidence = parse(proposal_bytes), parse(evidence_bytes)
    schema(proposal, "schema_version id candidate base_sha256 hypothesis scope source policy manifest", "proposal")
    schema(evidence, "schema_version proposal_sha256 grader_sha256 cases", "evidence")
    version1(proposal); version1(evidence)
    for key in ("id", "hypothesis", "scope"):
        string(proposal[key], key)
    sha(proposal["base_sha256"], "base hash", nullable=True)
    require(evidence["proposal_sha256"] == digest(proposal_bytes), "proposal hash changed")
    candidate = reference(root, proposal["candidate"])
    require(proposal["candidate"]["path"].endswith(".md"), "candidate must be Markdown")
    try:
        require(candidate.decode("utf-8").strip() and b"\x00" not in candidate, "candidate must be nonempty text")
    except UnicodeError as error:
        raise Invalid("candidate must be valid UTF-8") from error
    reference(root, proposal["source"])
    policy = parse(reference(root, proposal["policy"]))
    manifest = parse(reference(root, proposal["manifest"]))
    schema(policy, "schema_version min_trials min_heldout_tasks allow_efficiency", "policy")
    schema(manifest, "schema_version setup_id grader tasks", "manifest")
    version1(policy); version1(manifest)
    integer(policy["min_trials"], "min_trials", 2)
    integer(policy["min_heldout_tasks"], "min_heldout_tasks", 2)
    require(type(policy["allow_efficiency"]) is bool, "allow_efficiency must be boolean")
    string(manifest["setup_id"], "setup_id")
    reference(root, manifest["grader"])
    require(evidence["grader_sha256"] == manifest["grader"]["sha256"], "unmatched grader")
    require(type(manifest["tasks"]) is list and 0 < len(manifest["tasks"]) <= 10000, "invalid task list")
    tasks, expected = {}, set()
    for task in manifest["tasks"]:
        schema(task, "id split trials", "task")
        string(task["id"], "task id")
        require(task["id"] not in tasks and task["split"] in SPLITS, "duplicate task id or invalid split")
        integer(task["trials"], "trials", policy["min_trials"])
        require(task["trials"] <= 100, "at most 100 trials per task")
        tasks[task["id"]] = task
        expected.update((task["id"], trial) for trial in range(1, task["trials"] + 1))
    require({task["split"] for task in tasks.values()} == SPLITS, "repair, transfer, regression and heldout splits required")
    require(sum(t["split"] == "heldout" for t in tasks.values()) >= policy["min_heldout_tasks"], "insufficient heldout tasks")
    require(type(evidence["cases"]) is list, "cases must be a list")
    seen, reasons, wins, origins = set(), [], 0, set()
    for case in evidence["cases"]:
        schema(case, "task_id trial baseline candidate", "case")
        string(case["task_id"], "task_id"); integer(case["trial"], "trial", 1)
        key = (case["task_id"], case["trial"])
        require(key in expected and key not in seen, "undeclared or duplicate case")
        seen.add(key)
        for arm in ("baseline", "candidate"):
            run_record(root, case[arm], manifest["setup_id"])
            origins.add(case[arm]["origin"])
        for criterion in ("correct", "scope"):
            before, after = case["baseline"][criterion], case["candidate"][criterion]
            if not after:
                reasons.append("candidate_failed:" + case["task_id"] + ":" + str(case["trial"]) + ":" + criterion)
            wins += int(after and not before)
    require(seen == expected, "missing predeclared cases")
    usage, duration = metric_summary(evidence["cases"], "usage"), metric_summary(evidence["cases"], "duration")
    matched = usage["matched_successful_totals"]
    cheaper = matched is not None and matched["candidate"] < matched["baseline"]
    if not wins and not (policy["allow_efficiency"] and cheaper):
        reasons.append("no_quality_win_or_comparable_actual_token_reduction")
    base_hash, base_bytes = current(root)
    require(base_hash == proposal["base_sha256"], "stale base hash")
    result = {"schema_version": 1, "eligible": not reasons, "reasons": reasons, "cases": len(seen), "criterion_wins": wins,
              "grading_origins": sorted(origins), "usage": usage, "duration": duration,
              "claim_scope": "supplied records only; no proof of grader truth, heldout secrecy, or general improvement"}
    snapshot = {"candidate": candidate, "base": base_bytes, "base_sha256": base_hash, "candidate_sha256": digest(candidate),
                "proposal_sha256": digest(proposal_bytes), "evidence_sha256": digest(evidence_bytes),
                "policy_sha256": proposal["policy"]["sha256"], "manifest_sha256": proposal["manifest"]["sha256"]}
    return result, snapshot


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def exclusive(path, data):
    with path.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def atomic(path, data):
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".learn-", delete=False) as stream:
            name = stream.name
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        no_link(path)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(root):
    path = local(root, ".exactwork/learn.lock")
    token = uuid.uuid4().hex.encode("ascii")
    try:
        exclusive(path, token)
    except FileExistsError as error:
        raise Invalid("learning lock exists; inspect interrupted operation before recovery") from error
    try:
        yield
    finally:
        if read(root, ".exactwork/learn.lock") == token:
            path.unlink()


def promote(root, proposal_path, evidence_path, target, expected_base, apply=False):
    require(target == TARGET, "only .exactwork/procedure.md is a writable target")
    sha(expected_base, "expected base", nullable=True)
    result, snapshot = evaluate(root, proposal_path, evidence_path)
    require(snapshot["base_sha256"] == expected_base, "expected base does not match proposal")
    result["action"] = "preview"
    if not apply or not result["eligible"]:
        return result
    with locked(root):
        require(not local(root, ".exactwork/pending.json").exists(), "pending transaction requires rollback/recovery")
        checked, again = evaluate(root, proposal_path, evidence_path)
        require(checked["eligible"] and snapshot == again, "inputs changed during promotion")
        version = uuid.uuid4().hex
        directory = local(root, ".exactwork/versions")
        directory.mkdir(exist_ok=True)
        directory = local(root, ".exactwork/versions/" + version)
        directory.mkdir()
        record = {"schema_version": 1, "version": version, "target": TARGET, "created_utc": datetime.now(timezone.utc).isoformat(),
                  **{k: v for k, v in snapshot.items() if k not in ("base", "candidate")}, "evaluation": checked}
        if snapshot["base"] is not None:
            exclusive(directory / "base.bin", snapshot["base"])
        exclusive(directory / "record.json", encoded(record))
        pending = local(root, ".exactwork/pending.json")
        exclusive(pending, encoded({"version": version, "record_sha256": digest(encoded(record))}))
        try:
            require(current(root)[0] == expected_base, "target changed after preparation")
            atomic(local(root, TARGET), snapshot["candidate"])
            exclusive(directory / "committed.json", encoded({"candidate_sha256": snapshot["candidate_sha256"], "record_sha256": digest(encoded(record))}))
            pending.unlink()
        except Exception as error:
            raise Invalid("transaction incomplete; recover with rollback for version " + version + ": " + str(error)) from error
        return {**checked, "action": "promoted", "version": version, "target": TARGET, "sha256": snapshot["candidate_sha256"]}


def rollback(root, version, expected_current, apply=False):
    require(type(version) is str and re.fullmatch(r"[0-9a-f]{32}", version), "invalid version id")
    sha(expected_current, "expected current", nullable=True)
    prefix = ".exactwork/versions/" + version + "/"
    def prepare():
        record_bytes = read(root, prefix + "record.json")
        record = parse(record_bytes)
        schema(record, "schema_version version target created_utc base_sha256 candidate_sha256 proposal_sha256 evidence_sha256 policy_sha256 manifest_sha256 evaluation", "version record")
        version1(record)
        require(record["version"] == version and record["target"] == TARGET, "invalid version target")
        for key in ("base_sha256", "candidate_sha256", "proposal_sha256", "evidence_sha256", "policy_sha256", "manifest_sha256"):
            sha(record[key], key, nullable=key == "base_sha256")
        completed = local(root, prefix + "rolled-back.json").exists()
        pending_path = local(root, ".exactwork/pending.json")
        pending_exists = pending_path.exists()
        if pending_exists:
            pending = parse(read(root, ".exactwork/pending.json"))
            schema(pending, "version record_sha256", "pending record")
            require(pending == {"version": version, "record_sha256": digest(record_bytes)}, "another or changed transaction is pending")
        committed = local(root, prefix + "committed.json").exists()
        if committed:
            marker = parse(read(root, prefix + "committed.json"))
            require(marker == {"candidate_sha256": record["candidate_sha256"], "record_sha256": digest(record_bytes)}, "committed version record changed")
        rollback_prepared = local(root, prefix + "rollback-prepared.json").exists()
        if rollback_prepared:
            require(parse(read(root, prefix + "rollback-prepared.json")) == {"record_sha256": digest(record_bytes)}, "rollback record changed")
        allowed = {record["candidate_sha256"]}
        if (pending_exists and not committed) or rollback_prepared:
            allowed.add(record["base_sha256"])
        if completed:
            require(pending_exists and rollback_prepared, "version already rolled back")
            marker = parse(read(root, prefix + "rolled-back.json"))
            require(marker == {"action": "rollback_preview", "version": version, "target": TARGET, "restored_sha256": record["base_sha256"]}, "completed rollback record changed")
            allowed = {record["base_sha256"]}
        require(expected_current in allowed and current(root)[0] == expected_current, "current procedure changed; preserve user modifications")
        base = read(root, prefix + "base.bin") if record["base_sha256"] is not None else None
        require((digest(base) if base is not None else None) == record["base_sha256"], "backup hash changed")
        return base, pending_path if pending_exists else None, completed
    base, pending, completed = prepare()
    result = {"action": "rollback_preview", "version": version, "target": TARGET, "restored_sha256": digest(base) if base is not None else None}
    if apply:
        with locked(root):
            base, pending, completed = prepare()
            marker = local(root, prefix + "rollback-prepared.json")
            if not marker.exists():
                exclusive(marker, encoded({"record_sha256": digest(read(root, prefix + "record.json"))}))
            if not completed:
                if base is None:
                    if local(root, TARGET).exists():
                        local(root, TARGET).unlink()
                else:
                    atomic(local(root, TARGET), base)
                exclusive(local(root, prefix + "rolled-back.json"), encoded(result))
            if pending:
                pending.unlink()
        result["action"] = "rolled_back"
    return result


def hash_arg(value):
    return None if value == "absent" else value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("evaluate", "promote", "rollback"):
        item = sub.add_parser(command)
        item.add_argument("--project", required=True)
        if command != "rollback":
            item.add_argument("--proposal", required=True)
            item.add_argument("--evidence", required=True)
        if command == "promote":
            item.add_argument("--target", required=True)
            item.add_argument("--expected-base-sha256", type=hash_arg, required=True)
        if command == "rollback":
            item.add_argument("--version", required=True)
            item.add_argument("--expected-current-sha256", type=hash_arg, required=True)
        if command != "evaluate":
            item.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = project_root(args.project)
        if args.command == "evaluate":
            result = evaluate(root, args.proposal, args.evidence)[0]
        elif args.command == "promote":
            result = promote(root, args.proposal, args.evidence, args.target, args.expected_base_sha256, args.apply)
        else:
            result = rollback(root, args.version, args.expected_current_sha256, args.apply)
        sys.stdout.buffer.write(encoded(result))
        return 0 if result.get("eligible", True) else 1
    except (Invalid, OSError, TypeError, OverflowError) as error:
        sys.stdout.buffer.write(encoded({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
