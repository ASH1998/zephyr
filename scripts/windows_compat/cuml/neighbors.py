"""CPU k-NN fallback for the one cuML call used by DoMINO preprocessing.

RAPIDS cuML does not publish native-Windows wheels.  NVIDIA's design
sensitivity workflow only uses ``cuml.neighbors.NearestNeighbors`` while
building a fixed surface stencil; model inference and autograd remain on CUDA.
"""

from sklearn.neighbors import NearestNeighbors as _SklearnNearestNeighbors


class NearestNeighbors(_SklearnNearestNeighbors):
    """Translate cuML's ``rbc`` choice to scikit-learn's automatic backend."""

    def __init__(self, n_neighbors: int = 5, *, algorithm: str = "auto", **kwargs):
        if algorithm == "rbc":
            algorithm = "auto"
        super().__init__(n_neighbors=n_neighbors, algorithm=algorithm, **kwargs)
