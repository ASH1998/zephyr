# Live activity and idle rendering — 2026-09-20

## Cause

The API reported no active inference job on the completed sedan replay. The
Three.js viewer nevertheless requested and rendered every animation frame.
Pausing only froze the flow clock; it did not stop GPU draws. Pressure, mesh,
change and comparison views also redrew when nothing changed. Starting an
ordinary run disposed the preview before baseline fields arrived, while region
studies did not connect their current job to the main viewer at all.

## Changes

- Keep the car visible during work. An authored, explicitly illustrative scan
  moves across the surface before real fields are ready. It is not an indication
  of which mesh triangles the model is currently evaluating.
- Once baseline fields arrive, display the actual recorded pressure/sensitivity
  with only a light activity sweep. No pressure, sensitivity, displacement, force,
  acceptance or model outputs are altered by the presentation.
- Follow each study's actual current run in the main viewer, including after
  reload. The API supplies its allowlisted geometry identity for the preview.
- Stop the activity overlay on completion, cancellation or failure; pause it on
  connection/data errors. Respect reduced motion.
- Completed results and comparisons default to paused. The UI says **Calculation
  finished** and **Inference finished · viewer paused**; resuming the display
  explicitly says **viewer animation only**.
- Static views render on demand. Hidden/offscreen views stop scheduling frames.
  Steady airflow is capped at 30 fps; compute activity at 20 fps. Interactive
  camera/field changes still invalidate immediately. Pixel ratio is capped at
  1.35 instead of 1.7. No background mesh-normal recalculation for a static view.

## Verification

- 57 Python tests, 41 frontend tests and the production build pass. The existing
  bundle-size advisory remains.
- Browser QA: completed replay stayed at **40 rendered frames** across separated
  checks; resume advanced to 516 and pause stopped it again.
- Paused comparison: both canvases stayed at **3 frames**; a keyboard orbit
  advanced both to **4**, confirming linked interaction still works.
- Windows GPU Engine counter samples showed one Codex graphics process at
  approximately **11–13% before**, and **0.49% mean after** pausing/on-demand
  rendering. Another Codex process remained around 9%; total GPU load was 26%
  in that later sample. These are short observational samples, not a controlled
  whole-system benchmark or a promise of 0% GPU usage. Other apps were untouched.
- Real hood study `local-0311ec5eb7644523b573f674dff2c1cc`: complete, 67.15 s.
- Real recovery check `local-fff52c378fde41769a1bfecb65ab3485`: complete, 59.61 s;
  browser reload during work recovered the hatchback and its stage. At the fine
  negative probe, UI showed actual baseline pressure (-1679 to 1155 Pa), real
  60% batch progress, and the illustrative-sweep label. No browser shader errors.
- Final result had activity hidden, on-demand render state and paused viewer.
  Temporary QA tab closed; the original sedan replay remains available. Nemotron
  remains enabled. Local numerical policy and surrogate claims are unchanged.

Render counts are exposed as diagnostic `data-render-count` / `data-render-state`
attributes on each canvas, so idle regressions can be checked without estimating
GPU percentages from appearance alone.
