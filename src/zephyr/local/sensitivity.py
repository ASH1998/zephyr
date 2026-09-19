"""Audited adapter for the pinned upstream partial geometry gradient.

The upstream batch loop reuses a leaf tensor and adds its cumulative .grad
after every batch. Resetting that leaf before each forward counts each batch
once. This does NOT turn the partial derivative into a total mesh derivative:
SDFs, query locations, normals, areas and neighborhoods are separate inputs.
"""
from contextlib import contextmanager
import numpy as np

ADAPTER_VERSION = 'fresh-normals-batch-reset-v1'


@contextmanager
def independent_batch_gradients(model):
    def reset(_module, args):
        args[0]['geometry_coordinates'].grad = None
    hook = model.register_forward_pre_hook(reset)
    try:
        yield
    finally:
        hook.remove()


def evaluate_surface(domino, mesh, **kwargs):
    # Use the same geometry precision and freshly computed normals for baseline,
    # probes and candidate. Imported arrays otherwise survive a points edit.
    mesh.points = np.asarray(mesh.points, dtype=np.float64)
    for data in (mesh.cell_data, mesh.point_data):
        if 'Normals' in data:
            del data['Normals']
    with independent_batch_gradients(domino.model):
        return domino(mesh=mesh, **kwargs)
