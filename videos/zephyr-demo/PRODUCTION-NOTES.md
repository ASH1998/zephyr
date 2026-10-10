# Zephyr live demo v2 — review copy

Preview: http://localhost:3002/#project/zephyr-demo
Canonical project: F:/Projects/shorts/videos/zephyr-demo

Duration: 177.05 seconds (2:57). Widescreen 1920 × 1080, 60 fps timeline.
Every visual shot is recorded interaction with the real Zephyr application.
No still-image assets, invented 3D re-creations, detached architecture slides,
Manim insert, title-card scenes, silent section padding, or narration speed change.

The opening immediately identifies vehicle designers and small engineering teams,
and shows the requested moving blue/orange flow illustration. Subsequent actions
switch visibly to NVIDIA's predicted airflow and pressure. The explanation retains
surface pressure, friction, velocity, fixed-cabin geometry, shared comparison views,
grounded language answers and geometry/evidence export.

Nemotron is served by Nebius Token Factory. DoMINO runs on the local NVIDIA GPU.
These roles are named in narration and overlaid on the relevant live actions.
The saved research candidate is explicitly separate from the interactive 2 mm brief.
It has 3.333% lower predicted drag (621.70 N to 600.97 N), with zero cabin movement.
The selected candidate has not been accepted as a validated engineering improvement;
the narration accurately calls the result predicted drag. There is no separate
caveat segment in the video.

Actual fresh baseline evaluation completed during filming:
local-1dbc76b0e76d423a8cfb4f593a5fe6ad (138 seconds displayed).
Saved research comparison:
local-8907b340aebb4b1d800fb86c45451c71.
The paused research search was not resumed.

Voice: exact saved profile “jack british”
(ed4eb0bf-a1a1-41c9-9f8f-7367395b0111), Voicebox qwen3 TTS 1.7B.
Generation IDs: 3b305c41-15d3-4128-a651-f3ff4f4a50ec (148.97 s) and
57d85db9-2778-4364-9159-4069dec9d5f5 (28.08 s technical explanation).
Measured sections were joined with no added gaps. A single continuous WAV drives
the final composition. Target loudness is -16 LUFS / -1.5 dBTP. No music bed.
Script/transcript match: 96.03% and 98.9%. FFmpeg silencedetect at -38 dB found
no silence of 0.6 seconds or longer. No speaker playback was performed.
Vocal naturalness and pronunciation require listening in the review preview.

Raw capture frames and timestamps are in the Zephyr repository's
.local/live-demo-v2/. Source MP4s and metadata are assets/live-v2/.
These are recordings of browser display frames. Capture-tool stalls were trimmed
by capping inter-frame intervals at 80 ms; they are edited demonstrations, not
uncut inference benchmarks. Source delivery is 60 fps, using actual captured frames
(roughly 16–26 unique frames per second). No interpolated scientific motion is added.
All editorial crops are recorded in scripts/build-live-v2.py.

Rebuild with scripts/build-live-v2.py. The older scripts/build-demo.py is v1 only.
The exact edit, word alignment and beat boundaries are in logs/live-v2-edit.json.
Validation reports: logs/check-live-v2.json and logs/check-live-v2-final.json.
Automated checks do not establish a perceptual audio or final-export quality pass.

The user must review this revised Studio preview before final MP4 export, per the
shorts AGENTS.md and HyperFrames workflow. No final MP4 has been exported yet.
After approval, use the required quiet-render helper. This machine's current
NVENC driver/API combination failed during footage preparation, so CPU encoding
is the verified fallback; do not change GPU drivers for this task.

    pwsh -File F:/Projects/shorts/.agents/skills/hyperframes-quiet-render/scripts/quiet_render.ps1 -Project F:/Projects/shorts/videos/zephyr-demo -Output zephyr-demo-v2.mp4 -Quality high -Fps 60 -CpuEncode

Inspect the actual export before delivery. No upload is authorized.

Final automated preview check: PASS, zero lint errors/warnings, zero runtime or layout findings, 15/15 contrast checks. Muted playback reached the ending. Listening review and final export remain separate checks.

