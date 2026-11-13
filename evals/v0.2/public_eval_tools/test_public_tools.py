import json
from pathlib import Path
import tempfile
import unittest

from export_study import Redactor, observable_trace, session_values, export_study, digest
from portable_runner import parse_events


class PublicEvidenceTests(unittest.TestCase):
    def test_redaction_handles_slashes_nested_json_and_ids(self):
        redactor = Redactor([("C:/Users/example/study", "<STUDY_ROOT>"), ("C:/Users/example", "<LOCAL_HOME>")], {"synthetic-thread"})
        value = redactor.value({"thread_id": "synthetic-thread", "command": r'C:\\Users\\example\\study\\fixture synthetic-thread', "path": "c:/Users/example/tool"})
        self.assertNotIn("thread_id", value)
        self.assertEqual(value["command"], r'<STUDY_ROOT>\\fixture <SESSION_ID>')
        self.assertEqual(value["path"], "<LOCAL_HOME>/tool")
        redactor.assert_public(json.dumps(value))

    def test_unmapped_personal_path_fails_closed(self):
        for value in [r"C:\Users\unknown\file", "/home/unknown/file"]:
            with self.assertRaises(ValueError):
                Redactor([]).assert_public(value)

    def test_trace_omits_reasoning_and_removes_session_metadata(self):
        events = [
            {"type": "thread.started", "thread_id": "fake-session"},
            {"type": "item.completed", "item": {"type": "reasoning", "text": "PRIVATE INTERNAL CONTENT"}},
            {"type": "item.completed", "item": {"type": "agent_message", "channel": "analysis", "text": "ALSO INTERNAL"}},
            {"type": "item.completed", "item": {"id": "cmdid", "type": "command_execution", "command": "echo synthetic", "aggregated_output": "safe fake-session", "exit_code": 0}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Done."}},
        ]
        trace, omitted = observable_trace(events, Redactor([], session_values(events)))
        text = json.dumps(trace)
        for prohibited in ["PRIVATE INTERNAL CONTENT", "ALSO INTERNAL", "fake-session", "cmdid", "thread_id"]:
            self.assertNotIn(prohibited, text)
        self.assertIn("safe <SESSION_ID>", text)
        self.assertEqual(len(trace), 2)
        self.assertEqual(omitted["reasoning"], 1)

    def test_cumulative_totals_do_not_add_subsets_or_completions(self):
        values = [
            {"type": "turn.completed", "usage": {"input_tokens": 40, "output_tokens": 5}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 20, "reasoning_output_tokens": 10}},
        ]
        parsed = parse_events("\n".join(map(json.dumps, values)))
        self.assertEqual(parsed["usage"]["input_tokens"] + parsed["usage"]["output_tokens"], 120)

    def test_pending_rows_then_complete_export_are_repeatable(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            root = Path(temporary) / "study"
            root.mkdir()
            for phase, count in [("dev", 12), ("holdout", 18), ("ponytail", 5)]:
                jobs = [{"case": "case", "condition": "none", "trial": 1, "run_id": f"r{i}"} for i in range(count)]
                (root / f"{phase}-schedule.json").write_text(json.dumps({"phase": phase, "jobs": jobs}), encoding="utf-8")
            out = Path(temporary) / "export"
            first = export_study(root, out)
            self.assertEqual(first["exported_runs"], 0)
            self.assertFalse(first["complete"])
            for phase, count in [("dev", 12), ("holdout", 18), ("ponytail", 5)]:
                for i in range(count):
                    fixture = root / "runs" / phase / "case" / f"r{i}"
                    fixture.mkdir(parents=True)
                    (fixture / "answer.json").write_text('{"result": "synthetic"}', encoding="utf-8")
                    telemetry = fixture.with_name(fixture.name + "-telemetry")
                    telemetry.mkdir()
                    usage = {"input_tokens": 100, "cached_input_tokens": 80, "cache_write_input_tokens": 0, "output_tokens": 20, "reasoning_output_tokens": 10}
                    events = json.dumps({"type": "turn.completed", "usage": usage}) + "\n"
                    prompt = "synthetic private prompt not for redistribution"
                    record = {"exports": {"stdout.jsonl": digest(events.encode())}, "prompt_sha256": digest(prompt.encode()), "usage": usage, "completion_count": 1, "tool_call_item_count": 0, "tool_output_chars": 0, "fixture_before": {"files": {}}, "run_status": "completed"}
                    result = {"phase": phase, "case": "case", "condition": "none", "trial": 1, "run_id": f"r{i}"}
                    for name, value in [("record.json", record), ("study-result.json", result), ("grade.json", {"deterministic_success": True, "passed": 1, "total": 1})]:
                        (telemetry / name).write_text(json.dumps(value), encoding="utf-8")
                    (telemetry / "stdout.jsonl").write_bytes(events.encode("utf-8"))
                    (telemetry / "prompt.txt").write_text(prompt, encoding="utf-8")
            second = export_study(root, out)
            self.assertEqual(second["exported_runs"], 35)
            self.assertTrue(second["complete"])
            analysis = (out / "analysis.json").read_bytes()
            export_study(root, out)
            self.assertEqual(analysis, (out / "analysis.json").read_bytes())
            self.assertFalse(list(out.rglob("prompt.txt")))
            report = json.loads(analysis)
            self.assertTrue(all(row["total_tokens"] == 120 for row in report["runs"]))


if __name__ == "__main__":
    unittest.main()
