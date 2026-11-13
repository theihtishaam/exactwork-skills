"""Publish allowlisted evidence from this study's fresh scheduled runs.

No model requests, credential/configuration reads, or old-session discovery.
Source files are never changed. Raw diagnostics and reasoning are not exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
from typing import Any

from portable_runner import _plain_path, fixture_manifest, parse_events

PHASE_COUNTS = {"dev": 12, "holdout": 18, "ponytail": 5}
SESSION_KEYS = {"thread_id", "turn_id", "threadId", "turnId", "thread_ids", "turn_ids", "receiver_thread_ids", "sender_thread_id", "parent_thread_id", "session_id", "sessionId"}
ITEM_FIELDS = {
    "command_execution": ("command", "aggregated_output", "exit_code", "status"),
    "agent_message": ("text",),
    "file_change": ("changes", "status"),
    "mcp_tool_call": ("server", "tool", "arguments", "result", "error", "status"),
    "collab_tool_call": ("tool", "prompt", "agents_states", "status"),
    "web_search": ("query", "action"),
    "error": ("message",),
}
RECORD_FIELDS = {
    "schema_version", "harness", "harness_version", "version_evidence", "model", "model_selection", "run_dir", "telemetry_dir", "command", "windows_sandbox", "sandbox_configuration_reason", "prompt_sha256", "skill_sha256", "skill_text_present_in_prompt", "fixture_before", "timeout_seconds", "timed_out", "cleanup", "process_exit_code", "launch_error_type", "cost_usd", "usage_semantics", "operation_count_semantics", "tool_output_chars_semantics", "isolation_limit", "wall_seconds", "completion_count", "failure_event_count", "malformed_event_count", "event_counts", "usage", "usage_status", "tool_call_items", "tool_call_item_count", "tool_output_chars", "tool_output_chars_observed", "command_output_items_available", "command_output_items_missing", "failed_or_declined_operation_items", "file_change_items", "final_message_sha256", "run_status", "exports", "answer_sha256",
}
PERSONAL_PATH = re.compile(r"(?i)(?:\b[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"<>]+|/(?:home|Users)/[^/\s\"<>]+)")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def owned(root: Path, path: Path) -> Path:
    path = Path(os.path.abspath(path))
    _plain_path(path)
    if path == root or not path.is_relative_to(root):
        raise ValueError("Source path must stay beneath the explicit study root")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def session_values(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in SESSION_KEYS:
                if isinstance(child, str):
                    found.add(child)
                elif isinstance(child, list):
                    found.update(item for item in child if isinstance(item, str))
            found.update(session_values(child))
    elif isinstance(value, list):
        for child in value:
            found.update(session_values(child))
    return found


class Redactor:
    def __init__(self, replacements: list[tuple[str, str]], identifiers: set[str] | None = None):
        self.replacements = []
        for original, replacement in sorted(replacements, key=lambda p: len(p[0]), reverse=True):
            if not original or not re.fullmatch(r"<[A-Z_]+>", replacement):
                raise ValueError("Redaction must map a nonempty exact path to an uppercase placeholder")
            # Match both slash conventions and nested JSON escaping, without finding other files.
            parts = re.split(r"[\\/]+", original.rstrip("\\/"))
            expression = r"[\\/]+".join(re.escape(part) for part in parts)
            self.replacements.append((re.compile(expression, re.IGNORECASE), replacement))
        self.identifiers = sorted(identifiers or set(), key=len, reverse=True)

    def text(self, value: str) -> str:
        for expression, replacement in self.replacements:
            value = expression.sub(lambda _: replacement, value)
        for identifier in self.identifiers:
            if identifier:
                value = value.replace(identifier, "<SESSION_ID>")
        return value

    def value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, list):
            return [self.value(item) for item in value]
        if isinstance(value, dict):
            return {self.text(key): self.value(item) for key, item in value.items() if key not in SESSION_KEYS and key not in {"reasoning", "reasoning_text", "analysis"}}
        return value

    def assert_public(self, value: str) -> None:
        if PERSONAL_PATH.search(value):
            raise ValueError("Unmapped personal absolute path detected; supply an exact --redact-prefix mapping")
        if any(identifier and identifier in value for identifier in self.identifiers):
            raise ValueError("Session identifier survived redaction")


def observable_trace(events: list[dict], redactor: Redactor) -> tuple[list[dict], dict]:
    exported, omitted = [], Counter()
    for event in events:
        kind = event.get("type")
        if kind == "item.completed":
            item = event.get("item", {})
            item_type = item.get("type") if isinstance(item, dict) else None
            if item_type not in ITEM_FIELDS or item.get("channel") in {"analysis", "reasoning"}:
                omitted[str(item_type)] += 1
                continue
            safe = {"type": item_type, **{key: item[key] for key in ITEM_FIELDS[item_type] if key in item}}
            exported.append({"sequence": len(exported) + 1, "type": kind, "item": redactor.value(safe)})
        elif kind == "turn.completed":
            exported.append({"sequence": len(exported) + 1, "type": kind, "usage": redactor.value(event.get("usage"))})
        elif kind in {"turn.failed", "error"}:
            exported.append({"sequence": len(exported) + 1, "type": kind, "error": redactor.value(event.get("error", event.get("message")))})
        else:
            omitted[str(kind)] += 1
    return exported, dict(sorted(omitted.items()))


def encode_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_public(path: Path, data: bytes, redactor: Redactor) -> str:
    redactor.assert_public(data.decode("utf-8"))
    _plain_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".writing")
    _plain_path(temporary)
    temporary.write_bytes(data)
    temporary.replace(path)
    return digest(data)


def export_run(root: Path, out: Path, phase: str, job: dict, mappings: list[tuple[str, str]]) -> dict:
    row = {key: job[key] for key in ("case", "condition", "trial", "run_id")}
    row["phase"] = phase
    for key in ("case", "condition", "run_id"):
        if not re.fullmatch(r"[a-z0-9_-]+", str(row[key])):
            raise ValueError("Invalid scheduled path component")
    fixture = owned(root, root / "runs" / phase / row["case"] / row["run_id"])
    telemetry = owned(root, fixture.with_name(fixture.name + "-telemetry"))
    required = [telemetry / name for name in ("record.json", "study-result.json", "grade.json", "stdout.jsonl", "prompt.txt")]
    if not all(path.is_file() for path in required):
        row.update(export_status="pending_or_incomplete", missing_exports=[path.name for path in required if not path.is_file()])
        return row
    for path in required:
        owned(root, path)
    record, result, grade = [read_json(telemetry / name) for name in ("record.json", "study-result.json", "grade.json")]
    for key in ("case", "condition", "trial", "run_id", "phase"):
        if result.get(key) != row[key]:
            raise ValueError("Result identity does not match its frozen schedule")
    raw = (telemetry / "stdout.jsonl").read_bytes()
    raw_prompt = (telemetry / "prompt.txt").read_bytes()
    if record.get("exports", {}).get("stdout.jsonl") != digest(raw) or record.get("prompt_sha256") != digest(raw_prompt):
        raise ValueError("Source event or prompt hash differs from the recorded original")
    events = []
    malformed = 0
    for line in raw.decode("utf-8", errors="replace").splitlines():
        if line.strip():
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    events.append(event)
                else:
                    malformed += 1
            except json.JSONDecodeError:
                malformed += 1
    ids = session_values(events)
    replacements = list(mappings)
    command = record.get("command", [])
    if isinstance(command, list) and "exec" in command:
        for executable in command[:command.index("exec")]:
            if isinstance(executable, str) and ("/" in executable or "\\" in executable):
                replacements.append((executable, "<CODEX_CLI>"))
    redactor = Redactor(replacements, ids)
    destination = out / "runs" / phase / row["case"] / row["run_id"]
    trace, omitted = observable_trace(events, redactor)
    trace_data = "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in trace).encode("utf-8")
    exports = {"trace.jsonl": write_public(destination / "trace.jsonl", trace_data, redactor)}
    safe_record = redactor.value({key: value for key, value in record.items() if key in RECORD_FIELDS})
    # Hashes named "original" identify untouched local evidence; public bytes differ after redaction.
    exports["record.json"] = write_public(destination / "record.json", encode_json({"original_record": safe_record, "redacted": True}), redactor)
    exports["grade.json"] = write_public(destination / "grade.json", encode_json(redactor.value(grade)), redactor)
    answer_path = telemetry / "answer.txt"
    if answer_path.is_file():
        owned(root, answer_path)
        answer = answer_path.read_bytes()
        if record.get("answer_sha256") != digest(answer):
            raise ValueError("Source final-answer hash differs from the recorded original")
        exports["answer.txt"] = write_public(destination / "answer.txt", redactor.text(answer.decode("utf-8")).encode("utf-8"), redactor)

    after = fixture_manifest(fixture)
    before_files = record.get("fixture_before", {}).get("files", {})
    artifacts = []
    for relative, sha in after["files"].items():
        if before_files.get(relative) == sha:
            continue
        path = owned(root, fixture / relative)
        data = path.read_bytes()
        info = {"path": redactor.text(relative), "status": "changed" if relative in before_files else "new", "original_sha256": sha, "bytes": len(data)}
        try:
            public_data = redactor.text(data.decode("utf-8")).encode("utf-8")
            public_path = "artifacts/" + relative
            info["public_sha256"] = write_public(destination / public_path, public_data, redactor)
            exports[public_path] = info["public_sha256"]
        except UnicodeDecodeError:
            info["export_status"] = "binary_not_exported"
        artifacts.append(info)
    for relative, sha in before_files.items():
        if relative not in after["files"]:
            artifacts.append({"path": redactor.text(relative), "status": "deleted", "original_sha256": sha})

    parsed = parse_events(raw.decode("utf-8", errors="replace"))
    usage = parsed["usage"]
    compared = ("usage", "completion_count", "tool_call_item_count", "tool_output_chars")
    mismatches = [key for key in compared if parsed[key] != record.get(key)]
    if mismatches:
        raise ValueError("Usage/operation reparse differs from original record: " + ", ".join(mismatches))
    total = usage["input_tokens"] + usage["output_tokens"] if usage else None
    row.update(
        export_status="exported", run_status=record.get("run_status"), model=record.get("model"), harness_version=record.get("harness_version"),
        deterministic_success=grade.get("deterministic_success"), checks_passed=grade.get("passed"), checks_total=grade.get("total"), semantic_review_required=grade.get("semantic_review_required"),
        usage=usage, total_tokens=total, usage_status=parsed["usage_status"], completion_count=parsed["completion_count"],
        tool_call_item_count=parsed["tool_call_item_count"], tool_output_chars=parsed["tool_output_chars"], wall_seconds=record.get("wall_seconds"),
        prompt_sha256_original=record.get("prompt_sha256"), skill_sha256_original=record.get("skill_sha256"), fixture_manifest_sha256_original=record.get("fixture_before", {}).get("manifest_sha256"),
        source_hashes={name: digest((telemetry / name).read_bytes()) for name in ("record.json", "study-result.json", "grade.json", "stdout.jsonl", "prompt.txt")},
        public_files=exports, prompt_export="omitted; reconstruct from licensed frozen inputs and common prompt", trace_omitted_counts=omitted, malformed_raw_lines_omitted=malformed, artifacts=artifacts,
        evidence_path=destination.relative_to(out).as_posix(),
    )
    return redactor.value(row)


def export_study(study_root: Path, output_dir: Path, redactions: list[tuple[str, str]] | None = None) -> dict:
    root, out = [Path(os.path.abspath(path)) for path in (study_root, output_dir)]
    _plain_path(root)
    _plain_path(out)
    if not root.is_dir() or out == root or out.is_relative_to(root / "runs"):
        raise ValueError("Choose an existing study root and a separate public export directory")
    marker = out / ".public-evaluation-export"
    if out.exists() and not marker.is_file() and any(out.iterdir()):
        raise ValueError("Refusing to overwrite a directory not owned by this exporter")
    out.mkdir(parents=True, exist_ok=True)
    marker.write_text("Sanitized study evidence; raw source remains elsewhere.\n", encoding="utf-8")
    mappings = [(str(root), "<STUDY_ROOT>"), *(redactions or [])]
    redactor = Redactor(mappings)
    rows, schedules, inputs = [], {}, {}
    for phase, expected in PHASE_COUNTS.items():
        schedule_path = owned(root, root / f"{phase}-schedule.json")
        if not schedule_path.is_file():
            schedules[phase] = {"expected": expected, "status": "schedule_missing"}
            continue
        schedule = read_json(schedule_path)
        jobs = schedule.get("jobs", [])
        if len(jobs) != expected or schedule.get("phase") != phase:
            raise ValueError("Unexpected frozen schedule shape")
        if len({(job["case"], job["run_id"]) for job in jobs}) != expected:
            raise ValueError("Duplicate scheduled run")
        inputs[schedule_path.name] = {"original_sha256": digest(schedule_path.read_bytes()), "public_sha256": write_public(out / "inputs" / schedule_path.name, encode_json(redactor.value(schedule)), redactor)}
        phase_rows = [export_run(root, out, phase, job, mappings) for job in jobs]
        rows.extend(phase_rows)
        schedules[phase] = {"expected": expected, "scheduled": len(jobs), "exported": sum(row["export_status"] == "exported" for row in phase_rows)}
    for name in ("candidate-freeze.json", "study-plan.md"):
        path = owned(root, root / name)
        if path.is_file():
            raw = path.read_bytes()
            public = redactor.text(raw.decode("utf-8")).encode("utf-8")
            inputs[name] = {"original_sha256": digest(raw), "public_sha256": write_public(out / "inputs" / name, public, redactor)}
    summary = {"schema_version": 1, "expected_runs": sum(PHASE_COUNTS.values()), "scheduled_runs": len(rows), "exported_runs": sum(row["export_status"] == "exported" for row in rows), "phases": schedules, "inputs": inputs,
        "complete": len(rows) == 35 and all(row["export_status"] == "exported" for row in rows),
        "total_semantics": "Latest fresh-process cumulative input_tokens + output_tokens; cache and reasoning details are subsets, never added again.",
        "privacy": "Observable completed-item allowlist; no reasoning items, raw stderr, thread/turn/session IDs, or known personal absolute paths. Original hashes are separate from sanitized-file hashes.",
        "limits": ["Exact default model unknown", "Inherited instruction/skill catalog not proved absent", "Concurrent wall times are not speed evidence", "Scored schedules only; calibration infrastructure observations are not quality losses", "Deterministic grades do not replace required semantic review", "No pricing or paid cost inferred"], "runs": rows}
    write_public(out / "analysis.json", encode_json(summary), redactor)
    scalar_keys = ["phase", "case", "condition", "trial", "run_id", "export_status", "run_status", "deterministic_success", "checks_passed", "checks_total", "semantic_review_required", "total_tokens", "input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens", "tool_call_item_count", "tool_output_chars", "wall_seconds", "evidence_path"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=scalar_keys)
    writer.writeheader()
    for row in rows:
        flat = {**row, **(row.get("usage") or {})}
        writer.writerow({key: flat.get(key) for key in scalar_keys})
    write_public(out / "analysis.csv", stream.getvalue().encode("utf-8"), redactor)
    return {key: summary[key] for key in ("expected_runs", "scheduled_runs", "exported_runs", "complete", "phases")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--redact-prefix", action="append", default=[], metavar="PATH=<PLACEHOLDER>", help="Exact known local path prefix; does not inspect the path")
    args = parser.parse_args()
    mappings = []
    for specification in args.redact_prefix:
        original, separator, replacement = specification.rpartition("=")
        if not separator:
            parser.error("Redactions must have PATH=<PLACEHOLDER> form")
        mappings.append((original, replacement))
    print(json.dumps(export_study(args.study_root, args.output_dir, mappings), indent=2))


if __name__ == "__main__":
    main()
