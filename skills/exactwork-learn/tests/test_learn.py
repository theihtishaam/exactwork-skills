"""Synthetic record/transaction tests; these are not model-performance results."""
import copy
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "learn.py"
spec = importlib.util.spec_from_file_location("learn", SCRIPT)
learn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learn)
PROPOSAL = ".exactwork/proposal.json"
EVIDENCE = ".exactwork/evidence.json"


def fixture(root, existing=True):
    """Generate a complete, explicitly synthetic example in an explicit temporary root."""
    area = root / ".exactwork"
    area.mkdir(parents=True)
    def save(name, content):
        data = content if isinstance(content, bytes) else learn.encoded(content)
        path = area / name
        path.write_bytes(data)
        return {"path": ".exactwork/" + name, "sha256": learn.digest(data)}
    base = b"# Synthetic original\r\nKeep this exact newline.\r\n" if existing else None
    if existing:
        save("procedure.md", base)
    candidate = save("candidate.md", b"# SYNTHETIC candidate\nCheck the explicit task requirement.\n")
    source = save("source.txt", b"SYNTHETIC correction. No model call or measured performance.\n")
    grader = save("grader.txt", b"SYNTHETIC rubric: correctness and scope; labels are invented test data.\n")
    policy = save("policy.json", {"schema_version": 1, "min_trials": 2, "min_heldout_tasks": 2, "allow_efficiency": True})
    tasks = [{"id": split + str(index), "split": split, "trials": 2} for split in ("repair", "transfer", "regression", "heldout") for index in range(2 if split == "heldout" else 1)]
    manifest = save("manifest.json", {"schema_version": 1, "setup_id": "SYNTHETIC-setup-v1", "grader": grader, "tasks": tasks})
    proposal = {"schema_version": 1, "id": "synthetic-example", "candidate": candidate, "base_sha256": learn.digest(base) if base else None,
                "hypothesis": "Synthetic repaired rule", "scope": "Synthetic fixture only", "source": source, "policy": policy, "manifest": manifest}
    proposal_ref = save("proposal.json", proposal)
    cases = []
    for task in tasks:
        for trial in (1, 2):
            case = {"task_id": task["id"], "trial": trial}
            for arm in ("baseline", "candidate"):
                artifact = save(task["id"] + "-" + str(trial) + "-" + arm + ".txt", b"SYNTHETIC artifact; invented labels, not an agent result.\n")
                case[arm] = {"setup_id": "SYNTHETIC-setup-v1", "correct": arm == "candidate" or task["split"] != "repair",
                             "scope": True, "origin": "manual", "artifact": artifact, "usage": None, "duration": None}
            cases.append(case)
    evidence = {"schema_version": 1, "proposal_sha256": proposal_ref["sha256"], "grader_sha256": grader["sha256"], "cases": cases}
    save("evidence.json", evidence)
    return proposal, evidence, base


class LearnTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name).resolve()
        self.proposal, self.evidence, self.base = fixture(self.root)

    def tearDown(self):
        self.directory.cleanup()

    def save(self, relative, value):
        (self.root / relative).write_bytes(learn.encoded(value))

    def evidence_save(self):
        self.save(EVIDENCE, self.evidence)

    def proposal_save(self):
        self.save(PROPOSAL, self.proposal)
        self.evidence["proposal_sha256"] = learn.digest((self.root / PROPOSAL).read_bytes())
        self.evidence_save()

    def reference_save(self, name, value):
        ref = self.proposal[name]
        self.save(ref["path"], value)
        ref["sha256"] = learn.digest((self.root / ref["path"]).read_bytes())
        self.proposal_save()

    def evaluate(self):
        return learn.evaluate(self.root, PROPOSAL, EVIDENCE)[0]

    def promote(self, apply=True):
        return learn.promote(self.root, PROPOSAL, EVIDENCE, learn.TARGET, self.proposal["base_sha256"], apply)

    def no_gain(self):
        for case in self.evidence["cases"]:
            case["baseline"]["correct"] = True

    def usage(self):
        for case in self.evidence["cases"]:
            for arm in ("baseline", "candidate"):
                case[arm]["usage"] = {"kind": "actual", "measurement_id": "SYNTHETIC-provider-total-v1", "input_tokens": 100 if arm == "baseline" else 50, "output_tokens": 10}

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_evaluate_readonly_quality_win_and_unknown_metrics(self):
        before = self.snapshot()
        result = self.evaluate()
        self.assertTrue(result["eligible"])
        self.assertEqual(result["criterion_wins"], 2)
        self.assertEqual(result["cases"], 10)
        self.assertEqual(result["grading_origins"], ["manual"])
        self.assertIsNone(result["usage"]["matched_successful_totals"])
        self.assertEqual(before, self.snapshot())

    def test_no_change_is_not_improvement(self):
        self.no_gain(); self.evidence_save()
        self.assertFalse(self.evaluate()["eligible"])

    def test_comparable_actual_usage_can_gate_after_quality(self):
        self.no_gain(); self.usage(); self.evidence_save()
        result = self.evaluate()
        self.assertTrue(result["eligible"])
        self.assertEqual(result["usage"]["matched_successful_totals"]["baseline"], 1100)
        self.assertEqual(result["usage"]["matched_successful_totals"]["candidate"], 600)

    def test_partial_metrics_are_unknown_not_zero(self):
        self.no_gain(); self.usage()
        self.evidence["cases"][0]["candidate"]["usage"] = None
        self.evidence_save()
        result = self.evaluate()
        self.assertFalse(result["eligible"])
        self.assertIsNone(result["usage"]["matched_successful_totals"])

    def test_incompatible_measurements_cannot_establish_efficiency(self):
        self.no_gain(); self.usage()
        self.evidence["cases"][0]["candidate"]["usage"]["measurement_id"] = "different boundary"
        self.evidence_save()
        self.assertFalse(self.evaluate()["eligible"])

    def test_failed_runs_in_all_totals_separate_from_successful_pairs(self):
        self.usage(); self.evidence_save()
        result = self.evaluate()["usage"]
        self.assertEqual(result["successful_pairs"], 8)
        self.assertEqual(result["all_run_totals"]["baseline"], 1100)
        self.assertEqual(result["matched_successful_totals"]["baseline"], 880)

    def test_time_claim_requires_matching_measurements(self):
        for case in self.evidence["cases"]:
            for arm in ("baseline", "candidate"):
                case[arm]["duration"] = {"milliseconds": 1.5, "measurement_id": "same"}
        self.evidence_save()
        self.assertEqual(self.evaluate()["duration"]["matched_successful_totals"]["baseline"], 12)
        self.evidence["cases"][0]["baseline"]["duration"]["measurement_id"] = "different"
        self.evidence_save()
        self.assertIsNone(self.evaluate()["duration"]["all_run_totals"])

    def test_correctness_or_scope_failure_blocks_even_with_savings(self):
        self.usage()
        for criterion in ("correct", "scope"):
            with self.subTest(criterion=criterion):
                self.evidence["cases"][-1]["candidate"][criterion] = False
                self.evidence_save()
                result = self.promote()
                self.assertFalse(result["eligible"])
                self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)

    def test_strict_schema_and_duplicate_json_keys(self):
        for data in (b'{"x":1,"x":2}', b'{"value":NaN}', b'{"value":Infinity}', b'\xff'):
            with self.subTest(data=data), self.assertRaises(learn.Invalid):
                learn.parse(data)
        self.proposal["unexpected"] = True
        self.proposal_save()
        with self.assertRaises(learn.Invalid):
            self.evaluate()

    def test_duplicate_missing_and_undeclared_cases(self):
        original = copy.deepcopy(self.evidence)
        for change in ("duplicate", "missing", "undeclared"):
            self.evidence = copy.deepcopy(original)
            if change == "duplicate": self.evidence["cases"].append(self.evidence["cases"][0])
            if change == "missing": self.evidence["cases"].pop()
            if change == "undeclared": self.evidence["cases"][0]["task_id"] = "not-declared"
            self.evidence_save()
            with self.subTest(change=change), self.assertRaises(learn.Invalid):
                self.evaluate()

    def test_manifest_requires_heldout_and_repeats(self):
        original = learn.parse((self.root / self.proposal["manifest"]["path"]).read_bytes())
        for change in ("no-heldout", "one-heldout", "one-trial", "duplicate-task"):
            manifest = copy.deepcopy(original)
            if change == "no-heldout": manifest["tasks"] = [t for t in manifest["tasks"] if t["split"] != "heldout"]
            if change == "one-heldout": manifest["tasks"].pop()
            if change == "one-trial": manifest["tasks"][0]["trials"] = 1
            if change == "duplicate-task": manifest["tasks"].append(manifest["tasks"][0])
            self.reference_save("manifest", manifest)
            with self.subTest(change=change), self.assertRaises(learn.Invalid):
                self.evaluate()

    def test_setup_or_grader_mismatch(self):
        self.evidence["cases"][0]["candidate"]["setup_id"] = "different"
        self.evidence_save()
        with self.assertRaises(learn.Invalid): self.evaluate()
        self.evidence["cases"][0]["candidate"]["setup_id"] = "SYNTHETIC-setup-v1"
        self.evidence["grader_sha256"] = "0" * 64
        self.evidence_save()
        with self.assertRaises(learn.Invalid): self.evaluate()

    def test_artifact_source_candidate_policy_hash_tampering(self):
        refs = [self.evidence["cases"][0]["candidate"]["artifact"]] + [self.proposal[k] for k in ("source", "candidate", "policy", "manifest")]
        for ref in refs:
            path = self.root / ref["path"]
            before = path.read_bytes()
            path.write_bytes(before + b"changed")
            with self.subTest(path=ref["path"]), self.assertRaises(learn.Invalid): self.evaluate()
            path.write_bytes(before)

    def test_nonnumeric_nonfinite_negative_and_boolean_metrics(self):
        original = copy.deepcopy(self.evidence)
        for invalid in (-1, "12", True, 1.5, None):
            self.evidence = copy.deepcopy(original); self.usage()
            self.evidence["cases"][0]["candidate"]["usage"]["input_tokens"] = invalid
            self.evidence_save()
            with self.subTest(invalid=invalid), self.assertRaises(learn.Invalid): self.evaluate()
        for invalid in (-1, "12", True, float("inf")):
            self.evidence = copy.deepcopy(original)
            self.evidence["cases"][0]["candidate"]["duration"] = {"milliseconds": invalid, "measurement_id": "same"}
            (self.root / EVIDENCE).write_text(json.dumps(self.evidence), encoding="utf-8")
            with self.subTest(duration=invalid), self.assertRaises(learn.Invalid): self.evaluate()

    def test_estimated_usage_and_non_boolean_grades_rejected(self):
        self.usage(); self.evidence["cases"][0]["candidate"]["usage"]["kind"] = "estimated"; self.evidence_save()
        with self.assertRaises(learn.Invalid): self.evaluate()
        self.usage(); self.evidence["cases"][0]["candidate"]["correct"] = 1; self.evidence_save()
        with self.assertRaises(learn.Invalid): self.evaluate()

    def test_paths_traversal_absolute_ads_backslash_and_other_targets_rejected(self):
        for path in (".exactwork/../private", "/etc/passwd", "C:/private", "../.exactwork/a", ".exactwork/a:stream", ".exactwork\\file", "data/file"):
            with self.subTest(path=path), self.assertRaises(learn.Invalid): learn.local(self.root, path)
        with self.assertRaises(learn.Invalid):
            learn.promote(self.root, PROPOSAL, EVIDENCE, "AGENTS.md", self.proposal["base_sha256"], True)

    def test_symlink_and_junction_attributes_rejected(self):
        for mode, attributes in ((stat.S_IFLNK, 0), (stat.S_IFDIR, 0x400)):
            with self.subTest(mode=mode, attributes=attributes), patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=mode, st_file_attributes=attributes)), self.assertRaises(learn.Invalid):
                learn.local(self.root, ".exactwork/candidate.md")

    def test_preview_promotion_and_exact_rollback_roundtrip(self):
        before = self.snapshot()
        self.assertEqual(self.promote(False)["action"], "preview")
        self.assertEqual(before, self.snapshot())
        result = self.promote()
        self.assertEqual((self.root / learn.TARGET).read_bytes(), (self.root / self.proposal["candidate"]["path"]).read_bytes())
        before = self.snapshot()
        learn.rollback(self.root, result["version"], result["sha256"])
        self.assertEqual(before, self.snapshot())
        learn.rollback(self.root, result["version"], result["sha256"], True)
        self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)

    def test_absent_base_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fixture(root, existing=False)
            result = learn.promote(root, PROPOSAL, EVIDENCE, learn.TARGET, None, True)
            learn.rollback(root, result["version"], result["sha256"], True)
            self.assertFalse((root / learn.TARGET).exists())

    def test_stale_base_and_wrong_expected_hash(self):
        with self.assertRaises(learn.Invalid):
            learn.promote(self.root, PROPOSAL, EVIDENCE, learn.TARGET, "0" * 64, True)
        (self.root / learn.TARGET).write_bytes(b"user edit")
        with self.assertRaises(learn.Invalid): self.evaluate()

    def test_second_evaluation_detects_changed_input(self):
        original, calls = learn.evaluate, []
        def changing(*args):
            calls.append(1)
            if len(calls) == 2:
                (self.root / self.proposal["candidate"]["path"]).write_bytes(b"changed")
            return original(*args)
        with patch.object(learn, "evaluate", side_effect=changing), self.assertRaises(learn.Invalid): self.promote()
        self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)
        self.assertFalse((self.root / ".exactwork/learn.lock").exists())

    def test_failure_after_preparation_preserves_base_and_is_recoverable(self):
        with patch.object(learn, "atomic", side_effect=OSError("injected write failure")), self.assertRaises(learn.Invalid): self.promote()
        self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)
        pending = learn.parse((self.root / ".exactwork/pending.json").read_bytes())
        with self.assertRaises(learn.Invalid): self.promote()
        learn.rollback(self.root, pending["version"], self.proposal["base_sha256"], True)
        self.assertFalse((self.root / ".exactwork/pending.json").exists())

    def test_failure_after_replacement_is_recoverable(self):
        original = learn.exclusive
        def fail_commit(path, data):
            if path.name == "committed.json": raise OSError("injected commit failure")
            return original(path, data)
        with patch.object(learn, "exclusive", side_effect=fail_commit), self.assertRaises(learn.Invalid): self.promote()
        pending = learn.parse((self.root / ".exactwork/pending.json").read_bytes())
        learn.rollback(self.root, pending["version"], self.proposal["candidate"]["sha256"], True)
        self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)

    def test_rollback_preserves_user_edits(self):
        result = self.promote()
        (self.root / learn.TARGET).write_bytes(b"new user content")
        for expected in (result["sha256"], learn.digest(b"new user content")):
            with self.assertRaises(learn.Invalid): learn.rollback(self.root, result["version"], expected, True)
        self.assertEqual((self.root / learn.TARGET).read_bytes(), b"new user content")

    def test_corrupt_backup_and_version_record_rejected(self):
        result = self.promote()
        directory = self.root / ".exactwork/versions" / result["version"]
        (directory / "base.bin").write_bytes(b"tampered")
        with self.assertRaises(learn.Invalid): learn.rollback(self.root, result["version"], result["sha256"], True)
        (directory / "base.bin").write_bytes(self.base)
        record = learn.parse((directory / "record.json").read_bytes())
        record["proposal_sha256"] = "0" * 64
        (directory / "record.json").write_bytes(learn.encoded(record))
        with self.assertRaises(learn.Invalid): learn.rollback(self.root, result["version"], result["sha256"], True)

    def test_lock_is_not_overwritten(self):
        (self.root / ".exactwork/learn.lock").write_bytes(b"other writer")
        with self.assertRaises(learn.Invalid): self.promote()
        self.assertEqual((self.root / ".exactwork/learn.lock").read_bytes(), b"other writer")

    def test_rollback_marker_failure_can_be_retried_without_losing_base(self):
        result = self.promote()
        original = learn.exclusive
        def fail_marker(path, data):
            if path.name == "rolled-back.json": raise OSError("injected marker failure")
            return original(path, data)
        with patch.object(learn, "exclusive", side_effect=fail_marker), self.assertRaises(OSError):
            learn.rollback(self.root, result["version"], result["sha256"], True)
        self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)
        learn.rollback(self.root, result["version"], self.proposal["base_sha256"], True)

    def test_completed_rollback_pending_cleanup_can_be_retried(self):
        original = learn.exclusive
        def fail_commit(path, data):
            if path.name == "committed.json": raise OSError("injected commit failure")
            return original(path, data)
        with patch.object(learn, "exclusive", side_effect=fail_commit), self.assertRaises(learn.Invalid): self.promote()
        pending_path = self.root / ".exactwork/pending.json"
        pending = learn.parse(pending_path.read_bytes())
        original_unlink = Path.unlink
        def fail_cleanup(path, *args, **kwargs):
            if path == pending_path: raise OSError("injected pending cleanup failure")
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, "unlink", fail_cleanup), self.assertRaises(OSError):
            learn.rollback(self.root, pending["version"], self.proposal["candidate"]["sha256"], True)
        self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)
        before = self.snapshot()
        learn.rollback(self.root, pending["version"], self.proposal["base_sha256"])
        self.assertEqual(before, self.snapshot())
        with patch.object(learn, "atomic", side_effect=AssertionError("cleanup must not rewrite procedure")):
            learn.rollback(self.root, pending["version"], self.proposal["base_sha256"], True)
        self.assertFalse(pending_path.exists())
        self.assertEqual((self.root / learn.TARGET).read_bytes(), self.base)

    def test_falsey_pending_records_rejected_without_writes(self):
        result = self.promote()
        for invalid in ({}, [], None, False, 0, ""):
            self.save(".exactwork/pending.json", invalid)
            before = self.snapshot()
            with self.subTest(pending=invalid), self.assertRaises(learn.Invalid):
                learn.rollback(self.root, result["version"], result["sha256"], True)
            self.assertEqual(before, self.snapshot())

    def test_finite_duration_overflow_is_structured_cli_error(self):
        for case in self.evidence["cases"]:
            for arm in ("baseline", "candidate"):
                case[arm]["duration"] = {"milliseconds": 1e308, "measurement_id": "same"}
        self.evidence_save()
        with self.assertRaises(learn.Invalid): self.evaluate()
        args = [sys.executable, str(SCRIPT), "evaluate", "--project", str(self.root), "--proposal", PROPOSAL, "--evidence", EVIDENCE]
        run = subprocess.run(args, capture_output=True, check=False)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertIn("overflow", json.loads(run.stdout)["error"])
        self.assertEqual(run.stderr, b"")

    def test_real_cli_json_and_exit_statuses(self):
        args = [sys.executable, str(SCRIPT), "evaluate", "--project", str(self.root), "--proposal", PROPOSAL, "--evidence", EVIDENCE]
        run = subprocess.run(args, capture_output=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(run.stdout)["eligible"])
        self.no_gain(); self.evidence_save()
        run = subprocess.run(args, capture_output=True, check=False)
        self.assertEqual(run.returncode, 1)
        self.assertFalse(json.loads(run.stdout)["eligible"])
        (self.root / EVIDENCE).write_bytes(b"not JSON")
        run = subprocess.run(args, capture_output=True, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertIn("error", json.loads(run.stdout))

    def test_generated_example_is_valid_and_existing_directory_is_refused(self):
        destination = self.root / "synthetic-demo"
        args = [sys.executable, str(Path(__file__).resolve()), "--example", str(destination)]
        run = subprocess.run(args, capture_output=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("SYNTHETIC", json.loads(run.stdout)["notice"])
        self.assertTrue(learn.evaluate(destination, PROPOSAL, EVIDENCE)[0]["eligible"])
        before = (destination / PROPOSAL).read_bytes()
        run = subprocess.run(args, capture_output=True, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(before, (destination / PROPOSAL).read_bytes())


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--example":
        destination = Path(sys.argv[2]).absolute()
        if destination.exists():
            print("Example destination must be a new directory.", file=sys.stderr)
            raise SystemExit(2)
        destination.mkdir()
        proposal, _, _ = fixture(destination)
        sys.stdout.buffer.write(learn.encoded({"notice": "SYNTHETIC invented test labels; no performance measurement", "project": str(destination),
                                               "proposal": PROPOSAL, "evidence": EVIDENCE, "base_sha256": proposal["base_sha256"]}))
    else:
        unittest.main()
