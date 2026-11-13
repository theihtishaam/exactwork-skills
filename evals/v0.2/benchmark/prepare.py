"""Copy only manifest-listed public inputs to a fresh isolated task directory."""
from pathlib import Path
import argparse, hashlib, json

ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('case',choices=['d01','d02','d03','d04','h01','h02'])
ap.add_argument('destination',type=Path)
args=ap.parse_args()
manifest=json.loads((ROOT/'FROZEN-MANIFEST.json').read_text())
dest=args.destination.resolve()
if dest.exists():raise SystemExit('Refusing to reuse an existing trial directory.')
prefix='cases/'+args.case+'/input/'
files=[(name,digest) for name,digest in manifest['files'].items() if name.startswith(prefix)]
for name,digest in files:
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise SystemExit('Fixture hash drift: '+name)
dest.mkdir(parents=True)
for name,_ in files:
    target=dest/name[len(prefix):]
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write((ROOT/name).read_bytes())
print('Prepared '+args.case+' with '+str(len(files))+' public files.')
print((ROOT/'cases'/args.case/'prompt.txt').read_text())
