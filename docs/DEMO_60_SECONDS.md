# Zephyr: 60-second presentation

Use a wide desktop for the side-by-side view. At 979×882 the views stack and remain
linked. Start the local API on 8766 and UI on 5173; keep the configured GLM development
model. This walkthrough does not claim a Nemotron or Nebius GPU deployment.

## Rehearsal using recorded evidence

Open [the recorded hatchback replay](http://127.0.0.1:5173/?replay=local-336be40999c940e9acff6f83fa10bd8a).
The page must say **RECORDED REPLAY**. This is a completed local GPU calculation,
not a live inference or the separate illustrative design walkthrough.

| Time | Action and narration |
|---|---|
| 0–8 s | Show the hatchback and brief. “Zephyr explores a small change to this car while keeping the passenger cabin fixed. This is a recorded local GPU result.” |
| 8–15 s | Point to completed progress and elapsed time. “The NVIDIA model tested the original, we made a bounded rear taper, checked it, then tested the changed shape.” Do not play these stages as if a GPU is running now. |
| 15–30 s | Click **Compare Original / Changed**. “Original on the left, changed on the right. Orange shows where it moved. The largest actual movement was 3.60 millimeters; the shape movement here is enlarged 120 times.” Orbit either view; both move together. |
| 30–40 s | Uncheck enlargement, then select **Pressure** or **NVIDIA airflow**. “Each shape has its own calculated field, with the same color scale. These paths are steady predictions shown in slow motion.” |
| 40–50 s | Read the verdict. “Estimated resistance fell by 1.42 newtons, about 0.299 percent. Engineering acceptance is still refused: calibration and full intersection checks are unfinished. This is not independent CFD proof.” |
| 50–60 s | Close comparison. Select **NASA Global Hawk**, then **Flow illustration**. “Aircraft exploration is experimental. These two opposite-turning wingtip spirals are an illustration, not a flight-performance result.” |

For a short pitch, use the deterministic visible summary. An optional question such
as “Why was it rejected?” uses the configured model and may take extra time. Follow-up
questions remain attached to the same run and do not start another GPU calculation.

## Live rehearsal

Check `/api/health` for an idle GPU. Select Impreza hatchback, enter a bounded brief,
and click **Run bounded iteration** once. Use the real progress and elapsed clock;
never promise completion inside 60 seconds. If it runs long, explicitly switch to
the recorded replay above in another tab, without cancelling or duplicating the job.
Report the current live result even if resistance increases or acceptance is refused.

The recorded original took 22.087 seconds of worker time. Brief interpretation,
asset loading and browser polling are additional time. See `progress.md` and the
presentation evidence for the fresh rehearsal's actual run ID and duration.

## Repeatable regression fixtures

Development only: `/tests/browser-harness.html?scenario=missing-volume`, `failed`,
`cancelled`, `running`, or `reduced-motion`. These pages visibly label altered
recorded responses and block POST requests. They are excluded from the production
build. Never use a fixture page as inference evidence or as the presentation fallback.

Fresh rehearsal: `local-f76a1757dc7d4143abbbd8f69e53d5f3`, worker time 22.581 s,
474.9229 to 473.4725 N, 3.00 mm maximum, protected cabin unchanged, acceptance
refused. Its [recorded replay](http://127.0.0.1:5173/?replay=local-f76a1757dc7d4143abbbd8f69e53d5f3)
is also available; use the corresponding numbers if presenting this run.
The `publishing` fixture checks the interval between worker completion and final
API publication without launching another job.
