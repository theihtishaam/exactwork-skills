#!/usr/bin/env python3
"""Offline consistency audit of the v0.2 release; no model calls or grade changes.

Checks public bytes against PUBLIC hashes. Original hashes link review receipts
to pre-redaction artifacts; omitted private originals cannot be reauthenticated.
Semantic judgments are audited for attribution, not independently re-judged.
"""
import argparse
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def index(rows, fields):
    result = {tuple(row[f] for f in fields): row for row in rows}
    require(len(result) == len(rows), "duplicate rows: " + ",".join(fields))
    return result


def stats(rows):
    tokens = [r["total_tokens"] for r in rows]
    out = {"runs": len(rows), "token_median": statistics.median(tokens),
           "token_min": min(tokens), "token_max": max(tokens)}
    for dest, source in {"task_passes": "task_success", "original_deterministic_passes": "original_deterministic_success",
                         "literal_private_sensitivity_passes": "literal_private_sensitivity_success"}.items():
        out[dest] = sum(r[source] for r in rows)
    for key in ("total_tokens", "input_tokens", "output_tokens", "cached_input_tokens", "tool_calls"):
        out[key] = sum(r[key] for r in rows)
    return out


def grade_check(grade):
    index(grade["checks"], ("check",))
    count = sum(c["passed"] is True for c in grade["checks"])
    require((grade["passed"], grade["total"], grade["deterministic_success"]) ==
            (count, len(grade["checks"]), count == len(grade["checks"])), "inconsistent grade receipt")
    return grade["deterministic_success"]


def audit(root):
    root = root.resolve()
    verified = set()
    def hashed(path, expected):
        require(path.resolve().is_relative_to(root), "hash path escapes release")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "hash mismatch: " + str(path.relative_to(root)))
        verified.add(str(path.relative_to(root)))
    evidence = read(root / "evidence/analysis.json")
    final = read(root / "final-results.json")
    rows, summary = final["runs"], final["summary"]
    fields = ("phase", "case", "run_id")
    actual, exported = index(rows, fields), index(evidence["runs"], fields)
    expected = {(p, c, a, t) for p, cases, arms, trials in [
        ("dev", ("d01", "d02", "d03", "d04"), ("none", "v01", "v02"), (1,)),
        ("holdout", ("h01", "h02"), ("none", "v01", "v02"), (1, 2, 3))]
        for c in cases for a in arms for t in trials}
    expected |= {("ponytail", c, "ponytail", t) for c, ts in [("d02", (1,)), ("d04", (1,)), ("h02", (1, 2, 3))] for t in ts}
    require(set(index(rows, ("phase", "case", "condition", "trial"))) == expected, "missing/unexpected experimental cells")
    require(len(rows) == summary["runs"] == evidence["expected_runs"] == evidence["scheduled_runs"] == evidence["exported_runs"] == 35, "expected exactly 35 runs")
    require(evidence["complete"] and actual.keys() == exported.keys(), "incomplete export/join")
    for name, hashes in evidence["inputs"].items():
        hashed(root / "evidence/inputs" / name, hashes["public_sha256"])
    scheduled = []
    prompt_hash = read(root / "public_eval_tools/common-prompt-manifest.json")["common_prompt_sha256"]
    hashed(root / "public_eval_tools/common-prompt.txt", prompt_hash)
    for phase, count in (("dev", 12), ("holdout", 18), ("ponytail", 5)):
        schedule = read(root / "evidence/inputs" / (phase + "-schedule.json"))
        require(schedule["phase"] == phase and schedule["common_prompt_sha256"] == prompt_hash, "schedule prompt mismatch")
        scheduled.extend(dict(job, phase=phase) for job in schedule["jobs"])
        require(evidence["phases"][phase] == {"expected": count, "scheduled": count, "exported": count}, "phase export counts")
    schedule_index = index(scheduled, fields)
    require(schedule_index.keys() == actual.keys(), "schedule join mismatch")
    manifest = read(root / "benchmark/FROZEN-MANIFEST.json")
    for name, digest in (manifest["files"] | manifest["evaluator_files"]).items():
        hashed(root / "benchmark" / name, digest)
    receipt = read(root / "benchmark/evaluator/CONTRACT-GRADER-CORRECTION.json")
    for name, key in (("grade.py", "original_grade_sha256"), ("grade_corrected.py", "base_sha256"), ("grade_contract_corrected.py", "new_sha256")):
        hashed(root / "benchmark/evaluator" / name, receipt[key])
    hashed(root / "benchmark/FROZEN-MANIFEST.json", receipt["frozen_manifest_sha256"])
    semantic = read(root / "blind-review/semantic-grades.json")["records"]
    mapping = read(root / "blind-review/semantic-map.json")
    require(len(semantic) == 24 and semantic.keys() == mapping.keys(), "semantic map coverage")
    blind = {tuple(v[f] for f in fields): sample for sample, v in mapping.items()}
    require(len(blind) == 24, "duplicate semantic run mapping")
    require(blind.keys() == {k for k in actual if k[1] in {"d01", "h01", "h02"}}, "semantic run coverage mismatch")
    d03_map = {Path(v.replace("\\", "/")).parent.name: k for k, v in read(root / "blind-review/dev-evidence-map.json").items()}
    d03_review = read(root / "blind-review/dev-evidence/review.json")["answers"]
    d03_regrade = read(root / "blind-review/dev-evidence/regrade.json")["records"]
    h01_regrade = read(root / "blind-review/h01-contract-regrade.json")["records"]
    require(d03_map.keys() == {k[2] for k in actual if k[1] == "d03"} and len(d03_map) == 3, "d03 review mapping mismatch")
    require(set(d03_map.values()) == d03_review.keys() == d03_regrade.keys(), "d03 review coverage mismatch")
    require(h01_regrade.keys() == {blind[k] for k in blind if k[1] == "h01"}, "h01 regrade coverage mismatch")
    corrected_count = 0
    for key, row in actual.items():
        exp, schedule = exported[key], schedule_index[key]
        require(all(row[f] == exp[f] == schedule[f] for f in (*fields, "condition", "trial")), "run identity mismatch")
        base = root / "evidence" / exp["evidence_path"]
        require(base == root / "evidence/runs" / key[0] / key[1] / key[2], "evidence path mismatch")
        for name, digest in exp["public_files"].items():
            hashed(base / name, digest)
        record = read(base / "record.json")["original_record"]
        require(record["prompt_sha256"] == exp["prompt_sha256_original"] == exp["source_hashes"]["prompt.txt"], "original prompt provenance mismatch")
        require(record["skill_sha256"] == exp["skill_sha256_original"] and record["fixture_before"]["manifest_sha256"] == exp["fixture_manifest_sha256_original"], "original skill/fixture provenance mismatch")
        trace = [json.loads(line) for line in (base / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
        turns = [event for event in trace if event["type"] == "turn.completed"]
        require(len(turns) == record["completion_count"] == exp["completion_count"] == 1, "completion count mismatch")
        require(record["usage"] == exp["usage"] == turns[-1]["usage"], "usage receipt/trace mismatch")
        require(record["run_dir"].replace("\\", "/") == exp["evidence_path"], "record run directory mismatch")
        for metric in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens"):
            require(type(row[metric]) is int and row[metric] >= 0 and row[metric] == record["usage"][metric], "usage mismatch: " + metric)
        require(row["total_tokens"] == exp["total_tokens"] == row["input_tokens"] + row["output_tokens"], "token total mismatch")
        require(row["cached_input_tokens"] <= row["input_tokens"] and row["reasoning_output_tokens"] <= row["output_tokens"], "token subset mismatch")
        calls = sum(e["type"] == "item.completed" and e["item"]["type"] in {"command_execution", "mcp_tool_call", "collab_tool_call", "web_search"} for e in trace)
        require(row["tool_calls"] == record["tool_call_item_count"] == exp["tool_call_item_count"] == calls, "tool count mismatch")
        require(row["wall_seconds"] == record["wall_seconds"] == exp["wall_seconds"], "wall time mismatch")
        complete = record["run_status"] == exp["run_status"] == "completed"
        require(row["completed"] == complete and exp["export_status"] == "exported", "completion status mismatch")
        original = read(base / "grade.json")
        original_ok = grade_check(original)
        require(original["case"] == row["case"] and (original["passed"], original["total"]) == (exp["checks_passed"], exp["checks_total"]), "grade case/count mismatch")
        require(original_ok == exp["deterministic_success"] == row["original_deterministic_success"], "original grade mismatch")
        corrected_path = root / "corrected-grades" / key[0] / key[1] / key[2] / "grade.json"
        require(corrected_path.exists() == (row["case"] in {"d03", "h01"}), "correction coverage mismatch")
        corrected = read(corrected_path) if corrected_path.exists() else original
        corrected_count += corrected_path.exists()
        corrected_ok = grade_check(corrected)
        allowed = "sources identify data sections" if row["case"] == "d03" else "ROW_COUNT_MISMATCH cause evidence line"
        before, after = (sorted(g["checks"], key=lambda c: c["check"]) for g in (original, corrected))
        require(len(before) == len(after) and all(a == b or (a["check"] == b["check"] == allowed and b["passed"] is True) for a, b in zip(before, after)), "unapproved grade correction")
        sample, sem, strict = blind.get(key), True, True
        if sample or row["case"] == "d03":
            artifacts = {a["path"]: a for a in exp["artifacts"]}
            answer = artifacts["answer.json"]
            require(answer["public_sha256"] == exp["public_files"]["artifacts/answer.json"], "answer public hash mismatch")
            if sample:
                review = semantic[sample]
                require(mapping[sample] == {f: row[f] for f in (*fields, "condition", "trial")}, "blind condition map mismatch")
                require(review["case"] == row["case"] and review["answer_sha256"] == answer["original_sha256"], "semantic answer attribution mismatch")
                sem, strict = review["semantic_success"], review.get("literal_frozen_cause_probe_rule_satisfied", True)
            if row["case"] in {"d03", "h01"}:
                name = d03_map[row["run_id"]] if row["case"] == "d03" else sample
                proof = d03_regrade[name] if row["case"] == "d03" else h01_regrade[name]
                a, b = ("original", "corrected") if row["case"] == "d03" else ("original_strict", "contract_aligned")
                require(proof["answer_sha256"] == answer["original_sha256"] and proof[a]["success"] == original_ok and proof[b]["success"] == corrected_ok, "blind regrade receipt mismatch")
                if row["case"] == "d03":
                    hashed(root / "blind-review/dev-evidence" / (name + ".json"), answer["original_sha256"])
                    sem = d03_review[name]["semantic_success"]
        require(row["blind_sample"] == sample and row["semantic_success"] == sem, "semantic label mismatch")
        require(row["contract_deterministic_success"] == corrected_ok and row["task_success"] == (complete and corrected_ok and sem), "task result mismatch")
        require(row["literal_private_sensitivity_success"] == (complete and original_ok and sem and strict), "sensitivity result mismatch")
    for field, label in (("phase", "phases"), ("case", "cases")):
        grouped = {value: {arm: stats([r for r in rows if r[field] == value and r["condition"] == arm]) for arm in sorted({r["condition"] for r in rows if r[field] == value})} for value in sorted({r[field] for r in rows})}
        require(summary[label] == grouped, "aggregate drift: " + label)
    coding = {arm: stats([r for r in rows if r["condition"] == arm and r["case"] in {"d02", "d04", "h02"}]) for arm in ("none", "v01", "v02", "ponytail")}
    require(summary["matched_coding_subset"] == coding, "coding aggregate drift")
    holdout = index([r for r in rows if r["phase"] == "holdout"], ("case", "trial", "condition"))
    pairs = [dict(case=c, trial=t, none_tokens=holdout[c, t, "none"]["total_tokens"], v01_tokens=holdout[c, t, "v01"]["total_tokens"], v02_tokens=holdout[c, t, "v02"]["total_tokens"], v02_minus_none=holdout[c, t, "v02"]["total_tokens"]-holdout[c, t, "none"]["total_tokens"]) for c in ("h01", "h02") for t in (1, 2, 3)]
    require(summary["holdout_pairs"] == pairs and summary["holdout_candidate_lower_than_none_pairs"] == sum(p["v02_minus_none"] < 0 for p in pairs), "paired result drift")
    percentages = {}
    for arm in ("none", "v01"):
        value = 100 * (1 - sum(p["v02_tokens"] for p in pairs) / sum(p[arm + "_tokens"] for p in pairs))
        require(abs(summary["holdout_percent_reduction_vs_" + arm] - value) < 1e-10, "percentage drift")
        percentages["holdout_reduction_vs_" + arm] = value
    percentages["coding_reduction_vs_ponytail"] = 100 * (1 - coding["v02"]["total_tokens"] / coding["ponytail"]["total_tokens"])
    for case, arm in (("h01", "none"), ("h02", "none"), ("h02", "ponytail")):
        totals = summary["cases"][case]
        percentages[case + "_reduction_vs_" + arm] = 100 * (1 - totals["v02"]["total_tokens"] / totals[arm]["total_tokens"])
    with (root / "final-results.csv").open(encoding="utf-8-sig", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    require(csv_rows == [{k: "" if v is None else str(v) for k, v in row.items()} for row in rows], "CSV/JSON drift")
    return {"audit_passed": True, "runs": len(rows), "verified_public_files": len(verified), "semantic_receipts": 27, "corrected_grade_receipts": corrected_count, "task_passes": sum(r["task_success"] for r in rows), "percentages": percentages, "limits": "Internal consistency, not independent model execution or authentication of omitted private originals; semantic judgments retained."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    try:
        print(json.dumps(audit(parser.parse_args().root), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"audit_passed": False, "error": str(error)}, indent=2))
        sys.exit(1)
