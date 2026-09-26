# Bring your own car

Implemented 2026-09-26, experimental. The nine catalog geometries, original deformation gates, saved replays, and synthetic dent demonstration are retained.

## Use

Start the normal loopback API and frontend. Mesh import is local; photo interpretation requires the existing explicit `--enable-llm` option. Photo bytes are decoded, stripped of metadata, resized, and sent to Gemma 3 on Token Factory. Nemotron then selects a template. The dialog explains this before file selection.

1. Choose **Bring your own car** at the end of Geometry.
   After your first import, **Add another car** is also visible directly below the Geometry selector. Each upload gets its own ID; selecting the same file again is supported. The button waits for an active calculation to finish.
2. Upload STL, OBJ, GLB, embedded GLTF, PLY, PNG, JPEG or WebP. Mesh limit: 50 MB / 2 million triangles. Photo limit: 10 MB / 12 megapixels. GLTF buffers must be embedded; external references are not resolved.
3. If units are ambiguous, supply a known length before uploading. The heuristic (>100 = mm, >10 = cm, otherwise m) is fallible: for example a centimetre car export may need this override.
4. Review the closed proxy, grid, flow arrow, dashed sedan-size reference and protected/editable overlays. Rotate axes in 90-degree increments, flip the front, or enter a length; **Apply orientation & size** regenerates the actual inference surface. The front is not automatically recognized.
5. **Confirm & run baseline + airflow** freezes the geometry and starts an analysis through the existing GPU lock. Busy GPUs return a retryable conflict. Repeated confirmation cannot launch duplicate runs.
6. **Baseline ready** means the original shape was evaluated. For eligible imports, **Test a bounded shape change** starts a separate iteration using the normal brief and movement slider. A before/after comparison appears only if an actual candidate survives the existing gates. An explicit brief such as “Reduce drag using the upper rear taper. Keep the cabin unchanged. Maximum displacement: 3.6 mm.” grounds the numerical limit.

Out-of-range geometry has disabled shape controls and server-enforced baseline-only access, including preset, copilot and worker paths. It is distinct from a completed baseline run on a shape-test-eligible car.

## Evidence and limitations

Every import is a **DoMINO estimate, experimental geometry**. Photo imports are scaled catalog templates, not reconstructions. A photo of a Lamborghini must not be presented as CFD on that exact car. Review the chosen template before confirming. Templates now include named models and descriptions so Nemotron can distinguish a low supercar from a conventional M3 coupe; it must not select a sedan-like shape just to obtain shape-test eligibility.

`importer.RANGE_POLICY` is a versioned conservative sedan-like screening envelope covering length, width, height and proportions. It is not a verified DrivAerML parameter-spread boundary. Shape semantics cannot be established by dimensions alone. Photo pickup/open-wheel/other classifications and a model's more restrictive decision cannot be promoted to shape tests. The chosen template's support is also a floor. Thin features below roughly 70 mm can disappear in the voxel proxy. No published-car Cd comparisons or physical-validation claims are supported.

`prepare_surface(..., catalog=True)` retains the original recipe. `check-import-catalog.py` rebuilds in memory and never writes catalog assets. Six of eight current source-derived surfaces reproduce their saved hashes. Hatchback and wagon already differ from their current visual-source files under the **unchanged old recipe**; the shared recipe reproduces the old recipe exactly for both. Their saved surfaces and previews remain untouched. `prepare-vehicle-surfaces.py` now refuses to overwrite an existing surface if the regenerated hash differs.

Uploads live under `.local/uploads/upload-<32 hex>/`: source, closed `surface.vtp`, preview, report, and optional photo/template records. The manifest resolves only generated IDs. Confirmed surfaces are immutable and the worker verifies their file hash before evaluation. Reports retain source/surface hashes, scaling and orientation, screening policy, warnings, template selection, both validated model responses and credential-free model provenance.

## API

| Endpoint | Behavior |
|---|---|
| `POST /api/uploads` | Raw body, `X-Filename`; optional `X-Car-Length` in metres. Returns draft ID, report, preview. |
| `POST /api/uploads/<id>/prepare` | `{rotation:[0,0,0], flipFront:false, lengthM:null}`; rebuilds an unconfirmed draft. Quarter turns only. |
| `POST /api/uploads/<id>/confirm` | Same options; freezes and starts baseline/airflow, returning the normal job. |
| `GET /api/uploads/<id>` | Report, preview, confirmation and associated job state. |
| `GET /api/uploads/<id>/preview` | Validated display geometry and region masks. |
| `GET /api/uploads/<id>/airflow` | Completed baseline velocity artifact, or explicit unavailable status. |
| `GET /api/geometries` | Existing catalog plus confirmed uploads and photo-import availability. |

All routes inherit loopback Host/Origin checks. The importer does not execute uploaded files, resolve external mesh resources, or alter geometry/trust gates. Concurrent preparation is bounded to one import.

## Verification

The backend suite covers real mesh preparation, units/orientation overrides, nearby components, disconnected parts, large holes, parser failures, body-type restrictions, manifest identity, immutable confirmation, HTTP limits/origins, idempotency, photo schemas and a mocked two-model pipeline. Photo tests deliberately return an unsafe shape-tests decision for a pickup and require deterministic baseline-only output. No third-party test assets ship with this feature.

All **92 backend tests**, **45 frontend tests** and the production build pass. A user-uploaded photo completed both live model calls, surface preparation, confirmation, GPU baseline and velocity inference: run `local-216ffe315353411081c63bf7969b17e0`, 15.81 seconds, 548.74768 N baseline estimate on the selected coupe approximation. This verifies connectivity, not template accuracy: its conventional-coupe selection for a supercar prompted the improved template descriptions. The confirmed record remains unchanged.

Run `local-7859424d99d546d8ba85301acc0f960c` then exercised a fresh original/candidate comparison with a 3.6 mm upper rear taper. It completed in 41.36 s with geometry and fresh-evaluation gates passed, the cabin unchanged, and both velocity fields ready. Predicted drag increased to 549.69897 N (+0.173%). Acceptance was refused, with the existing experimental-domain restriction retained. Browser verification showed the comparison and no console errors. The import baseline needed no reinterpretation or modification.

The planned ten-real-photo/eight-correct qualification and non-car live evaluation remain pending. Mocked rejection and safety tests do not establish that benchmark. No independent CFD validation was added.
