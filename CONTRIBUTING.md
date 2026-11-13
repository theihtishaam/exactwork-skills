# Contributing

Start with a reproducible task where the current instructions fail, waste work, or trigger unnecessarily. Include the prompt, synthetic/minimized inputs, host/model versions when known, and the observable result. Remove private data and credentials.

Prefer a narrow instruction change over a new universal rule. Keep each skill independently usable, its discovery description specific, and its language portable. Add a supporting file only when the task needs it. Never copy a third party's text or code without preserving the required license.

Run:

```sh
python -m unittest discover -s tests -v
python tools/validate.py
python tools/measure.py
```

For behavior changes, run relevant [paired evaluations](evals/README.md) in clean contexts. Report failures, ties, and missing telemetry. Keep a held-out set for final performance claims. Small development cases are useful feedback; they are not broad benchmarks.

Do not add hooks, credential handling, network fetches, or automatic persistent state to the core without an explicit design discussion. Do not weaken correctness, data integrity, accessibility, or user requirements to reduce output length.
