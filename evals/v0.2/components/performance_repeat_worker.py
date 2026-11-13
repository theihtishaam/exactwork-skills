import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
from pathlib import Path
import time

root = Path(__file__).resolve().parent
variant, sample_id, output_dir = sys.argv[1:]
out = Path(output_dir)
script = (root / 'context_slice_before.py' if variant == 'original' else
          root.parents[2] / 'skills/exactwork-context/scripts/context_slice.py')
source = out / 'resource-800-2000.txt'
spec = importlib.util.spec_from_file_location('measured_selector', script)
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)
wall_start = time.perf_counter()
cpu_start = time.process_time()
result = selector.select(source, context=0, max_lines=800, max_bytes=400000)
encoded = selector.encode(result)
cpu_seconds = time.process_time() - cpu_start
wall_seconds = time.perf_counter() - wall_start
output_file = out / (sample_id + '.output.json')
output_file.write_bytes(encoded)
print(json.dumps({
    'sample_id': sample_id,
    'variant': variant,
    'wall_seconds': wall_seconds,
    'process_cpu_seconds': cpu_seconds,
    'output_bytes': len(encoded),
    'output_sha256': hashlib.sha256(encoded).hexdigest(),
    'output_file': str(output_file),
    'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
    'selected_line_count': result['selected_line_count'],
    'omitted_matched_lines': result['omitted_matched_lines'],
    'truncated_line_count': result['truncated_line_count'],
}))
