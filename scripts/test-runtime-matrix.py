"""Run the predeclared local GPU matrix and independently verify every result."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
import pyvista as pv
from zephyr.artifacts import _file_sha256
from zephyr.local.server import Jobs

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--live', action='store_true')
parser.add_argument('--plan', type=Path, default=ROOT / 'docs/evidence/runtime-2026-09-19/plan.json')
parser.add_argument('--output-dir', type=Path, help='Fresh directory for reports; defaults to the plan directory')
parser.add_argument('--start-case', type=int, choices=range(1, 5), default=1,
                    help='Resume at an unrun optimized case, retaining earlier matrix evidence')
args = parser.parse_args()
if not args.live:
    parser.error('GPU inference requires --live')
plan = json.loads(args.plan.read_text(encoding='utf-8'))
output = args.output_dir or args.plan.parent
if args.start_case == 1 and (output / 'matrix.json').exists():
    parser.error('Existing matrix evidence is preserved; choose a fresh --output-dir or resume an unrun case')
output.mkdir(parents=True, exist_ok=True)
if _file_sha256(ROOT / 'src/zephyr/local/trust.py') != plan['policySha256']:
    raise ValueError('Trust policy changed since matrix declaration')


def compare(reference_id, current_id):
    directories = [ROOT / '.local/runs' / name for name in (reference_id, current_id)]
    left, right = [json.loads((p / 'evidence.json').read_text(encoding='utf-8')) for p in directories]
    checks = {}
    for key in ('meshHash', 'candidateMeshHash'):
        checks[key] = left['provenance'][key] == right['provenance'][key]
    checks['amplitude'] = left['handle']['amplitudeM'] == right['handle']['amplitudeM']
    checks['decision'] = left['trust']['decision'] == right['trust']['decision']
    checks['calibrated'] = left['trust']['calibrated'] == right['trust']['calibrated']
    force_differences = {}
    for key in ('baselineDragN', 'candidateDragN', 'predictedDragN'):
        difference = abs(left['forces'][key] - right['forces'][key])
        force_differences[key] = difference
        checks[key] = difference <= 32 * np.finfo(np.float32).eps * max(abs(left['forces'][key]), 1.)
    checks['probeMeshes'] = [p['meshHash'] for p in left['calibration']['samples']] == [p['meshHash'] for p in right['calibration']['samples']]
    for a, b in zip(left['calibration']['samples'], right['calibration']['samples']):
        force_differences[a['name']] = abs(a['dragN'] - b['dragN'])
        checks[a['name']] = force_differences[a['name']] <= 32 * np.finfo(np.float32).eps * max(abs(a['dragN']), 1.)
    fields = {}
    for artifact in ('baseline.vtk', 'evaluate.vtk'):
        a, b = [pv.read(p / artifact) for p in directories]
        checks[artifact + ':coordinates'] = np.array_equal(a.points, b.points)
        checks[artifact + ':topology'] = np.array_equal(a.faces, b.faces)
        for key in ('pred_surf_pressure', 'pred_surf_wall_shear_stress', 'geometry_sensitivity'):
            x, y = a[key], b[key]
            checks[artifact + ':' + key] = bool(np.allclose(x, y, rtol=1e-6, atol=1e-5))
            fields[artifact + ':' + key] = float(np.max(np.abs(x - y)))
    return {'referenceRunId': reference_id, 'checks': {k: bool(v) for k, v in checks.items()},
            'forceAbsoluteDifferencesN': force_differences, 'fieldMaximumAbsoluteDifferences': fields,
            'passed': bool(all(checks.values()))}


report = {'planSha256': _file_sha256(args.plan), 'policySha256': plan['policySha256'], 'cases': []}
if args.start_case > 1:
    report = json.loads((output / 'matrix.json').read_text(encoding='utf-8'))
    if len(report['cases']) != args.start_case - 1 or report['planSha256'] != _file_sha256(args.plan):
        raise ValueError('Resume does not match completed cases and frozen plan')
jobs = Jobs()
try:
    # The first unmodified-process repeat is recorded separately before optimization.
    for index, case in enumerate(plan['cases'][1:], start=1):
        if index < args.start_case:
            continue
        job = jobs.start({'geometryId': case['geometry'], 'budgetMm': case['budgetMm'],
                          'brief': 'Reduce drag. Keep the cabin unchanged.', 'mode': 'iteration'})
        run_id = job['runId']
        print(json.dumps({'case': case, 'runId': run_id}), flush=True)
        previous = None
        while True:
            job = jobs.snapshot(run_id)
            if previous != job['stage']:
                print(json.dumps({k: job[k] for k in ('runId', 'state', 'stage', 'detail')}), flush=True)
                previous = job['stage']
            if job['state'] in ('complete', 'failed', 'cancelled'):
                break
            time.sleep(1)
        if job['state'] != 'complete':
            raise RuntimeError(job['detail'])
        target = output / f'case-{index}.json'
        subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/verify-local-acceptance.py'),
                        run_id, '--output', str(target)], check=True)
        evidence = json.loads(target.read_text(encoding='utf-8'))
        row = {**case, 'runId': run_id, 'verifiedEvidence': target.name,
               'forces': evidence['forces'], 'trust': evidence['trust'], 'timings': evidence['timings'],
               'effectiveAmplitudeM': evidence['handle']['amplitudeM'], 'calibrationStatus': evidence['calibration']['status']}
        if case['budgetMm'] == 3:
            reference = plan['referenceRuns']['sedan' if case['geometry'] == 'drivaer-1' else 'hatchback']
            row['parity'] = compare(reference, run_id)
        report['cases'].append(row)
        (output / 'matrix.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        print(json.dumps(row), flush=True)
        if not row.get('parity', {}).get('passed', True):
            print('Parity failure recorded; continuing predeclared cases without changing tolerances', flush=True)
finally:
    jobs.close()
report['complete'] = len(report['cases']) == len(plan['cases']) - 1
report['allParityChecksPassed'] = all(row.get('parity', {}).get('passed', True) for row in report['cases'])
(output / 'matrix.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
if not report['allParityChecksPassed']:
    raise SystemExit('Matrix completed with recorded parity failures; inspect matrix.json')
