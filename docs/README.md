# Zephyr documentation

This index separates setup, product behavior, and evidence so the project can be reproduced without treating presentation material as scientific validation.

## Start here

- [Clean installation](INSTALL.md) — prerequisites, environment setup, model assets, launch commands, verification, and troubleshooting.
- [System architecture](ARCHITECTURE.md) — runtime components, data flow, and local/cloud trust boundaries.
- [Real local DoMINO integration](LOCAL_DOMINO.md) — runtime architecture, safety boundaries, artifacts, and scientific limits.
- [Cars, aircraft, and airflow](CARS_AND_AIRFLOW.md) — geometry sources, rendering, volume prediction, and the aircraft boundary.
- [Nemotron interface](LLM_INTERFACE.md) — brief compilation, run Q&A, API behavior, and recorded smoke evidence.

## Product and demo

- [Body-region exploration](BODY_REGIONS.md) — supported deterministic car deformation handles.
- [Bring your own car](BRING_YOUR_OWN_CAR.md) — experimental mesh/photo imports, review controls, support limits and verification.
- [60-second presentation](DEMO_60_SECONDS.md) — a short evidence-aware walkthrough.
- [Synthetic sedan dent](SYNTHETIC_DENT.md) — a prescribed geometric defect and aerodynamic comparison, without crash or roadworthiness claims.
- [Viewer performance](VIEWER_PERFORMANCE.md) — visible computation, animation, and idle-render behavior.

## Strategy

- [Public competitor snapshot](COMPETITOR_ANALYSIS.md) — current public hackathon projects, differentiation, and demo risks.

## Validation and reproducibility

- [Day-0 gate](DAY0_GATE.md) — Token Factory and checkpoint availability checks.
- [Native Windows capability gate](WINDOWS_DOMINO_GATE.md) — validated hardware/software boundary and measured outcome.
- [Acceptance checks](ACCEPTANCE_CHECKS.md) — provisional trust policy and refusal criteria.
- [Runtime checks](RUNTIME_CHECKS.md) — frozen experiments, profiling, and repeatability results.
- [Sedan research](SEDAN_RESEARCH.md) — predeclared forward-search protocol, controls, independent checks, Nemotron decisions, and recorded deployment.
- [Browser-triggered local smoke](LOCAL_DOMINO_SMOKE.md) — browser-to-GPU execution evidence.
- [`evidence/`](evidence/) — compact, sanitized machine-readable evidence. Credentials and large local run artifacts are intentionally excluded.

## Project records

- [Current project plan](../PROJECT_PLAN.md)
- [Progress log](../progress.md)
- [`archive/`](archive/) — dated research history, not the current implementation contract.

Claims in the README and UI should trace back to these records. A passing surrogate gate means the candidate may proceed to further evaluation; it is not independent engineering validation.
