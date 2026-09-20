# Multi-region car exploration

Implemented 2026-09-20. The old front-82%-fixed restriction is no longer
the only editing option. Legacy rear handles remain available for replay
and comparison; the new tools edit the nose, hood, sides and rear deck.

| Tool | Motion | Main region |
|---|---|---|
| `nose-width-v1` | Symmetric lateral width | Front nose |
| `hood-height-v1` | Vertical | Hood contour |
| `side-shoulder-v1` | Symmetric lateral width | Sides below cabin |
| `deck-height-v1` | Vertical | Rear deck |
| `rear-width-upper-v1` | Symmetric lateral width | Upper rear taper |

`compare-body-regions` evaluates these five independently from the same
original mesh. This is not accumulated multi-step optimization. All outcomes,
including refusals and increased predicted drag, remain in the study history.

## Protection and compatibility

New tools preserve a conservative normalized spatial envelope: the lower
46% of height, plus the central upper cabin (25–80% of length, above 60%
of height), with smooth transition margins. These are geometric envelopes,
not semantic segmentation of arbitrary car parts. Each tool additionally
has local support; this does **not** claim that most mesh vertices are editable.
The cabin and wheel/ground envelope remain fixed. Roof, wheels and underbody
editing are not supported by these new presets.

The hard displacement limit remains 4 mm. Geometry backtracking, exact
intersection audits, local probe checks and acceptance thresholds were not
relaxed for this feature. Broadening the available regions does not guarantee
that most candidates improve or pass.

Each surface evaluation checks finite metre-scale coordinates, triangular
watertight topology, and the pinned checkpoint's surface input bounds. Supported
sedan inputs outside those bounds are rejected. Previously supported experimental
shapes may extrapolate outside the bounds, with an explicit compatibility warning
in the evidence; they remain ineligible for acceptance. In particular, the taller
SUV/van and wider aircraft exceed parts of the surface training envelope.
Baseline and candidate get separate full surface and volume evaluations.
This verifies runtime/input compatibility, not predictive accuracy.
Additional demo cars remain experimental; aircraft remain baseline-only.

## UI and language-model contract

The **Explore the body** region selector uses the displacement slider and
works without a language-model connection. It deliberately does not interpret
the free-text brief. Preset provenance says `user-selected-preset`, not an LLM.
For additional natural-language constraints, use the brief copilot.

The compiler and frontend validators share the supported region choices;
comparison tools require exploration mode. Model schema tests cover the new
tools. This feature's verification did not make new live language-model calls.
Camera position, changed-region marker and explanations now follow the
actual selected region instead of always describing the rear.

## Reproducible checks

- `scripts/check-body-regions.py`: preliminary geometry checks for both signs,
  five tools and two meshes; not a replacement for full production checks.
- `scripts/test-body-regions.py --live --output <new-path>`: opt-in local GPU
  production matrix, with every outcome retained.
- `scripts/verify-local-acceptance.py`: independently rechecks saved mesh
  hashes, geometry, intersections, force integration and decision; now uses
  the recorded handle's protection mask.
- `scripts/check-model-inputs.py`: all nine installed baselines and 70 signed
  car-region candidates checked against the training metadata; this is a static
  input contract, not proof of prediction quality or geometry acceptance.
- Evidence: [production matrix](evidence/body-regions-2026-09-20/production.json)
  and [preliminary geometry](evidence/body-regions-2026-09-20/geometry.json).

Browser QA checked hood replay, front-facing change view, actual movement
label, all region choices, aircraft exclusion and return to car controls.
The computer-use skill was used for these UI checks.

## Observed results, not promised gains

All six initial production cases completed surface and paired volume inference;
all candidates passed full-resolution geometry checks at 4 mm. All six remained
refused under the unchanged acceptance policy. The four hatchback cases remain
experimental, irrespective of their numerical improvement.

| Geometry / region | Fresh drag change | Local acceptance |
|---|---:|---|
| Hatchback nose | -0.110 N | Refused |
| Hatchback hood | -2.179 N (-0.459%) | Refused |
| Hatchback sides | -0.768 N | Refused |
| Hatchback deck | +1.058 N | Refused |
| Sedan hood | -1.605 N (-0.258%) | Refused: probe centering |
| Sedan upper rear | -0.248 N | Refused |

The sedan hood's held-out prediction disagreement was 3.12%, but its fine-probe
midpoint offset failed the separate centering gate. This feature does not establish
a majority acceptance rate. See the [source-capture qualification](evidence/body-regions-2026-09-20/PROVENANCE_NOTE.md)
before using the last initial-matrix run as reproducibility evidence.
