# Handoff: Bring your own car (upload + photo)

Status: implemented as an experimental local feature on 2026-09-26; see [implementation and verification](BRING_YOUR_OWN_CAR.md). The original plan below is retained for reference. The 10-photo quality qualification and measured training-spread validation remain pending.
Order: finish the current selected-candidate replay and dent demo first, then this.

## Goal

Let a user add a car to Zephyr in two ways:

1. **Upload a mesh** (STL / OBJ / GLB / GLTF / PLY).
2. **Upload a photo.** Classify the car, pick the closest template, scale it to real dimensions.

Both paths end in the normal workspace (baseline, pressure, airflow, body-region tools).
Every result is labeled experimental. This is a demo feature, not a validated one.

## Rules that do not change

- Deterministic code owns geometry. LLMs never move vertices or set millimetres.
- Existing geometry gates, protected masks, 4 mm / study limits and acceptance policy stay as-is.
- Uploaded or photo-derived drag numbers are "DoMINO estimate, experimental geometry".
  Never compare them with a real car's published Cd.
- Loopback only; uploaded files are parsed as meshes/images, never executed.

## What already exists

- `scripts/prepare-vehicle-surfaces.py`: visual mesh -> closed inference surface
  (35 mm voxelize, close, fill holes, contour, smooth, decimate to ~18k points,
  ground/centre/rotate, preview JSON with `protectedMask`). Currently a batch script with fixed paths.
- `src/zephyr/local/geometry.py` `body_basis`: region envelopes are fractions of the
  bounding box, so nose / hood / shoulders / deck / rear tools should work on new cars unchanged.
- `src/zephyr/local/cars.py`: static allowlist `CARS`, `car_definition()`, `mesh_path()`.
- Baseline-only analysis path (used for aircraft) and `predict_airflow` in `src/zephyr/local/volume.py`.
- `src/zephyr/token_factory.py`: Token Factory client.

## Part 1: Mesh upload (about 4–5 days)

### 1.1 Importer module: `src/zephyr/local/importer.py`
Move the core of `prepare-vehicle-surfaces.py` into `prepare_surface(mesh, options) -> (surface, preview, report)`.
Make the script call the same function so the catalog cars stay reproducible (hashes must not change;
check against existing `.local/cars/*.vtp` hashes).

- **Load:** `trimesh.load(force='mesh')`, merge parts. Caps: 50 MB file, 2M triangles.
- **Units:** longest extent is length. Over 100 means mm, over 10 means cm, else m. The user can override with "car length (m)".
- **Orientation:** longest axis is x (length). Up axis comes from the format convention (GLB Y-up, STL usually Z-up).
  Front/back is not auto-detected; the UI provides a flip button.
- **Closure:** reuse the voxel pipeline. Before `extract_largest()`, merge components within about 2 voxels
  (so separate wheels aren't dropped). If open edges remain, refuse with a plain reason.
- **Outputs:** `.local/uploads/<id>/source.<ext>`, `surface.vtp`, `preview.json`, `report.json`
  (units guess, scale, rotation, flip, hashes, steps applied, thin-feature warning).

### 1.2 Training-range check
Compare L, W, H, H/L and W/L against the DrivAer sedan and the DrivAerML parameter spread.
- **Close:** baseline and shape tests allowed, labeled *experimental*.
- **Far** (pickup, bus, open-wheel, motorbike): baseline only, shape tests refused, with a reason.
Write the thresholds into the report and keep them in one versioned constant.

### 1.3 Runtime registry
- `.local/uploads/manifest.json`.
- `car_definition()` / `mesh_path()` accept `upload-<32 hex>` ids validated against the manifest.
- Serve the preview from the API instead of `frontend/public`.
- Update the geometry list in the copilot system prompt (`src/zephyr/copilot.py`) to mention uploaded cars and their status.

### 1.4 Server (`src/zephyr/local/server.py`, stdlib handler)
- `POST /api/uploads`: raw body plus an `X-Filename` header. Returns id, report and preview.
- `POST /api/uploads/<id>/confirm` `{rotation, flipFront, lengthM}`: re-prepares, then queues baseline and airflow under the existing GPU lock.
- `GET /api/uploads/<id>`: status, report, preview.
- `/api/geometries` includes confirmed uploads.

### 1.5 Frontend
"Bring your own car" at the end of the vehicle selector:
1. Drop zone (mesh or photo; photo goes to Part 2).
2. Preview: ground plane, flow arrow, DrivAer outline for scale; rotate 90° on each axis, flip front/back, length field.
3. Overlay of the protected cabin and editable regions.
4. Progress: preparing surface → training-range check → baseline drag → airflow.
5. Opens in the normal workspace with a **"Your car · experimental"** badge.

### 1.6 Test files and tests
Collect CC-BY / CC0 files (Sketchfab / BlendSwap) and record licenses in `VEHICLE_CREDITS.md` if any ship:
- 2 ordinary sedans/hatchbacks (should pass);
- 1 in millimetres, Z-up (tests unit/orientation handling);
- 1 pickup or open-wheel car (should give baseline only or refuse);
- 1 mesh with large holes (should give a clean error).

Unit tests: unit guessing, orientation, component merge, manifest validation, size caps, error paths,
and hash stability of the existing catalog cars through the refactored importer.

## Part 2: Photo → template car (about 2 days, after Part 1)

### Important: no Nemotron model on our Token Factory accepts images
Probed 2026-09-26 with a test image through `/v1/chat/completions`:

| Model | Image input |
|---|---|
| `nvidia/Nemotron-3-Ultra-550b-a55b` | no (HTTP 400 "does not support image input") |
| `nvidia/nemotron-3-super-120b-a12b` | no |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | no |
| `nvidia/Nemotron-3_5-Lightning` | no |
| `google/gemma-3-27b-it` | **yes** |

So: **Gemma 3 looks at the photo, and Nemotron decides.** Re-probe before the submission in case the catalog changes.

### 2.1 Vision step (Gemma 3 27B, Token Factory)
Input: one photo (side or 3/4 view). Output: strict JSON only, validated by schema:
```json
{
  "isCar": true,
  "bodyType": "sedan|hatchback|estate|suv|coupe|van|pickup|open-wheel|other",
  "roof": "notchback|fastback|squareback|unknown",
  "makeModelGuess": "string or null",
  "makeModelConfidence": 0.0,
  "view": "side|three-quarter|front|rear|other",
  "features": ["rear-spoiler", "roof-rails", "..."]
}
```
No decisions in this step. Reject non-car photos here.

### 2.2 Decision step (Nemotron Ultra, Token Factory)
Input: the vision JSON plus the template catalog (id, body type, roof, dimensions, training-range status).
Output (schema-validated):
```json
{
  "templateId": "hatchback",
  "dimensionsM": {"length": 4.52, "width": 1.80, "height": 1.43},
  "dimensionSource": "known-model|class-typical",
  "support": "shape-tests|baseline-only|refuse",
  "reason": "one line",
  "explanation": "one line for the user"
}
```
Deterministic checks after the call: templateId must be in the catalog, dimensions within sane bounds
(e.g. L 2.5–7 m), and `support` can never be looser than the training-range check from 1.2.

### 2.3 Build the mesh (deterministic)
Scale the chosen template separately along x/y/z to the target dimensions, then run it through the Part 1 pipeline
(closure, protected mask, training-range check). Record template id, scale factors and both LLM
responses in the report.

Label: **"Approximated from photo · <template> scaled to L×W×H · experimental."**

### 2.4 Templates
Start with the current catalog (DrivAer sedan, hatchback, wagon, SUV, coupe, sports, van).
Optional: add DrivAerNet++ fastback / notchback / estate variants (check the license first; it may be non-commercial).

### 2.5 Evaluation (write the target before testing)
10 real photos with expected body types and one non-car. Pass: at least 8 of 10 correct templates, the non-car rejected,
and no pickup/open-wheel car given shape tests. Save results under `docs/evidence/`.

## Later, optional
Side-profile matching: have the vision step return the outline and choose/fit the template by profile, not just class.
This is the step toward defensible photo-based numbers.

## Out of scope
Phone photogrammetry / LiDAR scans (noise larger than the effects we measure), generating meshes directly from a photo
(TRELLIS etc.) unless templates prove too limiting, aircraft uploads, and physical-validation claims.

## Video beat (about 15 s)
Photo of a car → "Looks like a hatchback, scaled to 4.5 m" → body appears, airflow blooms → region tool suggests a
rear taper. Then a pickup photo → "Outside what the model knows: baseline only."
