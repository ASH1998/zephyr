# Zephyr system architecture

![Zephyr system architecture showing local and cloud trust boundaries](images/zephyr-architecture.png)

Zephyr separates language interpretation from geometry control and scientific acceptance. Nebius Token Factory supplies the optional Nemotron call; the geometry, NVIDIA DoMINO inference, validation, and evidence pipeline run on the local workstation.

## Data flow

1. The browser sends a design brief and selected allowlisted geometry to the local API.
2. With language-model support enabled, Nemotron compiles the brief into the supported structured intent schema. An explicit preset can bypass this call.
3. The deterministic controller applies only allowlisted fixed-topology handles, preserves protected regions, and enforces the 4 mm displacement ceiling.
4. The local NVIDIA GPU evaluates surface fields and, when available, volume airflow for the original and bounded candidate.
5. Geometry, repeatability, probe, and disagreement checks accept, shrink, or refuse the candidate without model discretion.
6. The browser receives linked fields and the trust verdict. Run evidence records hashes, constraints, timings, artifacts, and refusal reasons.

## Trust boundaries

- **Nemotron interprets intent.** It does not move vertices, relax thresholds, or approve a result.
- **Deterministic code controls geometry and trust.** The same inputs and pinned runtime produce the same requested handle and checks.
- **DoMINO is a surrogate.** Acceptance means accepted for further evaluation, not independently validated aerodynamics.
- **Aircraft are experimental.** They support baseline analysis only because the available DoMINO model is trained on cars.
- **Credentials stay out of evidence.** Sanitized reports record configuration presence and model identity without storing API keys.

## Runtime surfaces

| Surface | Responsibility |
|---|---|
| Browser workspace | Brief entry, geometry selection, 3D fields, comparison, progress, and evidence explanations |
| Local API | Input validation, job lifecycle, polling, cancellation, and copilot boundary |
| Nemotron intent compiler | Supported structured brief compilation and evidence-bound explanation |
| Deterministic geometry controller | Fixed-topology bounded candidates and protected-region enforcement |
| DoMINO surface model | Pressure, wall shear, drag integration, and sensitivity |
| DoMINO volume model | Velocity-field prediction and streamline export |
| Trust gates | Geometry integrity, repeatability, local probes, disagreement, and scope decisions |
| Run evidence | Request, identities, hashes, measurements, timings, artifacts, and final verdict |

For implementation and reproduction details, see [Real local DoMINO integration](LOCAL_DOMINO.md), [Acceptance checks](ACCEPTANCE_CHECKS.md), and the [Clean installation guide](INSTALL.md).
