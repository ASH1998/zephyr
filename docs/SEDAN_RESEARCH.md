# Sedan research — frozen protocol, 2026-09-25

The user authorized the seven-part headline-result plan, with the original UI
and aircraft behavior preserved. New experiments use `scripts/sedan-research.py`;
the original layout, styling, controls, interactive API and aircraft behavior are
preserved. The viewer accepts a separately marked, strictly validated research
replay and opens its larger displacement at true scale. Legacy runs retain their
existing magnification and 4 mm policy.

## Success rules declared before results

Policy `sedan-forward-study-v1` requires a fresh reduction **strictly greater
than 1% and 5 operational sigma**, repeatability, all geometry checks, and a
conservative confirmed winner beating the best equal-budget random control by
more than `max(5 sigma, 0.1% of baseline drag)`. This is a study decision, not a
statistical significance claim about optimizers in general. Do not lower these
thresholds after inspecting results.

Five baseline evaluations and ten smooth random perturbations below 0.1 mm
measure repeat SD and local perturbation SD separately. Operational sigma is
their maximum and a float32 roundoff guard. Perturbation variation can contain
real shape response; neither statistic measures surrogate bias or CFD error.

Search budget: 100 legal Latin-hypercube warm starts, 100 legal Optuna TPE
candidates, and 200 independent uniformly random legal candidates. Rejected
geometry proposals are retained, with no model call and no amplitude shrinking.
Each arm has a proposal cap. Unfinished studies cannot pass the equal-budget gate.
Top three distinct optimized shapes receive three fresh confirmation evaluations
each. Maximum planned forward calls: 424. A STOP file allows graceful interruption.
The default process time limit is four hours, with partial evidence retained.

## Geometry and training-distribution limits

Seven C2 spatial morphs change rear taper, deck height, hood camber, nose width,
side shoulders, front overhang and rear overhang. Individual limits are ±30 mm
(shoulders ±20 mm); combined displacement cannot exceed 60 mm. Cabin/greenhouse,
wheels and the lower underbody stay fixed. Roof and diffuser/ramp changes are
unsupported because they conflict with these protected envelopes.

Research-specific quality policy: cosine of each triangle's normal change >0.95,
area and edge-length ratios within (0.5, 2), aspect degradation ≤2, finite points,
identical topology, watertightness, exact protected coordinates, full libigl exact
intersection audit, baseline bounding box expanded by 60 mm, and checkpoint input
bounds. These are predeclared screening choices, not physical safety guarantees.
The legacy UI's stricter 4 mm policy is untouched.

Published analogues and ranges are recorded in `research/morphs.py`, from
[DrivAerML Table 5](https://arxiv.org/html/2408.11969v2#Sx7.T5).
The local morphs do not reproduce the original ANSA boxes. A subsequent
[published-baseline audit](evidence/sedan-research-2026-09-25/published-baseline/README.md)
identified the source STL as published run 1 by exact SHA-256 and recovered its
16 parameters. This does not establish a mapping from our C2 amplitudes to ANSA
coordinates. All local morphs remain **range-screened, training distribution
unverified**. Range compliance does
not turn this flag green. Final research acceptance requires verified domain
evidence and an independent comparison; numerical success is recorded separately.

## Reproduction

Use the existing documented DoMINO environment, plus
`uv pip install --python ..\.venv\Scripts\python.exe -r requirements-research.txt`.

```powershell
& ..\.venv\Scripts\python.exe scripts/sedan-research.py prepare --directory .local/research/sedan-2026-09-25
& ..\.venv\Scripts\python.exe scripts/sedan-research.py noise --live --directory .local/research/sedan-2026-09-25
& ..\.venv\Scripts\python.exe scripts/sedan-research.py search --live --directory .local/research/sedan-2026-09-25
& ..\.venv\Scripts\python.exe scripts/sedan-research.py confirm --live --directory .local/research/sedan-2026-09-25
& ..\.venv\Scripts\python.exe scripts/sedan-research.py status --directory .local/research/sedan-2026-09-25
```

Each plan is hash-bound before evaluation. Numerical sources, upstream commit,
checkpoint, installed model, input mesh, conditions, parameters, mesh hashes,
geometry checks, timing and all outcomes are retained. Resume verifies the plan,
source identity and deterministic proposal sequence. GPU leases are shared with
the existing application. Live commands use local CUDA only.

## Geometry-only correction before search

The initial morph implementation failed quality checks at the proposed larger
ranges around a few thin triangles. No search forces had been observed. The
revised morph adds symmetric compact C2 exclusion regions around triangles that
fail individual parameter endpoint tests. The exclusions are derived only from
baseline geometry and the frozen quality policy; they do not depend on force,
sensitivity or search outcomes. Every combined candidate still receives the full
quality/intersection check. Some combinations will still be refused.

The first 15-evaluation noise study remains archived as `sedan-2026-09-25` with
its original source snapshot. It measured exact baseline repeats at 621.695557 N
and perturbation SD 0.065227 N. The numerical success threshold was 6.216956 N.
These statistics belong to the initial morphs. Revised morphs require a fresh
study and noise calibration; thresholds have not been relaxed.

Standalone report command:

```powershell
& ..\.venv\Scripts\python.exe scripts/report-sedan-research.py --directory <study> --output <report-folder> --speed-kmh 120
```

CFD preparation uses `export-sedan-cfd.py` after confirmations. The generated
plan binds exact STL hashes, conditions and two predeclared mesh levels. Run
`run-sedan-cfd.py --live --directory <study>/cfd` inside the existing Linux
OpenFOAM environment. Missing/failed mesh or convergence checks remain failures.
The comparison requires both meshes to agree in direction and within 50% of the
surrogate fractional change, and the mesh levels to agree within 50% of the finer
change. This diagnostic includes explicit RANS, wall-resolution and ground-gap
limitations; it never confers engineering validation.

The fixed baseline may be computed earlier with
`export-sedan-cfd.py --baseline-only --directory <study>`, followed by
`run-sedan-cfd.py --live --directory <study>/cfd-baseline` in Linux. This writes no
independent comparison claim. The eventual paired command can add
`--baseline-cache <study>/cfd-baseline`; reuse requires identical protocol,
baseline STL, every solver input, runner version and verified cached file hashes.
The same mesh, convergence and agreement requirements still apply. CPU baseline
CFD can run alongside the exclusive GPU search.

`test-sedan-advisor.py --live` qualifies Nemotron against ten actual recorded
application briefs, without manual response edits. Some are scripted verification
briefs, so this does not establish held-out human rulebook performance. Range
presets, explicit user ceilings and allowed parameter names are enforced outside
the LLM. Advice applies to a subsequent search, not to the frozen primary control
experiment.

## Current execution and deployment

The first protocol's noise-only evidence is retained in
`.local/research/sedan-2026-09-25`. Geometry-only inspection found fragile thin
triangles, before any optimization force was observed. A separately frozen v2
study protects those patches with smooth radial factors and retains the same
numerical and mesh-quality thresholds. Its plan SHA-256 is
`534ce0d5e9411295e2a2d31bb4ea1398004abdffe79f4bd9e4a63703c783fbb7`.

The v2 noise study completed five baseline and ten perturbation evaluations:
baseline 621.695556640625 N, repeat SD 0 N, perturbation SD 0.0968954195 N.
The unchanged pass threshold is strictly more than 6.2169555664 N reduction;
the equal-budget control margin is strictly more than 0.6216955566 N.
On 2026-09-26 the user stopped further optimization and selected saved candidate
`tpe-0147` (600.973328 N, approximately 3.33% below the baseline) for a provisional
demo. The search stopped with 100 legal LHS and 90 legal TPE evaluations, zero
random controls and zero finalist repeats. Its original success gates remain
incomplete; the frozen plan and all records are retained. The newer best observed
candidate is also retained, but is not substituted for the selected demo.
No further optimization or follow-on search is scheduled.

`test-sedan-advisor.py` now requires `--sensitivity-run <recorded-run-folder>`.
It verifies the full baseline mesh, checkpoint, conditions, sensitivity adapter
and VTK hash, then projects recorded partial sensitivities onto each morph basis.
The caveats about partial derivatives and repeatability accompany those scores.
After the primary experiment and 8/10 qualification, `guided-sedan-search.py`
prepares a separate frozen follow-on experiment. It executes Nemotron's selected
ranges using TPE, with 20 legal evaluations against 20 full-range random controls
and three fresh winner repeats. It never replaces the primary experiment.
Each follow-on model attempt saves its exact brief, context, system prompt and
schema before calling Token Factory. Unedited responses, including refusals or
grounding failures, remain in a separate attempt folder even if no study is
created. Provider errors retain their type without persisting request secrets.

`publish-sedan-replay.py --live` creates a recorded viewer artifact after complete
matched budgets and winner repeats. It performs fresh surface/sensitivity and
volume evaluations for both shapes, and refuses if forces differ from the study.
For the explicitly paused study, `--provisional-candidate tpe-0147` selects that
saved record only when a STOP marker exists. It records an independent selection
receipt and fresh geometry/field checks, with `searchComplete: false`, no claimed
finalist repeats, and no research or engineering acceptance. This mode does not
alter the original experiment or lower its success thresholds.
`package-sedan-demo.py --run-id <id> --output <new-folder>` packages the built
original UI, all existing aircraft assets, the evidence and downloadable mesh.
The included Python server and Dockerfile serve recorded evidence without GPU
or credentials. Compute requests explicitly explain the deployment's recorded
mode. This does not provision or publish to a hosting service.

A deployment rehearsal using the historical result was checked in the browser:
sedan replay, linked Original/Changed comparison, Global Hawk and X-57 previews,
and X-57's experimental predicted airflow. This does not verify a new research
result. Live CFD, follow-on search and final research replay still require their
actual execution receipts. Nemotron qualification is recorded under
`docs/evidence/sedan-advisor-2026-09-26*`: first round 7/10; second round 10/10
after clarifying the preset definition and contiguous-quotation requirement.
No model response or expected-answer label was edited. Both complete rounds and
their distinct current-history contexts are retained. This is development-set
qualification on recorded briefs, not a held-out generalization claim.

CFD setup preflight: the initial tutorial-based mesh failed its skewness audit.
Both internal and boundary skewness limits were tightened to 3.5 during meshing,
before choosing the final candidate. The revised baseline mesh passes `checkMesh`
(maximum skewness 3.491995), and a single `simpleFoam` iteration ran successfully.
This preflight is not a converged force measurement or an independent comparison.

The subsequent 1,200-iteration baseline cases both completed and passed mesh
quality checks. Coarse drag was 739.162061 N and passed the frozen last-100
force-range check. Fine drag averaged 650.368448 N, but its 17.286757 N range
was about 2.66%, above the 0.2% limit. Therefore the fine baseline is
**not converged**, and no independent agreement can be claimed from this run.
The original output and thresholds are retained. Published-variant ranking is
being prepared as the plan's separate fallback, with geometry-only selection.
The [force-history plot](evidence/sedan-research-2026-09-25/independent-baseline-force-history.png)
shows the sustained fine-mesh oscillations and the much flatter coarse result;
passing one mesh's convergence rule does not establish mesh-independent accuracy.
Its [frozen protocol](evidence/sedan-research-2026-09-25/published-ranking/BENCHMARK.md)
uses the original and four nearest available published variants, with five fresh
forward calls after the primary experiment. This tests published-case ranking;
it cannot establish physical improvement for our custom shape.

The user subsequently requested a synthetic crash-damage use case and explicitly
chose to finish optimization first. Next: a labeled sedan dent scenario using
the same analysis views. Its scope is aerodynamic illustration, not structural
damage assessment or a roadworthiness decision; aircraft stay unchanged.

Update 2026-09-26: after the user stopped the search, the selected candidate and
the [synthetic hood dent](SYNTHETIC_DENT.md) both received fresh surface and volume
fields. The selected replay retains 3.333% predicted reduction; the dent produces
only -0.020% predicted drag change at 11.302 mm maximum inward movement. Neither
is physically validated. Both are available through Previous runs in the
recorded deployment bundle `.local/demo-sedan-and-dent-final-2026-09-26`.
