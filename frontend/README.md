# Live local mode (default)

The default page now runs the actual local DoMINO GPU integration. Start the
backend and frontend using [the local integration guide](../docs/LOCAL_DOMINO.md).
It supports baseline-only results, actual surface fields, bounded candidate
shrink/evaluation, cancellation and evidence. Trust is uncalibrated; no candidate
is accepted as an engineering improvement. With backend `--enable-llm`, the
main page also compiles your brief through the configured model and displays
LLM-ranked evidence after completion. See [copilot behavior](../docs/LLM_INTERFACE.md).

The older instructions below describe **only `?demo=1`** (illustrative walkthrough)
and the legacy v1 read-only artifact adapter. New live artifacts use
`zephyr.surface.v2` in `src/live-data.ts`, with a nullable candidate.

# Zephyr — Shape the flow.

A runnable aerodynamic-design interaction prototype: licensed concept vehicle, layered animated flow ribbons and wake, surface pressure, signed normal-sensitivity glyphs, mesh inspection, protected cabin, bounded geometry comparison, and an accept/shrink/refuse walkthrough.

**Illustrative preview — not CFD.** All bundled fields, forces and trust values are deterministic demo data. This app has not executed DoMINO, Nemotron, a checkpoint, or independent CFD. It starts no cloud services and makes no paid calls. It does not establish any Day-0 or engineering validation gate.

## Run locally

Requires Node 22.14+ (Vite requires Node 20.19+ or 22.12+; the test command uses Node's experimental TypeScript stripping).

```powershell
cd F:\github\nebius\zephyr\frontend
npm ci
npm run dev
# http://127.0.0.1:5173
npm test
npm run build
npm run preview
```

For an explicit port, bypass npm argument forwarding on Windows:

```powershell
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
```

Versions: Three.js **0.186.0**, Vite **8.3.0**, TypeScript **5.9.3**. TypeScript 7.0.2 installed but could not resolve `@typescript/typescript-win32-x64` on this machine, even after `--include=optional` and an explicit platform-package reinstall. The portable 5.9.3 compiler is the concrete compatibility fallback. `package-lock.json` is retained. The detailed default vehicle is the locally bundled Khronos CarConcept asset (CC BY 4.0, Eric Chadwick / Darmstadt Graphics Group GmbH). Attribution appears in the evidence dialog and `public/models/ATTRIBUTION.md`; its SHA-256 is recorded there and in run provenance. Display materials, orientation and bounded deformation are modified at runtime. No external CDN or font request is needed. The concept car is outside the claimed validated model envelope; it is a visual demo, not a watertight solver input. A small procedural fixture remains for dependency-free contract tests.

## Interaction and film path

1. Start on Airflow: a large sedan, coherent body-bypass ribbons, traveling highlights, a small oscillating wake and a small roof-lock marker. Persistent demo disclosure is visible above the workspace.
2. Edit “Reduce drag. Keep the cabin unchanged.” Choose a 1–4 mm budget. The offline intent handler deliberately understands only a narrow “reduce drag” vocabulary; it is not labelled as Nemotron.
3. **Run bounded iteration** advances through constraints → sensitivity → fixed-topology geometry → fresh evaluation → decision. The animation shows the mechanism, not an actual solver execution. A smaller budget changes the underlying demo candidate coordinates and its explicitly invented force fixture.
4. Scrub Baseline ↔ Candidate. The default **×24** magnification is explicitly labelled; turn it off to view metre-correct displacement. Protected vertices and the roof-lock marker never move.
5. A **4 mm** request demonstrates shrinking to 3.6 mm and replaying validation/evaluation. The threshold is uncalibrated demo data. **Test trust boundary — 12 mm** refuses at the hard constraint and retains the preceding candidate. “Reduce drag. Lower the cabin.” also refuses. Unknown intent refuses.
6. Inspect pressure, normal sensitivity and the triangulated surface; orbit with drag or keyboard arrows, zoom with wheel or +/- and reset the camera.
7. Evidence & provenance explains the boundary and exports the current JSON fixture. Proof remains “Not validated.”

Suggested strongest sequence: run at 3.6 mm, scrub the rear taper with the cabin locked, then press the 12 mm boundary test. The unchanged car and amber refusal make “It stops when it stops being trustworthy” visible without narration.

Desktop layout is composed for 1920×1080; narrow screens stack the viewer, controls and metrics. All inputs are labelled; focus outlines, keyboard camera controls, an aria-live decision region and native modal focus handling are present. Reduced motion disables flow advection/damping, makes geometry transitions immediate and shortens the staged demo. Pause Flow also stops advection.

## Data adapter contract

`src/data.ts` is the explicit boundary. `SimulationAdapter.load(signal?)` returns a runtime-validated `SimulationRun`. `VehicleDemoAdapter` loads the licensed model, bakes its exterior mesh transforms, and generates deterministic fields through the same surface contract. `DemoAdapter` retains the procedural test fixture. `HttpRunAdapter` fetches JSON and validates it; **failed fetches, unsupported schemas and invalid fields never fall back to demo data**.

Open `/?run=/api/runs/<id>` to load a supplied payload. Recorded/live runs are read-only: no demo optimizer, analytic airflow, procedural wheels or decorative car details are added. Surface fields, topology, forces, masks and evidence status come from the supplied artifact. The cabin envelope is derived from its mask bounds. Real runs require non-demo geometry/evaluation states and nonempty evidence references. Their source remains visible. The app never converts a surrogate result into independent-CFD truth.

`zephyr.surface.v1` uses inline numeric arrays so it can be exported, inspected, hashed and replayed without a separate parser:

| Field | Meaning |
|---|---|
| `schemaVersion`, `runId`, `source`, `createdAt` | Version, identity, explicit illustrative/recorded/live source and ISO timestamp |
| `coordinates` | Right-handed, metres, +Y up, +X streamwise; all fields vertex-associated |
| `baseline`, `candidate` | XYZ `positions`, identical indexed `triangles`, `pressurePa`, XYZ `wallShearPa`, XYZ `sensitivity`, scalar `normalSensitivity`, binary `protectedMask`, scalar `displacementM` |
| `sensitivity` | d(-drag N)/d(position m), converted by the producer to the declared coordinate convention |
| `conditions` | XYZ `streamVelocityMps`, `densityKgM3` |
| `forces` | Integrated baseline/candidate force vectors in N, separately reported predicted drag in N; drag is +X for v1 |
| `constraints` | Hard maximum displacement in metres and protected-region name (the current product UI is cabin-focused) |
| `trust` | accept/shrink/refuse, prediction error %, threshold %, and explicit calibration boolean |
| `validation` | Geometry/fresh-evaluation states, independent CFD state, evidence IDs |
| `provenance` | Artifact version, exact model/checkpoint version, mesh hash, evidence URLs, solver name or null |

The producer must convert face/cell fields to vertices explicitly and record that transformation in provenance, or introduce a new supported schema. Do not relabel face values as vertex values. The frontend rejects wrong units/axes, mismatched lengths, nonfinite values, altered connectivity/masks, movement in protected vertices, and disagreement between geometric displacement and its declared magnitude. These are payload guards, **not** a self-intersection, normal-quality, solver-domain or manufacturing validator. Those remain backend gates.

The browser payload is capped at 200,000 vertices. For larger solver surfaces, the backend should supply a separately versioned visualization LOD with traceable field interpolation and a link to the original full-resolution artifacts. The renderer currently expects passenger-car scale in metres; arbitrary CAD, upload repair and camera framing for other vehicle classes are out of scope.

### Backend transport and future updates

Recommended first integration: same-origin `GET /api/runs/:runId` serves `SimulationRun` JSON after the backend resolves and verifies its immutable mesh/field artifacts. Keep credentials on the backend. For efficient binary payloads, add an adapter that fetches metadata plus hashed Float32/Uint32 mesh/field blobs and assembles the same validated object. Do not change scene/UI semantics to accommodate the transport.

The polling/streaming seam is the `SimulationAdapter.load(AbortSignal)` call in `main.ts`. A future controller can poll it, or consume SSE stage events and fetch a complete immutable snapshot when its artifact ID changes. Abort stale requests, validate the complete snapshot, then atomically replace the displayed run (recreate `FlowScene` for changed topology/run identity). `FlowScene.setRun()` currently updates candidate fields for the *same topology*, used by demo-budget changes. Do not use it to change the baseline mesh. Never update force/decision labels from a different run than the displayed geometry.

True streamlines require a volume-velocity/streamline artifact: surface pressure and wall shear do not determine a volume flow field. Until that extension exists, analytic airflow is disabled for recorded/live runs. Wall-shear vectors are carried through the contract but do not yet have their own view mode. Pressure ranges and sensitivity legends derive from the payload. Sensitivity arrows visualize signed surface-normal projections; they are not optimizer commands.

## Verification and known limits

`npm test` checks deterministic fixtures, closed consistent edge connectivity on the procedural test fixture, protected vertices, selected displacement budgets, input corruption rejection, the decision branches, and explicit fetch/schema failure. `npm run build` performs strict TypeScript checking and a production Vite build. The Three.js + GLTF bundle is around 693 kB minified / 178 kB gzip, plus the locally bundled 12 MB model; Vite's default 500 kB advisory is expected for this self-contained 3D viewer.

Browser QA covers the 1920×1080 first frame, the field modes, comparison, iteration acceptance, refusal, shrink and a 390-pixel narrow viewport. Full notes are in `QA.md`.

Remaining integration work: authenticated backend orchestration, real Nemotron constraints, DoMINO pressure/shear/sensitivities/forces, calibrated trust, actual geometry validation evidence, independent CFD evidence, binary/LOD transport and true streamline artifacts. No physical improvement is claimed by this prototype.

### Cabin and presentation revision

`khronos-car-concept-2024-zephyr-cabin-v4` adjusts the actual source greenhouse from its 1.26 m roof to approximately 1.54 m. `src/vehicle-shape.ts` contains the baseline styling; the subsequent protected region stays fixed during the 1-4 mm demo iteration. A regression test reads actual positions and hierarchical transforms from the bundled GLB to check that the lift reaches the roof and stays bounded. This remains a modified concept coupe, not a production sedan or solver mesh.

Airflow now uses 11 slower, soft trails, with opacity reduced near the body so its paint and windows stay readable. A single roof anchor replaces the false cabin outline. Camera scale follows canvas aspect ratio rather than a blanket zoom-out below 700 px; materials and directional lighting emphasize the revised profile.

`src/vehicle-catalog.ts` is a typed geometry registry. `VehicleDemoAdapter(id)` resolves the available asset before loading it and continues returning `zephyr.surface.v1` through `SimulationAdapter`. The compact picker shows the licensed concept coupe; Sedan and SUV are disabled, explicitly unavailable placeholders. Unsupported IDs throw rather than silently loading the coupe. Adding geometry requires licensed files, per-asset preparation (the current adapter uses CarConcept node/material names), equivalent field mapping and visual/contract QA, followed by rebuilding the scene for the new topology. Recorded/live replay uses its supplied geometry and disables this picker. No new models were downloaded or licensing claims added.
