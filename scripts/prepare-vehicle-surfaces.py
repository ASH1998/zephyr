"""Build catalog inference surfaces with the shared, hash-stable legacy recipe."""
from pathlib import Path
import json
import sys
import trimesh
import pyvista as pv
from zephyr.local.cars import car_definition
from zephyr.local.importer import prepare_surface
from zephyr.local.conversion import mesh_hash

ROOT = Path(__file__).resolve().parents[1]
for kind in (sys.argv[1:] or ['hatchback', 'wagon', 'suv', 'coupe', 'sports', 'van']):
    car_definition(kind)
    if kind.startswith('upload-'):
        raise ValueError('This script only prepares the fixed catalog')
    (ROOT / '.local/cars').mkdir(parents=True, exist_ok=True)
    (ROOT / 'frontend/public/models/cars').mkdir(parents=True, exist_ok=True)
    visual = trimesh.load(ROOT / '.local/vehicle-sources' / f'{kind}-visual.ply', force='mesh')
    model, preview, report = prepare_surface(visual, geometry_id=kind, catalog=True)
    existing = ROOT / '.local/cars' / f'{kind}.vtp'
    if existing.exists() and mesh_hash(pv.read(existing)) != report['meshHash']:
        raise ValueError(f'{kind}: current source does not reproduce the saved catalog hash; existing assets were preserved')
    preview['visual'] = {'url': f'/models/vehicles/{kind}.glb', 'offset': report['visualOffset']}
    preview['provenance'] = 'Detailed licensed visual asset; simplified watertight surface derived from that asset for NVIDIA inference.'
    model.save(ROOT / '.local/cars' / f'{kind}.vtp')
    (ROOT / 'frontend/public/models/cars' / f'{kind}.json').write_text(json.dumps(preview, separators=(',', ':')))
    print(kind, model.n_points, model.n_cells, 'hash', report['meshHash'], 'offset', report['visualOffset'], flush=True)
