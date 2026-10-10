"""Exclusive local GPU runtime with pinned assets and source provenance."""
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from zephyr.artifacts import _file_sha256, validate_bundle, bundle_ready
from zephyr.local.worker import ROOT, WORKFLOW, ASSETS
from zephyr.local.locks import acquire_lock


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def save(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_bytes(canonical(value))
    temp.replace(path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def source_hashes():
    sources = [Path(__file__), Path(__file__).with_name('policy.py'), Path(__file__).with_name('morphs.py')]
    sources += [ROOT / 'src/zephyr/local' / n for n in
                ('forward.py', 'sensitivity.py', 'intersections.py', 'conversion.py', 'compatibility.py')]
    return {str(p.relative_to(ROOT)): _file_sha256(p) for p in sources}


class Runtime:
    def __enter__(self):
        self.stack = ExitStack()
        try:
            locks = ROOT / '.local/runs'
            locks.mkdir(parents=True, exist_ok=True)
            for name in ('gpu.lock', 'worker-gpu.lock'):
                self.stack.enter_context(acquire_lock(locks / name))
            self._load()
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *args):
        self.stack.close()

    def _load(self):
        pin = json.loads((ROOT / 'config/upstream-lock.json').read_text())['physicsnemo_cfd']['commit']
        actual = subprocess.check_output(['git', '-C', str(WORKFLOW), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(WORKFLOW), 'diff', 'HEAD', '--', '.'], text=True).strip()
        if actual != pin or dirty:
            raise ValueError('Pinned upstream mismatch')
        checks = validate_bundle(ROOT / 'config/domino-artifacts.json', ASSETS)
        if not bundle_ready(checks) or not all(c.checksum_matches for c in checks):
            raise ValueError('Checkpoint checksum mismatch')
        os.environ['WARP_CACHE_PATH'] = str(ROOT.parent / '.cache/warp')
        os.environ['LOCAL_CACHE'] = str(ROOT.parent / '.cache/physicsnemo')
        sys.path[:0] = [str(ROOT / 'scripts/windows_compat'), str(WORKFLOW)]
        import torch
        import pyvista as pv
        from omegaconf import OmegaConf
        import main as upstream
        import physicsnemo.models.domino.model as model_module
        from zephyr.local.cars import mesh_path
        from zephyr.local.conversion import mesh_hash
        from zephyr.research.morphs import SedanMorphs
        if not torch.cuda.is_available():
            raise RuntimeError('Local CUDA required; no synthetic fallback')
        cfg, training = OmegaConf.load(WORKFLOW / 'conf/config.yaml'), OmegaConf.load(ASSETS / 'config.yaml')
        for key in ('bounding_box', 'bounding_box_surface'):
            if OmegaConf.to_container(cfg.data[key]) != OmegaConf.to_container(training.data[key]):
                raise ValueError('Bounding box mismatch')
        self.box = OmegaConf.to_container(training.data.bounding_box_surface)
        self.mesh = pv.read(mesh_path('drivaer-1'))
        self.mesh.points = self.mesh.points.astype('float64')
        self.morphs = SedanMorphs(self.mesh)
        self.provenance = {'sources': source_hashes(), 'upstreamCommit': pin,
                           'checkpointSha256': checks[0].actual_sha256,
                           'installedModelSha256': _file_sha256(Path(model_module.__file__)),
                           'inputSha256': _file_sha256(mesh_path('drivaer-1')),
                           'meshHash': mesh_hash(self.mesh), 'gpu': torch.cuda.get_device_name(0),
                           'fragileTriangleProtection': self.morphs.fragile_regions,
                           'torch': torch.__version__, 'cuda': torch.version.cuda}
        torch.cuda.set_per_process_memory_fraction(.9)
        self.domino = upstream.DoMINOInference(cfg=cfg, model_checkpoint_path=ASSETS / 'DoMINO.0.501.mdlus', device=torch.device('cuda'))

    def evaluate(self, mesh, conditions):
        import numpy as np
        from zephyr.local.forward import evaluate_forward
        profile = {}
        result = evaluate_forward(self.domino, mesh, stream_velocity=conditions['velocityMps'],
                                  air_density=conditions['densityKgM3'], profile=profile)
        if any(not np.isfinite(v).all() for v in result.values()):
            raise ValueError('Nonfinite model output')
        force = result['aerodynamic_force'].astype(float)
        if force[0] <= 0:
            raise ValueError('Unexpected drag force sign')
        return force.tolist(), result, profile


class Evidence:
    """Hash-bound plan and individually atomic records, including rejected proposals."""
    def __init__(self, directory):
        self.root = Path(directory)
        self.plan = json.loads((self.root / 'plan.json').read_text())
        self.plan_hash = (self.root / 'plan.sha256').read_text().strip()
        if digest(self.plan) != self.plan_hash:
            raise ValueError('Frozen plan has changed; use a new study')

    def records(self):
        records = []
        for path in sorted((self.root / 'records').glob('*.json')):
            row = json.loads(path.read_text())
            expected = row.pop('recordSha256')
            if digest(row) != expected or row['planSha256'] != self.plan_hash:
                raise ValueError('Evidence integrity failure: ' + path.name)
            row['recordSha256'] = expected
            records.append(row)
        return records

    def append(self, row):
        row = {**row, 'planSha256': self.plan_hash}
        row['recordSha256'] = digest(row)
        path = self.root / 'records' / (row['id'] + '.json')
        if path.exists():
            raise ValueError('Evidence cannot be overwritten')
        save(path, row)
        return row


def evaluate_candidate(runtime, evidence, identifier, arm, parameters, *, micro=False, save_fields=False):
    from zephyr.local.conversion import mesh_hash
    from zephyr.research.morphs import domain_check
    started = time.perf_counter()
    target = runtime.morphs.deform(parameters, allow_micro=micro)
    checks = runtime.morphs.validate(target, evidence.plan['policy'], runtime.box)
    row = {'id': identifier, 'arm': arm, 'parametersMm': parameters, 'createdAt': utc(),
           'meshHash': mesh_hash(target), 'checks': checks, 'domain': domain_check(parameters),
           'provenance': runtime.provenance, 'status': 'geometry-refused'}
    if all(c['status'] == 'passed' for c in checks.values()):
        try:
            force, result, profile = runtime.evaluate(target, evidence.plan['policy']['conditions'])
            row.update(status='evaluated', forceN=force, dragN=force[0], profile=profile)
            if save_fields:
                for key in ('pred_surf_pressure', 'pred_surf_wall_shear_stress'):
                    target.cell_data[key] = result[key]
                target.field_data['aerodynamic_force'] = force
                path = evidence.root / 'meshes' / (identifier + '.vtk')
                target.save(path)
                row['artifact'] = {'path': str(path.relative_to(evidence.root)), 'sha256': _file_sha256(path)}
        except Exception as exc:
            row.update(status='evaluation-failed', errorType=type(exc).__name__)
            row['seconds'] = time.perf_counter() - started
            evidence.append(row)
            raise
    row['seconds'] = time.perf_counter() - started
    evidence.append(row)
    print(json.dumps({'id': identifier, 'arm': arm, 'status': row['status'],
                      'dragN': row.get('dragN'), 'seconds': round(row['seconds'], 2)}), flush=True)
    return row
