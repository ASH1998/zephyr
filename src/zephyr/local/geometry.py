"""Fixed-topology rear-width handle. No learned or raw-vertex controller."""
import numpy as np


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t ** 3 * (10 - 15 * t + 6 * t ** 2)


def rear_basis(points):
    p = np.asarray(points, dtype=np.float64)
    lo, hi = p.min(axis=0), p.max(axis=0)
    # Conservatively lock the front 82% (including the whole greenhouse),
    # underbody, and wheels. Rear width varies smoothly; x and z never move.
    start = lo[0] + .82 * (hi[0] - lo[0])
    weight = smoothstep((p[:, 0] - start) / (hi[0] - start))
    weight *= smoothstep((p[:, 2] - .05) / .25)
    basis = np.zeros_like(p)
    basis[:, 1] = -p[:, 1] * weight
    scale = np.abs(basis).max()
    if scale == 0:
        raise ValueError('Rear handle has no support')
    basis /= scale
    return basis, weight == 0, {'rearStartXMetres': float(start), 'heightStartMetres': .05,
        'heightTransitionMetres': .25, 'lateralNormalizationMetres': float(scale)}


def deform(mesh, amplitude_m, budget_m):
    """Apply a signed handle in metres, independent of a sensitivity field."""
    if not np.isfinite(budget_m) or not 0 < budget_m <= .004:
        raise ValueError('Displacement must be within (0, 4] mm')
    if not np.isfinite(amplitude_m) or abs(amplitude_m) > budget_m:
        raise ValueError('Signed handle amplitude exceeds displacement budget')
    basis, protected, definition = rear_basis(mesh.points)
    candidate = mesh.copy(deep=True)
    candidate.points = np.asarray(mesh.points, dtype=np.float64) + amplitude_m * basis
    candidate.points[protected] = mesh.points[protected]
    # Imported explicit normals, when present, no longer describe the new mesh.
    for data in (candidate.cell_data, candidate.point_data):
        if 'Normals' in data:
            del data['Normals']
    return candidate, protected, definition


def propose(mesh, budget_m, *, slope_n_per_m=None):
    basis, _, _ = rear_basis(mesh.points)
    faces = mesh.faces.reshape(-1, 4)[:, 1:]
    cell_basis = basis[faces].mean(axis=1)
    # Upstream g = d(-Fx)/d(cell-centroid). For this sample D = Fx,
    # so ASCEND g. Smoothing chooses the handle direction; raw g predicts.
    projection = float(np.sum(mesh.cell_data['smooth_sensitivity_cell'] * cell_basis))
    if slope_n_per_m is not None and not np.isfinite(slope_n_per_m):
        raise ValueError('Handle slope must be finite')
    amplitude = (np.sign(projection) if slope_n_per_m is None else -np.sign(slope_n_per_m)) * budget_m
    candidate, protected, definition = deform(mesh, amplitude, budget_m)
    displacement = candidate.points - mesh.points
    partial_delta = -float(np.sum(mesh.cell_data['geometry_sensitivity'] * displacement[faces].mean(axis=1)))
    predicted_delta = partial_delta if slope_n_per_m is None else float(slope_n_per_m * amplitude)
    checks = validate_geometry(mesh, candidate, protected, budget_m)
    # The continuum y -> y*(1-a*w(x,z)) is smooth, symmetric and injective.
    # Its discrete triangular approximation still needs an intersection audit.
    checks['symmetricHandle'] = {'status': 'passed', 'detail': 'x,z unchanged; odd lateral displacement about y=0. Input asymmetry is preserved.'}
    checks['transition'] = {'status': 'passed', 'detail': 'Quintic C2 transition; exactly zero on protected boundary.'}
    checks['selfIntersection'] = {'status': 'not-run', 'detail': 'Full triangle intersection audit unavailable; candidate cannot be accepted.'}
    return candidate, protected, {'handle': 'rear-width-quintic-v1', 'definition': definition,
        'amplitudeM': float(amplitude), 'smoothedProjectionNPerM': projection,
        'predictedDragDeltaN': predicted_delta, 'partialGradientDragDeltaN': partial_delta,
        'predictionMethod': 'partial-geometry-gradient' if slope_n_per_m is None else 'central-finite-difference',
        'checks': checks}


def validate_geometry(baseline, candidate, protected, budget_m):
    same = np.array_equal(baseline.faces, candidate.faces) and baseline.n_points == candidate.n_points
    if not same:
        return {'topology': {'status': 'failed'}}
    a, b = np.asarray(baseline.points), np.asarray(candidate.points)
    d = np.linalg.norm(b - a, axis=1)
    faces = baseline.faces.reshape(-1, 4)[:, 1:]
    def normals(p):
        t = p[faces]
        return np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    na, nb = normals(a), normals(b)
    area_a, area_b = np.linalg.norm(na, axis=1), np.linalg.norm(nb, axis=1)
    nonzero = (area_a > 1e-14) & (area_b > 1e-14)
    cos = np.sum(na * nb, axis=1) / np.maximum(area_a * area_b, 1e-30)
    ratio = area_b / np.maximum(area_a, 1e-30)
    def check(ok, **extra):
        return {'status': 'passed' if bool(ok) else 'failed', **extra}
    return {'topology': check(same), 'finite': check(np.isfinite(b).all()),
        'protected': check(np.array_equal(a[protected], b[protected]), vertices=int(protected.sum())),
        'bounds': check(d.max() <= budget_m + 1e-12, maximumM=float(d.max())),
        'normals': check(np.all(nonzero) and np.all(cos > .99), minimumCosine=float(cos.min())),
        'triangleArea': check(np.all(nonzero) and np.all((ratio > .8) & (ratio < 1.2)), minimumRatio=float(ratio.min()), maximumRatio=float(ratio.max())),
        'watertight': check(baseline.n_open_edges == 0 and candidate.n_open_edges == 0,
            baselineOpenEdges=baseline.n_open_edges, candidateOpenEdges=candidate.n_open_edges)}
