#!/usr/bin/env python3
"""Copy selected skills into an explicit project. Preview is the default.

Python 3.10+, standard library only. No network, config, or credential access.
Existing skills are accepted only when every file and directory is identical.
This installer does not overwrite, delete, or automatically update anything.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import stat
import sys


SKILLS = ("exactwork", "exactwork-research", "exactwork-review", "exactwork-handoff", "exactwork-context", "exactwork-learn")
CLIENT_ROOTS = {
    "codex": ".agents/skills",
    "shared": ".agents/skills",
    "claude": ".claude/skills",
    "opencode": ".opencode/skills",
    "harness": ".dsh/skills",
    "gemini": ".gemini/skills",
    "copilot": ".github/skills",
    "cursor": ".cursor/skills",
    "cline": ".cline/skills",
}


class InstallError(Exception):
    """A refused input, collision, or unsafe path; nothing should be replaced."""


def absolute(path: Path) -> Path:
    # Do not resolve links before checking them: that would conceal a junction.
    return Path(os.path.abspath(os.fspath(path)))


def path_stat(path: Path):
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def check_path(path: Path) -> None:
    """Reject links/reparse points at every existing component, including ancestors."""
    path = absolute(path)
    for component in reversed((path, *path.parents)):
        info = path_stat(component)
        if info is None:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise InstallError(f"Link or reparse point is not allowed: {component}")
        if component != path and not stat.S_ISDIR(info.st_mode):
            raise InstallError(f"Parent is not a directory: {component}")


def read_tree(
    root: Path,
    expected_files: set[str] | None = None,
    expected_directories: set[str] | None = None,
) -> tuple[dict[str, bytes], tuple[str, ...]]:
    check_path(root)
    info = path_stat(root)
    if info is None or not stat.S_ISDIR(info.st_mode):
        raise InstallError(f"Expected a directory: {root}")
    files: dict[str, bytes] = {}
    directories: list[str] = []

    def visit(folder: Path) -> None:
        for child in sorted(folder.iterdir()):
            check_path(child)
            info = child.lstat()
            relative = child.relative_to(root).as_posix()
            if stat.S_ISDIR(info.st_mode):
                if expected_directories is not None and relative not in expected_directories:
                    raise InstallError(f"Unexpected existing directory; refusing to merge: {child}")
                directories.append(relative)
                visit(child)
            elif stat.S_ISREG(info.st_mode):
                if expected_files is not None and relative not in expected_files:
                    raise InstallError(f"Unexpected existing file; refusing to merge: {child}")
                files[relative] = child.read_bytes()
            else:
                raise InstallError(f"Only regular files and directories are allowed: {child}")

    visit(root)
    return files, tuple(sorted(directories))


@dataclass(frozen=True)
class SkillPlan:
    name: str
    destination: Path
    files: dict[str, bytes]
    directories: tuple[str, ...]
    unchanged: bool


def plan_install(bundle: Path, project: Path, client: str, names: list[str]) -> list[SkillPlan]:
    """Preflight every selected skill before returning any writable plan."""
    bundle, project = absolute(bundle), absolute(project)
    if client not in CLIENT_ROOTS:
        raise InstallError(f"Unknown client: {client}")
    if not names:
        raise InstallError("Select at least one skill.")
    names = list(dict.fromkeys(names))
    for name in names:
        if name not in SKILLS:
            raise InstallError(f"Unknown skill: {name}")
    check_path(bundle)
    check_path(project)
    info = path_stat(project)
    if info is None or not stat.S_ISDIR(info.st_mode):
        raise InstallError(f"--project must name an existing directory: {project}")
    target = project / CLIENT_ROOTS[client]
    check_path(target)
    info = path_stat(target)
    if info is not None and not stat.S_ISDIR(info.st_mode):
        raise InstallError(f"Skill root is not a directory: {target}")

    plans = []
    for name in names:
        source = bundle / "skills" / name
        files, directories = read_tree(source)
        if "SKILL.md" not in files:
            raise InstallError(f"Missing SKILL.md: {source}")
        destination = target / name
        check_path(destination)
        unchanged = path_stat(destination) is not None
        if unchanged:
            old_files, old_directories = read_tree(destination, set(files), set(directories))
            if old_files != files or old_directories != directories:
                raise InstallError(
                    f"Existing skill differs; no files will be overwritten: {destination}. "
                    "Review and relocate the existing folder yourself before installing."
                )
        plans.append(SkillPlan(name, destination, files, directories, unchanged))
    return plans


def make_parents(path: Path) -> None:
    check_path(path)
    missing = []
    cursor = path
    while path_stat(cursor) is None:
        missing.append(cursor)
        cursor = cursor.parent
    if not cursor.is_dir():
        raise InstallError(f"Expected a directory: {cursor}")
    for directory in reversed(missing):
        check_path(directory)
        directory.mkdir()  # exclusive creation; a concurrent change aborts


def apply_plan(plans: list[SkillPlan]) -> None:
    """Apply a fully preflighted plan. I/O failure may leave partial new files.

    No rollback deletes are attempted. Do not change the destination concurrently.
    Exclusive file creation prevents replacing an existing final-path file.
    """
    # Recheck all destinations before the first mutation.
    for plan in plans:
        check_path(plan.destination)
        if plan.unchanged:
            if read_tree(plan.destination, set(plan.files), set(plan.directories)) != (plan.files, plan.directories):
                raise InstallError(f"Destination changed after preflight: {plan.destination}")
        elif path_stat(plan.destination) is not None:
            raise InstallError(f"Destination appeared after preflight: {plan.destination}")
    for plan in plans:
        if plan.unchanged:
            continue
        make_parents(plan.destination.parent)
        check_path(plan.destination)
        plan.destination.mkdir()
        for relative in plan.directories:
            directory = plan.destination / relative
            check_path(directory)
            directory.mkdir()
        for relative, content in plan.files.items():
            destination = plan.destination / relative
            check_path(destination)
            with destination.open("xb") as stream:
                stream.write(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path, help="Explicit existing project directory")
    parser.add_argument("--client", required=True, choices=CLIENT_ROOTS)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--skill", action="append", choices=SKILLS, help="Repeat to select several; default: exactwork")
    selection.add_argument("--all", action="store_true", help="Install all six skills")
    parser.add_argument("--apply", action="store_true", help="Copy files; without this flag, preview only")
    args = parser.parse_args(argv)
    bundle = absolute(Path(__file__)).parent.parent
    names = list(SKILLS) if args.all else (args.skill or ["exactwork"])
    try:
        plans = plan_install(bundle, args.project, args.client, names)
        if args.apply:
            apply_plan(plans)
        for plan in plans:
            status = "UNCHANGED" if plan.unchanged else ("INSTALLED" if args.apply else "WOULD INSTALL")
            print(f"{status}: {plan.destination} ({len(plan.files)} files)")
        if not args.apply:
            print("Preview only. No files changed. Add --apply to install.")
        return 0
    except InstallError as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"I/O error: {error}. No existing files were overwritten; new files may be partial.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
