"""Validate malformed-package failures and local-reference containment."""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).absolute().parents[1] / "tools"))
import validate


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="exactwork-validate-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "exactwork"
        self.skill.mkdir()
        self.entry = self.skill / "SKILL.md"
        self.write()

    def write(self, body="# Exactwork\n\nDo the task.\n", name="exactwork", description="Complete scoped tasks using evidence."):
        self.entry.write_text(f"---\nname: {name}\ndescription: {description}\nlicense: MIT\n---\n\n{body}", encoding="utf-8")

    def test_valid_skill_with_nested_reference(self):
        reference = self.skill / "references" / "case.md"
        reference.parent.mkdir()
        reference.write_text("# Case\n\n[Entry](../SKILL.md)\n", encoding="utf-8")
        self.write(body="# Entry\n\n[Case](references/case.md)\n")
        self.assertEqual(validate.validate_skill(self.skill), [])

    def test_mismatched_name_fails(self):
        self.write(name="another-name")
        self.assertTrue(any("match its directory" in error for error in validate.validate_skill(self.skill)))

    def test_duplicate_frontmatter_cannot_shadow_fields(self):
        self.entry.write_text("---\nname: exactwork\nname: attacker\ndescription: Task\nlicense: MIT\n---\nBody", encoding="utf-8")
        self.assertTrue(any("Duplicate" in error for error in validate.validate_skill(self.skill)))

    def test_multiline_yaml_is_not_silently_misparsed(self):
        self.entry.write_text("---\nname: exactwork\ndescription: >\n  Line one\nlicense: MIT\n---\nBody", encoding="utf-8")
        self.assertNotEqual(validate.validate_skill(self.skill), [])

    def test_non_string_yaml_description_is_rejected(self):
        for value in ("true", "false", "null", "~", "yes", "off", "123", "1.5", "0x10", ".inf", ".nan"):
            with self.subTest(value=value):
                self.write(description=value)
                self.assertNotEqual(validate.validate_skill(self.skill), [])

    def test_reserved_yaml_scalar_starts_are_rejected_even_after_whitespace(self):
        values = ("- example", "-", "? example", "?", ": example", ":", "@example", "`example",
                  "%example", "[example]", "{name: example}", "}example", "]example", ",example",
                  "&alias", "*alias", "!tag example", "|", ">", "#comment")
        for prefix in ("", "  ", "\t"):
            for value in values:
                with self.subTest(prefix=prefix, value=value):
                    self.write(description=prefix + value)
                    self.assertNotEqual(validate.validate_skill(self.skill), [])

    def test_quoted_reserved_values_are_supported(self):
        for value in ("- example", "@example", "`example", "%example", "[example]", "{name: example}", "true", "123"):
            with self.subTest(value=value):
                self.write(description="  " + json.dumps(value))
                self.assertEqual(validate.validate_skill(self.skill), [])

    def test_legitimate_plain_description_punctuation_is_preserved(self):
        values = ("-prefixed options, no extra scope.", "?questions only when needed.", ":names without whitespace.",
                  ".NET tasks and C# code.", "Use stdlib:json without dependencies.", "Check [inputs], {outputs}, and code.")
        for value in values:
            with self.subTest(value=value):
                self.write(description="  " + value + "  ")
                self.assertEqual(validate.validate_skill(self.skill), [])
                metadata, _ = validate.parse_frontmatter(self.entry.read_text(encoding="utf-8"))
                self.assertEqual(metadata["description"], value)

    def test_plain_mapping_and_comment_syntax_cannot_change_the_description(self):
        for value in ("Task:", "Task:\tname", "Task # ignored text", "Task\t# ignored text"):
            with self.subTest(value=value):
                self.write(description=value)
                self.assertNotEqual(validate.validate_skill(self.skill), [])

    def test_metadata_escaping_and_size_limits(self):
        self.write(description='"Handle a task: preserve its scope."')
        self.assertEqual(validate.validate_skill(self.skill), [])
        self.write(description="x" * 251)
        self.assertTrue(any("250" in error for error in validate.validate_skill(self.skill)))
        self.write(body="é" * 2500)
        self.assertTrue(any("4000-byte" in error for error in validate.validate_skill(self.skill)))

    def test_missing_reference_fails(self):
        self.write(body="[Missing](references/missing.md)")
        self.assertTrue(any("Broken local link" in error for error in validate.validate_skill(self.skill)))

    def test_reference_cannot_escape_standalone_skill(self):
        (self.root / "outside.md").write_text("outside", encoding="utf-8")
        for target in ("../outside.md", "%2e%2e/outside.md", "..\\outside.md"):
            with self.subTest(target=target):
                self.write(body=f"[Outside]({target})")
                self.assertTrue(any("escapes" in error for error in validate.validate_skill(self.skill)))

    def test_absolute_and_file_uri_links_fail(self):
        for target in ("/etc/passwd", "C:/private.txt", "file:///private.txt", "//example.com/file"):
            with self.subTest(target=target):
                self.write(body=f"[Invalid]({target})")
                self.assertNotEqual(validate.validate_skill(self.skill), [])

    def test_web_links_and_local_anchors_do_not_need_network(self):
        self.write(body="[Docs](https://example.com/docs) [Top](#top) [Mail](mailto:help@example.com)")
        self.assertEqual(validate.validate_skill(self.skill), [])

    def test_invalid_utf8_fails_cleanly(self):
        self.entry.write_bytes(b"\xff\xfe")
        self.assertTrue(any("UTF-8" in error for error in validate.validate_skill(self.skill)))

    def test_symlink_reference_is_rejected(self):
        outside = self.root / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            (self.skill / "linked.md").symlink_to(outside)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {error}")
        self.write(body="[Link](linked.md)")
        self.assertTrue(any("symlink" in error or "reparse" in error for error in validate.validate_skill(self.skill)))

    def test_missing_skill_is_reported_by_bundle_validation(self):
        errors = validate.validate_bundle(self.root)
        self.assertTrue(any("Expected skills" in error for error in errors))

    @unittest.skipUnless(os.name == "nt", "Windows junction check")
    def test_windows_junction_resource_is_rejected(self):
        outside = self.root / "outside resources"
        outside.mkdir()
        (outside / "note.md").write_text("outside", encoding="utf-8")
        junction = self.skill / "references"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write(body="[Reference](references/note.md)")
        self.assertTrue(any("reparse" in error for error in validate.validate_skill(self.skill)))

    def test_tilde_fenced_examples_are_not_active_links(self):
        for fence in ("~~~", "~~~~"):
            with self.subTest(fence=fence):
                self.write(body=f"{fence}markdown\\n[Example](does-not-exist.md)\\n{fence}\\n")
                self.assertEqual(validate.validate_skill(self.skill), [])

    def test_fence_requires_matching_marker_and_minimum_width(self):
        self.write(body=(
            "~~~~markdown\\n[Hidden one](inside-one.md)\\n"
            "~~~\\n[Hidden two](inside-two.md)\\n"
            "```\\n[Hidden three](inside-three.md)\\n"
            "~~~~\\n[Live](missing.md)\\n"
        ))
        errors = validate.validate_skill(self.skill)
        self.assertTrue(any("missing.md" in error for error in errors))
        self.assertFalse(any("inside-" in error for error in errors))

    def test_unclosed_fence_is_treated_as_code_to_end_of_file(self):
        self.write(body="~~~markdown\\n[Not active](does-not-exist.md)\\n")
        self.assertEqual(validate.validate_skill(self.skill), [])

    def test_fenced_link_example_is_not_an_active_reference(self):
        self.write(body="```markdown\n[Example](does-not-exist.md)\n```\n")
        self.assertEqual(validate.validate_skill(self.skill), [])


if __name__ == "__main__":
    unittest.main()
