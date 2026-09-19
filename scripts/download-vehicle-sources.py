"""Fetch licensed, pinned vehicle sources; never execute downloaded files."""
from pathlib import Path
from hashlib import sha256
import json, urllib.request, concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/vehicle-sources'
def fetch(item):
 target=(SOURCE/item['path']).resolve()
 if not target.is_relative_to(SOURCE.resolve()):raise ValueError('Invalid source destination')
 if target.exists() and sha256(target.read_bytes()).hexdigest()==item['sha256']:return
 data=urllib.request.urlopen(item['url'],timeout=90).read()
 if len(data)!=item['bytes'] or sha256(data).hexdigest()!=item['sha256']:raise ValueError('Source hash mismatch: '+item['path'])
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 print('Downloaded',item['path'],flush=True)
if __name__=='__main__':
 records=json.loads((ROOT/'config/vehicle-source-artifacts.json').read_text(encoding='utf8'))['artifacts']
 list(concurrent.futures.ThreadPoolExecutor(6).map(fetch,records))
 print('All vehicle sources verified.')
