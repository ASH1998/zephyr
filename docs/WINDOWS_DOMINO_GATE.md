# Native Windows DoMINO capability gate

Date: 2026-09-18

This gate proves that the pinned NVIDIA DoMINO design-sensitivity workflow can
execute locally on the development workstation without WSL or cloud compute.
It is a capability result, not an aerodynamic-accuracy validation.

## Tested system

- Windows x86-64
- NVIDIA GeForce RTX 4070 Ti SUPER, 15.99 GiB VRAM
- NVIDIA driver 591.86
- 63.8 GiB system RAM
- Python 3.12 in the workspace-level `../.venv`
- PyTorch 2.11.0+cu128
- PhysicsNeMo 2.2.2
- PhysicsNeMo-CFD commit `0612ec4ed54484a47bfa134eda7b3b012a607624`
- Warp 1.17.0

The checkpoint bundle matched every SHA-256 value in
`config/domino-artifacts.json` before execution.

## Native compatibility boundary

The upstream workflow lists NVIDIA Apex and RAPIDS cuML. Apex is not imported
by this inference path. cuML is used only for a nearest-neighbor query that
builds the fixed surface stencil. `scripts/windows_compat/cuml` supplies that
single API using scikit-learn on CPU; the DoMINO forward pass, SDF kernels and
autograd sensitivity calculation remain GPU-backed.

This compatibility layer does not change model weights, surface fields, drag
integration, or gradient calculation. It can affect preprocessing performance
and must remain covered by finite-difference validation.

## Gate result

- Strict `.mdlus` checkpoint load: passed
- Model parameters: 10,060,425
- Model-weight VRAM after load: 38.4 MiB
- Official DrivAerML `drivaer_1.stl`: downloaded and processed
- CUDA inference/autograd batches: 92/92 in approximately 58 seconds
- Laplacian smoothing: 20/20 iterations
- Export: `drivaer_1.vtk`, 106,956,139 bytes
- Mesh: 376,531 points and 753,234 cells
- All exported pressure, wall-shear and sensitivity values finite: yes
- Predicted surface pressure range: -3909.9402 to 1274.6292 Pa
- Predicted wall-shear component range: -21.9728 to 17.9644 Pa
- Smoothed normal-sensitivity range: -5.6278 to 9.0852
- Integrated streamwise force: -444.5109 N (sign follows mesh convention)

The generated STL and VTK remain under `.local/` and are intentionally ignored.

## Run again

For a fresh checkout, prepare the isolated environment from the repository root:

```powershell
.\scripts\setup-domino-windows.ps1
```

The setup keeps the Python runtime, environment and package cache on the
workspace drive in `../.tools`, `../.venv` and `../.cache` respectively.

Then run the official sample:

```powershell
.\scripts\run-domino-windows.ps1
```

For another STL:

```powershell
.\scripts\run-domino-windows.ps1 -InputFile C:\path\to\vehicle.stl
```

If VRAM becomes constrained, reduce the fixed stencil size deliberately and
rerun the gradient-validation evidence:

```powershell
.\scripts\run-domino-windows.ps1 -StencilSize 3
```

## Remaining proof work

1. Capture peak end-to-end VRAM and wall-clock timings in a repeatable report.
2. Run the finite-difference gradient notebook on a small epsilon sweep.
3. Create a bounded candidate mesh while holding protected vertices fixed.
4. Rerun DoMINO on that candidate and compare integrated drag.
5. Validate the baseline/candidate pair with an independent CFD method.

## Integration force-convention correction

The real browser integration captures `DoMINOInference`'s returned force directly:
its baseline Fx is approximately **+621.70 N**. The earlier -444.5109 N above was
an outward-normal reintegration of exported fields. Upstream uses inward normals,
so that old value must not be used as the returned surrogate drag. See
[LOCAL_DOMINO.md](LOCAL_DOMINO.md) for the explicit convention and live evidence.
