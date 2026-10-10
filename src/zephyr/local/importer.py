"""Deterministic, bounded surface preparation. Catalog mode preserves the original recipe."""
from __future__ import annotations

from io import BytesIO
import json
import math

MAX_BYTES = 50 * 1024 * 1024
MAX_TRIANGLES = 2_000_000
MESH_EXTENSIONS = {'.stl', '.obj', '.glb', '.gltf', '.ply'}
PITCH = .035
# Conservative demo screening, NOT a measured DrivAerML training-distribution boundary.
RANGE_POLICY = {'version': 'zephyr.import-range.v1', 'referenceDimensionsM': [4.61, 1.79, 1.42],
    'lengthM': [3.5, 5.2], 'widthM': [1.5, 2.1], 'heightM': [1.15, 1.75],
    'heightLength': [.24, .37], 'widthLength': [.32, .46],
    'limitation': 'Conservative sedan-like demo envelope; parameter-spread validation remains pending.'}


def training_range(dimensions, body_type=None):
    length, width, height = map(float, dimensions)
    if not all(math.isfinite(v) and v > 0 for v in (length, width, height)):
        raise ValueError('Geometry must have three finite positive dimensions')
    values = dict(lengthM=length, widthM=width, heightM=height,
                  heightLength=height / length, widthLength=width / length)
    failures = [key for key, value in values.items() if not RANGE_POLICY[key][0] <= value <= RANGE_POLICY[key][1]]
    if body_type in ('pickup', 'open-wheel', 'van', 'suv', 'other'):
        failures.append('body type')
    return {'policy': RANGE_POLICY, 'values': values, 'support': 'baseline-only' if failures else 'shape-tests',
            'reason': 'Outside conservative sedan-like limits: ' + ', '.join(failures) if failures
            else 'Within conservative sedan-like limits; shape tests remain experimental.'}


def validate_options(options):
    if not isinstance(options, dict) or set(options) - {'rotation', 'flipFront', 'lengthM'}:
        raise ValueError('Use rotation, flipFront and lengthM only')
    rotation = options.get('rotation', [0, 0, 0])
    if not isinstance(rotation, list) or len(rotation) != 3 or any(type(v) is not int or v not in (0, 90, 180, 270) for v in rotation):
        raise ValueError('Rotation must contain three quarter-turn angles')
    if type(options.get('flipFront', False)) is not bool:
        raise ValueError('flipFront must be true or false')
    length = options.get('lengthM')
    if length is not None and (type(length) not in (int, float) or not math.isfinite(length) or not 2.5 <= length <= 7):
        raise ValueError('Car length must be 2.5–7 metres')
    return {'rotation': rotation, 'flipFront': options.get('flipFront', False), 'lengthM': length}


def load_mesh(data, extension):
    """Load only in-memory geometry: external GLTF buffers and OBJ materials cannot resolve."""
    import numpy as np
    import trimesh
    if extension not in MESH_EXTENSIONS:
        raise ValueError('Choose STL, OBJ, GLB, embedded GLTF or PLY')
    if not 0 < len(data) <= MAX_BYTES:
        raise ValueError('Mesh must be between 1 byte and 50 MB')
    if extension == '.gltf':
        try:
            doc = json.loads(data)
            if any(not item.get('uri', '').startswith('data:') for item in doc.get('buffers', [])):
                raise ValueError('GLTF must embed its buffers; export as GLB for a single-file upload')
        except (UnicodeError, json.JSONDecodeError, AttributeError, TypeError) as exc:
            raise ValueError('Invalid embedded GLTF') from exc
    try:
        mesh = trimesh.load(BytesIO(data), file_type=extension[1:], force='mesh',
                            resolver={}, skip_materials=True)
    except Exception as exc:
        raise ValueError('Could not read this mesh. Export a single-file triangle mesh and retry.') from exc
    if not isinstance(mesh, trimesh.Trimesh) or not 4 <= len(mesh.faces) <= MAX_TRIANGLES:
        raise ValueError('Mesh must contain 4–2,000,000 triangles')
    if not np.isfinite(mesh.vertices).all() or np.any(mesh.extents <= 0):
        raise ValueError('Mesh must have finite vertices and three nonzero dimensions')
    return mesh


def orient_mesh(mesh, extension, options):
    import numpy as np
    import trimesh
    options = validate_options(options)
    mesh = mesh.copy()
    extent = float(max(mesh.extents))
    units, scale = ('mm', .001) if extent > 100 else ('cm', .01) if extent > 10 else ('m', 1.)
    if options['lengthM'] is not None:
        scale = options['lengthM'] / extent
    mesh.apply_scale(scale)
    # Canonical viewer coordinates are X length, Y up, Z width.
    up = 1 if extension in ('.glb', '.gltf', '.obj') else 2
    longest = int(np.argmax(mesh.extents))
    if longest == up:
        up = min((i for i in range(3) if i != longest), key=lambda i: mesh.extents[i])
    remaining = next(i for i in range(3) if i not in (longest, up))
    matrix = np.eye(3)[[longest, up, remaining]]
    if np.linalg.det(matrix) < 0:
        matrix[2] *= -1
    transform = np.eye(4); transform[:3, :3] = matrix
    mesh.apply_transform(transform)
    for axis, angle in zip(np.eye(3), options['rotation']):
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle), axis))
    if options['flipFront']:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]))
    if options['lengthM'] is not None:
        correction = options['lengthM'] / mesh.extents[0]
        mesh.apply_scale(correction); scale *= correction
    dims = mesh.extents[[0, 2, 1]]
    if not 2.5 <= dims[0] <= 7 or not .5 <= dims[1] <= 3 or not .4 <= dims[2] <= 3.5:
        raise ValueError('Check orientation and length: expected L 2.5–7 m, W 0.5–3 m, H 0.4–3.5 m')
    return mesh, {'unitsGuess': units, 'scale': float(scale), 'automaticRotation': matrix.tolist(),
                  **options, 'dimensionsM': dims.tolist()}


def prepare_surface(mesh, options=None, *, geometry_id='import-preview', catalog=False):
    """Input is a visual mesh in X-length/Y-up coordinates, in metres."""
    import numpy as np
    import pyvista as pv
    from scipy import ndimage
    from zephyr.local.conversion import ROTATION, mesh_hash
    from zephyr.local.geometry import rear_basis, body_basis, BODY_HANDLES
    options = options or {}
    if not catalog:
        dims = np.asarray(mesh.extents)
        if not np.isfinite(mesh.vertices).all() or len(mesh.faces) > MAX_TRIANGLES or np.prod(np.ceil(dims / PITCH) + 8) > 8_000_000:
            raise ValueError('Geometry exceeds the bounded preparation grid')
    vox = mesh.voxelized(PITCH); matrix = np.pad(vox.matrix, 3)
    closed = ndimage.binary_closing(matrix, iterations=2)
    solid = ndimage.binary_fill_holes(closed)
    if not catalog:
        # A substantially open shell stays hollow after closing. Do not quietly turn it into a plate.
        if not mesh.is_watertight and np.count_nonzero(solid) < 1.15 * np.count_nonzero(closed):
            raise ValueError('Large holes remain in the mesh. Close the body shell before uploading.')
        labels, count = ndimage.label(solid)
        if count > 1:
            merged = ndimage.binary_fill_holes(ndimage.binary_closing(solid, iterations=2))
            labels, count = ndimage.label(merged)
            sizes = np.bincount(labels.ravel()); sizes[0] = 0
            if count > 1 and np.partition(sizes, -2)[-2] >= 8:
                raise ValueError('Disconnected parts are more than two voxels apart; connect the wheels/body and retry')
            solid = merged
    grid = pv.ImageData(dimensions=solid.shape, spacing=(PITCH,) * 3, origin=vox.translation - 3 * PITCH)
    grid.point_data['solid'] = ndimage.gaussian_filter(solid.astype(float), .65).ravel(order='F')
    model = grid.contour([.5], scalars='solid').extract_largest().triangulate().clean(tolerance=1e-7, absolute=True)
    if not model.n_points:
        raise ValueError('No closed surface could be recovered; check the mesh and units')
    model = model.smooth(n_iter=12, relaxation_factor=.08, boundary_smoothing=False)
    reduced = model.decimate_pro(max(0, 1 - 18000 / model.n_points), preserve_topology=True,
                                splitting=False, boundary_vertex_deletion=False)
    if reduced.n_open_edges == 0:
        model = reduced
    ground = float(model.points[:, 1].min()); center = float((model.bounds[0] + model.bounds[1]) / 2)
    side = float((model.bounds[4] + model.bounds[5]) / 2)
    display = model.points - np.array([center, ground, side])
    upstream = display @ ROTATION
    upstream[:, 0] += .5 * (display[:, 0].max() - display[:, 0].min()) - .8
    upstream[:, 2] -= .32
    model.points = upstream
    model = model.compute_normals(auto_orient_normals=True, consistent_normals=True, split_vertices=False)
    if model.n_open_edges or not model.n_cells or (not catalog and model.n_points > 120000):
        raise ValueError('Could not produce a closed surface within the browser vertex limit')
    origin = np.array([(model.bounds[0] + model.bounds[1]) / 2, 0, model.bounds[4]])
    _, protected, _ = rear_basis(model.points)
    preview = {'schemaVersion': 'zephyr.geometry-preview.v1', 'geometryId': geometry_id, 'units': 'm',
        'meshHash': mesh_hash(model), 'positions': np.round((model.points - origin) @ ROTATION.T, 6).ravel().tolist(),
        'triangles': model.faces.reshape(-1, 4)[:, 1:].ravel().tolist(), 'protectedMask': protected.astype(int).tolist()}
    report = {'schemaVersion': 'zephyr.import-report.v1', 'meshHash': preview['meshHash'],
        'steps': ['voxelize-35mm', 'close-2-voxels', 'fill-holes', 'contour', 'smooth', 'decimate', 'align'],
        'thinFeatureWarning': 'Features thinner than 70 mm may be lost. This closed proxy is experimental.',
        'visualOffset': [-center, -ground, -side], 'vertices': model.n_points, 'triangles': model.n_cells}
    if not catalog:
        preview['regionMasks'] = {h: (body_basis(model.points, h)[1] if not h.startswith('rear-') else rear_basis(model.points, h)[1]).astype(int).tolist() for h in BODY_HANDLES}
        report['trainingRange'] = training_range(np.ptp(model.points, axis=0))
    return model, preview, report
