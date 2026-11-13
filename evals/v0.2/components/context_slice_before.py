#!/usr/bin/env python3
"""Select recoverable excerpts from one explicit UTF-8 text file, read-only.

Python 3.10+, standard library only. JSON stdout, including its final newline,
never exceeds --max-bytes. This selects text; it does not diagnose errors or
determine whether the process that wrote the source succeeded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys


MAX_SOURCE_BYTES = 20 * 1024 * 1024
MAX_SOURCE_LINES = 1_000_000
DEFAULT_PATTERN = re.compile(
    r"\b(?:error|fatal|panic|exception|traceback|failed|failure|assertionerror)\b",
    re.IGNORECASE,
)
POLICY = "matched lines earliest/latest alternation, then nearest context"


class SelectionError(ValueError):
    pass


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected an integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("Expected a positive integer")
    return number


def nonnegative_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected an integer") from error
    if number < 0:
        raise argparse.ArgumentTypeError("Expected a nonnegative integer")
    return number


def parse_range(value: str) -> tuple[int, int]:
    if not re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", value):
        raise argparse.ArgumentTypeError("Range must be START:END, inclusive, starting at 1")
    start, end = map(int, value.split(":"))
    if start > end:
        raise argparse.ArgumentTypeError("Range start must not exceed its end")
    return start, end


def edge_order(values: list[int]):
    left, right = 0, len(values) - 1
    while left <= right:
        yield values[left]
        if left != right:
            yield values[right]
        left += 1
        right -= 1


def merge_ranges(ranges: list[tuple[int, int]]) -> list[list[int]]:
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def source_lines(text: str) -> list[str]:
    """Remove only LF and CRLF line terminators; retain other source characters."""
    if not text:
        return []
    chunks = text.split("\n")
    terminated_count = len(chunks) - 1
    if chunks[-1] == "":
        chunks.pop()
    return [chunk[:-1] if i < terminated_count and chunk.endswith("\r") else chunk
            for i, chunk in enumerate(chunks)]


def encode(result: dict) -> bytes:
    return (json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def read_source(path: Path) -> bytes:
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise SelectionError("Source must be a regular file")
        if info.st_size > MAX_SOURCE_BYTES:
            raise SelectionError(f"Source exceeds {MAX_SOURCE_BYTES} bytes; select a smaller explicit file")
        with path.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
    except OSError as error:
        raise SelectionError(f"Cannot read source: {error}") from error
    if len(raw) > MAX_SOURCE_BYTES:
        raise SelectionError("Source grew beyond the file-size limit while reading")
    return raw


def select(path: Path, queries: list[str] | None = None,
           line_range: tuple[int, int] | None = None, context: int = 3,
           max_lines: int = 120, max_bytes: int = 16000) -> dict:
    if queries is not None and line_range is not None:
        raise SelectionError("Queries and a range are mutually exclusive")
    if queries is not None and (not queries or any(not query for query in queries)):
        raise SelectionError("Queries must be nonempty literal strings")
    if not 0 <= context <= 1000:
        raise SelectionError("Context must be between 0 and 1000")
    if not 1 <= max_lines <= 10000:
        raise SelectionError("Max lines must be between 1 and 10000")
    if not 1024 <= max_bytes <= 1024 * 1024:
        raise SelectionError("Max bytes must be between 1024 and 1048576")

    raw = read_source(path)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise SelectionError(f"Source is not valid UTF-8 at byte {error.start}; no replacement decoding") from error
    if "\x00" in text:
        raise SelectionError("Source contains a NUL byte; expected UTF-8 text")
    lines = source_lines(text)
    if len(lines) > MAX_SOURCE_LINES:
        raise SelectionError(f"Source exceeds {MAX_SOURCE_LINES} lines")
    total = len(lines)
    if line_range is not None:
        start, end = line_range
        if start < 1 or end < start or end > total:
            raise SelectionError(f"Range must lie within source lines 1:{total}")
        mode = "range"
        matches = None
        requested = [[start, end]]
        # Range expansion is deliberately sequential, making continuation simple.
        priority = list(range(start, min(end + 1, start + max_lines)))
    else:
        mode = "literal" if queries is not None else "default-pattern"
        matches = [i for i, line in enumerate(lines, 1)
                   if (any(query in line for query in queries) if queries is not None
                       else DEFAULT_PATTERN.search(line) is not None)]
        requested = merge_ranges([(max(1, i - context), min(total, i + context)) for i in matches])
        priority = []
        chosen = set()

        def add(number: int) -> None:
            if 1 <= number <= total and number not in chosen and len(priority) < max_lines:
                chosen.add(number)
                priority.append(number)

        for number in edge_order(matches):
            add(number)
            if len(priority) == max_lines:
                break
        if len(priority) < max_lines:
            for distance in range(1, context + 1):
                for number in edge_order(matches):
                    add(number - distance)
                    add(number + distance)
                    if len(priority) == max_lines:
                        break
                if len(priority) == max_lines:
                    break

    requested_count = sum(end - start + 1 for start, end in requested)
    match_set = set(matches or [])
    source = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
              "bytes": len(raw), "lines": total}

    def result_for(entries: dict[int, str]) -> dict:
        selected = sorted(entries)
        omitted_matches = len(match_set - set(selected)) if matches is not None else None
        truncated_matches = (sum(i in match_set and len(value) < len(lines[i - 1])
                                 for i, value in entries.items()) if matches is not None else None)
        truncations = sum(len(value) < len(lines[i - 1]) for i, value in entries.items())
        excerpts = []
        for i in selected:
            excerpt = {"line": i, "text": entries[i]}
            missing = len(lines[i - 1]) - len(entries[i])
            if missing:
                excerpt["omitted_characters"] = missing
            excerpts.append(excerpt)
        return {
            "format_version": 1, "source": source, "mode": mode,
            "line_terminators": "LF/CRLF excluded; other characters preserved",
            "match_count": len(matches) if matches is not None else None,
            "requested_line_count": requested_count,
            "selected_line_count": len(selected),
            "selected_ranges": merge_ranges([(i, i) for i in selected]),
            "omitted_matched_lines": omitted_matches,
            "truncated_matched_lines": truncated_matches,
            "omitted_requested_lines": requested_count - len(selected),
            "truncated_line_count": truncations,
            "complete_for_matches": (omitted_matches == 0 and truncated_matches == 0) if matches is not None else None,
            "complete_for_selection": len(selected) == requested_count and truncations == 0,
            "source_process_status": "unknown",
            "selection_policy": "sequential range" if line_range is not None else POLICY,
            "excerpts": excerpts,
        }

    if len(encode(result_for({}))) > max_bytes:
        raise SelectionError("Metadata alone exceeds max-bytes; increase the budget or use a shorter source path")

    # Keep line identities before allocating excerpt text. If metadata cannot fit,
    # drop lowest-priority lines; all omitted coverage remains in the counters.
    low, high = 0, len(priority)
    while low < high:
        middle = (low + high + 1) // 2
        candidate = {i: "" for i in priority[:middle]}
        if len(encode(result_for(candidate))) <= max_bytes:
            low = middle
        else:
            high = middle - 1
    priority = priority[:low]
    full = {i: lines[i - 1] for i in priority}
    full_result = result_for(full)
    if len(encode(full_result)) <= max_bytes:
        return full_result

    # Share the available bytes so a single giant line cannot erase every other
    # selected line. Prefix truncation is explicit and measured in characters.
    entries = {i: "" for i in priority}
    for index, number in enumerate(priority):
        current_size = len(encode(result_for(entries)))
        ceiling = current_size + (max_bytes - current_size) // (len(priority) - index)
        value = lines[number - 1]
        entries[number] = value
        if len(encode(result_for(entries))) <= ceiling:
            continue
        # Fully preserved lines omit the truncation field, so handle that
        # discontinuity before binary-searching only truncated prefixes.
        low, high = 0, max(0, len(value) - 1)
        while low < high:
            middle = (low + high + 1) // 2
            entries[number] = value[:middle]
            if len(encode(result_for(entries))) <= ceiling:
                low = middle
            else:
                high = middle - 1
        entries[number] = value[:low]
    result = result_for(entries)
    if len(encode(result)) > max_bytes:
        raise SelectionError("Cannot fit selected excerpts into byte budget")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="One explicitly authorized UTF-8 text file")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--query", action="append", help="Repeat for case-sensitive literal OR matches")
    choice.add_argument("--range", dest="line_range", type=parse_range, help="Inclusive START:END; no extra context")
    parser.add_argument("--context", type=nonnegative_int, default=3)
    parser.add_argument("--max-lines", type=positive_int, default=120)
    parser.add_argument("--max-bytes", type=positive_int, default=16000, help="Entire JSON stdout budget, 1024..1048576")
    args = parser.parse_args(argv)
    try:
        result = select(args.path, args.query, args.line_range, args.context, args.max_lines, args.max_bytes)
    except (SelectionError, OSError) as error:
        print(f"Selection failed: {error}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(encode(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
