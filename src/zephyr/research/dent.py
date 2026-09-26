"""A prescribed synthetic hood dent, never an impact or structural simulation."""
import numpy as np
from zephyr.artifacts import _file_sha256
from pathlib import Path
from zephyr.local.conversion import mesh_hash
from zephyr.research.runtime import digest, utc

PRESET = {'name': 'synthetic-hood-dent-v1', 'centreM': [0.0, .22, .74],
          'radiiM': [.34, .30, .25], 'depthMm': 12., 'direction': [0., 0., -1.],
          'profile': 'max(0, 1 - squared ellipsoid radius)^3',
          'scope': 'Prescribed geometric dent; not a crash, material, or structural simulation'}


def dent_mesh(morphs, *, depth_mm=12.):
    if isinstance(depth_mm, bool) or not np.isfinite(depth_mm) or not 0 < depth_mm <= 12:
        raise ValueError('Synthetic dent depth must be in (0, 12] mm')
    points = morphs.points
    q = (points - np.array(PRESET['centreM'])) / np.array(PRESET['radiiM'])
    weights = np.maximum(0., 1. - np.sum(q*q, axis=1)) ** 3
    weights[morphs.protected] = 0.
    if weights.max() <= 0:
        raise ValueError('Dent preset does not touch an editable surface')
    candidate = morphs.mesh.copy(deep=True)
    delta = weights[:, None] * np.array(PRESET['direction']) * depth_mm / 1000
    candidate.points = points + delta
    candidate.clear_data()
    return candidate


def prepare_dent(runtime, parent):
    candidate = dent_mesh(runtime.morphs)
    policy = {**parent.plan['policy'], 'maximumDisplacementMm': PRESET['depthMm']}
    checks = runtime.morphs.validate(candidate, policy, runtime.box)
    if not all(c['status'] == 'passed' for c in checks.values()):
        raise ValueError('Synthetic dent failed geometry screening: ' +
                         ', '.join(k for k, v in checks.items() if v['status'] != 'passed'))
    receipt = {'createdAt': utc(), 'preset': PRESET, 'parentPlanSha256': parent.plan_hash,
               'baselineMeshHash': mesh_hash(runtime.mesh), 'meshHash': mesh_hash(candidate),
               'checks': checks, 'sourceSha256': _file_sha256(Path(__file__)),
               'trainingDistributionVerified': False, 'engineeringValidated': False,
               'structuralAssessment': False, 'roadworthinessAssessment': False,
               'accepted': False}
    receipt['scenarioSha256'] = digest(receipt)
    return candidate, receipt
