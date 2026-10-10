"""Generate genuine fields for a research candidate or prescribed synthetic dent.

Publication means a local recorded-run artifact, not public website deployment.
No search result or acceptance status is fabricated to fit the legacy interface.
"""
import argparse
from copy import deepcopy
import gc
import json
from pathlib import Path
import sys
import time
from uuid import uuid4
import numpy as np
from zephyr.artifacts import _file_sha256
from zephyr.local.conversion import mesh_hash, display_mapping, surface, ROTATION
from zephyr.research.runtime import ROOT, Evidence, Runtime, save, utc
from zephyr.research.study import verify_runtime, verified_noise
from zephyr.research.report import make_report
from zephyr.research.replay import paused_selection


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--live', action='store_true')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--provisional-candidate', help='Saved candidate ID from a user-stopped search; never marks research complete')
    mode.add_argument('--synthetic-dent', action='store_true', help='One prescribed hood dent on the original sedan; no optimization or crash simulation')
    args = p.parse_args()
    if not args.live: p.error('Use --live for two fresh sensitivity and two volume evaluations')
    e = Evidence(args.directory); rows = e.records(); noise = verified_noise(e)
    provisional = bool(args.provisional_candidate)
    dent = args.synthetic_dent
    result = {} if dent else paused_selection(e, args.provisional_candidate) if provisional else make_report(args.directory, e.root / 'report')
    if not (provisional or dent) and result['counts'] != {'optimized': 200, 'random': 200, 'winnerConfirmations': 3}:
        p.error('Complete the matched experiment and winner confirmations first')
    if not (provisional or dent) and not all(result['decision']['checks'].get(key) is True
               for key in ('phaseBudgetsComplete', 'allFinalistsRepeated')):
        p.error('Complete both optimization phases and repeat all three finalists first')
    winner = result.get('winner')
    if winner and not all(c['status'] == 'passed' for c in winner['checks'].values()):
        p.error('Winner geometry must pass all checks')
    started = time.perf_counter()
    with Runtime() as runtime:
        import torch
        from zephyr.local.sensitivity import evaluate_surface
        verify_runtime(e, runtime)
        original = runtime.mesh.copy(deep=True)
        if dent:
            from zephyr.research.dent import prepare_dent
            candidate, scenario = prepare_dent(runtime, e)
            fresh_checks = scenario['checks']
        else:
            candidate = runtime.morphs.deform(winner['parametersMm'])
            if mesh_hash(candidate) != winner['meshHash']:
                raise ValueError('Winner reconstruction mismatch')
            fresh_checks = runtime.morphs.validate(candidate, e.plan['policy'], runtime.box)
        if not all(c['status'] == 'passed' for c in fresh_checks.values()):
            raise ValueError('Reconstructed candidate failed geometry checks')
        rid = 'local-' + uuid4().hex
        target = ROOT / '.local/runs' / rid; target.mkdir(exist_ok=False)
        if dent: save(target / 'scenario.json', scenario)  # Freeze before observing forces.
        force, timings = {}, {}
        for name, mesh, expected in (('baseline', original, noise['baselineMeanN']), ('evaluate', candidate, None if dent else winner['dragN'])):
            t = time.perf_counter(); values = evaluate_surface(runtime.domino, mesh)
            if any(not np.isfinite(v).all() for v in values.values()):
                raise ValueError('Nonfinite final fields')
            force[name] = values['aerodynamic_force'].astype(float)
            if expected is not None and abs(force[name][0] - expected) > max(2*noise['operationalSigmaN'], noise['float32GuardN']):
                raise ValueError('Fresh demo evaluation differs from saved research force')
            for key, value in values.items():
                if len(value) == mesh.n_cells: mesh.cell_data[key] = value
                elif len(value) == mesh.n_points: mesh.point_data[key] = value
            for key, value in runtime.domino.postprocess_point_sensitivities(results=values, mesh=mesh).items():
                mesh[key] = value
            mesh.field_data['aerodynamic_force'] = force[name]
            mesh.save(target / (name + '.vtk'))
            timings[name + 'Seconds'] = time.perf_counter() - t
            print(f"{name}: fresh drag {force[name][0]:.6f} N, fields saved", flush=True)
        origin = np.array([(original.bounds[0]+original.bounds[1])/2, 0, original.bounds[4]])
        ids, triangles, reduction = display_mapping(original)
        before, ranges = surface(original, ids, triangles, runtime.morphs.protected, origin)
        after, _ = surface(candidate, ids, triangles, runtime.morphs.protected, origin, baseline=original)
        payload = {'schemaVersion': 'zephyr.surface.v2', 'runId': rid, 'source': 'recorded',
            'createdAt': utc(), 'status': 'comparison', 'geometryId': 'drivaer-1',
            'car': {'id': 'drivaer-1', 'label': 'DrivAer sedan', 'experimental': False, 'category': 'car'},
            'handle': {'handle': 'synthetic-hood-dent-v1' if dent else 'sedan-research-v1', 'label': 'Synthetic hood dent' if dent else 'Combined sedan research morphs'},
            'coordinates': {'units': 'm', 'up': '+Y', 'streamwise': '+X', 'handedness': 'right',
                'fieldAssociation': 'vertex', 'rotation': ROTATION.tolist(), 'upstreamOriginM': origin.tolist(),
                'transform': '(upstream - origin) @ rotation.T'},
            'provenance': {**runtime.provenance, 'modelVersion': 'DoMINO.0.501.mdlus',
                'candidateMeshHash': mesh_hash(candidate), 'evidenceUrls': ['/api/runs/' + rid + '/evidence'],
                'forceConvention': 'Fresh upstream Fx in N; full surface integration.',
                'fieldTransfer': 'Area-weighted cells to points, retained common display vertices.',
                'sensitivityConvention': 'Measured partial d(-Fx)/dX; explanatory only. Known raw repeatability limitation. No gradient step control.',
                'reduction': reduction, 'fullResolutionRanges': ranges,
                'publisherSha256': _file_sha256(Path(__file__))},
            'conditions': {'streamVelocityMps': [38.889, 0, 0], 'densityKgM3': 1.205},
            'baseline': before, 'candidate': after,
            'forces': {'baselineN': (force['baseline'] @ ROTATION.T).tolist(),
                'candidateN': (force['evaluate'] @ ROTATION.T).tolist(),
                'baselineDragN': float(force['baseline'][0]), 'candidateDragN': float(force['evaluate'][0]),
                'predictedDragN': None},
            'constraints': {'maxDisplacementM': .012 if dent else .060, 'protectedRegion': 'Cabin, greenhouse, lower body and fragile triangle regions fixed'},
            'trust': {'decision': 'refuse', 'calibrated': False, 'predictionErrorPercent': None,
                'engineeringValidated': False, 'policyVersion': 'synthetic-hood-dent-v1' if dent else 'sedan-forward-study-v1',
                'reason': ('Synthetic dent with experimental aerodynamic predictions. Not a crash simulation, structural inspection or safe-to-drive assessment. Independent validation has not been performed.' if dent else
                          ('Provisional demo from a user-stopped search. Matched controls and finalist repeats are incomplete. Training-distribution mapping and physical improvement remain unverified.' if provisional else
                           'Recorded forward-search candidate. Training-distribution mapping is unverified. Research gates: ' + ', '.join(result['decision']['failedChecks'])))},
            **({'syntheticDent': {'schemaVersion': 'zephyr.synthetic-dent.v1', 'scenarioSha256': scenario['scenarioSha256'],
                'preset': scenario['preset'], 'trainingDistributionVerified': False, 'structuralAssessment': False,
                'roadworthinessAssessment': False}} if dent else {'research': {'policyVersion': 'sedan-forward-study-v1', 'planSha256': e.plan_hash,
                'candidateRecordSha256': winner['recordSha256'], 'searchComplete': not provisional, 'confirmationCount': 0 if provisional else 3,
                **({'provisional': True, 'selectionSha256': result['selectionSha256'], 'phaseCounts': result['phaseCounts']} if provisional else {}),
                'numericalResearchPassed': result['decision']['numericalResearchPassed'], 'trainingDistributionVerified': False}}),
            'validation': {'geometry': 'passed', 'freshEvaluation': 'passed',
                'independentCfd': result.get('independentComparison', {}).get('status', 'not-run'),
                'evidenceIds': [rid+':baseline', rid+':candidate', e.plan_hash], 'checks': fresh_checks},
            'timings': timings}
        del runtime.domino; gc.collect(); torch.cuda.empty_cache()
        from zephyr.local.volume import predict_airflow
        payload['airflow'] = {'baseline': predict_airflow(original, origin, target / 'volume-baseline', 'drivaer-1'),
                              'candidate': predict_airflow(candidate, origin, target / 'volume-candidate', 'drivaer-1')}
        payload['airflowStatus'] = 'ready'; timings['totalSeconds'] = time.perf_counter()-started
        baseline_payload = deepcopy(payload)
        baseline_payload.update(status='analysis', candidate=None)
        baseline_payload['forces'].update(candidateN=None, candidateDragN=None, predictedDragN=None)
        baseline_payload['validation']['freshEvaluation'] = 'not-run'
        baseline_payload['airflow'] = {'baseline': payload['airflow']['baseline']}
        save(target / 'baseline.json', baseline_payload)
        save(target / 'result.json', payload)
        evidence = {k: v for k, v in payload.items() if k not in ('baseline', 'candidate')}
        evidence['artifacts'] = {p.name: {'sha256': _file_sha256(p), 'bytes': p.stat().st_size} for p in target.glob('*.vtk')}
        evidence['syntheticDentScenario' if dent else 'researchSummary'] = scenario if dent else result
        save(target / 'evidence.json', evidence)
        save(e.root / ('dent-replay.json' if dent else 'replay.json'), {'runId': rid, 'url': f'http://127.0.0.1:5173/?replay={rid}',
                                      'source': 'recorded', 'createdAt': utc()})
        print(f'Recorded sedan replay: http://127.0.0.1:5173/?replay={rid}', flush=True)


if __name__ == '__main__': main()
