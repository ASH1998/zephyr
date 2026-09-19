# Local acceptance checks

The user authorized this work on 2026-09-19 after reviewing the misleading
change-relative prediction error and unconditional refusal. This is a local
surrogate step check, not an engineering certification or physical confidence
score. Independent CFD has not been run.

## Corrections

1. The pinned NVIDIA loop reuses `geometry_coordinates` across batches. Its
   `.grad` accumulates, and the loop adds that cumulative gradient after each
   batch. Zephyr's scoped forward hook clears this leaf before each forward,
   so each batch contributes once. A three-batch regression distinguishes the
   incorrect total 10 from the correct 6. The pinned upstream stays unchanged.
2. Imported normal arrays survive point edits. Every evaluation now uses
   float64 mesh coordinates and removes imported normal arrays, allowing the
   upstream datapipe to compute normals for the actual geometry. The model
   still receives its expected float32 inputs.
3. That corrected gradient is still only a **partial** derivative. Precomputed
   SDFs, surface queries, normals, areas, neighborhoods and center-of-mass inputs
   also change when the mesh changes. Four fresh full-pipeline probes provide
   the directional prediction; the partial gradient is retained separately.
4. A fresh candidate tests the prediction; its force is never used to fit the
   predictor. Absolute disagreement in N is shown. The change-relative error
   is null when the predicted change is numerically unresolved, rather than
   dividing by an arbitrary near-zero denominator. It is not model accuracy.

## Policy `local-handle-check-v1`

These are explicit **provisional numerical policy choices**, fixed in code
before the final GPU regressions. They are not an empirically established
physical uncertainty interval and must not be chosen or changed by the LLM.

- Repeat the baseline. Numerical floor is the larger of the repeat difference
  and `32 × float32 epsilon × max(abs(baseline drag), 1 N)`. Exact repetition
  still has a nonzero floor; this floor does not estimate surrogate bias.
- Start `h = min(budget / 2, 1 mm)`. Test geometry at `+h, -h, +h/2, -h/2`;
  halve h as needed, at most six halvings. No unsafe probe is evaluated.
- Evaluate all four valid probes and record mesh hashes, amplitudes and forces.
  Central slopes at h and h/2 must have the same sign and disagree by at most
  20% relative to the larger slope magnitude. Both paired force differences
  must exceed five numerical floors. The fine pair's midpoint must lie within
  20% of its half-difference plus the floor of the baseline force. This catches
  curvature/discontinuity hidden by agreement between central slopes alone.
- Choose a separate candidate direction from the fine slope. Start at the
  user's bounded budget and halve for failed geometry checks, up to four times.
  Exact protected coordinates and topology, finite positions, displacement,
  cosine >0.99 normal preservation, area ratio 0.8–1.2, closed edges, handle
  symmetry and smooth boundary checks must pass.
- Audit all original and candidate triangles with
  `libigl==2.6.3`, `igl.predicates.find_self_intersections`: AABB search and exact
  predicates. Missing/wrong-version/failed audits cannot earn acceptance.
- The separate candidate must reduce fresh surrogate drag by more than five
  numerical floors, predict a reduction above that same floor, and differ from
  the predicted reduction by no more than 25%. Equivalently, its reduction
  ratio must be 0.75–1.25 when the signal is resolved.
- Only the primary DrivAer sample is eligible for acceptance. Other installed
  geometries are experimental. All checks must pass; missing checks fail closed.

`trust.calibrated` means the local probe and separate candidate checks passed
for **this mesh, handle and conditions**. `calibrationScope` explicitly records
`local-surrogate-handle-only`; `engineeringValidated` remains false. The UI says
“Local check passed” and “Accepted for further evaluation only.”

## Reproduce

From the Zephyr repository, with the documented Windows environment installed:

```powershell
& ..\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
& ..\.venv\Scripts\python.exe -X utf8 scripts/test-local-acceptance.py --live --geometry drivaer-1
& ..\.venv\Scripts\python.exe -X utf8 scripts/test-local-acceptance.py --live --geometry hatchback
```

The GPU script uses the production worker and exclusive GPU leases. No cloud
GPU or LLM call is needed. Its request uses the same deterministic preset
accepted by the API without language compilation. GLM remains configured for
interactive brief interpretation. The extra surface evaluations increase run
time: this is no longer a two-surface-pass latency claim.

Each result retains VTK fields, raw forces, probe amplitudes/hashes, source and
checkpoint hashes, adapter version, audit results and a versioned policy under
`.local/runs/<runId>/`. `calibration.json` also binds run, mesh, checkpoint,
upstream commit, handle and conditions. Historical runs are not rewritten.

## Checker verification

Tests include noncoplanar crossing faces, coplanar containment, separated faces,
a clean closed sphere, unavailable checker versions, gradient accumulation,
stale normals, unresolved signals, unstable/offset probes, worsening candidates,
missing checks and out-of-domain refusal. PyMeshLab 2025.7 was tried during
development but missed the coplanar-containment fixture, so it was replaced.

Primary reference: [libigl exact intersection predicate API](https://libigl.github.io/libigl-python-bindings/api/igl_predicates/#find_self_intersections).
The pinned NVIDIA implementation inspected is
`0612ec4ed54484a47bfa134eda7b3b012a607624` in `config/upstream-lock.json`.

## Final measured results

| Measure | DrivAer sedan | Impreza hatchback (experimental) |
|---|---:|---:|
| Baseline drag | 621.6955566 N | 474.9229126 N |
| Fresh candidate drag | 621.6051025 N | 473.7896118 N |
| Predicted change | -0.0964508 N | -0.7098999 N |
| Fresh change | -0.0904541 N | -1.1333008 N |
| Absolute prediction difference | 0.0059967 N | 0.4234009 N |
| Difference / predicted change magnitude | 6.2174% | 59.6423% |
| Actual / predicted reduction | 0.937826 | 1.596423 |
| Maximum movement | 0.375 mm | 3.000 mm |
| Protected vertices unchanged | 340,330 | 14,967 |
| Two-scale local probe check | Passed | Failed (midpoint/linearity) |
| Baseline + candidate triangle audit | Passed | Passed |
| Decision | Accepted for further evaluation | Refused |
| Worker duration, including volume models | 472.074 s | 30.433 s |

The sedan used +/-0.5 mm and +/-0.25 mm probes after the 1 mm probe failed the
unchanged normal-preservation gate. Its requested 3 mm candidate shrank through
1.5 and 0.75 mm to a **0.375 mm outward rear-width step**. The prediction used
the independent fine-probe slope; the candidate was not one of those probes.
The 3.80% slope disagreement, resolved signals, midpoint check, 6.22% candidate
disagreement and all geometry checks passed the predeclared numerical policy.
The small 0.09045 N reduction is a surrogate result, not a physical accuracy claim.

The hatchback's midpoint offset was 0.15375 N despite exact repeatability of its
baseline. This failed the local linearity check; its candidate disagreement also
exceeded 25%. Its experimental domain independently excludes acceptance. This
case demonstrates that a larger reduction does not automatically pass.

Both baseline forces repeated exactly in this environment. Independent double-precision
reintegration of saved pressure/shear on fresh triangle normals differed from the
recorded Fx by at most 0.000130 N, below the numerical floor. VTK hashes, full
topology, protection, displacement and separate surface/volume mesh binding were
verified. All five recorded local numerical source hashes match the files at
commit `85f5ec5`, before the subsequent runtime optimization.

- Sedan: `local-c29499fe827b4d7e9b7ac01f29ff8428`;
  [verified evidence](evidence/acceptance-2026-09-19/sedan-final.json).
- Hatchback: `local-dfd56fe51ebc497a9d768d7498cede7a`;
  [verified evidence](evidence/acceptance-2026-09-19/hatchback-final.json).
- Three development regressions are retained unchanged under `.local/runs`:
  `local-f4da449420594954a71dde7d66448341`,
  `local-e8c1f4f4825d4b4b819ab0be937c7889`,
  `local-56e4e0e7146847c99ebcc9bc2eff7754`. The final two runs supersede them.

Verification: **43 Python + 36 frontend tests passed (79 total)**; production
build passed (770.43 kB JS / 202.32 kB gzip; existing chunk warning remains).
The hidden browser checked the real sedan acceptance, real hatchback refusal,
and a separately labeled synthetic acceptance fixture. GLM answered “Why did the
local check pass?” using the accepted-step, 0.006 N difference, cabin and 0.375 mm
facts, retaining the independent-validation limitation. Checked tabs logged no
browser errors/warnings. Screenshots are in the evidence directory.

The idle API was restarted on 8766 with its existing `--enable-llm` flags; GLM
remains `zai-org/GLM-5.3-Flash`. Port 8765 was untouched. No cloud GPU, physical
CFD, deployment, commit or push was performed. The temporary PyMeshLab package
was removed; libigl 2.6.3 is the pinned production dependency.

Subsequent [runtime and repeatability checks](RUNTIME_CHECKS.md) preserve this
policy and both reference runs. The optimized matching sedan reproduces forces,
pressure/shear, geometry and decision exactly. Raw partial sensitivity is not
fully repeatable even with unchanged code; the failed field-tolerance checks and
all neighboring-budget outcomes are retained in that report.
