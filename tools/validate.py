#!/usr/bin/env python3
"""Validate this package's deliberately small Agent Skills subset, offline.

This is a structural check, not proof of model quality or native host loading.
Frontmatter supports exactly name, description, and license as one-line strings.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit


EXPECTED = {"exactwork", "exactwork-research", "exactwork-review", "exactwork-handoff", "exactwork-context", "exactwork-learn"}
MAX_BYTES = 4000
MAX_DESCRIPTION = 250
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[\"'][^\n]*[\"'])?\s*\)")


def plain_path(path: Path) -> bool:
    path = Path(os.path.abspath(os.fspath(path)))
    for component in (path, *path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            return False
    return True


def scalar(value: str) -> str:
    # YAML separates a scalar from its surrounding horizontal whitespace.
    # Normalize before checking indicators so extra spaces cannot hide them.
    value = value.strip(" \t")
    if value.startswith('"'):
        parsed = json.loads(value)
        if not isinstance(parsed, str):
            raise ValueError("Expected a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'") or "'" in value[1:-1].replace("''", ""):
            raise ValueError("Invalid single-quoted string")
        return value[1:-1].replace("''", "'")
    if (
        not value
        or value[0] in "[]{},|>!&*#%@`"
        or re.match(r"[-?:](?:\s|$)", value)
        or re.search(r":(?:\s|$)|\s#", value)
    ):
        raise ValueError("Use a plain one-line string or quote the value")
    if value.lower() in {"null", "true", "false", "~", "yes", "no", "on", "off"}:
        raise ValueError("Expected a string, not a YAML keyword")
    if (
        re.fullmatch(r"[-+]?(?:\d[\d_]*(?:\.[\d_]*)?|\.[\d_]+)(?:[eE][-+]?\d+)?", value)
        or re.fullmatch(r"[-+]?0(?:[xX][0-9a-fA-F_]+|[oO][0-7_]+|[bB][01_]+)", value)
        or value.lower() in {".inf", "+.inf", "-.inf", ".nan"}
    ):
        raise ValueError("Quote numeric-looking strings")
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("File must begin with YAML frontmatter (---), without a BOM")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("Missing closing frontmatter delimiter") from None
    values = {}
    for line in lines[1:end]:
        match = re.fullmatch(r"([a-z][a-z-]*): (.+)", line)
        if not match:
            raise ValueError("Frontmatter must contain one key: value per line")
        key, value = match.groups()
        if key in values:
            raise ValueError(f"Duplicate frontmatter field: {key}")
        values[key] = scalar(value)
    if set(values) != {"name", "description", "license"}:
        raise ValueError("Frontmatter requires exactly name, description, and license")
    return values, "\n".join(lines[end + 1:])


def strip_fenced_examples(source: str) -> str:
    """Exclude Markdown code fences without hiding links in surrounding prose."""
    kept, character, minimum = [], None, 0
    for line in source.splitlines(keepends=True):
        if character is None:
            opener = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if opener:
                character, minimum = opener.group(1)[0], len(opener.group(1))
            else:
                kept.append(line)
        else:
            closer = re.fullmatch(r" {0,3}([`~]{3,})[ \\t]*(?:\\r?\\n)?", line)
            if closer and len(closer.group(1)) >= minimum and set(closer.group(1)) == {character}:
                character, minimum = None, 0
    return "".join(kept)


def validate_links(text: str, document: Path, root: Path) -> list[str]:
    errors = []
    # Inline code and fenced examples are not documentation links.
    prose = strip_fenced_examples(text)
    prose = re.sub(r"`[^`\n]+`", "", prose)
    for match in LINK.finditer(prose):
        raw = match.group(1).strip("<>")
        parsed = urlsplit(raw)
        if parsed.scheme in {"http", "https", "mailto"}:
            continue
        if parsed.scheme or parsed.netloc:
            errors.append(f"Unsupported link target: {raw}")
            continue
        path = unquote(parsed.path).replace("\\", "/")
        if not path:  # an anchor in this document
            continue
        if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
            errors.append(f"Link must be relative: {raw}")
            continue
        target = Path(os.path.abspath(document.parent / path))
        if not target.is_relative_to(root):
            errors.append(f"Link escapes its standalone skill: {raw}")
        elif not plain_path(target):
            errors.append(f"Link crosses a symlink or reparse point: {raw}")
        elif not target.exists():
            errors.append(f"Broken local link: {raw}")
    return errors


def validate_skill(directory: Path) -> list[str]:
    directory = Path(os.path.abspath(os.fspath(directory)))
    errors = []
    entry = directory / "SKILL.md"
    if not plain_path(entry):
        return ["Skill path crosses a symlink or reparse point"]
    try:
        raw = entry.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as error:
        return [f"Cannot read UTF-8 SKILL.md: {error}"]
    if len(raw) > MAX_BYTES:
        errors.append(f"SKILL.md exceeds the {MAX_BYTES}-byte package budget ({len(raw)} bytes)")
    if "\x00" in text:
        errors.append("SKILL.md contains a null byte")
    try:
        metadata, body = parse_frontmatter(text)
        name = metadata["name"]
        if len(name) > 64 or not NAME.fullmatch(name) or name != directory.name:
            errors.append("Skill name must match its directory and use lowercase hyphenated words (max 64 characters)")
        description = metadata["description"]
        if not description.strip() or len(description) > MAX_DESCRIPTION or "\n" in description:
            errors.append(f"Description must contain 1-{MAX_DESCRIPTION} characters on one line")
        if metadata["license"] != "MIT":
            errors.append("This package's skills must declare license: MIT")
        if not body.strip():
            errors.append("Skill body is empty")
    except (ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))

    # Check all bundled Markdown resources, not only the entry point.
    for current, dirs, files in os.walk(directory, followlinks=False, onerror=lambda error: errors.append(str(error))):
        for child in (*dirs, *files):
            path = Path(current) / child
            if not plain_path(path):
                errors.append(f"Bundled link/reparse point is not allowed: {path.relative_to(directory)}")
        dirs[:] = [name for name in dirs if plain_path(Path(current) / name)]
        for name in files:
            path = Path(current) / name
            if path.suffix.lower() == ".md" and plain_path(path):
                try:
                    if not stat.S_ISREG(path.lstat().st_mode):
                        errors.append(f"Expected a regular Markdown file: {path.relative_to(directory)}")
                        continue
                    resource = path.read_text(encoding="utf-8")
                    errors.extend(f"{path.relative_to(directory)}: {error}" for error in validate_links(resource, path, directory))
                except (OSError, UnicodeError) as error:
                    errors.append(f"Cannot read {path.relative_to(directory)}: {error}")
    return errors


def validate_bundle(root: Path) -> list[str]:
    root = Path(os.path.abspath(os.fspath(root)))
    if not plain_path(root) or not root.is_dir():
        return [f"Expected a regular skills directory: {root}"]
    try:
        children = list(root.iterdir())
    except OSError as error:
        return [f"Cannot list skills directory: {error}"]
    names = {child.name for child in children if plain_path(child) and child.is_dir()}
    errors = []
    if names != EXPECTED:
        errors.append(f"Expected skills {sorted(EXPECTED)}; found {sorted(names)}")
    for child in sorted(children):
        if not plain_path(child) or child.is_dir():
            errors.extend(f"{child.name}: {error}" for error in validate_skill(child))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=Path(__file__).absolute().parent.parent / "skills")
    args = parser.parse_args(argv)
    errors = validate_bundle(args.skills_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated six skill folders: metadata, size budgets, and local Markdown links.")
    print("Structural validation does not establish model performance or host activation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
