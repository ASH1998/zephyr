# Local repeatability and runtime checks — 2026-09-19

The acceptance policy is unchanged. Fresh surface evaluations now omit unused
autograd for the repeated baseline and four directional probes. Baseline and
candidate evaluations still compute the original partial sensitivity and save
their full-resolution fields. Independent CFD remains unrun.

## Frozen experiment

[plan.json](evidence/runtime-2026-09-19/plan.json) was written before optimization.
It fixes the reference commit `85f5ec5`, sedan and hatchback runs, trust-policy
SHA-256, five cases and tolerances. It includes an unmodified separate-process
sedan repeat, the optimized matching sedan, 0.25 and 0.5 mm sedan budgets, and the
refused hatchback control. No requested case or failed comparison is discarded.

The force tolerance is 32 float32 epsilons times max(abs(reference force), 1 N).
All pressure, shear and raw partial sensitivity components are compared with
rtol=1e-6 and atol=1e-5. Matching requests also require identical coordinates,
topology, probe/candidate mesh hashes, selected amplitude and acceptance decision.

## Profiling and implementation

Measured fresh baseline evaluations on the local RTX 4070 Ti SUPER:

| Shape | Full autograd | Forward only | Forward with within-evaluation geometry reuse |
|---|---:|---:|---:|
| Sedan, 92 batches | 58.194 s | 52.405 s | 20.558 s |
| Hatchback, 5 batches | 1.834 s | 1.202 s | 1.091 s |

Both forward variants reproduced every pressure, shear, integrated force and
geometry-coordinate value **exactly** in these tests. Reports record checkpoint,
upstream, installed model and local adapter hashes:
[sedan profile](evidence/runtime-2026-09-19/profile-sedan.json),
[hatchback profile](evidence/runtime-2026-09-19/profile-hatchback.json).
These are sequential measurements, not statistically characterized latency claims.

`src/zephyr/local/forward.py` preserves the pinned upstream preprocessing, 8,192
face batches, physical scaling and float32 force accumulation order. The global
surface geometry encoder receives identical geometry/grid/SDF tensors across
batches. In evaluation mode with gradients disabled, an exact-input cache computes
that encoding once and reuses it for the remaining batches. Every new evaluation
builds fresh normals, stencils and signed-distance inputs and owns a new cache.
There is no cross-mesh, cross-run or candidate-result cache. Mutated inputs
invalidate the cache; scope exit and exceptions restore the model method.

The worker records adapter/source hashes, preprocessing/batch times and cache-hit
counts in `surfaceProfiles`. Probe events say “GPU forward batches”; baseline and
candidate events still report autograd. The isolated worker and both GPU leases
are preserved, as are cancellation and all geometry/trust gates.

## Unmodified repeat and sensitivity limitation

Run `local-cdd1b1d4afbf40b8b5e9af03e8c07ddb` repeated the frozen sedan in **459.679 s**,
versus the original **472.074 s**. Source hashes, forces, all four probes, geometry,
pressure, shear, selected step and decision matched exactly. Fresh raw-artifact
verification passed: [repeat evidence](evidence/runtime-2026-09-19/sedan-repeat.json).

The **raw partial sensitivity repeatability check failed** even with unchanged
code. The baseline's largest difference was 1.297891e-5 N/m; 7 of 2,259,702
components exceeded the predeclared tolerance. Candidate sensitivity differed by
at most 3.769994e-6 N/m and stayed within tolerance. Both raw gradient fields were
not bitwise identical. The failed comparison is retained in
[repeat-parity.json](evidence/runtime-2026-09-19/repeat-parity.json).

This does not change the local verdict: candidate direction and trust use measured
full-pipeline finite differences, not the raw partial sensitivity. The optimization
leaves baseline/candidate autograd unchanged. We do not claim every field is
repeatable or relax the tolerance to obtain a passing report.

## Production matrix

Results and independent full-resolution artifact verification are recorded in
[matrix.json](evidence/runtime-2026-09-19/matrix.json) and its linked case reports.

The matching optimized sedan took **271.387 s (4m31s)**: 42.5% less than the frozen
472.074 s reference, or 41.0% less than the 459.679 s unmodified repeat. Each fresh
repeat/probe took about 21 s rather than 59 s. Baseline/candidate sensitivity
evaluations still took about 61 s each. The remaining time includes loading,
geometry checks, conversion and two volume predictions. All pressure/shear and
force values, probe meshes, candidate coordinates/topology and the acceptance
decision matched exactly. Baseline raw sensitivity again failed its tolerance
(maximum difference 3.832579e-5 N/m); candidate sensitivity stayed within tolerance.

The 0.25 mm budget was refused. Its coarse/fine slopes disagreed by 79.48%, the
fine probe pair was below the required signal-to-noise ratio, and its midpoint
failed the centering gate. The fresh candidate reduction was 0.069824 N versus
0.013062 N predicted (434.58% disagreement). A smaller step is not automatically
more trustworthy when its derivative estimate is unresolved.

All five production cases completed and passed independent artifact verification:

| Case | Requested / effective mm | Predicted / fresh reduction N | Disagreement | Decision | Worker time |
|---|---:|---:|---:|---|---:|
| Unmodified sedan repeat | 3 / 0.375 | 0.096451 / 0.090454 | 6.22% | Accept for further evaluation | 459.679 s |
| Optimized sedan | 3 / 0.375 | 0.096451 / 0.090454 | 6.22% | Accept for further evaluation | 271.387 s |
| Smaller sedan step | 0.25 / 0.25 | 0.013062 / 0.069824 | 434.58% | Refuse | 268.852 s |
| Larger sedan step | 0.5 / 0.5 | 0.127319 / 0.116882 | 8.20% | Refuse | 268.240 s |
| Hatchback control | 3 / 3 | 0.709900 / 1.133301 | 59.64% | Refuse | 28.205 s |

The 0.5 mm candidate agrees within the 25% candidate tolerance but still fails:
its fine-probe midpoint offset is 0.020782 N, above the centering allowance of
0.008738 N. Slopes agreeing within 1% are insufficient on their own. Changing the
requested budget also changes the probe radius under the unchanged policy, so
this matrix does not establish a monotonic safe step size or broad trust radius.

The hatchback reproduced forces, pressure/shear, geometry and refusal exactly.
Its candidate raw sensitivity exceeded tolerance (maximum difference
1.591444e-5 N/m); its baseline sensitivity stayed within tolerance. Therefore
**neither matching-case report passes every field-parity check**, despite exact
acceptance-driving outputs. These failures remain in `matrix.json` and the
[final verification summary](evidence/runtime-2026-09-19/summary.json).

Each run has fresh original/candidate volume fields, verified mesh binding and
source hashes. Both GPU leases were released at completion. Browser rehearsal
overlapped the 0.25 mm run; its duration is recorded but is not an isolated latency
benchmark. The main matching-sedan timing above preceded that browser work.

## Reproduction

Run from the Zephyr repository with the configured local Python environment and
installed CUDA dependencies. Each live command requires an idle GPU and takes its
own lease. No paid cloud resources are provisioned.

```powershell
python -X utf8 -m unittest discover -s tests
python -X utf8 scripts/profile-surface-forward.py --live --geometry drivaer-1 --output profile-sedan.json
python -X utf8 scripts/profile-surface-forward.py --live --geometry hatchback --output profile-hatchback.json
python -X utf8 scripts/test-runtime-matrix.py --live --output-dir .local/runtime-recheck-1
```

The original unmodified repeat must use the frozen reference implementation.
Use a fresh output directory to preserve earlier evidence. A partial matrix can
resume at its next unrun case with `--start-case`; a completed matrix with a failed
parity check reports that failure instead of silently passing the regression.
Running `test-local-acceptance.py` after this change exercises the optimized worker.
`scripts/verify-local-acceptance.py` separately checks saved VTK hashes, geometry,
protected coordinates, exact-predicate intersections, force reintegration and
recomputed decisions without launching inference or modifying historical runs.

The [presentation script](DEMO_60_SECONDS.md) uses clearly labeled frozen replays
for the accepted sedan and refused hatchback, with their original run-specific
timings. Sixty seconds is the presentation length, not a live sedan latency target.
The two replay verdicts, movement labels, comparison interactions and pressure
scale were checked in a temporary hidden browser tab, then the tab was closed.
[Browser rehearsal record](evidence/runtime-2026-09-19/browser-rehearsal.json).
