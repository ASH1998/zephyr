# Day-0 capability gate

This gate answers whether Zephyr's load-bearing dependencies exist in the real account and exact artifact bundle. It does not launch a GPU endpoint.

## A. Token Factory catalog

1. Set `NEBIUS_API_KEY` in a local secret store.
2. Set `NEBIUS_AI_PROJECT_ID` if the account requires project-scoped model listing.
3. Run `zephyr-day0 --live-models --output build/evidence/day0.json`.
4. Select a model whose live metadata supports the required structured-output/tool behavior. Do not infer availability from public marketing pages.
5. Record the selected model ID in local configuration as `ZEPHYR_NEMOTRON_MODEL`.

Pass: the account returns at least one NVIDIA/Nemotron candidate and the selected model is present.

Fail: authentication, account access or a qualifying runtime path cannot be established.

## B. Structured constraint probe

Run:

```powershell
zephyr-day0 --live-models --structured-model $env:ZEPHYR_NEMOTRON_MODEL --output build/evidence/day0.json
```

The model must produce a strict object representing the instruction:

> Reduce drag. Keep the cabin unchanged. Maximum displacement: 4 mm.

Pass requires:

- `objective` is exactly `reduce_drag`;
- `locked_regions` includes `cabin`;
- `max_displacement_mm` is exactly `4`;
- no additional fields appear.

This is only a transport/schema smoke test. The full benchmark remains 30 labelled briefs with deterministic post-validation.

## C. DoMINO artifact bundle

Place the exact files named in `config/domino-artifacts.json` under the directory in `ZEPHYR_DOMINO_ASSETS_DIR`. The local probe verifies presence and non-zero size. Before a reproducible run, populate and verify SHA-256 values in the manifest or a versioned lock file.

Pass: `.mdlus`, matching scaler and matching training-domain configuration are all present.

Fail: never substitute the separate Automotive Aerodynamics NIM while retaining checkpoint-specific sensitivity claims.

The publisher workflow revision is separately pinned in `config/upstream-lock.json`. Re-resolving it is a deliberate upgrade that requires rerunning the sample workflow and finite-difference gate.

## Evidence rules

- The generated report records booleans and public model IDs, never secrets.
- `build/` is ignored until a report has been manually reviewed for publication.
- A report is evidence of capability, not evidence of aerodynamic accuracy.
- Paid compute and endpoint creation require a separate explicit decision.
