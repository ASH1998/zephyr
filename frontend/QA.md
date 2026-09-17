# Frontend verification — 2026-09-18

## Build and contract checks

- `npm install`: completed; lock retained; dependency audit reported 0 vulnerabilities.
- Requested TypeScript 7.0.2 failed to resolve its native Windows compiler, including after `npm install --include=optional` and explicit native-package installation. Switched compiler only to 5.9.3. Three.js 0.186.0 and Vite 8.3.0 retained.
- `npm test`: six tests pass. Deterministic procedural fixture, consistent closed edge connectivity for that fixture, protected coordinates, actual budget scaling, malformed payload rejection, accept/shrink/refuse, and fetch/schema failures without demo fallback.
- The Node test runner initially hit sandbox `spawn EPERM`; the same command passed when allowed to start its local worker process. This was not a test failure.
- `npm run build`: strict type check and production build pass. Final output: 695.32 kB JS / 178.96 kB gzip plus 14.09 kB CSS / 4.07 kB gzip. Vite emits its expected advisory for the >500 kB 3D bundle. Bundled model: 11,778,688 bytes.

## Browser QA performed

Chrome and the Codex in-app Chromium viewer both rendered the local WebGL frontend. The first localhost error was a dev-command argument being interpreted as a folder; direct Vite invocation fixed the server root. No browser security bypass was used.

- 1920×1080 CSS-pixel composition verified from DOM viewport dimensions and screenshots. The car, cabin label, controls, decision and all four metrics fit the frame. Browser zoom/DPR was accounted for when requesting Chrome's physical viewport size.
- 390×844 narrow-screen layout inspected. Corrected the initial nose clipping by resizing the canvas and adjusting camera zoom. Full car, view modes, comparison and constraint annotation remain visible; controls and metrics stack below.
- Default, side and rear-quarter views inspected using keyboard orbit. Source concept vehicle's low canopy was corrected with a baseline-only lift above the beltline, preserving authored normals with the deformation Jacobian. The original GLB remains unmodified.
- Airflow: replaced the original dense line/point field with 30 thin shader ribbons, traveling highlights, coherent over-body/flank paths and gentle downstream wake variation. Flow is still analytic illustration, explicitly labelled.
- Pressure: surface-attached coloring and data-derived range observed.
- Sensitivity: rear-region color and signed normal arrows observed; cabin retains its distinct protected treatment.
- Mesh: observed 44,127 exterior vertices and 72,343 triangles on the detailed model, with indexed mesh overlay.
- Bounded iteration: observed all five stages completing and `Candidate accepted · demo only`; comparison moved to candidate and maximum displacement was 3.6 mm.
- Shrink: 4 mm request produced `Step shrunk & re-evaluated · demo` and 3.6 mm result, with geometry/evaluation stages replayed.
- Refusal: final browser pass observed “Refused. The boundary holds.” and “12 mm exceeds the 4 mm hard limit. Candidate refused; accepted geometry is preserved.” No new evaluation ran. Cabin-conflict and other decision branches are also covered by tests. Final in-app browser error log was empty.
- Invalid data: `/?run=/package.json` (dev server only) visibly produced `Simulation data rejected: unsupported schema version. Expected zephyr.surface.v1.` with the scene removed and no fallback metrics.
- Keyboard camera movement, comparison controls, native modal structure and visible focus treatment checked. Reduced-motion behavior is implemented through the media query; an OS-level reduced-motion emulation pass was not available through the browser capability.

## Honest limits

The licensed vehicle is an adapted concept coupe, not a production sedan, validated DrivAer mesh, or watertight solver input. Its panel seams and wheel textures can still alias at low angles; surface fields do not turn that visual asset into engineering evidence. The roof-lock marker identifies the protected cabin; it is not a CAD tolerance boundary. The 24× geometry magnification is labelled and switchable.

No FPS benchmark across devices, real DoMINO payload, backend polling/SSE session, Nemotron compiler, self-intersection validator, calibrated trust region or independent CFD run was tested. The full real-payload integration remains to be performed with the backend. Surface wall shear is carried in the adapter contract but does not yet have its own view mode. Recorded/live airflow stays disabled until a volume-flow artifact is supported.


## Complete authored file manifest

All changes are new, uncommitted files under `frontend/`. No backend, plan, probe, artifact-lock, root README or sibling-repository file was edited.

- `.gitignore`
- `index.html`
- `package.json`
- `package-lock.json`
- `tsconfig.json`
- `src/data.ts`
- `src/main.ts`
- `src/scene.ts`
- `src/style.css`
- `src/vehicle.ts`
- `tests/data.test.ts`
- `public/models/car-concept.glb`
- `public/models/ATTRIBUTION.md`
- `README.md`
- `QA.md`

Ignored generated output: `node_modules/` and `dist/`. The development server was left running at `http://127.0.0.1:5173/`, launched with `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort`.


## Cabin/profile and clean Airflow pass - 2026-09-18

- Found the source roof at approximately 1.26 m after uniform normalization. The previous 1.13-1.43 m lift window only partially reached it. Replaced it with a 0.98-1.24 m window and a bounded 0.28 m lift, producing a roughly 1.54 m roof while retaining original mesh connectivity and transformed authored normals.
- Checked the front three-quarter, side and rear three-quarter profiles in the browser at 723 x 882. Roof/window depth is visible in all three, and the false floating cabin outline is gone. Only a point and short leader remain.
- Checked 1920 x 1080 and 390 x 844. The default vehicle remains fully framed. Camera zoom now depends on canvas aspect ratio, avoiding the abrupt 0.72 zoom at a 700 px panel width. Narrow layout retains readable tabs, comparison and controls.
- Reduced Airflow to 11 soft moving trails; attenuated trails around the body, retained depth testing, slowed highlights and removed the unused particle path. Topology renders only in Mesh mode. Materials and key/rim light were adjusted; glass and paint remain distinct.
- Browser workflow: accepted at 3.6 mm, refused at 12 mm while retaining the candidate, and shrank the 4 mm request to 3.6 mm. Pause changes to Resume and keyboard orbit/reset work. The persistent illustrative disclosure and unvalidated proof state remain intact.
- Added a compact typed geometry catalog/picker. The licensed concept coupe is the sole available model; Sedan and SUV are explicitly disabled. Unknown/unavailable IDs throw. No new asset, license, solver or CFD support is implied.
- Automated verification: 8/8 tests passed, including a test reading the actual GLB positions and hierarchy to check roof lift and unchanged wheel coordinates, plus catalog rejection. Production TypeScript/Vite build passed; the existing >500 kB bundle advisory remains.
- Changed this pass: src/vehicle.ts, src/vehicle-shape.ts (new), src/vehicle-catalog.ts (new), src/scene.ts, src/main.ts, src/style.css, tests/vehicle.test.ts (new), public/models/ATTRIBUTION.md, README.md, QA.md. No model bytes, backend or sibling files changed.
