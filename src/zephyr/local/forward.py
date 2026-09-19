"""Fresh force-only inference for finite-difference probes.

Mirrors the pinned NVIDIA surface loop's preprocessing, batching, scaling and
float32 force accumulation. It omits unused autograd and may reuse the identical
global geometry encoding across batches of ONE evaluation. No cross-mesh or
cross-run result is reused. Baseline/candidate sensitivity paths stay upstream.
"""
from contextlib import contextmanager
import time
import numpy as np

FORWARD_VERSION = 'fresh-probe-forward-v1'


@contextmanager
def geometry_encoding_cache(module, stats):
    """One-evaluation, exact-input cache, forbidden whenever gradients are on."""
    import torch
    original = module.forward
    had_override = 'forward' in module.__dict__
    saved = module.__dict__.get('forward')
    previous = None
    result = None
    stats.update(geometryCalls=0, geometryCacheHits=0)

    def forward(*args):
        nonlocal previous, result
        if torch.is_grad_enabled() or module.training:
            raise RuntimeError('Geometry reuse requires evaluation mode with gradients disabled')
        stats['geometryCalls'] += 1
        same = previous is not None and len(args) == len(previous) and all(
            a.shape == b.shape and a.dtype == b.dtype and a.device == b.device and torch.equal(a, b)
            for a, b in zip(args, previous))
        if same:
            stats['geometryCacheHits'] += 1
            return result
        result = original(*args)
        previous = tuple(a.detach().clone() for a in args)
        return result

    module.forward = forward
    try:
        yield
    finally:
        if had_override:
            module.forward = saved
        else:
            del module.forward


def evaluate_forward(domino, mesh, *, stream_velocity=38.889, air_density=1.205,
                     stencil_size=7, progress=None, profile=None, reuse_geometry=True):
    import torch
    from contextlib import nullcontext
    import main as upstream
    from zephyr.local.sensitivity import prepare_surface

    stats = profile if profile is not None else {}
    stats.update(method=FORWARD_VERSION, freshGeometry=True, autograd=False,
                 geometryReuseScope='within-evaluation' if reuse_geometry else 'none')
    started = time.perf_counter()
    prepare_surface(mesh)
    torch.random.manual_seed(0)
    model = upstream._unwrap_model(domino.model)
    if model.output_features_vol is not None or model.training:
        raise ValueError('Force-only path supports the pinned evaluation-mode surface checkpoint only')
    def sync():
        if domino.device.type == 'cuda':
            torch.cuda.synchronize(domino.device)
    sync()
    with torch.no_grad():
        datapipe = upstream.DesignDatapipe(
            mesh=mesh, bounding_box=domino.bounding_box_volume_min_max,
            bounding_box_surface=domino.bounding_box_surface_min_max,
            grid_resolution=model.grid_resolution, stencil_size=stencil_size,
            device=domino.device, produce_volume_inputs=False)
        loader = torch.utils.data.DataLoader(datapipe, batch_size=2**13, shuffle=False)
        inputs = {k: v.unsqueeze(0) for k, v in datapipe.out_dict.items()}
        globals_col = torch.tensor([[stream_velocity], [air_density]], dtype=torch.float32,
                                   device=domino.device).unsqueeze(0)
        inputs['global_params_values'] = globals_col
        inputs['global_params_reference'] = globals_col
        sync()
        stats['preprocessingSeconds'] = time.perf_counter() - started
        batches_started = time.perf_counter()
        force = np.zeros(3, dtype=np.float32)
        fields = []
        total = len(loader)
        if progress:
            progress(0, total)
        cache = geometry_encoding_cache(model.geo_rep_surface, stats) if reuse_geometry else nullcontext()
        with cache:
            for index, batch in enumerate(loader):
                batch_inputs = {**inputs, **{k: batch[k].unsqueeze(0) for k in upstream.DesignDatapipe.SURFACE_KEYS}}
                _, prediction = domino.model(batch_inputs)
                prediction = (upstream.unnormalize(prediction, domino.surf_factors[0], domino.surf_factors[1])
                              * stream_velocity**2.0 * air_density)
                area, normals = batch_inputs['surface_areas'][0], batch_inputs['surface_normals'][0]
                force_batch = torch.sum(area[:, None] * (normals * prediction[0, :, 0, None]
                                        - prediction[0, :, 1:4]), dim=0)
                # Deliberately retain the reference loop's ordering and precision.
                force += force_batch.cpu().numpy()
                fields.append(prediction[0].cpu().numpy())
                if progress:
                    progress(index + 1, total)
        sync()
        stats['batchSeconds'] = time.perf_counter() - batches_started
        stats['batches'] = total
        stats['totalSeconds'] = time.perf_counter() - started
        predictions = np.concatenate(fields, axis=0)
        return {'geometry_coordinates': inputs['geometry_coordinates'][0].cpu().numpy(),
                'pred_surf_pressure': predictions[:, 0],
                'pred_surf_wall_shear_stress': predictions[:, 1:4], 'aerodynamic_force': force}
