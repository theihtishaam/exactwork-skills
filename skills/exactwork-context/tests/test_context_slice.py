import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "context_slice.py"
spec = importlib.util.spec_from_file_location("context_slice", SCRIPT)
slice_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slice_tool)


class ContextSliceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="exactwork-context-")
        self.root = Path(self.temp.name)
        self.source = self.root / "log with spaces.txt"

    def tearDown(self):
        self.temp.cleanup()

    def put(self, content):
        raw = content.encode("utf-8") if isinstance(content, str) else content
        self.source.write_bytes(raw)
        return raw

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.source), *args],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_literal_selection_preserves_source_and_identity(self):
        raw = self.put("hello\nrequest-42 value=7\nworld\n")
        result = slice_tool.select(self.source, queries=["request-42"], context=0)
        self.assertEqual(result["source"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["source"]["bytes"], len(raw))
        self.assertEqual(result["source"]["lines"], 3)
        self.assertEqual(result["excerpts"], [{"line": 2, "text": "request-42 value=7"}])
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertTrue(result["complete_for_matches"])
        self.assertTrue(result["complete_for_selection"])
        self.assertEqual(result["source_process_status"], "unknown")

    def test_overlapping_context_is_merged_without_duplicates(self):
        self.put("zero\nERROR one\nERROR two\nthree\nfour\n")
        result = slice_tool.select(self.source, context=1)
        self.assertEqual(result["match_count"], 2)
        self.assertEqual(result["selected_ranges"], [[1, 4]])
        self.assertEqual([x["line"] for x in result["excerpts"]], [1, 2, 3, 4])
        self.assertEqual(result["requested_line_count"], 4)

    def test_repeated_queries_are_or_matches_not_duplicate_lines(self):
        self.put("alpha beta\nalpha\nbeta\nALPHA\n")
        result = slice_tool.select(self.source, queries=["alpha", "beta", "alpha"], context=0)
        self.assertEqual(result["match_count"], 3)
        self.assertEqual(result["selected_ranges"], [[1, 3]])

    def test_query_is_literal_not_regex(self):
        self.put("a.*b\naxxb\n")
        result = slice_tool.select(self.source, queries=["a.*b"], context=0)
        self.assertEqual(result["match_count"], 1)
        self.assertEqual(result["excerpts"][0]["line"], 1)

    def test_default_patterns_are_candidates_and_status_stays_unknown(self):
        self.put("INFO ready\nERROR failed\nTraceback (most recent call last):\nfatal: stop\n0 errors\n")
        result = slice_tool.select(self.source, context=0)
        self.assertEqual(result["match_count"], 3)
        self.assertEqual(result["source_process_status"], "unknown")
        self.assertNotIn("success", result)

    def test_empty_source_and_zero_matches_are_distinct_from_job_success(self):
        for content, lines in [("", 0), ("all ordinary text\n", 1)]:
            with self.subTest(content=content):
                self.put(content)
                result = slice_tool.select(self.source)
                self.assertEqual(result["source"]["lines"], lines)
                self.assertEqual(result["match_count"], 0)
                self.assertEqual(result["excerpts"], [])
                self.assertEqual(result["source_process_status"], "unknown")

    def test_unicode_line_terminators_and_missing_final_newline(self):
        self.put("ERROR café 雪\r\nsecond\nlast\r".encode("utf-8"))
        result = slice_tool.select(self.source, line_range=(1, 3))
        self.assertEqual([x["text"] for x in result["excerpts"]], ["ERROR café 雪", "second", "last\r"])
        self.assertIsNone(result["match_count"])
        self.assertIsNone(result["complete_for_matches"])
        self.assertTrue(result["complete_for_selection"])

    def test_unicode_separators_are_not_silently_new_lines(self):
        self.put("ERROR one\u2028two\vthree\n")
        result = slice_tool.select(self.source, context=0)
        self.assertEqual(result["source"]["lines"], 1)
        self.assertEqual(result["excerpts"][0]["text"], "ERROR one\u2028two\vthree")

    def test_line_budget_keeps_earliest_and_latest_matches_and_reports_omissions(self):
        self.put("\n".join(f"ERROR incident {i}" for i in range(1, 11)))
        result = slice_tool.select(self.source, context=0, max_lines=3)
        self.assertEqual([x["line"] for x in result["excerpts"]], [1, 2, 10])
        self.assertEqual(result["omitted_matched_lines"], 7)
        self.assertEqual(result["omitted_requested_lines"], 7)
        self.assertFalse(result["complete_for_matches"])
        self.assertFalse(result["complete_for_selection"])

    def test_matches_receive_priority_over_context(self):
        self.put("before\nERROR one\nafter\ncontext\nFATAL two\nend\n")
        result = slice_tool.select(self.source, context=2, max_lines=2)
        self.assertEqual([x["line"] for x in result["excerpts"]], [2, 5])
        self.assertTrue(result["complete_for_matches"])
        self.assertFalse(result["complete_for_selection"])
        self.assertEqual(result["omitted_requested_lines"], 4)

    def test_explicit_range_is_inclusive_and_sequential(self):
        self.put("\n".join(str(i) for i in range(1, 8)))
        result = slice_tool.select(self.source, line_range=(3, 6), context=999, max_lines=2)
        self.assertEqual([x["line"] for x in result["excerpts"]], [3, 4])
        self.assertEqual(result["requested_line_count"], 4)
        self.assertEqual(result["omitted_requested_lines"], 2)
        self.assertFalse(result["complete_for_selection"])

    def test_long_unicode_line_is_explicitly_truncated_within_entire_output_budget(self):
        text = "ERROR " + "雪😀" * 20000
        self.put(text)
        result = slice_tool.select(self.source, context=0, max_bytes=1200)
        self.assertLessEqual(len(slice_tool.encode(result)), 1200)
        item = result["excerpts"][0]
        self.assertTrue(text.startswith(item["text"]))
        self.assertEqual(len(item["text"]) + item["omitted_characters"], len(text))
        self.assertEqual(result["truncated_matched_lines"], 1)
        self.assertFalse(result["complete_for_matches"])
        self.assertFalse(result["complete_for_selection"])

    def test_giant_first_line_cannot_remove_later_matched_identity(self):
        self.put("ERROR " + "x" * 50000 + "\nERROR distinct final cause\n")
        result = slice_tool.select(self.source, context=0, max_bytes=1300)
        self.assertEqual([x["line"] for x in result["excerpts"]], [1, 2])
        self.assertEqual(result["excerpts"][1]["text"], "ERROR distinct final cause")
        self.assertLessEqual(len(slice_tool.encode(result)), 1300)

    def test_low_byte_budget_preserves_truthful_counts(self):
        self.put("\n".join("ERROR " + str(i) for i in range(100)))
        result = slice_tool.select(self.source, context=0, max_bytes=1024)
        self.assertLessEqual(len(slice_tool.encode(result)), 1024)
        self.assertLess(result["selected_line_count"], 100)
        self.assertEqual(result["selected_line_count"] + result["omitted_matched_lines"], 100)
        self.assertFalse(result["complete_for_matches"])

    def test_invalid_utf8_and_nul_fail_without_excerpt_output(self):
        for content in [b"ERROR before\n\xff", b"ERROR\x00after"]:
            with self.subTest(content=content):
                self.put(content)
                run = self.cli()
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, b"")
                self.assertTrue(run.stderr)

    def test_oversized_source_refused_without_reading_full_payload(self):
        with self.source.open("wb") as stream:
            stream.truncate(slice_tool.MAX_SOURCE_BYTES + 1)
        with self.assertRaisesRegex(slice_tool.SelectionError, "exceeds"):
            slice_tool.select(self.source)

    def test_line_limit_rejected_before_materializing_lines(self):
        for content in [b"one\ntwo\nthree\n", b"one\ntwo\nthree"]:
            with self.subTest(content=content):
                self.put(content)
                with mock.patch.object(slice_tool, "MAX_SOURCE_LINES", 2), \
                        mock.patch.object(slice_tool, "source_lines") as split_lines:
                    with self.assertRaisesRegex(slice_tool.SelectionError, "exceeds 2 lines"):
                        slice_tool.select(self.source)
                    split_lines.assert_not_called()

    def test_line_limit_boundary_respects_final_line_terminator(self):
        for content, expected in [(b"one\ntwo\n", 2), (b"one\ntwo", 2), (b"\n\n", 2), (b"", 0)]:
            with self.subTest(content=content):
                self.put(content)
                with mock.patch.object(slice_tool, "MAX_SOURCE_LINES", 2):
                    result = slice_tool.select(self.source)
                self.assertEqual(result["source"]["lines"], expected)

    def test_many_truncated_lines_do_not_reencode_whole_result_per_probe(self):
        self.put(("ERROR " + "x" * 1993 + "\n") * 200)
        full_result_encodings = 0
        original_encode = slice_tool.encode

        def observed_encode(value):
            nonlocal full_result_encodings
            if "source" in value:
                full_result_encodings += 1
            return original_encode(value)

        with mock.patch.object(slice_tool, "encode", side_effect=observed_encode):
            result = slice_tool.select(self.source, context=0, max_lines=200, max_bytes=100000)
        self.assertLessEqual(full_result_encodings, 16)
        self.assertEqual(result["selected_line_count"], 200)
        self.assertEqual(result["truncated_line_count"], 200)
        self.assertLessEqual(len(original_encode(result)), 100000)

    def test_incremental_budget_handles_escaping_and_counter_boundaries(self):
        for count in [9, 10, 11, 99, 100, 101]:
            content = ["ERROR " + ('雪😀\t"\\' * (300 if i % 3 == 0 else 1))
                       for i in range(count)]
            self.put("\n".join(content))
            for budget in [1024, 2400, 16000]:
                for use_range in [False, True]:
                    with self.subTest(count=count, budget=budget, use_range=use_range):
                        result = slice_tool.select(self.source, context=0, max_lines=count,
                                                   max_bytes=budget,
                                                   line_range=(1, count) if use_range else None)
                        self.assertLessEqual(len(slice_tool.encode(result)), budget)
                        truncated = 0
                        for item in result["excerpts"]:
                            source = content[item["line"] - 1]
                            self.assertTrue(source.startswith(item["text"]))
                            missing = len(source) - len(item["text"])
                            self.assertEqual(item.get("omitted_characters", 0), missing)
                            truncated += bool(missing)
                        self.assertEqual(result["truncated_line_count"], truncated)
                        self.assertEqual(result["omitted_requested_lines"],
                                         count - result["selected_line_count"])
                        complete = result["selected_line_count"] == count and truncated == 0
                        self.assertEqual(result["complete_for_selection"], complete)
                        if not use_range:
                            self.assertEqual(result["truncated_matched_lines"], truncated)
                            self.assertEqual(result["complete_for_matches"], complete)

    def test_directory_and_missing_file_rejected(self):
        for path in [self.root, self.root / "missing.txt"]:
            with self.subTest(path=path), self.assertRaises(slice_tool.SelectionError):
                slice_tool.select(path)

    def test_invalid_cli_arguments_return_error_not_success(self):
        self.put("ERROR one\nsecond\n")
        bad_args = [
            ("--query", ""), ("--query", "ERROR", "--range", "1:2"),
            ("--range", "0:2"), ("--range", "2:1"), ("--range", "1:3"),
            ("--range", "1"), ("--context", "-1"), ("--context", "1001"),
            ("--max-lines", "0"), ("--max-lines", "10001"),
            ("--max-bytes", "1023"), ("--max-bytes", "1048577"),
        ]
        for args in bad_args:
            with self.subTest(args=args):
                run = self.cli(*args)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, b"")

    def test_cli_json_roundtrip_and_byte_budget(self):
        self.put("ERROR café\n")
        run = self.cli("--max-bytes", "1024", "--context", "0")
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["excerpts"][0]["text"], "ERROR café")
        self.assertLessEqual(len(run.stdout), 1024)

    def test_seeded_invariants_for_budgets_coverage_and_source_fidelity(self):
        rng = random.Random(41)
        for case in range(30):
            count = rng.randint(1, 120)
            content = [("ERROR " if rng.random() < .35 else "INFO ") +
                       "雪" * rng.randint(0, 100) + f" item {i}" for i in range(count)]
            raw = self.put("\n".join(content))
            cap = rng.randint(1024, 4000)
            line_cap = rng.randint(1, 25)
            with self.subTest(case=case):
                result = slice_tool.select(self.source, max_bytes=cap, max_lines=line_cap,
                                           context=rng.randint(0, 4))
                self.assertLessEqual(len(slice_tool.encode(result)), cap)
                self.assertLessEqual(result["selected_line_count"], line_cap)
                actual = [item["line"] for item in result["excerpts"]]
                self.assertEqual(actual, sorted(set(actual)))
                for item in result["excerpts"]:
                    source = content[item["line"] - 1]
                    self.assertTrue(source.startswith(item["text"]))
                    self.assertEqual(len(source) - len(item["text"]), item.get("omitted_characters", 0))
                matches = {i for i, line in enumerate(content, 1) if line.startswith("ERROR ")}
                self.assertEqual(result["omitted_matched_lines"], len(matches - set(actual)))
                self.assertEqual(self.source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
