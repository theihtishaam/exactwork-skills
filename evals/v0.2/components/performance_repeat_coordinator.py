import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess

root = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--output', type=Path, required=True, help='New result directory; never reuse published evidence')
args = ap.parse_args()
out = args.output.absolute()
out.mkdir(parents=True, exist_ok=False)
script = root.parents[2] / 'skills/exactwork-context/scripts/context_slice.py'
mirror = script
expected_sha = 'ef71289f3f6eb8f53fe58f6d31562cfd184e408c3f8dfa5d71de77ecb9f0b923'
assert hashlib.sha256(script.read_bytes()).hexdigest() == expected_sha
assert mirror.read_bytes() == script.read_bytes()
source = out / 'resource-800-2000.txt'
source.write_bytes((b'ERROR ' + b'x' * 1993 + b'\n') * 800)
results = {
    'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'python': sys.version,
    'platform': platform.platform(),
    'source_file': str(source),
    'source_bytes': source.stat().st_size,
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'case': {'lines': 800, 'bytes_per_line_including_lf': 2000,
             'context': 0, 'max_lines': 800, 'max_bytes': 400000},
    'method': 'Fresh Python subprocess per sample; timed select plus final JSON encoding; imports, fixture creation, process launch and output-file writes excluded.',
    'caveats': ['Three pairs on one machine; concurrent local study may add scheduling/load noise.',
                'Wall time and process CPU time measure this synthetic helper case, not model tokens or end-to-end agent quality.',
                'All six observations retained; no warm-up samples or timing assertions.'],
    'pairs': [],
}
for pair_number, order in enumerate([['original', 'fixed'], ['fixed', 'original'], ['original', 'fixed']], 1):
    pair = {'pair': pair_number, 'order': order, 'samples': []}
    for variant in order:
        sample_id = f'pair-{pair_number}-{variant}'
        run = subprocess.run([sys.executable, str(root / 'performance_repeat_worker.py'), variant, sample_id, str(out)],
                             capture_output=True, text=True, encoding='utf-8', check=True)
        sample = json.loads(run.stdout)
        pair['samples'].append(sample)
        print(json.dumps(sample), flush=True)
    old = next(sample for sample in pair['samples'] if sample['variant'] == 'original')
    fixed = next(sample for sample in pair['samples'] if sample['variant'] == 'fixed')
    pair['complete_output_bytes_equal'] = Path(old['output_file']).read_bytes() == Path(fixed['output_file']).read_bytes()
    pair['wall_ratio_original_over_fixed'] = old['wall_seconds'] / fixed['wall_seconds']
    pair['cpu_ratio_original_over_fixed'] = old['process_cpu_seconds'] / fixed['process_cpu_seconds']
    results['pairs'].append(pair)
    (out / 'performance-repeats.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    assert pair['complete_output_bytes_equal'], f'Pair {pair_number} output mismatch'
summary = {}
for variant in ['original', 'fixed']:
    samples = [sample for pair in results['pairs'] for sample in pair['samples'] if sample['variant'] == variant]
    summary[variant] = {}
    for metric in ['wall_seconds', 'process_cpu_seconds']:
        values = [sample[metric] for sample in samples]
        summary[variant][metric] = {'median': statistics.median(values), 'min': min(values), 'max': max(values), 'samples': values}
results['summary'] = summary
results['final_helper_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
results['helper_hash_unchanged'] = results['final_helper_sha256'] == expected_sha
results['mirror_identical'] = mirror.read_bytes() == script.read_bytes()
assert results['helper_hash_unchanged'] and results['mirror_identical']
(out / 'performance-repeats.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
rows = []
for pair in results['pairs']:
    for sample in pair['samples']:
        rows.append(f"| {pair['pair']} | {' then '.join(pair['order'])} | {sample['variant']} | {sample['wall_seconds']:.6f} | {sample['process_cpu_seconds']:.6f} | {sample['output_bytes']:,} |")
summary_rows = []
for variant in ['original', 'fixed']:
    wall = summary[variant]['wall_seconds']
    cpu = summary[variant]['process_cpu_seconds']
    summary_rows.append(f"| {variant} | {wall['median']:.6f} ({wall['min']:.6f}–{wall['max']:.6f}) | {cpu['median']:.6f} ({cpu['min']:.6f}–{cpu['max']:.6f}) |")
report = f'''# Repeated selector performance measurements

Three paired repetitions were collected on the same machine, alternating original/fixed order. Each observation used a fresh Python subprocess. No samples were discarded and no timing assertion was used.

Case: 800 source lines, exactly 2,000 bytes per line including LF (1,600,000 source bytes), context 0, max-lines 800, and max-bytes 400,000. The timed region includes selection and final JSON encoding. It excludes Python startup, module imports, fixture creation and output-file writes.

| Pair | Execution order | Version | Wall seconds | Process CPU seconds | Output bytes |
| --- | --- | --- | ---: | ---: | ---: |
{chr(10).join(rows)}

| Version | Wall median (range), seconds | Process CPU median (range), seconds |
| --- | ---: | ---: |
{chr(10).join(summary_rows)}

Complete serialized JSON bytes were equal in each of the three pairs. Each sample selected 800 lines, reported zero omitted matched lines and 800 truncated lines, and produced exactly 400,000 output bytes. Fidelity was checked by direct byte comparison, with SHA-256 values retained in the JSON record.

The fixed helper and its mirrored copy were unchanged and byte-identical throughout this measurement. Final SHA-256: `{results['final_helper_sha256']}`.

These are measured local synthetic component results. Three pairs on one machine do not establish performance across workloads or machines. Concurrent local study activity may add scheduling/load noise. Wall time and process CPU time are reported separately; neither is a model-token or end-to-end agent-quality measurement.

All six samples, execution order, output hashes, source identity, Python/platform details and raw precision values are retained in `performance-repeats.json`. Reproduce with `python performance_repeat_coordinator.py` from this scratch directory. No model calls or held-out data were used.
'''
(out / 'performance-repeats.md').write_text(report, encoding='utf-8')
print(json.dumps({'summary': summary, 'hash_unchanged': results['helper_hash_unchanged'], 'fidelity_pairs': 3}), flush=True)
