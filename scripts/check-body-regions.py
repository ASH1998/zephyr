"""Record full-resolution geometry compatibility for every new body handle."""
import argparse
import json
from pathlib import Path
import numpy as np
import pyvista as pv
from zephyr.local.geometry import BODY_HANDLES, deform, validate_geometry
from zephyr.local.cars import mesh_path
from zephyr.artifacts import _file_sha256

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
rows = []
for geometry in ('drivaer-1', 'hatchback'):
    mesh = pv.read(mesh_path(geometry))
    for handle in BODY_HANDLES:
        for sign in (-1, 1):
            c, protected, definition = deform(mesh, sign*.004, .004, handle)
            checks = validate_geometry(mesh, c, protected, .004)
            rows.append({'geometry': geometry, 'handle': handle, 'signedBudgetMm': sign*4,
                'editableVertices': int((~protected).sum()), 'totalVertices': mesh.n_points,
                'checks': checks, 'definition': definition})
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps({'geometrySourceSha256': _file_sha256(Path(__file__).resolve().parents[1]/'src/zephyr/local/geometry.py'),
    'scope': 'Preliminary geometry checks only; exact intersections and fresh GPU inference are separate.', 'cases': rows}, indent=2))
for row in rows:
    print(row['geometry'], row['handle'], row['signedBudgetMm'], f"{row['editableVertices']/row['totalVertices']:.1%} editable",
          {k:v for k,v in row['checks'].items() if v['status']!='passed'})
