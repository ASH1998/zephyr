# Zephyr — current project plan

2026-09-26 implementation update: [Bring your own car](docs/BRING_YOUR_OWN_CAR.md)
adds experimental mesh and photo-template imports, orientation/scale review,
immutable registered geometry, baseline/airflow jobs and conservatively gated
shape tests. Existing catalog assets, replays, aircraft and acceptance policy are
preserved. The ten-photo qualification and measured training-spread validation
remain pending; earlier statements that uploads are unimplemented are historical.

2026-09-26 user revision: stop further optimization, retain the saved approximately
3.33% candidate as a provisional demonstration, then add a synthetic sedan dent
comparison. Preserve the original UI and aircraft. The incomplete research gates
stay incomplete; no further search or comparison experiment is scheduled.

2026-09-25 priority: implement and verify the [sedan headline research protocol](docs/SEDAN_RESEARCH.md),
then prepare reproducible sedan demo/deployment artifacts. Preserve the original
UI and aircraft features. The seven-part user plan supersedes the older next-work
priorities below; historical milestones and their evidence remain valid records.

2026-09-20 implementation update: [multi-region body exploration](docs/BODY_REGIONS.md)
adds nose, hood, side and rear-deck tools, a five-region comparison, explicit
presets, region-aware presentation and checkpoint input checks. This supersedes
the rear-only editing description below; historical validation limits remain.

Updated: 2026-09-19. Committed implementation baseline: `85f5ec5` on `main`.
Status: before-and-after demo and local acceptance checks completed; independent physical validation remains pending.
Tracking: [progress.md](progress.md). Earlier research and its source list are retained in
[the archived plan](docs/archive/PROJECT_PLAN_RESEARCH_2026-09-18.md).

## 1. Product direction

**Zephyr — Shape the flow.** Explore a vehicle, describe a bounded change, run the
NVIDIA models, and understand what changed and what the result means.

The presentation milestone made the GPU result visible: a non-expert should see
motion, understand GPU progress, and distinguish the original from the changed
shape. On 2026-09-19 the user promoted acceptance fixes and testing to active work.
Local numerical checks are specified in [ACCEPTANCE_CHECKS.md](docs/ACCEPTANCE_CHECKS.md).
Independent physical validation remains separate. Attractive illustrations must still be identified as
illustrations; physical improvement cannot be invented to make the demo work.

The hero story remains a car design change. Aircraft extend visual exploration;
they do not currently support shape optimization or validated flight analysis.

## 2. What exists today

| Area | Implemented behavior | Limits |
|---|---|---|
| Geometry | DrivAer sedan, Impreza hatchback, Hummer SUV, touring wagon, M3 coupe, Veneno sports car, Sprinter van; NASA X-57 and Global Hawk | Wagon is an adapted hatchback; planes are scaled to 3.3 m span; additional shapes are outside car-model training distribution |
| Detailed models | Licensed GLBs, preserved materials, closed simplified inference surfaces, pinned source manifests and credits | Inference surface approximates the detailed visible model |
| Brief copilot | Configured GLM `zai-org/GLM-5.3-Flash`, grounded quotes, schema validation, intent binding and stricter brief/slider limit | Nemotron switch and runtime acceptance tests remain pending; one supported car handle |
| GPU surface work | Local NVIDIA DoMINO pressure, wall shear, force, sensitivity; original and fresh candidate evaluation | Model estimates, not independent CFD |
| Geometry editing | Deterministic rear-width taper in last 18% of car length; cabin/front/underbody protected; fixed faces; shrink/refuse gates | At most one candidate per run; no broad optimization, upload or multi-handle search |
| GPU volume work | Separate NVIDIA volume checkpoint; saved baseline paths for all nine geometries; fresh original/candidate fields during car iteration | Steady predicted velocity, not time-resolved turbulence; car-trained model is experimental on planes |
| Flow illustration | Default blue paths around original geometry; broad car corridor; orange paired wingtip spirals turning in opposite directions | Authored explanation, not computed speed or candidate improvement |
| NVIDIA prediction view | Separate toggle; mesh-bound paths, true sample timing slowed for display, moving streaks, remote paths filtered | Do not substitute illustrative vortices into this view |
| Existing comparison | Linked Original / Changed views, field modes, actual mm, 120× Change-view enlargement, replay | Available for completed car runs with a real candidate |
| Progress | Five plain-English stages, elapsed time, real batch counts, cancellation and failure states; browser regression completed | Percentages describe stages, not a promised finish time |
| Result explanation | Readable deterministic summary, evidence-bound Q&A and follow-ups, expandable calculation checks; acceptance and refusal checked | Local surrogate evidence, not an unconstrained engineering assistant |
| Evidence | Downloadable run JSON, source hashes, retained VTK/raw fields, exact intersection audits and local handle calibration | Independent CFD and transferable physical calibration remain pending |

See [vehicle/airflow details](docs/CARS_AND_AIRFLOW.md),
[local GPU workflow](docs/LOCAL_DOMINO.md), and [copilot contract](docs/LLM_INTERFACE.md).

## 3. Completed presentation milestone: make the GPU result obvious

### P0 — audit and regression before new UI

Use the existing local app and a recorded completed run first. Verify the nine
models, flow toggle, wingtip vortices, wide car flow, pause/resume, camera reset,
view switching, and stale-result clearing. Run the existing automated tests and
production build. Log actual failures with reproducible steps in `progress.md`.
Do not rebuild the progress stages or result explanation; they already exist.

### P1 — simultaneous original/changed comparison

- Add a discoverable Compare view for completed car runs with a real candidate.
- Show Original and Changed together, using the same run, camera orientation,
  zoom, lighting, field scale and playback clock. Orbit either side to move both.
- Show actual displacement and clearly label any display enlargement. Keep
  Airflow at true geometry scale; magnification belongs in Change view.
- Compare each shape's own pressure and NVIDIA volume data. If a candidate
  field is missing, show it as unavailable or clearly label original-only flow.
- Keep default original-shape illustration separate from calculated improvement.
  Do not invent narrower wakes, smaller vortices, or a better number after a run.
- Below the pair, state the force difference in N and %, whether resistance went
  up or down, and acceptance status as a separate conclusion.
- Baseline-only, running, cancelled and failed jobs must never show a fake pair.
- At narrow widths, use stacked synchronized views or a clearly named A/B switch.
  Keep labels readable and controls clear of the models at roughly 979×882 and
  a wider desktop viewport. Respect reduced motion and dispose GPU/render resources.

Done when an unfamiliar viewer can identify the original, the changed area,
the actual movement and the calculated outcome without reading technical checks.

### P2 — connect progress and result to the comparison

Reuse `run-progress.ts`, `run-assistant.ts` and the current backend events.
Confirm the story reads: testing original → making a small change → checking it
→ testing changed shape → comparing results. Percentages must refer to actual
reported batches, not elapsed-time guesses. GPU computation should not be depicted
as a physically meaningful continuously deforming car during inference.

Keep the verdict honest: improved estimate, worsened estimate, unchanged result,
and missing candidate all need correct copy. A lower estimate can coexist with
refused engineering acceptance. Preserve Q&A run binding and follow-up context.

### P3 — repeatable 60-second walkthrough

Use the detailed hatchback as the first rehearsal candidate, since a completed
run already exists. Start with a recorded run clearly labeled as replay; then
verify the live path on the local GPU. Show one brief, protected cabin, progress,
side-by-side change and a plain-English verdict. End with an aircraft vortex view.
A slow live run may exceed 60 seconds: report real duration and use an explicitly
labeled replay for the short presentation. Do not promise a fixed live latency.

Deliver a short demo script, browser-tested steps, and evidence references.
A worsened/refused result is an acceptable demo outcome; do not cherry-pick a
lower number and describe it as validated aerodynamic improvement.

## 4. Later milestones

1. **Nemotron and competition readiness:** verify exact available Nemotron ID,
   endpoint, schema output and Q&A; switch explicitly, record identity/latency and
   compare supported briefs. Keep GLM for development until this planned switch.
   Recheck official rules, deadlines, runtime requirements and judge access before
   publishing competition claims. Dates and cloud architecture in the archived
   research plan are not newly verified here.
2. **Public demo:** reproducible setup, deployment and credential isolation,
   recovery, usage limits, asset notices, judge path and clean-install verification.
   Local GPU success is not evidence of Nebius GPU deployment. Paid cloud resources
   require an explicit budget/authorization; existing enabled model calls are authorized.
3. **Design exploration:** add and validate semantic handles before multi-candidate
   search. Calibrate repeatability and gradient direction; show full outcomes.
4. **Scan/upload pipeline:** asset upload, units/orientation, cleanup, watertight
   proxy, protected regions and a supported-domain check. Scanning and arbitrary
   uploads are not implemented. Do not imply any scan is simulation-ready.
5. **Scientific validation:** transferable calibrated trust radius,
   held-out benchmarking, independent CFD and direction/ranking checks. Preserve
   the archived benchmarks as future research targets, not hackathon UI blockers
   or completed results. No flight-performance claims from aircraft previews.

## 5. Operating rules

- Follow `AGENTS.md`: deterministic geometry/acceptance, exact artifact identity,
  protected vertices, bounded edits, and evidence tied to the actual run.
- Open surface checkpoint, open volume checkpoint and Automotive Aero NIM are
  different artifacts. Never borrow NIM benchmark claims.
- Never expose `.env` values. Model credentials stay behind the local API.
- Preserve the user's latest model selection and any active GPU job during QA.
  Use a temporary hidden browser tab for visual checks when possible.
- Do not kill the unrelated service on 8765. Local API uses 8766; Vite uses 5173.
- Update `progress.md` after a verified milestone, test failure, or scope decision.
  Cite evidence and distinguish implemented, tested, pending and deferred.

## 6. Milestone acceptance and handoff

The immediate milestone requires the existing automated suite and production
build to pass, linked comparison verified in browser, one live car iteration
without duplicate jobs, correct missing-field/failure behavior, and a short
rehearsal script. Record exact run IDs and what was visually checked.

The historical full verification before the presentation milestone was 32 Python +
29 frontend tests (61 total), plus the production build. The existing ~759 KB
frontend bundle warning is known; investigate growth if dual rendering worsens
loading or frame rate. Do not call these scientific validation tests.

Keep code and tracking in the Zephyr repository, not the parent portfolio repo.

## 7. Acceptance hardening completed on 2026-09-19

The subsequent user request authorized fixing acceptance and testing it. The
worker now corrects upstream batch gradient accumulation and stale normal
arrays, checks full-pipeline finite differences at geometry-safe probe radii,
audits intersections with libigl exact predicates, and tests a separate candidate
under an explicit provisional numerical policy. All check names are required;
missing/failed checks and experimental geometries cannot earn acceptance.

The final sedan run passed the local check at 0.375 mm: predicted reduction
0.09645 N, fresh reduction 0.09045 N, disagreement 6.22%. The final hatchback run
remained refused. This is acceptance for further evaluation, with independent
CFD and a reusable physical trust radius still pending. See
[policy, measured results and evidence](docs/ACCEPTANCE_CHECKS.md).
Final suite: 43 Python + 36 frontend tests; production build and real browser
acceptance/refusal/Q&A checks passed. Prior presentation evidence is preserved.

## 8. Repeatability and runtime milestone — 2026-09-19

The user authorized the predeclared R01–R03 work in `progress.md`. The worker now
uses fresh forward-only repeat/probe evaluations with geometry encoding reused
only across identical inputs within one evaluation. Baseline and candidate
autograd, all geometry gates, trust thresholds and GPU leases are preserved.
The matching sedan fell from 472.074 to 271.387 seconds, with exact force,
pressure/shear, geometry and decision parity. The raw partial sensitivity field
did not meet the strict repeatability tolerance even in an unmodified process
repeat; this failed check remains recorded. See [RUNTIME_CHECKS.md](docs/RUNTIME_CHECKS.md)
for all matrix outcomes, source hashes and limitations.

The [60-second script](docs/DEMO_60_SECONDS.md) now presents the accepted sedan and
refused hatchback as clearly labeled recordings. Both were browser checked.
Forty-six Python tests passed. The existing frontend was unchanged. Nemotron,
public deployment and independent CFD remain separate later work.
