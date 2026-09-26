# Zephyr progress

## 2026-09-26 — bring your own car

- Added isolated mesh/photo import preparation, runtime registry, loopback API,
  3D size/orientation/protection review, immutable confirmation, and normal GPU
  baseline/airflow integration. No catalog surface, replay, dent or trust gate changed.
- Server, preset, copilot and worker paths enforce imported baseline-only limits.
  Photo responses are schema-validated and cannot relax deterministic screening.
- Fixed confusing initial-run copy: **Baseline ready**, with an enabled **Test a
  bounded shape change** action when supported. Photos explicitly remain scaled
  templates. Added model-specific template descriptions after observing a wrong
  conventional-coupe choice for the user's supercar photo; that existing receipt
  remains unchanged.
- **92 Python tests, 45 frontend tests, production build passed.** Browser showed
  the existing workspace, import dialog, recovered imported baseline, and rendered
  original/changed comparison with no console errors.
- User photo import: `local-216ffe315353411081c63bf7969b17e0`, 15.81 s, surface and
  airflow ready. One subsequent 3.6 mm upper-rear test:
  `local-7859424d99d546d8ba85301acc0f960c`, 41.36 s, 548.74768 → 549.69897 N
  (+0.173%), geometry/fresh evaluation passed, cabin fixed, acceptance refused.
  Existing experimental-domain refusal policy stays authoritative.
- Shared catalog recipe matches the old recipe. Six saved source-derived hashes
  reproduce; hatchback/wagon source-to-saved drift also occurs under the unchanged
  old script. Saved files were preserved and regeneration now refuses mismatches.
- Ten-photo accuracy qualification, live non-car rejection benchmark and measured
  training-spread validation remain pending. See [implementation record](docs/BRING_YOUR_OWN_CAR.md).

## 2026-09-26 — shorter interactive sedan comparisons

- Cancelled the user-started five-region study and verified the GPU became idle.
- Added opt-in `--fast-demo`, enabled on the local API: sedan iterations use the
  existing partial sensitivity to choose one bounded candidate. Skip the baseline
  repeat and four direction probes; retain fresh original/candidate surface fields,
  geometry/intersection checks and separate airflow predictions.
- Keep skipped calibration as `not-run` in evidence and never grant local acceptance.
  Existing panels show the completed comparison without adding badges or changing
  layout/CSS. Initial sedan region defaults to Hood contour; all-five remains available.
- Full calculations remain available without the flag. Aircraft, dent replay and
  selected 3.33% replay are unchanged. No research search was resumed.
- One live hood comparison verified the full path in 155.196 s versus 377.636 s
  for the earlier full hood run (~59% shorter, observed on this machine). Run
  `local-baaf7bf079804b4fbb31c81ad530c65c` has two surface evaluations, no probes,
  passing geometry checks and separate mesh-bound volume fields. This particular
  change increased predicted drag by 0.162%; the viewer reports that outcome.
- Validation: 21 focused backend checks and 18 frontend checks passed; production
  build and diff checks passed. Browser comparison and both NVIDIA airflow fields
  verified. Original CSS bundle hash unchanged. Local API restarted with the flag;
  verification run finished and the GPU is idle.

## 2026-09-26 — search stopped; selected candidate replay

- User stopped further optimization and chose the previously reported 3.33%
  prediction (`tpe-0147`, 600.973328 N versus 621.695557 N). The search finished
  its in-flight evaluation and exited with 100 LHS / 90 TPE / 0 random controls /
  0 finalist repeats. All source records and the frozen original plan remain.
- A separate provisional replay path retains incomplete research status, reruns
  geometry checks and creates fresh surface/sensitivity/volume fields. It never
  marks the original experiment complete or accepted. Selection evidence is in
  `docs/evidence/sedan-research-2026-09-25/paused-demo/`.
- No further optimization or ranking jobs are scheduled. Synthetic dent work
  follows the selected candidate demonstration. Original layout and aircraft
  remain unchanged.
- Selected replay complete: `local-8907b340aebb4b1d800fb86c45451c71`, freshly
  reproduced 621.695557 → 600.973328 N (3.333%), actual maximum 32.174 mm.
- Synthetic hood dent complete: `local-ca75fe9aeef644539bd878baa617f84b`, freshly
  evaluated 621.695557 → 621.573425 N (-0.020%), actual inward maximum 11.302 mm.
  Prescribed geometry only; no impact, structural, home-scan or safety assessment.
- Both have fresh surface/sensitivity/volume fields. Independent artifact checks
  re-integrate forces, verify mesh/file hashes, rerun full-resolution geometry
  checks and bind each airflow field to its own mesh. Both pass these checks;
  neither has independent physical validation or research acceptance.
- Browser QA found that reduced display vertices understated the dent maximum.
  Metrics now use the full-resolution geometry evidence; linked comparisons show
  true scale with the same existing layout and controls.
- Final regression: 80 Python tests, 44 frontend tests and production build passed.
  Both scenarios are packaged in `.local/demo-sedan-and-dent-final-2026-09-26`
  with the original aircraft assets, export licenses and recorded-only server.
  No public deployment, commit or push was performed.

## 2026-09-25 — sedan headline study started

- Posthoc provenance audit identifies the sedan source STL as published DrivAerML
  run 1 by exact hash and preserves its 16-parameter vector and force coefficients
  at an immutable dataset revision. C2-to-ANSA mapping and checkpoint split
  membership remain unverified; the frozen search and acceptance policy are unchanged.
- V2 noise study complete: five baseline repeats at 621.6955566 N, ten tiny
  perturbations with SD 0.0968954 N. Frozen >1% and >5-sigma gates remain unchanged.
  Full search/control/confirmation is in progress; no final improvement claimed.
- An external tool-host interruption terminated the primary worker after 100 LHS
  and 35 TPE evaluations. All 349 recorded outcomes, the frozen plan and numerical
  sources passed integrity checks, and no worker or GPU lease survived. The same
  search resumed successfully, reconstructing its exact recorded proposals before
  evaluating new ones. The interruption receipt records the preserved hashes;
  possible interrupted-attempt overhead is separate from successful budgets.
- Backend regression: 74 tests passed, including published-ranking selection,
  strict phase budgets, guided execution/resume and
  recorded HTTP deployment; frontend: 42 passed and build passed.
- Original styling/layout and aircraft previews preserved. Research replays
  open at true scale using existing controls. Recorded deployment was rehearsed
  with the historical sedan result; this is not new scientific evidence.
- User requested synthetic crash/dent analysis, then explicitly prioritized
  finishing optimization first. Dent demo follows; no structural-safety claims.
- CFD mesh setup now passes the quality audit after tightening boundary skewness
  during meshing. One solver iteration verifies setup only; final converged
  baseline/candidate calculations are still pending.
- The two predeclared baseline CFD cases are now running on the local CPU while
  DoMINO searches on the GPU. Baseline reuse is conditional on exact matching
  protocol, STL, solver inputs, runner version and output hashes; altered-input
  and altered-force cache checks were verified to fail closed.
- Both baseline CFD cases subsequently finished: coarse 739.162061 N passed
  the force convergence check; fine 650.368448 N failed (last-100 range
  17.286757 N, about 2.66%, versus the frozen 0.2% limit). Both meshes passed
  `checkMesh`. These are baseline-only results, not an independent agreement
  claim. Receipts are in `independent-baseline-results.json`. The requested
  published-variant ranking fallback is being prepared without selecting by force.
- The five-case published-ranking fallback is now frozen and downloaded: runs
  1, 303, 296, 353 and 320, selected using range-normalized geometry distance.
  All source hashes and input geometry checks pass. GPU evaluation waits for
  primary optimization, controls and all nine repeats. It will not substitute
  for validation of the custom winner or claim held-out model performance.
- Nemotron qualification first scored 7/10, including a provider failure and
  two rejected interpretations. After clarifying the named preset and exact
  contiguous quotes, the second complete round scored 10/10 without response
  edits. Both rounds, prompts, inputs and source snapshots are retained under
  `docs/evidence/sedan-advisor-2026-09-26*`. These are recorded application briefs,
  partly scripted, not held-out human rulebook validation. Actual follow-on
  optimization will use the completed primary search plus the verified map.

- User authorized the full noise/morph/search/control/independent-check/Nemotron
  plan and required the original UI and aircraft features to stay unchanged.
- Added a separate local research workflow; protocol and success thresholds are
  predeclared in [SEDAN_RESEARCH.md](docs/SEDAN_RESEARCH.md). No new aerodynamic
  improvement is claimed. Research implementation and live verification are ongoing.
- Training-range analogues are explicitly distinguished from verified ANSA
  parameterization; approximate morphs cannot claim proven training membership.
- Deployment/demo work will center on reproducible sedan evidence while preserving
  existing aircraft exploration. No paid cloud GPU or publication has been started.

## 2026-09-20 — Nemotron runtime verified

- Verified `nvidia/Nemotron-3-Ultra-550b-a55b` in the authenticated Nebius
  Token Factory catalog and exercised live structured brief compilation and
  evidence-bound run Q&A.
- Sanitized runtime evidence is recorded in
  [`docs/evidence/nemotron-final.json`](docs/evidence/nemotron-final.json).
  Fifteen of sixteen exact evaluation checks passed; the remaining response was
  evidence-grounded but missed one expected comparison label. This verifies the
  runtime path without claiming a perfect evaluation score.

## 2026-09-20 — visible computation and idle GPU fix

- Added a labeled illustrative activity scan, replaced by actual baseline fields
  with a light sweep once available; studies now drive the main viewer's progress.
- Completed views pause, static frames render on demand, hidden views stop, and
  active flow/scan frame rates are capped. Inference completion and viewer playback
  are labeled separately. Nemotron stays enabled.
- Verified two real GPU jobs, reload recovery, zero idle redraws and linked camera
  updates. 57 Python + 41 frontend tests and production build pass.
- [Measured behavior and limits](docs/VIEWER_PERFORMANCE.md).

## 2026-09-20 — body-region expansion

- Added nose width, hood contour, side shoulders and rear-deck height alongside
  the existing rear tools; five-region comparisons start from the same original.
- Explicit region presets work without the language model. Compiler schema and
  frontend validation support all tools; aircraft shape editing remains blocked.
- Protected spatial envelopes replace the front-82% lock for the four new tools.
  The 4 mm limit and numerical/geometry acceptance gates remain unchanged.
- Fresh GPU surface and volume checks are recorded in the
  [production matrix](docs/evidence/body-regions-2026-09-20/production.json).
  Six cases completed with geometry checks passing; none passed every acceptance
  gate. Sedan hood: -1.605 N (-0.258%), refused on probe centering. Final-runtime
  hood repeat completed in 41.3 s with exactly matching candidate force and verified
  current worker hash; all seven stored candidates passed independent artifact audits.
- Browser QA verified front-facing hood changes, region-specific labels,
  aircraft exclusion and return to car controls. 57 Python and 37 frontend
  tests pass; production build passes (existing large-bundle warning).
- [Feature contract and limitations](docs/BODY_REGIONS.md).

## Previous snapshot

Last updated: 2026-09-19. Product plan: [PROJECT_PLAN.md](PROJECT_PLAN.md).
Implementation baseline: [`85f5ec5`](https://github.com/ASH1998/zephyr/commit/85f5ec51703898421f266bc55d45bdf15551cbd6), committed and pushed to `origin/main`.
Current phase: R01–R03 measurements and demo update completed. Force/pressure/shear
parity passed; raw partial sensitivity parity failed and remains an open limitation.

## Current snapshot

- Latest verification: **46 Python tests passed**, including fresh forward-force
  and cache-scope checks. The unchanged frontend previously passed 36 tests and
  production build; the updated acceptance/refusal replay walkthrough was checked.
- DrivAer passed the provisional local-surrogate policy at **0.375 mm**:
  predicted reduction **0.09645 N**, fresh reduction **0.09045 N**, prediction
  disagreement **6.22%**. Full-resolution geometry and intersection checks passed.
- Hatchback remained refused: failed local probe linearity, 59.64% candidate
  disagreement, and experimental model domain. A larger reduction did not bypass gates.
- Sedan runtime: **472.074 → 271.387 s (4m 31s)**, 42.5% less worker time.
  Two full sensitivity evaluations remain; five fresh calibration evaluations
  use forward-only inference and within-evaluation geometry encoding reuse.
- Matched sedan forces, probes, geometry, pressure/shear and decision are exact.
  Raw baseline partial sensitivity exceeds the frozen field tolerance in both
  the unmodified repeat and optimized run; this limitation is retained, not waived.
- All five production cases completed and passed independent artifact verification.
  The 0.375 mm sedan step remained accepted; 0.25 and 0.5 mm steps were refused.
  The hatchback remained refused at 3 mm and took 28.205 s. Its raw candidate
  sensitivity also exceeded tolerance; acceptance-driving outputs matched exactly.
- Acceptance means **accepted for further evaluation**, not engineering validation.
  Independent CFD and a transferable physical trust radius remain pending.
- Commit `85f5ec5` includes comparison, numerical fixes, tests and recorded evidence.
  Push succeeded to `ASH1998/zephyr` on `main`; the tree was clean after that push.
  The subsequent runtime implementation, evidence and documentation are local
  and have not been committed.

Evidence and policy: [ACCEPTANCE_CHECKS.md](docs/ACCEPTANCE_CHECKS.md).
New measurements: [RUNTIME_CHECKS.md](docs/RUNTIME_CHECKS.md).
The dated entries below preserve earlier states; this snapshot and the next-work
table describe the current handoff.

## Status rules

Use **Done** only with code or evidence; **Verified** means the stated check passed,
not that the physics is independently validated. Keep original evidence dates and
model/run identities. Add failures and decisions instead of silently removing them.
The archived plan is research history; the root plan controls current priorities.

## Completed and verified

| ID | Work | Evidence / location |
|---|---|---|
| D01 | Native Windows NVIDIA surface inference on local RTX 4070 Ti SUPER | `docs/WINDOWS_DOMINO_GATE.md`; `docs/evidence/local-domino-2026-09-18.json` |
| D02 | Strict local job API, original/candidate artifacts, polling, cancellation, fixed topology and bounded rear taper | `src/zephyr/local/server.py`, `worker.py`, `tests/test_local.py` |
| D03 | Nemotron brief compilation, server-owned intent binding, quote grounding and combined brief/slider ceiling | `src/zephyr/copilot.py`; `docs/LLM_INTERFACE.md` |
| D04 | Readable result summary and evidence-bound Q&A with follow-ups | `frontend/src/run-assistant.ts`; `src/zephyr/run_answers.py`; corresponding tests |
| D05 | Five-stage progress, actual batch counts, elapsed time, Change-view replay and labeled 120× enlargement | `frontend/src/run-progress.ts`, `live.ts`; frontend tests |
| D06 | Seven cars and two aircraft, detailed GLBs, simplified inference geometry, credits and pinned sources | `src/zephyr/local/cars.py`; `frontend/public/models/VEHICLE_CREDITS.md` |
| D07 | NVIDIA volume model integration; nine saved fields; fresh original/candidate fields during car tests | `src/zephyr/local/volume.py`; `config/domino-volume-artifacts.json`; `tests/test_airflow.py` |
| D08 | Explicit Flow illustration / NVIDIA prediction toggle; timed moving ribbons, pause/resume, preserved raw prediction paths | `frontend/src/flow-ribbons.ts`, `airflow.ts`, `scene.ts`; browser checked |
| D09 | Paired opposite-turning wingtip spirals, wider car corridor over twice body width | `frontend/src/flow-illustration.ts`; placement/rotation/width tests; both planes visually checked |
| D10 | Model switches clear previous results; aircraft reject car deformation requests | Geometry/flow identity tests and both aircraft request-validator tests |
| D11 | Original vehicle/airflow implementation committed and pushed | `0c40934b95e20e837f48a59f29800f2d45090921` |
| D12 | Plan audit and tracking document | Root plan rewritten; old research plan preserved in `docs/archive/`; current doc inconsistencies corrected |
| D13 | Linked Original / Changed comparison and presentation regression | Completed N01–N08 below; `docs/evidence/presentation-2026-09-19/` |
| D14 | Batch-gradient correction, fresh normals and geometry-safe full-pipeline probes | `src/zephyr/local/sensitivity.py`, `trust.py`; `tests/test_acceptance.py` |
| D15 | Exact-predicate intersection audit and scoped local acceptance | `src/zephyr/local/intersections.py`; final sedan/hatchback evidence in `docs/evidence/acceptance-2026-09-19/` |
| D16 | 79 automated tests, production build, real acceptance/refusal and model explanation checks | Acceptance-hardening entry below; `docs/ACCEPTANCE_CHECKS.md` |
| D17 | Presentation and acceptance changes committed and pushed | `85f5ec51703898421f266bc55d45bdf15551cbd6`, `origin/main` |

## Recorded GPU evidence

Current detailed assets: [detailed-vehicles-aircraft-smoke.json](docs/evidence/detailed-vehicles-aircraft-smoke.json).

- Hatchback run `local-336be40999c940e9acff6f83fa10bd8a`: 22.087 s total;
  original 474.9229 N → candidate 473.5019 N (about −0.299%); 3.6 mm max movement;
  protected coordinates unchanged; both volume fields generated. Acceptance refused
  because calibration/full intersection checks are incomplete. Timing is one run,
  not a latency guarantee, and the lower estimate is not independently proven.
- Global Hawk run `local-7e61426fe5664b8e9de44a8a3e8dbfe3`: 14.405 s total;
  original-only surface and volume output, no candidate; 3.3 m scaled aircraft.
- `seven-cars-volume-smoke.json` covers retired blockout models. Keep it as historical
  evidence only. Do not attach its numbers to the detailed replacements.
- `output/understanding-zephyr/` contains earlier full-page annotated explanations;
  screenshots and UI descriptions there precede the current volume/illustration views.

## Historical verification before presentation and acceptance work

2026-09-19, before the plan-only changes:

- **32 Python tests passed**: `python -m unittest discover -s tests`.
- **29 frontend tests passed**: `npm.cmd --prefix frontend test`.
- **Production build passed**: `npm.cmd --prefix frontend run build`.
- `git diff --check` passed. Configured credential scan of the committed changes
  found no matches; `.env` and `.local/` remain ignored.
- Browser: sedan/hatchback, both planes, separate flow modes, wider car corridor,
  visible wingtip spirals, pause/resume; paused screenshot pair identical;
  no observed browser console errors in checked tabs.
- Known warning: frontend bundle about 759 KB before gzip.

This is not a complete regression of every UI action and is not CFD validation.

## Completed presentation checklist

| ID | Priority / status | Work and acceptance |
|---|---|---|
| N01 | P0 / Done + Verified | Audit current app, run tests/build, inspect existing recorded result, log reproducible bugs; don't rebuild completed stages or Q&A |
| N02 | P1 / Done + Verified | Implement simultaneous original/changed car comparison with linked camera/zoom, consistent scales and explicit actual/magnified display |
| N03 | P1 / Done + Verified | Bind both views to the same completed run and their own fields; original-only or missing-field states cannot imply a calculated candidate |
| N04 | P1 / Done + Verified | Validate readable progress and verdict for improvement, worsening, no candidate, failure and cancellation; retain run-bound Q&A |
| N05 | P1 / Done + Verified | Browser-check roughly 979×882 and wide desktop; both flow modes, field views, synchronized orbit/zoom, reduced motion, pause/reset and cleanup |
| N06 | P2 / Done + Verified | One fresh local car iteration with real event progression; verify no duplicate GPU job, correct current run IDs, hashes, forces and displacement |
| N07 | P2 / Done + Verified | Write a 60-second rehearsal script and clearly labeled recorded fallback; finish with aircraft vortices; report actual live duration |
| N08 | P2 / Done + Verified | Update this log with files, commands, test counts, run IDs, screenshots/observations, and remaining limitations |

N01–N08 are complete; do not restart them as unfinished work. Use saved artifacts
for repeated UI development and reserve GPU runs for meaningful verification.

## Repeatability and runtime milestone — authorized 2026-09-19

| ID | Priority / status | Work | Completion evidence |
|---|---|---|---|
| R01 | P0 / Measured; sensitivity limitation | Establish repeatability around the accepted sedan step: repeat the accepted case in a separate process, test a small predeclared set of smaller/larger budgets, and retain a refused control. Keep policy thresholds fixed. | Record every requested/effective step, predicted/fresh change, decision, source hash and duration. Explain any decision changes; one accepted case is not broad calibration. |
| R02 | P0 / Implemented; force parity verified | Profile the 472 s sedan path and reduce unnecessary work. Investigate forward-only repeat/probe evaluations and reusable inputs where mathematically valid; preserve a fresh candidate evaluation. | Compare against the current raw-force and field evidence within explicit numerical tolerances; preserve geometry/acceptance decisions, cancellation and GPU leases. Report measured latency, not a promised speed target. |
| R03 | P1 / Verified | Update the 60-second walkthrough to show the accepted sedan alongside the refused hatchback. Present long computations using clearly labeled replay. | Browser rehearsal with correct movement, prediction disagreement, real elapsed time, acceptance scope and run IDs; no implication of a live sub-minute sedan run. |
| R04 | P2 / Nemotron verified; public demo pending | Keep the verified Nemotron runtime path and prepare competition/public-demo requirements. | The authenticated catalog, structured brief schemas and evidence-bound Q&A are verified in `docs/evidence/nemotron-final.json`; recheck deployment and judge-access requirements before making public-demo claims. |
| R05 | Research / Pending | Compare the original and accepted candidate with independent CFD and quantify numerical uncertainty. | Establish whether the very small surrogate reduction is resolvable and whether its direction agrees with independent simulation before claiming physical improvement. |

The reference evidence and policy were frozen before optimization. The production
matrix is complete; force-only profiling passed with exact outputs on both shapes.
Within-evaluation encoding reuse shares an identical intermediate across batches;
every mesh evaluation remains fresh, with no cross-run evidence reuse. Baseline
and candidate autograd remain unchanged. Full raw sensitivity parity has a
documented failure; no tolerance or trust threshold was relaxed.

The user authorized this local GPU work and demo update. Nemotron is verified and
selected; paid cloud resources, deployment and independent CFD are deferred.

## Deferred and release gaps

- Public-demo packaging and clean-start rehearsal of the verified Nemotron path.
- Official competition requirements/deadlines/runtime eligibility recheck.
- Nebius GPU deployment, public judge demo, rate limits and clean-install rehearsal.
- Raw partial sensitivity reproducibility: the unmodified repeat, optimized
  sedan baseline and hatchback candidate exceed the field tolerance; pressure/shear and
  acceptance-driving forces remain exact.
- Multi-handle optimization and a transferable calibrated trust radius.
  Full triangle intersection checking is now implemented and tested locally.
- Independent CFD, public-case benchmarking and verified held-out split.
- Scan/upload/import workflow; arbitrary geometry and aircraft optimization.
- Candidate STL export and broad design history are not established deliverables.

Presentation and local acceptance hardening are complete. Keep these remaining
limits visible without presenting research gates as implemented features.

## Local handoff details

- Actual application repository: `F:\github\nebius\zephyr` (separate Git repository).
- Saved Codex project `nebius` points to parent `F:\github\nebius`; a parent
  worktree does **not** contain this nested untracked application. Verify Git root.
- Application baseline is on Zephyr `main`, remote `git@github.com:ASH1998/zephyr.git`.
- Python: `F:\github\nebius\.venv\Scripts\python.exe`.
- UI: `http://127.0.0.1:5173/`; API: `http://127.0.0.1:8766/api/health`.
- Check health and active run before starting/restarting anything. Keep the unrelated
  8765 server intact. Existing local GPU and configured development-model testing
  are authorized; do not launch paid cloud GPU resources.
- Launch only if needed: `python -X utf8 -m zephyr.local.server --enable-llm --port 8766`
  from the actual repo; `npm.cmd --prefix frontend run dev` for Vite.
- Never print `.env`. Keep Nemotron selected during this milestone. Use CUA for browser
  inspection and a temporary tab to avoid disrupting the user's active page.
- N01–N08 are complete. R01–R03 are the authorized runtime/repeatability milestone;
  preserve all outcomes and the raw sensitivity limitation in the handoff.

## Change log

- 2026-09-19: audited implementation at `0c40934`; rewrote active plan around
  presentation-first milestones; retained original research; created tracking and
  testing checklist. No new comparison implementation or GPU run during this audit.

## Historical presentation handoff

- Task: Zephyr: test the app and build linked before-and-after comparison.
- Task ID: `01a0b8d3-73f0-7db1-838f-d38255d15c6e`.
- Started 2026-09-19 with N01–N08, runtime/evidence details, and instructions to preserve these documentation edits.
- Uses the local saved project and the explicit Zephyr repository path; the parent repository has no HEAD commit, so a parent worktree could not be created.
- First response confirmed audit/testing before comparison implementation and recorded results before a fresh GPU run.

## Presentation milestone audit (2026-09-19)

- N01: inspected the existing detailed hatchback artifact and API health while idle. Existing suite passed: 32 Python, 29 frontend; build 759.24 kB. Initial sandbox attempts failed with Windows file/process permission errors; the same commands passed with process access.
- All nine geometry choices reached airflow-ready in a temporary hidden CUA tab. X-57 illustration visibly has paired wingtip spirals; prediction switches to independent volume paths. Pause and camera reset work.
- Reproducible code finding: the enlargement multiplier affected Pressure/Sensitivity/Mesh as well as Change; fixing it to apply only in Change. Candidate volume absence previously fell back to original geometry/flow; linked comparison will show an unavailable field instead.

## Presentation milestone delivery (2026-09-19)

### Implementation

- `frontend/src/comparison.ts` and `comparison-data.ts`: discoverable Original / Changed comparison for completed car runs with a real, freshly evaluated candidate. Linked camera orbit/zoom/reset, identical lighting, shared pressure/sensitivity/displacement ranges and one playback clock. Narrow layouts stack the pair. Each side selects its own surface and volume fields from the same validated run.
- `frontend/src/scene.ts`: fixed comparison endpoints, changed-shape sensitivity colors, true-scale Airflow/Pressure/Sensitivity/Mesh, enlargement only in Change, explicit unavailable volume instead of substitution in the pair. Reduced motion starts paused; explicit Resume can animate. Offscreen render work is skipped; observers, linked cameras, animation frames, scene resources and WebGL contexts are released on disposal.
- `frontend/src/live.ts`: completed-run gating, labeled `?replay=<runId>` recovery, comparison/stale-result clearing on new runs and geometry changes, no saved-field substitution in completed runs, and guarded async installs. Replay URLs are cleared when selecting a new shape or starting a new run.
- `frontend/src/detailed-vehicle.ts`: release loader source geometry/materials and superseded asynchronous assets.
- `frontend/src/run-progress.ts`: reuse existing stages; add a publication state so a worker-complete event cannot announce a baseline-only conclusion while the API is still publishing the candidate. Second-pass smoothing stays in the changed-shape stage.
- `frontend/src/style.css`: comparison layouts with labels and controls outside the model panels.
- `frontend/tests/comparison.test.ts`: four new regression tests for eligibility, honest verdicts, shared playback and worker/API completion timing.
- `frontend/tests/browser-harness.html`: development-only labeled fixtures for missing candidate volume, failure, cancellation, running, publication and reduced motion. Blocks every POST and is excluded from the production build.
- `docs/DEMO_60_SECONDS.md`: rehearsable recorded walkthrough, explicit fallback labeling, honest live timing and aircraft finale.

### Verification and observed fixes

- Final automated suite: **32 Python + 33 frontend tests passed**; production build passed. Bundle ~768.3 kB (~201.6 kB gzip), up ~9.0 kB / 1.2% from 759.24 kB. Existing large-chunk warning remains; no formal FPS or GPU-memory benchmark was performed.
- CUA browser checks used temporary hidden tabs. Tested 979x882 stacked comparison and 1440x1000 desktop pair, both field sources, actual/enlarged Change, pressure/sensitivity, camera orbit/zoom from either side, reset, pause/resume, close/reopen and geometry switching. All nine previews reached ready. Original illustration trails are repeated unchanged on both sides and explicitly labeled, with no improvement claim.
- Original/candidate field binding is validated by existing schema/hash gates and the fresh-run checks below. Missing-volume fixture visibly shows no paths on the Changed side and says unavailable. Running/failed/cancelled fixtures show no comparison and candidate force remains absent. Recorded Global Hawk baseline has no pair or candidate. Publication fixture waits for the complete result, without claiming completion early.
- Reduced-motion fixture started paused with identical screenshots across observations. Closing comparison reduced rendered canvas count from three to one; changing geometry cleared numbers, old Q&A and the pair, leaving one canvas. Browser console inspection returned no warnings/errors in the checked result tab.
- Existing run Q&A was preserved. On the fresh run, “Why was it rejected?” explained incomplete validation; follow-up “Does that mean the cabin moved?” answered that the protected cabin stayed exactly fixed and the rear moved 3.000 mm.
- Bugs actually found: enlargement leaking into other field views; stale original scene at new job start; premature baseline-only completion during result publication; second-pass smoothing reverting the progress narrative. These are corrected. A small raster change while paused led to removal of redundant camera updates in linked scenes; final paused comparison screenshots were byte-identical.
- Screenshots: `docs/evidence/presentation-2026-09-19/` contains wide/narrow Change, own-field volume, reduced-motion fixture and aircraft views. Fixtures and recorded replays are labeled; screenshots are visual QA, not scientific validation.

### Exactly one fresh local GPU iteration

Run **`local-f76a1757dc7d4143abbbd8f69e53d5f3`**, Impreza hatchback.
Brief: “Reduce drag with a small rear taper. Keep the cabin unchanged. Limit movement to 3 mm.”
The configured development model parsed the brief; the 3.0 mm brief limit correctly overrode the 3.6 mm slider ceiling. This historical run predates the verified Nemotron qualification above.

- Original force: **474.9229126 N**; changed force: **473.4724731 N**.
- Difference: **-1.4504395 N (-0.3054%)**, an estimate only.
- Maximum actual movement: **3.0000000 mm**; all **14,967 protected vertices** exactly unchanged; triangle topology unchanged.
- Worker total: **22.5813837 s** (baseline 2.9831 s, changed surface 1.7159 s; total also includes other worker work). This excludes brief interpretation, browser loading/polling and publication overhead; it is not a 60-second live guarantee.
- Original surface/volume hash: `7c3558aa9e514dd2a5414f6e2f216c28ddff47b4ac6776c5cd115ebb421dd0bd`.
- Changed surface/volume hash: `49f5eb76a1685294a4e7ef0d1cc57415c690f278710be66008bb27a743091e84`.
- Both fresh volume fields were present; surface field arrays differed. Geometry checks remain incomplete and acceptance is **refused**. Independent CFD was not run.
- Evidence: `docs/evidence/presentation-2026-09-19/fresh-run.json` includes real event sequence, forces, timings, source identity, volume binding, intent/model provenance and validation. Full artifacts remain under `.local/runs/<runId>/`.
- API was idle before the request and again after completion. One iteration request was started; all other UI development used recorded artifacts/fixtures. No services were restarted and port 8765 was untouched.

### Remaining limits

Engineering acceptance, calibration, full intersection validation and independent CFD remain pending. Aircraft are experimental scaled models with baseline analysis only. Model migration and cloud deployment remain deferred. Failure/cancellation/partial publication were browser-tested with labeled fixtures rather than interrupting an extra expensive GPU job. Reduced motion was emulated in the development fixture without altering the user's OS setting. No public deployment or Git commit was made; prior documentation edits are preserved.

## Acceptance hardening — 2026-09-19, subsequent authorized milestone

User requested “lets fix this and test” after reviewing unconditional refusal
and the misleading tiny-denominator prediction-error percentage. The earlier
presentation milestone's one-run constraint applied to that completed milestone;
this work used five separately recorded local GPU regression runs.

- Fixed cumulative upstream leaf gradients being counted repeatedly across batches
  with a scoped local hook; pinned NVIDIA files remain unchanged. Normal arrays
  are rebuilt from current geometry, with consistent float64 mesh preprocessing.
- Replaced the partial-centroid gradient as controller predictor with separate
  +/-h and +/-h/2 full-pipeline probes plus a baseline repeat. Probes shrink
  through the unchanged geometry gates before evaluation. The candidate is
  separate from the probes and must agree with their prediction.
- Added versioned provisional numerical criteria, required-check enforcement,
  absolute N error, unresolved-relative-error handling, and experimental-domain
  refusal. Accepted means local surrogate check passed for further evaluation;
  `engineeringValidated` is false and physical CFD remains not-run.
- A regression exposed PyMeshLab's missed coplanar containment. Replaced it with
  pinned libigl 2.6.3 AABB/exact predicates; crossing, coplanar, separated, closed
  mesh and unavailable-checker regressions pass. Temporary PyMeshLab removed.
- Final sedan **local-c29499fe827b4d7e9b7ac01f29ff8428**: 621.6955566 ->
  621.6051025 N; predicted reduction 0.0964508 N vs actual 0.0904541 N;
  **6.2174% change-relative error, 0.0059967 N absolute difference**. Requested
  3 mm shrank to a 0.375 mm outward step. All 340,330 protected vertices fixed;
  topology/bounds/normal/area/closed-surface/full intersection checks passed.
  Local step accepted; worker 472.074 s including separate volume inference.
- Final hatchback **local-dfd56fe51ebc497a9d768d7498cede7a**: 474.9229126 ->
  473.7896118 N at 3 mm, 59.6423% change-relative disagreement and failed probe
  midpoint check. Refused; experimental domain is an additional exclusion.
  Geometry checks passed and all 14,967 protected vertices stayed fixed.
  Worker 30.433 s. Both final baselines repeated exactly; this is not physical
  uncertainty validation.
- `scripts/verify-local-acceptance.py` independently checked raw VTK hashes,
  full mesh constraints, exact intersections, force reintegration, decisions
  and surface/volume bindings. Largest force reintegration difference 0.000130 N.
  Final run local numerical source hashes all match the final source files.
- **43 Python + 36 frontend tests passed**; production build passed (770.43 kB /
  202.32 kB gzip), existing chunk warning only. Browser checked real acceptance,
  refusal, explicit synthetic acceptance fixture, updated comparison verdict,
  and the model's accepted-step answer with the physical-validation limitation.
  No browser console errors/warnings in checked tabs. Temporary browser tab closed.
- API 8766 restarted while idle with model calls enabled to load updated
  explanations; final health is idle and port 8765 untouched.
  No deployment, commit or push. Prior edits and historical run artifacts remain.

Full policy, development-run IDs, commands and limits: [ACCEPTANCE_CHECKS.md](docs/ACCEPTANCE_CHECKS.md).
Final compact verified artifacts and browser screenshots:
`docs/evidence/acceptance-2026-09-19/`.


## Runtime and repeatability results — 2026-09-19

- The frozen five-case plan is complete. `trust.py` SHA-256 remains
  `2a4319a95a50d5a724dcf2c7aadf062eacca4574db4ce6eb52ea835e50623d69`.
- Unmodified sedan repeat: `local-cdd1b1d4afbf40b8b5e9af03e8c07ddb`, 459.679 s,
  accepted at 0.375 mm; all forces, pressure/shear and geometry matched exactly.
- Optimized matching sedan: `local-cb9886c7e716448e957a595e4556a9d7`, 271.387 s,
  accepted at 0.375 mm, 6.22% candidate disagreement, exact force/pressure/shear
  parity. Worker time fell 42.5% against the original 472.074 s reference.
- Smaller budget: `local-26b4f0c324844c4d9fd17cc066df9c71`, 0.25 mm, 268.852 s,
  refused: unresolved fine probes, 79.48% slope disagreement, failed centering,
  434.58% candidate disagreement. Browser rehearsal overlapped this measurement.
- Larger budget: `local-830086728750406597352c1ce6576dd3`, 0.5 mm, 268.240 s,
  refused: probe midpoint offset 0.020782 N exceeds the 0.008738 N allowance,
  despite only 8.20% candidate disagreement. No safe-radius claim follows.
- Hatchback control: `local-f9d19c3398f84b9cabbef3ca574d45d2`, 3 mm, 28.205 s,
  refusal and forces/pressure/shear matched the reference exactly.
- Raw partial sensitivity exceeded rtol=1e-6 / atol=1e-5 in the unmodified sedan
  baseline (max 1.297891e-5 N/m), optimized sedan baseline (3.832579e-5 N/m), and
  hatchback candidate (1.591444e-5 N/m). Full field parity is **failed**. These
  fields do not drive acceptance; no tolerance or policy threshold was relaxed.
- All five runs passed independent raw-artifact verification: full geometry,
  protected coordinates, exact intersection audit, force reintegration and
  recomputed verdict. Each optimized run has both fresh volume fields, and its
  recorded numerical source hashes match the final files. Both GPU leases released.
- Forward-only profiling matched full autograd pressure/shear/force arrays exactly
  on both cars. Within-evaluation geometry reuse reduced the sedan forward path
  from 52.405 to 20.558 s; baseline/candidate sensitivity paths remain unchanged.
- **46 Python tests passed** including cache mutation/scope/error restoration,
  analytic two-batch force integration and existing cancellation/lease tests.
  Frontend code was unchanged; its prior 36 tests and production build still form
  the baseline. Browser rehearsal checked both frozen replays and no console errors.
- The 60-second script now shows accepted sedan and refused hatchback, with explicit
  recorded labels, original run timings, actual movement, enlargement and CFD limits.
- Runtime code, scripts, evidence and docs are local, uncommitted changes after
  `85f5ec5`. Nemotron is now verified and configured. No cloud resource or CFD run.

Evidence: [RUNTIME_CHECKS.md](docs/RUNTIME_CHECKS.md),
[matrix](docs/evidence/runtime-2026-09-19/matrix.json),
[verification summary](docs/evidence/runtime-2026-09-19/summary.json).
Next numerical work: investigate partial sensitivity variability and design a
predeclared calibration study across probe scales. Independent CFD is required
before interpreting this small surrogate reduction as physical improvement.
