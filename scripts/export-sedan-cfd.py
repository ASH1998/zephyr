"""Export the exact confirmed sedan pair for an independent two-mesh CFD check."""
import argparse
import json
from pathlib import Path
import pyvista as pv
from zephyr.artifacts import _file_sha256
from zephyr.research.runtime import Evidence, save, utc
from zephyr.research.report import artifact_path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--baseline-only', action='store_true', help='Prepare the fixed baseline while optimization runs')
args = p.parse_args()
e = Evidence(args.directory); rows = e.records()
baseline = next(r for r in rows if r['id'] == 'baseline-00')
confirmed = [r for r in rows if r['id'].startswith('confirm-0-') and r['status'] == 'evaluated']
if not args.baseline_only and len(confirmed) != e.plan['policy']['confirmationRepeats']:
    raise SystemExit('Complete winner confirmation first')
candidate = None if args.baseline_only else max(confirmed, key=lambda r: r['dragN'])
out = e.root / ('cfd-baseline' if args.baseline_only else 'cfd'); out.mkdir(exist_ok=False)
a = pv.read(artifact_path(e, baseline))
shift = -float(a.points[:, 2].min()) + .001
files = {}
meshes = [('baseline', a)]
if candidate is not None: meshes.append(('candidate', pv.read(artifact_path(e, candidate))))
for name, mesh in meshes:
    mesh.points[:, 2] += shift
    path = out / (name + '.stl'); mesh.save(path)
    files[name] = {'file': path.name, 'sha256': _file_sha256(path)}
save(out / 'plan.json', {'createdAt': utc(), 'planSha256': e.plan_hash,
    'stage': 'baseline-only' if args.baseline_only else 'comparison',
    'baselineMeshHash': baseline['meshHash'], 'candidateMeshHash': candidate['meshHash'] if candidate else None,
    'conditions': e.plan['policy']['conditions'], 'files': files,
    'groundTranslationM': shift, 'wheelGroundGapM': .001,
    'solver': 'OpenFOAM simpleFoam kOmegaSST', 'levels': {'coarse': [4, 5], 'fine': [5, 6]},
    'iterations': 1200, 'forceTailSamples': 100, 'forceTailRelativeRange': .002,
    'maximumCommandSeconds': 3600, 'maximumGlobalCells': 4000000,
    'purpose': 'Independent direction and rough-size comparison; not physical certification',
    'limitations': ['Steady RANS differs from training HRLES', 'Static wheels with moving ground',
                    'No boundary-layer cells in this bounded diagnostic', 'Two mesh levels do not prove asymptotic convergence',
                    '1 mm wheel-ground gap added equally to both geometries']})
print(out)
