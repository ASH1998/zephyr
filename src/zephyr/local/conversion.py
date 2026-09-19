"""Explicit full-mesh -> display-mesh conversion. Never integrate display fields."""
from hashlib import sha256
import numpy as np
from scipy.spatial import cKDTree
import pyvista as pv

# Proper rotation (det +1): upstream X/Y/Z -> viewer X/Z/-Y.
ROTATION = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)


def mesh_hash(mesh):
    h = sha256()
    h.update(np.asarray(mesh.points, dtype='<f8').tobytes())
    h.update(np.asarray(mesh.faces, dtype='<i8').tobytes())
    return h.hexdigest()


def display_mapping(mesh, limit=120000):
    if not 3 <= limit <= 200000:
        raise ValueError('Invalid browser vertex limit')
    if not mesh.is_all_triangles:
        raise ValueError('Only triangular surfaces supported')
    if mesh.n_points <= limit:
        return np.arange(mesh.n_points), mesh.faces.reshape(-1, 4)[:, 1:], {'method': 'identity'}
    geometry = pv.PolyData(mesh.points, mesh.faces)
    reduced = geometry.decimate_pro(1 - (limit * .92 / mesh.n_points), preserve_topology=True,
        splitting=False, boundary_vertex_deletion=False)
    if reduced.n_points > limit:
        raise ValueError('Topology-preserving display reduction exceeds vertex cap')
    distance, ids = cKDTree(mesh.points).query(reduced.points)
    if distance.max() > 1e-9:
        raise ValueError('Reduction moved retained vertices; mapping would be ambiguous')
    return ids, reduced.faces.reshape(-1, 4)[:, 1:], {'method': 'VTK DecimatePro; preserve topology; retained original vertices',
        'sourceVertices': mesh.n_points, 'sourceTriangles': mesh.n_cells, 'displayVertices': reduced.n_points,
        'displayTriangles': reduced.n_cells, 'maximumRetainedPointErrorM': float(distance.max()),
        'mapSha256': sha256(np.asarray(ids, dtype='<i8').tobytes()).hexdigest(),
        'limitation': 'Display approximation. Small features/extrema can be omitted; forces use every original cell.'}


def cell_to_point(mesh, values):
    """Area-weighted adjacent-cell interpolation, not unweighted VTK averaging."""
    values = np.asarray(values, dtype=float)
    faces = mesh.faces.reshape(-1, 4)[:, 1:]
    tri = mesh.points[faces]
    areas = np.linalg.norm(np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]), axis=1) / 2
    out = np.zeros((mesh.n_points,) + values.shape[1:])
    weights = np.zeros(mesh.n_points)
    weighted = values * areas.reshape((-1,) + (1,) * (values.ndim - 1))
    for k in range(3):
        np.add.at(out, faces[:, k], weighted)
        np.add.at(weights, faces[:, k], areas)
    if np.any(weights <= 0):
        raise ValueError('Isolated/zero-area vertices')
    return out / weights.reshape((-1,) + (1,) * (values.ndim - 1))


def surface(mesh, ids, triangles, protected, origin, baseline=None):
    fields = {
        'pressurePa': cell_to_point(mesh, mesh.cell_data['pred_surf_pressure']),
        'wallShearPa': cell_to_point(mesh, mesh.cell_data['pred_surf_wall_shear_stress']) @ ROTATION.T,
        'sensitivity': np.asarray(mesh.point_data['smooth_sensitivity_point']) @ ROTATION.T,
        'normalSensitivity': np.asarray(mesh.point_data['smooth_sensitivity_normal_point']),
        'positions': (np.asarray(mesh.points, dtype=float) - origin) @ ROTATION.T,
        'protectedMask': np.asarray(protected, dtype=int),
        'displacementM': np.zeros(mesh.n_points) if baseline is None else np.linalg.norm(mesh.points-baseline.points, axis=1)}
    if any(not np.isfinite(v).all() for v in fields.values()):
        raise ValueError('Non-finite model/geometry field')
    result = {key: value[ids].reshape(-1).tolist() for key, value in fields.items()}
    result['triangles'] = triangles.reshape(-1).tolist()
    ranges = {key: [float(np.min(value)), float(np.max(value))] for key, value in fields.items() if key in ('pressurePa', 'normalSensitivity')}
    return result, ranges
