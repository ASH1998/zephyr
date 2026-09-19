"""Download only the pinned NVIDIA volume bundle, verifying every file hash."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'config/domino-volume-artifacts.json').read_text(encoding='utf-8'))
directory=ROOT/'.local/domino-volume';directory.mkdir(parents=True,exist_ok=True)
for entry in manifest['required']:
 path=directory/entry['path']
 if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']:continue
 url=manifest['source']+'/resolve/'+manifest['revision']+'/domino_drivaerml_volume_checkpoint/'+entry['path']
 with urllib.request.urlopen(url,timeout=120) as response:data=response.read()
 if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Checksum mismatch: '+entry['path'])
 path.write_bytes(data);print('Verified',entry['path'],len(data),'bytes')
