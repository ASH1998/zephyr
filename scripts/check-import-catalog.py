"""Read-only regression: shared preparation must reproduce every saved catalog mesh hash."""
from pathlib import Path
import json
import pyvista as pv
import trimesh
from zephyr.local.conversion import mesh_hash
from zephyr.local.importer import prepare_surface

ROOT = Path(__file__).resolve().parents[1]
results = []
for kind in ('hatchback', 'wagon', 'suv', 'coupe', 'sports', 'van', 'x57', 'global-hawk'):
    source = ROOT / '.local/vehicle-sources' / f'{kind}-visual.ply'
    expected = mesh_hash(pv.read(ROOT / '.local/cars' / f'{kind}.vtp'))
    model, preview, report = prepare_surface(trimesh.load(source, force='mesh'), geometry_id=kind, catalog=True)
    actual = mesh_hash(model)
    row = {'id': kind, 'expected': expected, 'actual': actual, 'matches': expected == actual}
    results.append(row); print(json.dumps(row), flush=True)
path = ROOT / '.local/byoc-catalog-hashes.json'
path.write_text(json.dumps(results, indent=2))
if not all(r['matches'] for r in results):
    raise SystemExit('Catalog hash regression')
