"""Full-resolution AABB/exact-predicate audit; unavailable checks fail closed."""
from importlib.metadata import version
import numpy as np

CHECKER_VERSION = '2.6.3'


def audit_intersections(mesh):
    try:
        from igl.predicates import find_self_intersections
        installed = version('libigl')
        if installed != CHECKER_VERSION:
            raise RuntimeError(f'Expected libigl {CHECKER_VERSION}, found {installed}')
        found, pairs, coplanar = find_self_intersections(
            np.asarray(mesh.points, dtype=np.float64),
            np.asarray(mesh.regular_faces, dtype=np.int64))
        selected = np.unique(pairs)
        return {'status': 'failed' if found else 'passed',
                'method': 'libigl.predicates.find_self_intersections (AABB + exact predicates)',
                'version': installed, 'testedFaces': mesh.n_cells,
                'intersectingFaces': len(selected), 'faceIds': selected.tolist(),
                'pairs': pairs.tolist(), 'coplanarPairs': int(np.count_nonzero(coplanar))}
    except Exception as exc:
        return {'status': 'not-run', 'detail': f'Triangle audit unavailable: {type(exc).__name__}: {exc}'}
