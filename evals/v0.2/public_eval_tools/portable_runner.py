"""Fresh Codex CLI trial runner for this synthetic evaluation workspace.

No prior sessions, auth files, user configuration, or environment values are read.
Uses the CLI's normal host-managed authentication. Does not select a new model.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import time
from typing import Any


USAGE_FIELDS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens",
)
TOOL_ITEM_TYPES = {"command_execution", "mcp_tool_call", "collab_tool_call", "web_search"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _plain_path(path: Path) -> None:
    """Reject symlink/reparse traversal rather than resolve it into another tree."""
    for component in (path, *path.parents):
        if not component.exists() and not component.is_symlink():
            continue
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Linked paths are outside this runner's scope: {component.name}")


def fixture_manifest(run_dir: Path) -> dict[str, Any]:
    """Hash only files in the explicitly provided synthetic fixture directory."""
    files: dict[str, str] = {}
    for current, directories, names in os.walk(run_dir, followlinks=False):
        for name in (*directories, *names):
            _plain_path(Path(current) / name)
        for name in sorted(names):
            path = Path(current) / name
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError("Fixture must contain only regular files and directories")
            files[path.relative_to(run_dir).as_posix()] = sha256_bytes(path.read_bytes())
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"files": files, "manifest_sha256": sha256_bytes(canonical)}


def parse_events(jsonl: str) -> dict[str, Any]:
    """Read only exported events for the new invocation; never inspect history.

    A completion carries cumulative thread usage. Keep the latest completion,
    never sum it. Missing/all-zero usage is unavailable, not a free run.
    """
    event_counts: Counter[str] = Counter()
    completed_items: dict[tuple[str, str], dict[str, Any]] = {}
    completions: list[dict[str, Any]] = []
    parse_errors = 0
    failure_events = 0
    final_message = None
    for line_number, line in enumerate(jsonl.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            parse_errors += 1
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            parse_errors += 1
            continue
        kind = event["type"]
        event_counts[kind] += 1
        if kind == "turn.completed":
            completions.append(event)
        elif kind in {"turn.failed", "error"}:
            failure_events += 1
        elif kind == "item.completed":
            item = event.get("item")
            if not isinstance(item, dict):
                parse_errors += 1
                continue
            item_type = item.get("type")
            if not isinstance(item_type, str):
                parse_errors += 1
                continue
            identifier = str(item.get("id", f"line-{line_number}"))
            completed_items[(identifier, item_type)] = item
            if item_type == "agent_message" and isinstance(item.get("text"), str):
                final_message = item["text"]

    usage = None
    usage_status = "missing_completion" if not completions else "missing_or_invalid_usage"
    if completions:
        raw = completions[-1].get("usage")
        if isinstance(raw, dict):
            fields = {
                key: value if isinstance(value := raw.get(key), int) and not isinstance(value, bool) and value >= 0 else None
                for key in USAGE_FIELDS
            }
            if fields["input_tokens"] is not None and fields["output_tokens"] is not None:
                if fields["input_tokens"] == 0 and fields["output_tokens"] == 0:
                    usage_status = "all_zero_unavailable"
                else:
                    usage = fields
                    usage_status = "reported"

    item_counts = Counter(kind for _, kind in completed_items)
    tool_counts = {kind: item_counts[kind] for kind in sorted(TOOL_ITEM_TYPES)}
    failed_operations = Counter(
        kind for (_, kind), item in completed_items.items()
        if kind in TOOL_ITEM_TYPES and (item.get("status") in {"failed", "declined"} or (
            kind == "command_execution" and isinstance(item.get("exit_code"), int) and item["exit_code"] != 0
        ))
    )
    commands = [item for (_, kind), item in completed_items.items() if kind == "command_execution"]
    command_outputs = [item["aggregated_output"] for item in commands if isinstance(item.get("aggregated_output"), str)]
    output_chars = sum(len(value) for value in command_outputs)
    missing_outputs = len(commands) - len(command_outputs)
    return {
        "completion_count": len(completions),
        "failure_event_count": failure_events,
        "malformed_event_count": parse_errors,
        "event_counts": dict(sorted(event_counts.items())),
        "usage": usage,
        "usage_status": usage_status,
        "tool_call_items": tool_counts,
        "tool_call_item_count": sum(tool_counts.values()),
        "tool_output_chars": output_chars if missing_outputs == 0 else None,
        "tool_output_chars_observed": output_chars,
        "command_output_items_available": len(command_outputs),
        "command_output_items_missing": missing_outputs,
        "failed_or_declined_operation_items": dict(sorted(failed_operations.items())),
        "file_change_items": item_counts["file_change"],
        "final_message": final_message,
    }


def _stop_own_tree(process: subprocess.Popen) -> dict[str, Any]:
    """Terminate only the process tree this function started."""
    if process.poll() is not None:
        return {"method": "already_exited", "complete": True}
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15,
            check=False,
        )
        complete = result.returncode == 0
        method = "taskkill_owned_pid_tree"
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            complete = True
        except ProcessLookupError:
            complete = True
        method = "kill_owned_process_group"
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
        complete = False  # Parent stopped; child-tree termination was not confirmed.
    return {"method": method, "complete": complete}


def run_trial(
    study_root: str | Path,
    run_dir: str | Path,
    prompt: str,
    timeout: float = 240,
    *,
    skill_text: str | None = None,
    cli_argv: tuple[str, ...] | list[str] = ("codex",),
    windows_sandbox: str | None = None,
    cli_version: str | None = None,
) -> dict[str, Any]:
    """Run one fresh local trial, return metadata, and save new-run evidence.

    Call only for an explicitly prepared synthetic fixture.
    cli_argv is an executable plus optional wrapper arguments; no shell is used.
    Optional skill_text records the exact candidate text hash; no skill = None.
    It does not independently prove that an agent loaded that skill.
    Existing telemetry directory causes refusal, never overwrite. CLI answer and
    logs are saved beside the fixture so they do not change the task's files.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("A nonempty synthetic task prompt is required")
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    root = Path(os.path.abspath(os.fspath(study_root)))
    _plain_path(root)
    if not root.is_dir():
        raise ValueError("study_root must exist")
    if not cli_argv or any(not isinstance(x, str) or not x for x in cli_argv):
        raise ValueError("cli_argv must contain nonempty strings")
    if windows_sandbox not in {None, "elevated", "unelevated"}:
        raise ValueError("Select a supported Windows sandbox implementation")
    directory = Path(os.path.abspath(os.fspath(run_dir)))
    _plain_path(directory)
    if not directory.is_relative_to(root) or directory == root or not directory.is_dir():
        raise ValueError("run_dir must be an existing synthetic fixture beneath study_root")
    telemetry_dir = directory.with_name(directory.name + "-telemetry")
    _plain_path(telemetry_dir)
    answer = telemetry_dir / "answer.txt"
    initial = fixture_manifest(directory)
    telemetry_dir.mkdir()  # Exclusive creation; never replaces a prior trial.
    prompt_bytes = prompt.encode("utf-8")
    (telemetry_dir / "prompt.txt").write_bytes(prompt_bytes)
    command = [
        *cli_argv, "exec", "--ignore-user-config", "--ephemeral",
        *(["-c", f'windows.sandbox="{windows_sandbox}"'] if windows_sandbox else []),
        "--json", "--sandbox", "workspace-write", "--skip-git-repo-check",
        "--cd", str(directory), "--output-last-message", str(answer), "-",
    ]
    record: dict[str, Any] = {
        "schema_version": 1,
        "harness": "codex-cli",
        "harness_version": cli_version,
        "version_evidence": "caller-supplied public CLI version; null if not supplied",
        "model": None,
        "model_selection": "CLI inherited default; exact model not reported by this collector",
        "run_dir": directory.relative_to(root).as_posix(),
        "telemetry_dir": telemetry_dir.relative_to(root).as_posix(),
        "command": command,
        "windows_sandbox": windows_sandbox,
        "sandbox_configuration_reason": "Codex 0.145.0 on Windows downgrades workspace-write to read-only when its Windows sandbox is disabled. A selected Windows sandbox mode is passed per invocation; workspace-write and managed requirements are retained.",
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "skill_sha256": sha256_bytes(skill_text.encode("utf-8")) if skill_text is not None else None,
        "skill_text_present_in_prompt": skill_text in prompt if skill_text is not None else None,
        "fixture_before": initial,
        "timeout_seconds": timeout,
        "timed_out": False,
        "cleanup": None,
        "process_exit_code": None,
        "launch_error_type": None,
        "cost_usd": None,
        "usage_semantics": "Latest cumulative thread usage from a fresh one-turn process. Do not sum cache/reasoning subsets into input/output. All-zero/missing is unavailable.",
        "operation_count_semantics": "Unique completed command_execution, mcp_tool_call, collab_tool_call, and web_search items. File-change items are separate. These are exported activity counts, not every internal raw API/tool call.",
        "tool_output_chars_semantics": "Unicode code points in exported aggregated_output strings of unique completed command_execution items only. Not tokens, bytes, full untruncated output, or all tool types. Total is null when any command lacks an output string; observed partial sum and missing count are retained.",
        "isolation_limit": "Fresh process/fixture and ignored user config do not prove absence of every inherited instruction or global skill.",
    }
    started = time.monotonic()
    stdout_path, stderr_path = telemetry_dir / "stdout.jsonl", telemetry_dir / "stderr.txt"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            options = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, cwd=directory, **options)
            try:
                process.communicate(input=prompt_bytes, timeout=timeout)
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
                try:
                    record["cleanup"] = _stop_own_tree(process)
                except (OSError, subprocess.TimeoutExpired) as error:
                    process.kill()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        pass
                    record["cleanup"] = {"method": "parent_kill_fallback", "complete": False, "error_type": type(error).__name__}
            record["process_exit_code"] = process.poll()
        except OSError as error:
            record["launch_error_type"] = type(error).__name__
    record["wall_seconds"] = round(time.monotonic() - started, 6)
    parsed = parse_events(stdout_path.read_text(encoding="utf-8", errors="replace"))
    final_message = parsed.pop("final_message")
    record.update(parsed)
    if final_message is not None:
        record["final_message_sha256"] = sha256_bytes(final_message.encode("utf-8"))
    else:
        record["final_message_sha256"] = None
    if record["launch_error_type"]:
        record["run_status"] = "launch_error"
    elif record["timed_out"]:
        record["run_status"] = "timeout"
    elif record["process_exit_code"] != 0 or record["failure_event_count"] or not record["completion_count"]:
        record["run_status"] = "failed_or_incomplete"
    elif record["malformed_event_count"]:
        record["run_status"] = "completed_with_event_parse_errors"
    else:
        record["run_status"] = "completed"
    record["exports"] = {
        "stdout.jsonl": sha256_bytes(stdout_path.read_bytes()),
        "stderr.txt": sha256_bytes(stderr_path.read_bytes()),
    }
    if answer.is_file() and not answer.is_symlink():
        _plain_path(answer)
        record["answer_sha256"] = sha256_bytes(answer.read_bytes())
    else:
        record["answer_sha256"] = None
    (telemetry_dir / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Launch one explicitly requested fresh synthetic Codex CLI trial")
    parser.add_argument("--study-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--skill-file", type=Path)
    parser.add_argument("--cli-argv-json", default='["codex"]', help="Explicit executable argv JSON; no shell is used")
    parser.add_argument("--cli-version", help="Version independently checked with public --version")
    parser.add_argument("--windows-sandbox", choices=["elevated", "unelevated"])
    parser.add_argument("--timeout", type=float, default=240)
    args = parser.parse_args()
    cli_argv = json.loads(args.cli_argv_json)
    if not isinstance(cli_argv, list):
        parser.error("--cli-argv-json must be an array")
    for path in [args.prompt_file, *([args.skill_file] if args.skill_file else [])]:
        checked = Path(os.path.abspath(path))
        _plain_path(checked)
        if not checked.is_relative_to(Path(os.path.abspath(args.study_root))):
            parser.error("Prompt and skill must be task-owned files beneath study-root")
    result = run_trial(args.study_root, args.run_dir, args.prompt_file.read_text(encoding="utf-8"), args.timeout,
        skill_text=args.skill_file.read_text(encoding="utf-8") if args.skill_file else None,
        cli_argv=cli_argv, cli_version=args.cli_version, windows_sandbox=args.windows_sandbox)
    print(json.dumps({key: result[key] for key in ("run_dir", "run_status", "usage", "usage_status")}, indent=2))


if __name__ == "__main__":
    main()
