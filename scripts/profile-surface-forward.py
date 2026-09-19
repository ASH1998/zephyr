"""Opt-in fresh GPU comparison of upstream gradients and probe forward paths."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--live', action='store_true')
parser.add_argument('--geometry', choices=['drivaer-1', 'hatchback'], required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not args.live:
    parser.error('GPU inference requires --live')

from zephyr.local.worker import WORKFLOW, ASSETS
from zephyr.local.locks import acquire_lock
from zephyr.artifacts import validate_bundle, bundle_ready, _file_sha256

with ExitStack() as stack:
    for name in ('gpu.lock', 'worker-gpu.lock'):
        stack.enter_context(acquire_lock(ROOT / '.local/runs' / name))
    pin = json.loads((ROOT / 'config/upstream-lock.json').read_text())['physicsnemo_cfd']['commit']
    actual = subprocess.check_output(['git', '-C', str(WORKFLOW), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(WORKFLOW), 'diff', 'HEAD', '--', '.'], text=True).strip()
    if actual != pin or dirty:
        raise ValueError('Pinned upstream mismatch or modification')
    checks = validate_bundle(ROOT / 'config/domino-artifacts.json', ASSETS)
    if not bundle_ready(checks) or not all(c.checksum_matches for c in checks):
        raise ValueError('Checkpoint bundle failed SHA-256 verification')
    os.environ['WARP_CACHE_PATH'] = str(ROOT.parent / '.cache/warp')
    os.environ['LOCAL_CACHE'] = str(ROOT.parent / '.cache/physicsnemo')
    sys.path[:0] = [str(ROOT / 'scripts/windows_compat'), str(WORKFLOW)]
    import numpy as np
    import pyvista as pv
    import torch
    from omegaconf import OmegaConf
    import main as upstream
    import physicsnemo.models.domino.model as model_module
    from zephyr.local.cars import mesh_path
    from zephyr.local.sensitivity import evaluate_surface
    from zephyr.local.forward import evaluate_forward
    cfg = OmegaConf.load(WORKFLOW / 'conf/config.yaml')
    training = OmegaConf.load(ASSETS / 'config.yaml')
    for key in ('bounding_box', 'bounding_box_surface'):
        if OmegaConf.to_container(cfg.data[key]) != OmegaConf.to_container(training.data[key]):
            raise ValueError('Bounding box mismatch')
    torch.cuda.set_per_process_memory_fraction(.9)
    domino = upstream.DoMINOInference(cfg=cfg, model_checkpoint_path=ASSETS / 'DoMINO.0.501.mdlus', device=torch.device('cuda'))
    report = {'geometry': args.geometry, 'upstreamCommit': pin,
              'checkpointSha256': checks[0].actual_sha256,
              'installedModelSha256': _file_sha256(Path(model_module.__file__)),
              'localNumericsSha256': {name: _file_sha256(ROOT / 'src/zephyr/local' / name)
                                      for name in ('sensitivity.py', 'forward.py', 'trust.py')}, 'evaluations': {}}
    reference = None
    for method in ('autograd', 'forward', 'forward-reuse'):
        print('Profiling ' + method, flush=True)
        mesh = pv.read(mesh_path(args.geometry))
        profile = {}
        torch.cuda.synchronize()
        started = time.perf_counter()
        if method == 'autograd':
            result = evaluate_surface(domino, mesh)
        else:
            result = evaluate_forward(domino, mesh, reuse_geometry=method == 'forward-reuse', profile=profile)
        torch.cuda.synchronize()
        profile['wallSeconds'] = time.perf_counter() - started
        profile['forceN'] = result['aerodynamic_force'].astype(float).tolist()
        if reference is None:
            reference = result
        else:
            parity = {}
            for key in ('geometry_coordinates', 'pred_surf_pressure', 'pred_surf_wall_shear_stress', 'aerodynamic_force'):
                left, right = reference[key], result[key]
                tolerance = 32 * np.finfo(np.float32).eps * np.maximum(np.abs(left), 1.)
                passed = (np.array_equal(left, right) if key == 'geometry_coordinates' else
                          bool(np.all(np.abs(left - right) <= tolerance)) if key == 'aerodynamic_force' else
                          bool(np.allclose(left, right, rtol=1e-6, atol=1e-5)))
                parity[key] = {'passed': passed, 'maxAbsoluteDifference': float(np.max(np.abs(left - right)))}
            profile['parity'] = parity
        report['evaluations'][method] = profile
        print(json.dumps({method: profile}), flush=True)
    report['passed'] = all(p['passed'] for e in report['evaluations'].values() for p in e.get('parity', {}).values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    if not report['passed']:
        raise SystemExit('Forward parity failed; inspect report')
