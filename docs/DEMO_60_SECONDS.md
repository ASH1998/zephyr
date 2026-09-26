# Zephyr: 60-second sedan and dent demo

Use a wide desktop for linked views. Local workstation: UI 5173, API 8766. The
prepared recorded deployment runs on 8780 and needs no GPU or credentials.
Nemotron through Nebius Token Factory remains connected in the local app.

## Open the recorded results

- [Selected sedan](http://127.0.0.1:5173/?replay=local-8907b340aebb4b1d800fb86c45451c71): 621.695557 → 600.973328 N, **3.333% lower predicted drag**, maximum movement 32.174 mm. The user stopped the search; controls and finalist repeats are incomplete. Fresh display-field generation took approximately 3m 18s, separately from search time.
- [Synthetic hood dent](http://127.0.0.1:5173/?replay=local-ca75fe9aeef644539bd878baa617f84b): 621.695557 → 621.573425 N, **0.020% lower predicted drag**, maximum inward movement 11.302 mm. This small change is not an established performance benefit. Fresh display-field generation took approximately 2m 32s.

Both must say **RECORDED REPLAY**. These are distinct comparisons against the
original sedan. The dent is not applied to the optimized candidate. Both remain
unvalidated aerodynamic predictions; neither is engineering acceptance.

## Walkthrough

| Time | Action and narration |
|---|---|
| 0–10 s | Show the selected sedan. “Zephyr evaluates shape changes with NVIDIA DoMINO on a local GPU. This saved candidate predicts 3.33% lower drag. The search was stopped early, so this is a provisional demonstration.” |
| 10–25 s | Open **Compare Original / Changed**, select **Change**, and orbit. “Orange marks actual movement. The cabin stays fixed. These shapes are shown at true scale.” |
| 25–35 s | Select **Pressure**, then **NVIDIA airflow**. “Each shape has its own fresh model fields. This is a prediction, not independent CFD.” |
| 35–50 s | Switch to the dent tab, open comparison, and orbit toward the hood. “Here we prescribe an 11.3-millimetre inward hood dent and evaluate both shapes. The map locates the geometric change.” |
| 50–60 s | Show the dent result and limits. “This case predicts only a tiny drag difference. It does not tell us crash severity or whether a car is safe. Photos, scans and structural inspection are not implemented.” |

The original **Previous runs** list switches between both scenarios in the
packaged deployment. Existing aircraft previews remain available after the demo.
**Flow illustration** is an authored visual; select **NVIDIA airflow** for actual
recorded volume-model predictions. Leave displacement enlargement off for the
true-scale comparison.

## Deployment

The prepared bundle is `.local/demo-sedan-and-dent-final-2026-09-26`. Run its
`serve.py` with the existing Python environment, or use its Dockerfile. The
server opens the selected 3.33% replay by default. It serves both scenarios,
verified candidate downloads and all original vehicle/aircraft assets. It refuses
fresh compute requests explicitly. No public hosting has been provisioned.

See [synthetic dent details](SYNTHETIC_DENT.md) and
[selection and artifact verification](evidence/sedan-research-2026-09-25/paused-demo/README.md).
Historical acceptance and runtime comparisons remain in [RUNTIME_CHECKS.md](RUNTIME_CHECKS.md).
