"""One isolated CUDA process per job; structured events on stdout, artifacts on disk."""
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / '.local/physicsnemo-cfd/workflows/domino_design_sensitivities'
ASSETS = ROOT / '.local/domino-assets'


def emit(stage, detail, **extra):
    print('@ZEPHYR ' + json.dumps({'stage': stage, 'detail': detail, **extra}), flush=True)


def write_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def execute(job_dir):
    started = time.perf_counter()
    request = json.loads((job_dir / 'request.json').read_text())
    os.environ['WARP_CACHE_PATH'] = str(ROOT.parent / '.cache/warp')
    os.environ['LOCAL_CACHE'] = str(ROOT.parent / '.cache/physicsnemo')
    sys.path[:0] = [str(ROOT / 'scripts/windows_compat'), str(WORKFLOW)]
    emit('loading', 'Verifying pinned workflow and checkpoint bundle')
    from zephyr.artifacts import validate_bundle, bundle_ready, _file_sha256
    import subprocess
    pin = json.loads((ROOT / 'config/upstream-lock.json').read_text())['physicsnemo_cfd']['commit']
    actual = subprocess.check_output(['git', '-C', str(WORKFLOW), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != pin:
        raise ValueError('PhysicsNeMo-CFD commit does not match lock')
    dirty = subprocess.check_output(['git', '-C', str(WORKFLOW), 'diff', 'HEAD', '--', '.'], text=True).strip()
    if dirty:
        raise ValueError('Pinned upstream has tracked modifications')
    checks = validate_bundle(ROOT / 'config/domino-artifacts.json', ASSETS)
    if not bundle_ready(checks) or not all(c.checksum_matches for c in checks):
        raise ValueError('Checkpoint bundle failed SHA-256 verification')
    import numpy as np
    import pyvista as pv
    import torch
    from omegaconf import OmegaConf
    import main as upstream
    from zephyr.local.geometry import rear_basis, propose
    from zephyr.local.conversion import mesh_hash, display_mapping, surface, ROTATION
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required; no CPU or illustrative fallback')
    torch.cuda.set_per_process_memory_fraction(.9)
    cfg = OmegaConf.load(WORKFLOW / 'conf/config.yaml')
    training = OmegaConf.load(ASSETS / 'config.yaml')
    for key in ('bounding_box', 'bounding_box_surface'):
        if OmegaConf.to_container(cfg.data[key]) != OmegaConf.to_container(training.data[key]):
            raise ValueError('Inference bounding boxes differ from training bundle')
    mesh = pv.read(WORKFLOW / 'geometries/drivaer_1.stl')
    if not mesh.is_all_triangles or mesh.n_open_edges:
        raise ValueError('Official input must be triangular and watertight')
    emit('loading', 'Loading DoMINO.0.501.mdlus on ' + torch.cuda.get_device_name(0))
    domino = upstream.DoMINOInference(cfg=cfg, model_checkpoint_path=ASSETS / 'DoMINO.0.501.mdlus', device=torch.device('cuda'))
    phase = 'baseline'
    def progress(iterable, **kwargs):
        total = len(iterable)
        emit(phase, 'GPU forward + autograd batches', completed=0, total=total)
        for index, item in enumerate(iterable):
            yield item
            emit(phase, 'GPU forward + autograd batches', completed=index + 1, total=total)
    upstream.tqdm = progress  # Presentation hook only; pinned numerical code is unchanged.
    timings = {}
    def evaluate(target, name):
        nonlocal phase
        phase = name
        t = time.perf_counter()
        emit(name, 'Building geometry stencils and CUDA signed-distance inputs')
        results = domino(mesh=target, stream_velocity=38.889, air_density=1.205, stencil_size=7, verbose=False)
        torch.cuda.synchronize()
        for key, value in results.items():
            if not np.isfinite(value).all():
                raise ValueError('Non-finite DoMINO output: ' + key)
            if len(value) == target.n_cells:
                target.cell_data[key] = value
            elif len(value) == target.n_points:
                target.point_data[key] = value
        emit('smoothing', name + ': smoothing normal sensitivity (20 iterations)')
        for key, value in domino.postprocess_point_sensitivities(results=results, mesh=target).items():
            target[key] = value
        target.field_data['aerodynamic_force'] = results['aerodynamic_force']
        target.save(job_dir / (name + '.vtk'))
        timings[name + 'Seconds'] = time.perf_counter() - t
        return results['aerodynamic_force'].astype(float)
    force = evaluate(mesh, 'baseline')
    if force[0] <= 0:
        raise ValueError('Sample force convention changed: expected positive upstream Fx')
    emit('converting', 'Reducing display geometry; preserving full-resolution force evidence')
    ids, triangles, reduction = display_mapping(mesh)
    _, protected, _ = rear_basis(mesh.points)
    origin = np.array([(mesh.bounds[0] + mesh.bounds[1]) / 2, 0, mesh.bounds[4]])
    baseline, ranges = surface(mesh, ids, triangles, protected, origin)
    run_id = job_dir.name
    evidence_url = '/api/runs/' + run_id + '/evidence'
    payload = {'schemaVersion': 'zephyr.surface.v2', 'runId': run_id, 'source': 'live',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'status': 'analysis',
        'coordinates': {'units': 'm', 'up': '+Y', 'streamwise': '+X', 'handedness': 'right', 'fieldAssociation': 'vertex',
            'rotation': ROTATION.tolist(), 'upstreamOriginM': origin.tolist(), 'transform': '(upstream - origin) @ rotation.T'},
        'provenance': {'artifactVersion': 'domino-local-v1', 'modelVersion': 'DoMINO.0.501.mdlus',
            'checkpointSha256': checks[0].actual_sha256, 'bundle': [c.to_dict() for c in checks], 'upstreamCommit': pin,
            'workflowFilesSha256': {str(p.relative_to(WORKFLOW)): _file_sha256(p) for p in sorted(WORKFLOW.rglob('*.py'))},
            'meshHash': mesh_hash(mesh), 'inputStlSha256': _file_sha256(WORKFLOW / 'geometries/drivaer_1.stl'),
            'evidenceUrls': [evidence_url], 'solver': None, 'reduction': reduction,
            'fieldTransfer': 'Pressure/shear: area-weighted adjacent cells -> original points -> retained vertices. Sensitivity: upstream 20-step smoothed point field.',
            'sensitivityConvention': 'Upstream d(-Fx)/dX at geometry cell centroids; displayed smoothed normal projection, N/m. Drag D=Fx; the sensitivity ascends -drag.',
            'forceConvention': 'Upstream sum A*(p*n_inward - wallShear), n_inward=-VTK cell normal. Raw signed Fx > 0 on this sample; displayed drag D=Fx. Full source mesh, not reduced display mesh.',
            'fullResolutionRanges': ranges, 'gpu': torch.cuda.get_device_name(0)},
        'conditions': {'streamVelocityMps': [38.889, 0, 0], 'densityKgM3': 1.205},
        'baseline': baseline, 'candidate': None,
        'forces': {'baselineN': (force @ ROTATION.T).tolist(), 'candidateN': None, 'baselineDragN': float(force[0]), 'candidateDragN': None, 'predictedDragN': None},
        'constraints': {'maxDisplacementM': request['budgetMm'] / 1000, 'protectedRegion': 'Front 82% including cabin; underbody below z=0.05 m upstream'},
        'trust': {'decision': 'refuse', 'calibrated': False, 'predictionErrorPercent': None, 'reason': 'Analysis only; no candidate evaluated'},
        'validation': {'geometry': 'not-run', 'freshEvaluation': 'not-run', 'independentCfd': 'not-run', 'evidenceIds': [run_id + ':baseline'], 'checks': {}},
        'timings': timings}
    if request.get('intent'):
        payload['intent'] = request['intent']
    write_json(job_dir / 'baseline.json', payload)
    emit('baseline-ready', 'Real baseline fields ready', artifact='baseline')
    if request['mode'] == 'iteration':
        emit('candidate', 'Projecting smoothed sensitivity onto bounded rear-width handle')
        attempts = []
        for factor in (1, .5, .25, .125, .0625):
            candidate, protected, handle = propose(mesh, request['budgetMm'] / 1000 * factor)
            attempts.append(handle)
            invalid = any(v['status'] == 'failed' for v in handle['checks'].values())
            if not invalid:
                break
            emit('validate', f"Geometry gate refused {abs(handle['amplitudeM'])*1000:.3f} mm; shrinking the same handle")
        payload['handle'] = handle
        payload['attempts'] = attempts
        payload['validation']['checks'] = handle['checks']
        if invalid:
            payload['trust']['reason'] = 'Geometry checks failed; candidate not evaluated'
            payload['validation']['geometry'] = 'failed'
            emit('validate', payload['trust']['reason'])
        else:
            emit('validate', 'Topology, protected points, bounds, normals and watertightness passed; intersection audit pending')
            candidate_force = evaluate(candidate, 'evaluate')
            candidate_surface, candidate_ranges = surface(candidate, ids, triangles, protected, origin, mesh)
            payload['candidate'] = candidate_surface
            payload['status'] = 'comparison'
            payload['provenance']['candidateMeshHash'] = mesh_hash(candidate)
            payload['provenance']['candidateFullResolutionRanges'] = candidate_ranges
            drag = float(candidate_force[0])
            predicted = float(force[0]) + handle['predictedDragDeltaN']
            actual_delta = drag - float(force[0])
            error = abs(actual_delta - handle['predictedDragDeltaN']) / max(abs(handle['predictedDragDeltaN']), 1e-6) * 100
            payload['forces'].update(candidateN=(candidate_force @ ROTATION.T).tolist(), candidateDragN=drag, predictedDragN=predicted)
            reason = 'Fresh surrogate drag worsened; step refused.' if actual_delta >= 0 else 'Fresh surrogate drag decreased, but trust radius and triangle intersection audit are not validated; acceptance refused.'
            if candidate_force[0] <= 0:
                reason = 'Candidate signed force left expected convention; refused.'
            if len(attempts) > 1:
                reason = f"Geometry checks shrank {request['budgetMm']:.3f} to {abs(handle['amplitudeM'])*1000:.3f} mm. " + reason
            payload['trust'].update(reason=reason, predictionErrorPercent=error)
            payload['validation'].update(geometry='incomplete', freshEvaluation='passed')
            payload['validation']['evidenceIds'].append(run_id + ':candidate')
    timings['totalSeconds'] = time.perf_counter() - started
    payload['provenance']['peakCudaAllocatedBytes'] = torch.cuda.max_memory_allocated()
    write_json(job_dir / 'result.json', payload)
    evidence = {k: v for k, v in payload.items() if k not in ('baseline', 'candidate')}
    evidence['artifacts'] = {p.name: {'sha256': _file_sha256(p), 'bytes': p.stat().st_size} for p in job_dir.glob('*.vtk')}
    write_json(job_dir / 'evidence.json', evidence)
    emit('complete', payload['trust']['reason'], artifact='result', elapsedSeconds=timings['totalSeconds'])


if __name__ == '__main__':
    try:
        from zephyr.local.locks import acquire_lock
        directory = Path(sys.argv[1]).resolve()
        # Even if the API crashes, this process owns its own GPU lease.
        with acquire_lock(directory.parent / 'worker-gpu.lock'):
            execute(directory)
    except Exception as exc:
        emit('failed', str(exc))
        raise
