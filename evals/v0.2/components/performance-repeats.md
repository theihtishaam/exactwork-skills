# Repeated selector performance measurements

Three paired repetitions were collected on the same machine, alternating original/fixed order. Each observation used a fresh Python subprocess. No samples were discarded and no timing assertion was used.

Case: 800 source lines, exactly 2,000 bytes per line including LF (1,600,000 source bytes), context 0, max-lines 800, and max-bytes 400,000. The timed region includes selection and final JSON encoding. It excludes Python startup, module imports, fixture creation and output-file writes.

| Pair | Execution order | Version | Wall seconds | Process CPU seconds | Output bytes |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | original then fixed | original | 18.472024 | 17.796875 | 400,000 |
| 1 | original then fixed | fixed | 0.104185 | 0.093750 | 400,000 |
| 2 | fixed then original | fixed | 0.173869 | 0.140625 | 400,000 |
| 2 | fixed then original | original | 17.169410 | 16.875000 | 400,000 |
| 3 | original then fixed | original | 19.577326 | 18.265625 | 400,000 |
| 3 | original then fixed | fixed | 0.074132 | 0.078125 | 400,000 |

| Version | Wall median (range), seconds | Process CPU median (range), seconds |
| --- | ---: | ---: |
| original | 18.472024 (17.169410–19.577326) | 17.796875 (16.875000–18.265625) |
| fixed | 0.104185 (0.074132–0.173869) | 0.093750 (0.078125–0.140625) |

Complete serialized JSON bytes were equal in each of the three pairs. Each sample selected 800 lines, reported zero omitted matched lines and 800 truncated lines, and produced exactly 400,000 output bytes. Fidelity was checked by direct byte comparison, with SHA-256 values retained in the JSON record.

The fixed helper and its mirrored copy were unchanged and byte-identical throughout this measurement. Final SHA-256: `ef71289f3f6eb8f53fe58f6d31562cfd184e408c3f8dfa5d71de77ecb9f0b923`.

These are measured local synthetic component results. Three pairs on one machine do not establish performance across workloads or machines. Concurrent local study activity may add scheduling/load noise. Wall time and process CPU time are reported separately; neither is a model-token or end-to-end agent-quality measurement.

All six samples, execution order, output hashes, source identity, Python/platform details and raw precision values are retained in `performance-repeats.json`. Reproduce with `python performance_repeat_coordinator.py` from this scratch directory. No model calls or held-out data were used.
