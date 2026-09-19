# Real local DoMINO integration

The default browser Run button starts a fresh local CUDA worker. `?demo=1`
retains the illustrative concept-car walkthrough; it does not run a model.
This integration uses the open `.mdlus` checkpoint, not the Automotive Aero NIM.
The default API mode makes no cloud calls. Add `--enable-llm` to opt in to
configured Token Factory calls from the main interface; no cloud GPU is created.

## Start on Windows

Use the relocated environment. From `F:\github\nebius\zephyr`, terminal 1:

```powershell
& ..\.venv\Scripts\python.exe -m zephyr.local.server
```

Terminal 2:

```powershell
cd F:\github\nebius\zephyr\frontend
npm run dev
```

Open http://127.0.0.1:5173 and click **Run bounded iteration**. A baseline-only
button is also available. Without `--enable-llm`, use the exact preset brief
shown in the UI. With it, the configured model interprets supported drag-reduction
briefs and ranks the resulting evidence. See [LLM integration](LLM_INTERFACE.md).
The runtime must already be installed using `scripts/setup-domino-windows.ps1`.
The sample `drivaer_1.stl` must already exist in the pinned workflow's geometries
folder (the capability-gate script downloads it). No runtime download is hidden
behind Run. Frontend `npm ci` is needed only on a fresh checkout.

The backend binds only `127.0.0.1:8766`. Vite proxies `/api` to it. Preview builds
need the same proxy or a reverse proxy; the documented development command is
the supported local launch. There is no upload/path endpoint. Only the installed
sample geometry, fixed 38.889 m/s and 1.205 kg/m³, and a finite (0,4] mm budget
are accepted. A second request receives HTTP 409 while the GPU job is active.

## What is live

- Strict checkpoint, scaler and training-config SHA-256 verification; pinned
  upstream commit and tracked-workflow-diff guard.
- The actual upstream `DoMINOInference` API, CUDA forward pass and autograd.
  The existing Windows scikit-learn cuML neighbor shim is retained. Warp and
  PhysicsNeMo caches remain on the workspace drive.
- Structured progress after each completed GPU batch, plus real loading,
  preprocessing, smoothing, conversion, geometry checks and evaluation stages.
  Stages without an actual numerical fraction use an indeterminate progress bar.
- A full baseline VTK and a `zephyr.surface.v2` analysis artifact, with **null
  candidate and null candidate forces**. Baseline fields render while later
  work continues. Failures never substitute an illustrative result.
- One deterministic rear-width taper, restricted to the last 18% of the source
  x extent and above the underbody. The entire cabin and the rest of the front
  body are exactly fixed. The lateral displacement uses C2 quintic ramps and
  is odd about y=0. Existing input asymmetry is preserved, not repaired.
- Hard geometry gates: exact faces, finite coordinates, exact protected points,
  displacement bound, normals (cosine >0.99), area ratios (0.8–1.2), and no open
  or non-manifold edges. Failed attempts halve the same handle up to four times;
  all attempts are recorded. Gates are not relaxed to get a result.
- A fresh full-resolution GPU evaluation of the surviving candidate, with raw
  forces, actual mm displacement, predicted delta and measured prediction error.
- Comparison controls, pressure and sensitivity heatmaps, actual displacement
  map, true scale by default and a labelled ×24 display option. The default
  Airflow view overlays labelled illustrative ribbons and tracer particles on
  the actual geometry. The paths stay identical across candidate comparisons;
  neither their shape nor animation speed represents a computed velocity field.
  This checkpoint does not provide a volume-flow solution. A geometry-only
  preview loads before inference, with field modes disabled until real results
  arrive. Shape interpolation and magnification are display only.

## Scientific limits and refusal

All candidates are currently **refused for acceptance**. Full triangle
self-intersection checking, finite-difference handle calibration, empirical
trust/noise thresholds and independent CFD remain unvalidated. A geometrically
permitted research candidate may still be freshly evaluated and compared. A
lower surrogate force is not a validated physical improvement or an accepted
manufacturable design. Manufacturing feasibility beyond the smooth handle is
not certified. Worsening results remain visible and are refused.

The scalar projection uses smoothed upstream sensitivity to select the handle
sign. The raw cell-centroid sensitivity predicts `delta D = -sum(g · delta X)`.
This is a local model prediction with fixed preprocessing terms; fresh inference
rebuilds stencils and geometry inputs, so disagreement is measured, not hidden.

### Force convention correction

The upstream datapipe uses **inward normals**, `n_inward = -VTK cell normal`.
Its force is `sum A * (p*n_inward - wallShear)` and streamwise drag is `D=Fx`.
The returned baseline force is about **+621.70 N**, not −444.51 N. The latter
number in the earlier Windows capability report came from reintegrating with
outward VTK normals; it is not the workflow's returned aerodynamic force.
The integration captures the return value directly and records this convention.

## Display conversion and evidence

Full-resolution inference uses 376,531 source vertices and 753,234 triangles.
VTK DecimatePro preserves topology and retains original vertices, with an
explicit nearest-original-index mapping checked for zero coordinate error.
The default reduction produced 110,339 display vertices and 220,850 triangles.
It is deterministic for the pinned VTK environment. The display is an
approximation and can omit small features or extrema; full-source ranges are
recorded. No force is recomputed on the reduced mesh.

Source `(X,Y,Z)` metres become viewer `(X,Z,-Y)`, after translating x to the
vehicle centre and z to the ground. The proper rotation has determinant +1;
vector shear and sensitivity receive the same rotation. Scalar sensitivity
retains its sign. Pressure and shear use area-weighted adjacent-cell to point
interpolation before sampling retained vertices. Upstream point-smoothed normal
sensitivity is sampled directly. Baseline and candidate share the exact display
indices and retained original vertex mapping.

Every job owns `.local/runs/<runId>/`: `request.json`, `worker.log`, full
`baseline.vtk`, optionally `evaluate.vtk`, `baseline.json`, `result.json`, and
`evidence.json`. VTK field data includes the actual integrated force. Evidence
contains checkpoint/bundle hashes, upstream Python file hashes, input STL hash,
canonical full-mesh hash, reduction-map hash, force and field conventions,
constraint results, attempts, timings, GPU identity, peak CUDA allocation and
VTK file hashes. These large artifacts are ignored; retain only compact evidence
summaries in versioned docs. No credentials are printed or included.

The browser polls by run ID and monotonic sequence, rejects mismatched events,
and retains the current run in session storage across refreshes. Cancellation
terminates the isolated process and releases the lock; a completed baseline can
still be inspected. Backend restarts do not resume jobs or republish disk
artifacts automatically. The API retains the latest 16 job summaries in memory;
artifacts remain on disk. This is a local development service, not a public
multi-user deployment. The subprocess/event/artifact boundary allows a future
remote worker without changing the renderer contract.

## Verification

```powershell
& ..\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm --prefix frontend test
npm --prefix frontend run build
```

GPU integration tests require the existing model environment. API unit tests
use explicitly synthetic subprocesses to cover lifecycle, failure, cancellation,
cross-service locking, invalid inputs and origin checks. Conversion tests cover
area weighting, proper rotation, finite values and deterministic reduction;
geometry tests cover protected points, bounds, topology and symmetry. Frontend
tests cover analysis-only states, fresh comparisons, field/force provenance,
run IDs and event ordering. The measured browser-click smoke evidence is in
`LOCAL_DOMINO_SMOKE.md`.
