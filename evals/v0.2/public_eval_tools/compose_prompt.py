"""Compose one explicit-load trial prompt from licensed frozen task inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from portable_runner import _plain_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", type=Path, required=True)
    parser.add_argument("--case-prompt", type=Path, required=True)
    parser.add_argument("--common-prompt", type=Path, required=True)
    parser.add_argument("--procedure-file", type=Path, action="append", default=[])
    parser.add_argument("--helper", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--procedure-output", type=Path, help="Optional exact assembled procedure for portable_runner --skill-file")
    args = parser.parse_args()
    root = Path(os.path.abspath(args.study_root))
    paths = [args.case_prompt, args.common_prompt, *args.procedure_file, args.output, *([args.helper] if args.helper else []), *([args.procedure_output] if args.procedure_output else [])]
    for path in paths:
        checked = Path(os.path.abspath(path))
        _plain_path(checked)
        if not checked.is_relative_to(root) or checked == root:
            parser.error("All named inputs and output must be inside the explicit task-owned study root")
    procedure = "\n\n".join(path.read_text(encoding="utf-8") for path in args.procedure_file)
    if args.helper:
        if not procedure:
            parser.error("A helper requires its procedure instructions")
        procedure += "\n\nFor this run the optional helper is at: " + str(Path(os.path.abspath(args.helper))) + ". Execute it from that path; the current fixture remains the working directory.\n"
    prompt = args.common_prompt.read_text(encoding="utf-8") + ("PROCEDURE FOR THIS TASK\n" + procedure + "\n\n" if procedure else "") + "TASK\n" + args.case_prompt.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as target:
        target.write(prompt.encode("utf-8"))
    if args.procedure_output:
        args.procedure_output.parent.mkdir(parents=True, exist_ok=True)
        with args.procedure_output.open("xb") as target:
            target.write(procedure.encode("utf-8"))
    print(json.dumps({"prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "skill_sha256": hashlib.sha256(procedure.encode("utf-8")).hexdigest() if procedure else None}))


if __name__ == "__main__":
    main()
