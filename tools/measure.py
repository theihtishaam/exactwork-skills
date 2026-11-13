"""Measure instruction footprint, not inference usage. Python standard library only."""
import argparse
import hashlib
import json
from pathlib import Path


def measure(path):
    raw = path.read_bytes()
    content = raw.decode("utf-8")
    return {
        "utf8_bytes": len(raw),
        "characters": len(content),
        "whitespace_words": len(content.split()),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, help="Optional local baseline SKILL.md")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = {
        "kind": "static_instruction_footprint",
        "note": "Bytes, characters, and words are not model tokens or task savings.",
        "skills": {p.parent.name: measure(p) for p in sorted((root / "skills").glob("*/SKILL.md"))},
    }
    if args.baseline:
        report["baseline"] = measure(args.baseline)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
