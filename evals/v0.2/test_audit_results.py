"""Mutation checks against an isolated copy of the exported evidence."""
import json
import shutil
import tempfile
from pathlib import Path
from audit_results import audit


def run(source):
    passed = []
    with tempfile.TemporaryDirectory(prefix="audit-test-", dir=Path(__file__).parent) as temporary:
        root = Path(temporary)
        for name in ("evidence", "benchmark", "blind-review", "corrected-grades", "public_eval_tools"):
            shutil.copytree(source / name, root / name)
        for name in ("final-results.json", "final-results.csv"):
            shutil.copy2(source / name, root / name)
        assert audit(root)["runs"] == 35
        passed.append("unmodified release")

        def reject(label, path, mutate, message):
            target = root / path
            original = target.read_bytes()
            try:
                data = json.loads(original)
                mutate(data)
                target.write_text(json.dumps(data), encoding="utf-8")
                try:
                    audit(root)
                except ValueError as error:
                    assert message in str(error), (label, error)
                    passed.append(label)
                else:
                    raise AssertionError("mutation escaped: " + label)
            finally:
                target.write_bytes(original)

        reject("duplicate run", "final-results.json", lambda d: d["runs"].append(d["runs"][0]), "duplicate rows")
        reject("missing run", "final-results.json", lambda d: d["runs"].pop(), "missing/unexpected experimental cells")
        reject("actual usage drift", "final-results.json", lambda d: d["runs"][0].__setitem__("input_tokens", 1), "usage mismatch")
        reject("phase aggregation drift", "final-results.json", lambda d: d["summary"]["phases"]["dev"]["none"].__setitem__("total_tokens", 1), "aggregate drift: phases")
        reject("coding aggregation drift", "final-results.json", lambda d: d["summary"]["matched_coding_subset"]["v02"].__setitem__("task_passes", 0), "coding aggregate drift")
        reject("claim percentage drift", "final-results.json", lambda d: d["summary"].__setitem__("holdout_percent_reduction_vs_none", 99), "percentage drift")
        reject("semantic label drift", "blind-review/semantic-grades.json", lambda d: d["records"]["sample-096b853333"].__setitem__("semantic_success", True), "semantic label mismatch")
        reject("anonymized answer mismatch", "blind-review/semantic-grades.json", lambda d: d["records"]["sample-096b853333"].__setitem__("answer_sha256", "0"*64), "semantic answer attribution mismatch")
        def extra_correction(data):
            data["checks"][0]["passed"] = False
            data["passed"] -= 1
            data["deterministic_success"] = False
        reject("unapproved grade change", "corrected-grades/dev/d03/m02/grade.json", extra_correction, "unapproved grade correction")
        target = root / "evidence/runs/dev/d01/m04/trace.jsonl"
        target.write_bytes(target.read_bytes() + b"\n")
        try:
            audit(root)
        except ValueError as error:
            assert "hash mismatch" in str(error)
            passed.append("public evidence byte tamper")
        else:
            raise AssertionError("hash mutation escaped")
    return {"tests_passed": len(passed), "checks": passed}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    print(json.dumps(run(parser.parse_args().root), indent=2))
