# Browser-triggered local smoke evidence — 2026-09-18

**Observed outcome:** the browser's **Run bounded iteration** button POSTed a
new job, executed baseline and candidate DoMINO GPU passes, and rendered the
returned fields on the official DrivAer sample. This was not a recorded replay
or a direct worker invocation. Subsequent browser reloads recovered the same
completed job through its ID and did not run inference again.

Run: `local-656d4eb6c81d4c4881d37e05bb3dd168`.
Compact, machine-readable evidence: [local-domino-2026-09-18.json](evidence/local-domino-2026-09-18.json).
Full artifacts and stdout remain ignored under `.local/runs/<runId>/`.

| Measurement | Observed |
|---|---:|
| GPU | RTX 4070 Ti SUPER |
| Baseline inference + smoothing + VTK export | 61.617 s |
| Candidate inference + smoothing + VTK export | 64.190 s |
| Worker total, through result generation | 144.442 s |
| GPU batches | 92 baseline + 92 candidate |
| Peak allocated CUDA tensor memory (not total VRAM) | 3,127,602,176 bytes |
| Baseline surrogate drag, D=Fx | 621.695556640625 N |
| Candidate surrogate drag, D=Fx | 621.8065795898438 N |
| Fresh delta | +0.11102294921875 N (+0.01786%) |
| Gradient-predicted delta | −0.0352389730905 N |
| Prediction error relative to predicted delta | 415.057% |
| Requested displacement bound | 3.6 mm |
| Evaluated candidate maximum | 0.45 mm |
| Exactly fixed source vertices | 340,330 |
| Display vertices / triangles | 110,339 / 220,850 |
| Baseline JSON / final JSON | 29,186,719 / 58,573,461 bytes |
| Baseline VTK / candidate VTK | 106,956,198 / 111,474,571 bytes |

**Decision: refuse.** The fresh surrogate result worsened. Trust calibration,
full triangle self-intersection checks and independent CFD are not complete.
No physical improvement, solver validation, or accepted candidate is claimed.

The controller kept the original topology and all protected coordinates fixed.
Normal-angle checks rejected 3.6, 1.8 and 0.9 mm. The 0.45 mm attempt passed
normal cosine (>0.99), finite/bounded positions, area ratios, unchanged faces
and watertightness. Every attempt appears in the evidence JSON. The final
self-intersection state is explicitly `not-run`; aggregate geometry is
`incomplete`, not passed.

Browser verification observed:

- live loading, GPU batch, smoothing, conversion and candidate stages;
- baseline-only fields before final evaluation completed;
- real pressure and signed, smoothed sensitivity maps on the source geometry;
- a rear-focused displacement map, baseline/candidate switch, actual 0.45 mm,
  protected cabin 0.00 mm, true-scale default and labelled ×24 option;
- final 621.70 → 621.81 N comparison, worsening color, 415.1% prediction error,
  refusal and incomplete geometry evidence;
- refresh/reconnection to the same job without launching a duplicate;
- browser 12 mm boundary request refused by the API while retaining the completed result.

Sensitivity display uses a labelled signed asinh color scale (blue negative,
gray zero, orange positive). The numeric fields are unchanged. Pressure uses
shared baseline/candidate extrema. No invented volume flow or wake is shown.

Automated verification after implementation:

- 18 Python unittest cases passed, including the existing probes/config tests;
- 16 frontend tests passed, including live schema/event guards;
- TypeScript and Vite production build passed (existing large-bundle warning);
- `git diff --check` passed.

The CPU API tests use synthetic subprocesses; only the explicitly identified
browser smoke above is GPU evidence. Timing is one run, not a p50/p95 benchmark.
The last safety/UI changes (independent worker lease, final view state and color
presentation) were unit/build and browser checked; they do not alter numerical
inference. No huge generated artifacts, dependencies or credentials are tracked.
