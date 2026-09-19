# Zephyr

**Shape the flow.**

Zephyr helps engineers reshape vehicles for lower drag—with AI-guided changes and simulation-backed proof.

The local application runs NVIDIA DoMINO surface and volume models, displays seven cars and two aircraft, and provides linked original/changed comparison, a brief copilot and result Q&A. Local acceptance and [runtime checks](docs/RUNTIME_CHECKS.md) record both passing and refused steps; independent physical validation remains pending. See the [current project plan](PROJECT_PLAN.md) and [progress tracker](progress.md) for evidence and next steps.

## Live local GPU application

The default frontend now starts real DoMINO jobs on the local NVIDIA GPU and
renders the returned surface fields. It can generate, shrink and freshly evaluate
one bounded rear-width candidate; acceptance remains refused pending trust and
intersection validation. See [local launch and limits](docs/LOCAL_DOMINO.md) and
[browser smoke evidence](docs/LOCAL_DOMINO_SMOKE.md). The illustrative walkthrough
remains available at `?demo=1`. The [main-interface copilot](docs/LLM_INTERFACE.md)
uses the configured model to compile briefs and rank measured evidence; start
the API with `--enable-llm` to opt in to these model calls.

## Day-0 capability probe

The initial scaffold checks, without starting GPU infrastructure:

- whether Nebius credentials and an AI project ID are configured, without printing either value;
- which models the authenticated Token Factory account actually exposes;
- whether a chosen Nemotron model can return Zephyr's strict constraint schema;
- whether the exact DoMINO checkpoint bundle is complete;
- whether evidence can be written as a sanitized JSON report.

The official Token Factory API is OpenAI-compatible at `https://api.tokenfactory.nebius.com/v1`. Model names are discovered live and are never guessed in code.

## Quick start

```powershell
uv venv
uv pip install -e .
Copy-Item .env.example .env
```

Load the environment variables using your preferred secret manager. Do not commit `.env`.

Run the safe local probe:

```powershell
zephyr-day0
```

Run the authenticated model catalog probe explicitly:

```powershell
zephyr-day0 --live-models --output build/evidence/day0.json
```

After selecting a real Nemotron model ID from that report, test structured constraint compilation:

```powershell
zephyr-day0 --live-models --structured-model $env:ZEPHYR_NEMOTRON_MODEL --output build/evidence/day0.json
```

Run the test suite in the prepared local model environment:

```powershell
python -m unittest discover -s tests -v
```

## Repository shape

```text
config/                    Expected artifact manifest
docs/                      Gate procedures and evidence contract
src/zephyr/                Probe and application code
tests/                     Offline contract tests
PROJECT_PLAN.md            Current product direction and milestones
progress.md                Verified work, test evidence and next-task checklist
```

## Source contracts

- [Nebius Token Factory model-list API](https://docs.tokenfactory.nebius.com/api-reference/models/list-models)
- [Nebius structured output](https://docs.tokenfactory.nebius.com/ai-models-inference/json)
- [NVIDIA DoMINO sensitivity workflow](https://github.com/NVIDIA/physicsnemo-cfd/tree/main/workflows/domino_design_sensitivities)
- [NVIDIA DrivAerML checkpoint bundle](https://huggingface.co/nvidia/domino_drivaerml/tree/main/domino_drivaerml_surface_checkpoint)

NVIDIA PhysicsNeMo-CFD is locked in `config/upstream-lock.json`; builds must use that commit rather than floating `main` until the lock is deliberately reviewed and updated.

## Status

The native-Windows DoMINO capability gate now passes on the development RTX
4070 Ti SUPER. The pinned checkpoint completed surface inference, drag
integration, autograd sensitivity, smoothing, and VTK export on NVIDIA's
official DrivAer sample. See [docs/WINDOWS_DOMINO_GATE.md](docs/WINDOWS_DOMINO_GATE.md)
and reproduce it with `scripts/setup-domino-windows.ps1` followed by
`scripts/run-domino-windows.ps1`.

No cloud GPU endpoint has been launched. Configured Token Factory model calls
are available through the explicitly enabled local copilot.
The successful sample is runtime evidence, not independent aerodynamic
validation.
