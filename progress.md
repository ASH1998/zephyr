# Zephyr progress

Last updated: 2026-09-19. Product plan: [PROJECT_PLAN.md](PROJECT_PLAN.md).
Implementation baseline: `0c40934` (pushed to `origin/main`).
Current phase: presentation milestone implemented and verified locally.

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
| D03 | GLM brief compilation, server-owned intent binding, quote grounding and combined brief/slider ceiling | `src/zephyr/copilot.py`; `docs/LLM_INTERFACE.md` |
| D04 | Readable result summary and evidence-bound Q&A with follow-ups | `frontend/src/run-assistant.ts`; `src/zephyr/run_answers.py`; corresponding tests |
| D05 | Five-stage progress, actual batch counts, elapsed time, Change-view replay and labeled 120× enlargement | `frontend/src/run-progress.ts`, `live.ts`; frontend tests |
| D06 | Seven cars and two aircraft, detailed GLBs, simplified inference geometry, credits and pinned sources | `src/zephyr/local/cars.py`; `frontend/public/models/VEHICLE_CREDITS.md` |
| D07 | NVIDIA volume model integration; nine saved fields; fresh original/candidate fields during car tests | `src/zephyr/local/volume.py`; `config/domino-volume-artifacts.json`; `tests/test_airflow.py` |
| D08 | Explicit Flow illustration / NVIDIA prediction toggle; timed moving ribbons, pause/resume, preserved raw prediction paths | `frontend/src/flow-ribbons.ts`, `airflow.ts`, `scene.ts`; browser checked |
| D09 | Paired opposite-turning wingtip spirals, wider car corridor over twice body width | `frontend/src/flow-illustration.ts`; placement/rotation/width tests; both planes visually checked |
| D10 | Model switches clear previous results; aircraft reject car deformation requests | Geometry/flow identity tests and both aircraft request-validator tests |
| D11 | Full implementation committed and pushed | `0c40934b95e20e837f48a59f29800f2d45090921` |
| D12 | Plan audit and tracking document | Root plan rewritten; old research plan preserved in `docs/archive/`; current doc inconsistencies corrected |

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

## Last verification

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

## Next task checklist

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

Do not start N02 before N01 identifies which behavior already works. Use saved
artifacts for repeated UI development, and reserve GPU runs for meaningful end-to-end
verification. If there is no fresh result, say so; do not manufacture evidence.

## Deferred and release gaps

- Nemotron configuration switch and fresh runtime/schema/Q&A verification.
- Official competition requirements/deadlines/runtime eligibility recheck.
- Nebius GPU deployment, public judge demo, rate limits and clean-install rehearsal.
- Multi-handle optimization, calibrated trust, full self-intersection checking.
- Independent CFD, public-case benchmarking and verified held-out split.
- Scan/upload/import workflow; arbitrary geometry and aircraft optimization.
- Candidate STL export and broad design history are not established deliverables.

The user prioritizes clear presentation. Keep these limitations visible without
blocking ordinary UI work or presenting later research gates as implemented features.

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
- Never print `.env`. Keep GLM selected during this milestone. Use CUA for browser
  inspection and a temporary tab to avoid disrupting the user's active page.
- The next task should test and implement N01–N08, not just produce another plan.

## Change log

- 2026-09-19: audited implementation at `0c40934`; rewrote active plan around
  presentation-first milestones; retained original research; created tracking and
  testing checklist. No new comparison implementation or GPU run during this audit.

## Active handoff

- Task: Zephyr: test the app and build linked before-and-after comparison.
- Task ID: `01a0b8d3-73f0-7db1-838f-d38255d15c6e`.
- Started 2026-09-19 with N01–N08, runtime/evidence details, and instructions to preserve these documentation edits.
- Uses the local saved project and the explicit Zephyr repository path; the parent repository has no HEAD commit, so a parent worktree could not be created.
- First response confirmed audit/testing before comparison implementation and recorded results before a fresh GPU run.

## Presentation milestone audit (2026-09-19)

- N01: inspected the existing detailed hatchback artifact and API health (idle, GLM retained). Existing suite passed: 32 Python, 29 frontend; build 759.24 kB. Initial sandbox attempts failed with Windows file/process permission errors; the same commands passed with process access.
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
GLM remained `zai-org/GLM-5.3-Flash`; the 3.0 mm brief limit correctly overrode the 3.6 mm slider ceiling.

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
  and GLM's accepted-step answer with the physical-validation limitation.
  No browser console errors/warnings in checked tabs. Temporary browser tab closed.
- API 8766 restarted while idle with existing GLM-enabled flags to load updated
  explanations; final health is idle, GLM unchanged, port 8765 untouched.
  No deployment, commit or push. Prior edits and historical run artifacts remain.

Full policy, development-run IDs, commands and limits: [ACCEPTANCE_CHECKS.md](docs/ACCEPTANCE_CHECKS.md).
Final compact verified artifacts and browser screenshots:
`docs/evidence/acceptance-2026-09-19/`.
