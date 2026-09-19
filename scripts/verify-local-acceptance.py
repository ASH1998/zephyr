"""Independently check saved production artifacts; no inference or edits to runs."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
import pyvista as pv
from zephyr.artifacts import _file_sha256
from zephyr.local.conversion import mesh_hash
from zephyr.local.geometry import rear_basis, validate_geometry
from zephyr.local.intersections import audit_intersections
from zephyr.local.trust import decide_step

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run_id')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not re.fullmatch(r'local-[0-9a-f]{32}', args.run_id):
    parser.error('Expected a local run id')
root = Path(__file__).resolve().parents[1]
directory = root / '.local/runs' / args.run_id
evidence = json.loads((directory / 'evidence.json').read_text(encoding='utf-8'))
assert evidence['runId'] == args.run_id
baseline, candidate = [pv.read(directory / name) for name in ('baseline.vtk', 'evaluate.vtk')]
for name in ('baseline.vtk', 'evaluate.vtk'):
    assert _file_sha256(directory / name) == evidence['artifacts'][name]['sha256']
assert mesh_hash(baseline) == evidence['provenance']['meshHash']
assert mesh_hash(candidate) == evidence['provenance']['candidateMeshHash']
_, protected, _ = rear_basis(baseline.points)
checks = validate_geometry(baseline, candidate, protected, evidence['constraints']['maxDisplacementM'])
assert all(c['status'] == 'passed' for c in checks.values()), checks
audits = {'baseline': audit_intersections(baseline), 'candidate': audit_intersections(candidate)}
assert all(a['status'] == 'passed' for a in audits.values()), audits
checks.update({key: evidence['validation']['checks'][key] for key in ('symmetricHandle', 'transition')})
checks['selfIntersection'] = {'status': 'passed', **audits}
integrations = {}
for name, mesh in (('baseline', baseline), ('candidate', candidate)):
    # Geometry-only surface avoids accepting an incorrect cached normal array.
    clean = pv.PolyData(mesh.points, mesh.faces)
    area = clean.compute_cell_sizes(length=False, area=True, volume=False).cell_data['Area']
    integrated = np.sum(area[:, None] * (-clean.cell_normals * mesh.cell_data['pred_surf_pressure'][:, None]
                        - mesh.cell_data['pred_surf_wall_shear_stress']), axis=0)
    recorded = evidence['forces'][name + 'DragN']
    error = abs(float(integrated[0]) - recorded)
    tolerance = 32 * np.finfo(np.float32).eps * max(abs(recorded), 1.)
    assert error < tolerance, (name, error, tolerance)
    assert float(mesh.field_data['aerodynamic_force'][0]) == recorded
    integrations[name] = {'reintegratedFxN': float(integrated[0]), 'recordedFxN': recorded,
                          'absoluteDifferenceN': error, 'toleranceN': float(tolerance)}
decision = decide_step(evidence['forces']['baselineDragN'], evidence['forces']['candidateDragN'],
                       evidence['handle']['predictedDragDeltaN'], evidence['calibration'], checks,
                       experimental=evidence['car']['experimental'])
assert decision['decision'] == evidence['trust']['decision']
assert decision['calibrated'] == evidence['trust']['calibrated']
report = {k: evidence[k] for k in ('schemaVersion', 'runId', 'source', 'createdAt', 'geometryId', 'car',
          'provenance', 'conditions', 'constraints', 'forces', 'trust', 'calibration', 'handle',
          'attempts', 'validation', 'timings', 'artifacts', 'airflowStatus')}
report['artifactVerification'] = {'scriptSha256': _file_sha256(Path(__file__)),
    'sourceEvidenceSha256': _file_sha256(directory / 'evidence.json'),
    'fullResolutionGeometry': checks, 'forceReintegration': integrations,
    'recomputedDecision': decision, 'status': 'passed'}
report['surfaceProfiles'] = evidence.get('surfaceProfiles', {})
report['airflowBinding'] = {key: {'meshHash': field['meshHash'], 'geometryId': field['geometryId']}
                            for key, field in evidence.get('airflow', {}).items()}
for key, binding in report['airflowBinding'].items():
    assert binding['meshHash'] == mesh_hash(baseline if key == 'baseline' else candidate)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
print(json.dumps({'runId': args.run_id, 'status': 'passed', 'trust': decision, 'output': str(args.output)}))
