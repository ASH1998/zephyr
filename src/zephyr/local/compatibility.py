"""Distinguish valid runtime inputs from the checkpoint's training envelope."""
import numpy as np


def check_surface_input(mesh, box, *, experimental):
    points = np.asarray(mesh.points)
    if not mesh.is_all_triangles or mesh.n_open_edges or not np.isfinite(points).all():
        raise ValueError('DoMINO requires finite triangular watertight surface inputs')
    inside = bool(np.all(points >= np.asarray(box['min'])) and np.all(points <= np.asarray(box['max'])))
    if not inside and not experimental:
        raise ValueError('Geometry exceeds the pinned DoMINO surface training bounds')
    return {'status': 'input-checked' if inside else 'experimental-outside-training-bounds',
            'withinTrainingBounds': inside, 'surfaceBoundsM': box,
            'units': 'm', 'axes': 'upstream X streamwise, Z up',
            'topology': 'fixed triangular watertight',
            'scope': 'Input and runtime compatibility only; predictive accuracy requires independent validation.'}
