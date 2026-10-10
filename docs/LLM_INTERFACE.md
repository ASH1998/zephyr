# LLM in the main interface

Current runtime: NVIDIA `nvidia/Nemotron-3-Ultra-550b-a55b` through Nebius Token
Factory, verified in [the sanitized runtime receipt](evidence/nemotron-final.json).
DoMINO inference runs on the local NVIDIA GPU. The recorded demo package serves
saved results and does not make live model calls. The GLM smoke records below
are historical development evidence, not the current model identity.

Start the local API from `F:\github\nebius\zephyr`:

```powershell
& ..\.venv\Scripts\python.exe -m zephyr.local.server --enable-llm
```

Run `npm run dev` in `frontend`, then open http://127.0.0.1:5173/.
The flag explicitly enables paid Token Factory calls. Without it, the existing
exact-preset local GPU workflow remains available without model calls.

The server reads `.env` using the same config loader as the model probe.
`ZEPHYR_ACTIVE_MODEL` selects the model; `ZEPHYR_TOKEN_FACTORY_BASE_URL` selects
the endpoint. Credentials stay on the server, never in frontend variables or
artifacts. Changing model or endpoint requires restarting the API. There is no
automatic model fallback. The interface displays the actual configured model
and labels non-Nemotron models as development models.

## Interaction

1. Write a brief such as “Reduce drag with a subtle rear taper. Keep the cabin
   unchanged. Maximum displacement 2 mm.”
2. **Interpret brief** previews the plan without running the GPU. It shows exact
   quotations, the effective budget, model, latency and token count. The run
   buttons also interpret automatically when needed.
3. A ready plan permits the existing bounded rear-taper controller. A request
   to change unsupported regions or add geometry is refused or needs
   clarification. Edit the brief and try again. The rear-taper example covers
   the last 18% of car length above the underbody; additional supported tools
   are documented in [body-region exploration](BODY_REGIONS.md).
4. **Run bounded iteration** evaluates the baseline and a deterministic bounded
   candidate. A numeric mm ceiling in the brief is combined with the slider
   using the smaller bound. The 4 mm product ceiling, fixed cabin/topology,
   geometry gates and trust decisions are never controlled by the model.
5. On completion, **Your result, explained** shows a short readable summary.
   **Ask about this result** accepts plain-English questions and follow-ups.
   Summaries are free deterministic text. For questions, Nemotron chooses up to four
   relevant supplied facts; it cannot author numbers or change the decision.
   Detailed evidence and calculation checks stay in expandable sections.

Each request is bound to a server-owned `intentId`, including brief, geometry,
mode and slider budget. Changed inputs or expired IDs cannot start a worker.
Interpretations use strict structured output, exact brief quotations and runtime
validation. Numeric constraints that cannot be grounded require clarification.
The language interpretation is still fallible; inspect the compiled constraints.
Unsupported geometry or trust settings cannot be executed even if misclassified.

Identical briefs reuse their interpretation during the server session. Summary
and reload do not make paid calls. Each submitted question uses one model call;
identical question/run/parent combinations are cached. Follow-ups include up to
four earlier turns, bound to the same completed run. Questions do not launch GPU
work. There is one concurrent model request and one concurrent GPU job. Calls
have a 60-second timeout and a 2,048-token output cap, without automatic retries.

## API and evidence

- `GET /api/health`: active GPU run and safe model status.
- `POST /api/intent`: `{geometryId, budgetMm, brief, mode}` → validated plan.
- `POST /api/runs`: same request plus `intentId` when LLM mode is enabled.
- `POST /api/runs/<id>/explain`: empty JSON body; uses completed server evidence.
- `GET /api/runs/<id>/explanation`: legacy cached explanation, with no model call.
- `GET /api/runs/<id>/summary`: readable recorded result, with no model call.
- `POST /api/runs/<id>/questions`: `{question, parentAnswerId?}`; server evidence only.

Plans, explanations, and question responses are saved under ignored `.local/copilot/`. The exact
plan is also embedded in the run request, result and evidence JSON. Plans record
requested/returned model, prompt and request hashes, elapsed time and usage.
Plan authorization and conversation history expire on restart. Completed runs
with matching evidence and result files are recovered from disk when requested. This is a local development service, not a multiuser deployment.

Independent CFD and calibrated physical trust remain pending. Full-resolution
intersection checks are part of the geometry validation path; see the recorded
[sedan artifact checks](evidence/sedan-research-2026-09-25/paused-demo/README.md).
These model features do not change the scientific acceptance boundary.

## Verified browser smoke

[Recorded evidence](evidence/llm-interface-smoke.json) covers a real browser run
with the configured development model: interpretation took 8.2 seconds and
1,152 tokens. A brief requesting 2 mm overrode the larger 3.6 mm slider ceiling.
The local GPU iteration completed in 243.9 seconds, shrinking the candidate to
0.500 mm. Fresh surrogate drag increased from 621.696 to 621.826 N, and the
controller refused acceptance. The automatic explanation retained this refusal,
reported the measured movement and forces, and linked the scientific limits.
Model identity and exact usage for both calls are recorded in the evidence.

Verification: 24 Python tests, 18 frontend tests, and the production frontend
build passed. The existing large frontend bundle warning remains.

## Presentation update

The live interface now has **Show me the change**, a 3.5-second original/changed
replay. It turns to the rear and enlarges movement 120 times on screen. The label
and checkbox expose the enlargement; actual displacement and force numbers are
unchanged. Reduced-motion users receive the final comparison without replay.

GPU progress shows five understandable stages, elapsed time, and percentages
only when actual batch counts are available. Each calculation has its own
percentage. Completed-run progress collapses to leave room for the car.

Verification: 29 backend tests and 21 frontend tests passed; production build
passed with the existing bundle-size warning. Historical evidence above describes
the previous automatic-explanation UI, retained here as a dated smoke record.

Browser verification on the existing completed run: GLM answered “Why does it
look like nothing changed?” with the actual 0.500 mm movement, the display replay,
and the smaller brief limit. A follow-up “So the orange is not heat?” retained
that context. No GPU job was started by either question. The result and Q&A now
appear at the top of the sidebar; Edit brief / run again returns to the controls.
