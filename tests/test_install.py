"""Exercise installation against disposable fixtures, never installed user skills."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).absolute().parents[1] / "tools"))
import install


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="exactwork-install-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle with spaces"
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        for name in install.SKILLS:
            source = self.bundle / "skills" / name
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text(f"skill fixture: {name}\n", encoding="utf-8")
        source = self.bundle / "skills" / "exactwork"
        (source / "references" / "nested").mkdir(parents=True)
        (source / "references" / "nested" / "case.md").write_bytes(b"fixture\r\nwith exact bytes\r\n")

    def plan(self, names=None, client="codex"):
        return install.plan_install(self.bundle, self.project, client, names or ["exactwork"])

    def make_link(self, link, target, directory=True):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {error}")

    def test_dry_run_creates_no_project_files(self):
        before = list(self.project.iterdir())
        plans = self.plan()
        self.assertFalse(plans[0].unchanged)
        self.assertEqual(list(self.project.iterdir()), before)
        self.assertFalse((self.project / ".agents").exists())

    def test_cli_preview_defaults_to_core_without_writes(self):
        tools = self.bundle / "tools"
        tools.mkdir()
        script = tools / "install.py"
        shutil.copyfile(Path(install.__file__), script)
        result = subprocess.run(
            [sys.executable, str(script), "--project", str(self.project), "--client", "codex"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WOULD INSTALL", result.stdout)
        self.assertIn("Preview only", result.stdout)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_apply_preserves_nested_files_and_spaces(self):
        plans = self.plan()
        install.apply_plan(plans)
        target = self.project / ".agents" / "skills" / "exactwork"
        self.assertEqual(install.read_tree(target), install.read_tree(self.bundle / "skills" / "exactwork"))

    def test_idempotence_does_not_rewrite_identical_files(self):
        install.apply_plan(self.plan())
        target = self.project / ".agents" / "skills" / "exactwork" / "SKILL.md"
        os.utime(target, ns=(1_600_000_000_000_000_000, 1_600_000_000_000_000_000))
        before = target.stat().st_mtime_ns
        again = self.plan()
        self.assertTrue(again[0].unchanged)
        install.apply_plan(again)
        self.assertEqual(target.stat().st_mtime_ns, before)

    def test_later_collision_prevents_all_selected_changes(self):
        collision = self.project / ".agents" / "skills" / "exactwork-review"
        collision.mkdir(parents=True)
        marker = collision / "SKILL.md"
        marker.write_bytes(b"user content")
        with self.assertRaises(install.InstallError):
            self.plan(["exactwork", "exactwork-review"])
        self.assertFalse((collision.parent / "exactwork").exists())
        self.assertEqual(marker.read_bytes(), b"user content")

    def test_extra_destination_file_is_a_collision(self):
        install.apply_plan(self.plan())
        extra = self.project / ".agents" / "skills" / "exactwork" / "user-note.txt"
        extra.write_bytes(b"retain me")
        with self.assertRaises(install.InstallError):
            self.plan()
        self.assertEqual(extra.read_bytes(), b"retain me")

    def test_missing_source_in_later_selection_writes_nothing(self):
        (self.bundle / "skills" / "exactwork-review" / "SKILL.md").unlink()
        with self.assertRaises(install.InstallError):
            self.plan(["exactwork", "exactwork-review"])
        self.assertEqual(list(self.project.iterdir()), [])

    def test_traversal_and_unknown_names_rejected(self):
        for name in ("../outside", "exactwork/../outside", "/tmp/outside", "unknown"):
            with self.subTest(name=name), self.assertRaises(install.InstallError):
                self.plan([name])
        self.assertEqual(list(self.project.iterdir()), [])

    def test_missing_project_is_not_created(self):
        missing = self.root / "missing project"
        with self.assertRaises(install.InstallError):
            install.plan_install(self.bundle, missing, "codex", ["exactwork"])
        self.assertFalse(missing.exists())

    def test_source_symlink_is_rejected(self):
        source = self.bundle / "skills" / "exactwork" / "shortcut.md"
        outside = self.root / "outside.md"
        outside.write_bytes(b"not part of package")
        self.make_link(source, outside, directory=False)
        with self.assertRaises(install.InstallError):
            self.plan()
        self.assertEqual(list(self.project.iterdir()), [])

    def test_destination_ancestor_symlink_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.make_link(self.project / ".agents", outside)
        with self.assertRaises(install.InstallError):
            self.plan()
        self.assertEqual(list(outside.iterdir()), [])

    def test_source_ancestor_symlink_is_rejected(self):
        alias = self.root / "bundle alias"
        self.make_link(alias, self.bundle)
        with self.assertRaises(install.InstallError):
            install.plan_install(alias, self.project, "codex", ["exactwork"])

    @unittest.skipUnless(os.name == "nt", "Windows junction check")
    def test_windows_destination_junction_is_rejected(self):
        outside = self.root / "junction destination"
        outside.mkdir()
        junction = self.project / ".agents"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.assertRaises(install.InstallError):
            self.plan()
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(os.name == "nt", "Windows junction check")
    def test_windows_source_ancestor_junction_is_rejected(self):
        alias = self.root / "source junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(self.bundle)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.assertRaises(install.InstallError):
            install.plan_install(alias, self.project, "codex", ["exactwork"])
        self.assertEqual(list(self.project.iterdir()), [])

    def test_destination_created_after_plan_aborts_before_other_writes(self):
        plans = self.plan(["exactwork", "exactwork-review"])
        conflict = plans[1].destination
        conflict.mkdir(parents=True)
        (conflict / "keep.txt").write_bytes(b"concurrent content")
        with self.assertRaises(install.InstallError):
            install.apply_plan(plans)
        self.assertFalse(plans[0].destination.exists())

    def test_duplicate_selections_install_once(self):
        plans = self.plan(["exactwork", "exactwork"])
        self.assertEqual(len(plans), 1)
        install.apply_plan(plans)

    def test_each_client_uses_its_documented_project_directory(self):
        for client, relative in install.CLIENT_ROOTS.items():
            with self.subTest(client=client):
                plans = self.plan(client=client)
                self.assertEqual(plans[0].destination, self.project / relative / "exactwork")

    def test_target_parent_file_is_not_overwritten(self):
        blocked = self.project / ".agents"
        blocked.write_bytes(b"not a directory")
        with self.assertRaises(install.InstallError):
            self.plan()
        self.assertEqual(blocked.read_bytes(), b"not a directory")


if __name__ == "__main__":
    unittest.main()
