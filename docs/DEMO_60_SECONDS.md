# Zephyr: 60-second presentation

Use a wide desktop for linked Original / Changed views. At narrower widths the views stack. Local API: 8766; UI: 5173. Keep the configured GLM development model. This walkthrough makes no Nemotron, Nebius GPU deployment or independent CFD claim.

## Prepare two recorded results

Open these completed local GPU results in separate tabs before presenting:

- [Accepted sedan](http://127.0.0.1:5173/?replay=local-c29499fe827b4d7e9b7ac01f29ff8428): 621.69556 → 621.60510 N; predicted reduction 0.09645 N, fresh reduction 0.09045 N, disagreement 6.22%; actual maximum movement 0.375 mm. Worker time **7m 52s**.
- [Refused hatchback](http://127.0.0.1:5173/?replay=local-dfd56fe51ebc497a9d768d7498cede7a): 474.92291 → 473.78961 N; predicted reduction 0.70990 N, fresh reduction 1.13330 N, disagreement 59.64%; maximum movement 3.00 mm. Worker time **30.43s**.

Both pages must visibly say **RECORDED REPLAY**. The same fixed local policy is used for both; the hatchback also lies outside the model's supported training domain. Use these run IDs and numbers together. New optimized runs have their own IDs and timings in [RUNTIME_CHECKS.md](RUNTIME_CHECKS.md); do not attach those timings to these older recordings.

## Walkthrough

| Time | Action and narration |
|---|---|
| 0–8 s | Show the sedan and replay label. “Zephyr tests a small shape change while keeping the cabin fixed. This is a recorded local GPU calculation.” |
| 8–18 s | Open **Compare Original / Changed** and select **Change**. “It checked the original, measured small test changes, then evaluated this candidate independently. Geometry checks reduced the requested 3 millimeters to 0.375 millimeters.” |
| 18–30 s | Orbit the linked pair; point to actual movement and enlargement label. “Both views move together. Orange marks the changed area. Movement is enlarged 120 times so you can see it.” Turn enlargement off before comparing true geometry. |
| 30–42 s | Read the sedan verdict, then select **Pressure**. “The model predicted a 0.096-newton reduction and measured 0.090 in the fresh candidate evaluation: 6.22 percent disagreement. It passes our local checks for further evaluation. Independent CFD is still required.” |
| 42–55 s | Switch to the hatchback tab and open comparison. “This car shows a larger estimated reduction, but we refuse the step: the probe check failed, prediction disagreement is 59.64 percent, and this shape is experimental for the model.” |
| 55–60 s | Point to the refusal and replay label. “A lower model estimate alone is not enough. Zephyr shows the evidence and the limits.” |

Pressure and NVIDIA airflow use each shape's own calculated fields with shared scales. **Flow illustration** is an authored explanation. Aircraft and their illustrated wingtip spirals are optional exploration after the timed walkthrough.

Optional Q&A (“Why was this accepted?” / “Why was this refused?”) remains bound to the selected run and may take extra time. Use the deterministic summary for the timed presentation. Do not describe local surrogate acceptance as physical proof.

## Live rehearsal

Check `/api/health` for an idle GPU before starting a job. Select DrivAer sedan, use the bounded rear-width brief and 3 mm ceiling, then click **Run bounded iteration** once. Report actual progress and elapsed time. If presenting while it runs, switch explicitly to one of the recordings above; do not cancel or duplicate the job just to meet the presentation length. Report a fresh refusal if it occurs.

The 60 seconds covers the presentation, not live sedan computation. GPU worker timings exclude brief interpretation, asset loading and browser polling.

## Development regression fixtures

`/tests/browser-harness.html?scenario=missing-volume`, `failed`, `cancelled`, `running`, `publishing`, or `reduced-motion` are visibly labeled synthetic fixtures that block POST requests and are excluded from production builds. They are not inference evidence or presentation fallbacks. Earlier hatchback rehearsals remain historical evidence in `progress.md`; this script uses the two frozen acceptance references above.
