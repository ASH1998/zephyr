# LLM in the main interface

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
   clarification. Edit the brief and try again. The supported handle covers
   only the last 18% of the car length, above the underbody.
4. **Run bounded iteration** evaluates the baseline and a deterministic bounded
   candidate. A numeric mm ceiling in the brief is combined with the slider
   using the smaller bound. The 4 mm product ceiling, fixed cabin/topology,
   geometry gates and trust decisions are never controlled by the model.
5. On completion, **LLM-ranked evidence** orders measured facts. Every displayed
   force, displacement and decision is generated from the server's evidence,
   with links to that run. The LLM selects fact IDs; it cannot invent numbers or
   turn a controller refusal into acceptance. Explanation failure leaves the
   GPU result available and offers an explicit retry.

Each request is bound to a server-owned `intentId`, including brief, geometry,
mode and slider budget. Changed inputs or expired IDs cannot start a worker.
Interpretations use strict structured output, exact brief quotations and runtime
validation. Numeric constraints that cannot be grounded require clarification.
The language interpretation is still fallible; inspect the compiled constraints.
Unsupported geometry or trust settings cannot be executed even if misclassified.

Identical brief requests reuse the cached interpretation during the server
session. Explanations are cached per run. Reload only retrieves an existing
explanation; it does not automatically make a paid call for a completed run.
There is one concurrent model request and one concurrent GPU job. Each model
call has a 60-second timeout and a 2,048-token output cap, with no automatic
paid retries. A first complete iteration normally uses two model requests.

## API and evidence

- `GET /api/health`: active GPU run and safe model status.
- `POST /api/intent`: `{geometryId, budgetMm, brief, mode}` → validated plan.
- `POST /api/runs`: same request plus `intentId` when LLM mode is enabled.
- `POST /api/runs/<id>/explain`: empty JSON body; uses completed server evidence.
- `GET /api/runs/<id>/explanation`: cached explanation, with no model call.

Plans and explanations are saved under ignored `.local/copilot/`. The exact
plan is also embedded in the run request, result and evidence JSON. Plans record
requested/returned model, prompt and request hashes, elapsed time and usage.
The API's run registry and plan authorization expire on server restart; files
remain on disk. This is a local development service, not a multiuser deployment.

Independent CFD, calibrated trust and full intersection validation remain
pending. These model features do not change the scientific acceptance boundary.

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
