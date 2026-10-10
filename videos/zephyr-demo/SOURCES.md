# Video claim and footage sources

The storyboard describes this implementation, not an unverified future cloud
deployment. All paths below are relative to the Zephyr repository root.

| Claim or shot | Source | Boundary |
|---|---|---|
| Nemotron served by Nebius Token Factory | `docs/evidence/nemotron-final.json`, `src/zephyr/token_factory.py`, `src/zephyr/copilot.py` | Historical verified runtime; recheck provider response when filming live |
| Exact model ID | `nvidia/Nemotron-3-Ultra-550b-a55b` in the sanitized receipt | Do not imply current catalog availability from a historical receipt |
| Structured intent, exact quotes, hard controller limits | `src/zephyr/copilot.py`, `docs/LLM_INTERFACE.md` | LLM interpretation is fallible and validated by code |
| Evidence-bound answers | `src/zephyr/copilot.py`, `src/zephyr/run_answers.py` | Model selects supplied facts; does not author numeric results |
| Local physics execution | `docs/ARCHITECTURE.md`, `docs/LOCAL_DOMINO.md` | DoMINO is not currently served on Nebius AI Cloud |
| Selected research candidate | `.local/runs/local-8907b340aebb4b1d800fb86c45451c71/evidence.json` | Separate research protocol, not the interactive 4 mm workflow |
| 621.695556640625 → 600.9733276367188 N | Same run evidence and `docs/evidence/sedan-research-2026-09-25/paused-demo/` | 3.3331795253% lower predicted drag, displayed as 3.33%; no physical savings claim |
| 32.174 mm maximum displacement | Selected run's full-resolution geometry evidence | True-scale display, fixed cabin |
| Incomplete validation | `docs/SEDAN_RESEARCH.md`, paused-demo `README.md` | No random controls, no finalist repeats, no independent candidate CFD |
| Recorded judge path | `.local/demo-sedan-and-dent-final-2026-09-26/` | No live Nemotron or GPU inference in recorded-only server |

## Revision 2 live capture receipts

- Raw: F:/github/nebius/zephyr/.local/live-demo-v2/, timestamped capture.json per take.
- Encoded footage and metadata: assets/live-v2/. Video sources are real app frames.
- Brief: live Nemotron interpretation through the configured Nebius integration, 3.1 s / 1,130 tokens shown in the recorded UI.
- Answer: “Where this answer comes from” identifies nvidia/Nemotron-3-Ultra-550b-a55b as selecting this run's facts.
- Fresh baseline: local-1dbc76b0e76d423a8cfb4f593a5fe6ad, completed during recording.
- Geometry export: clicked the actual candidate.zip link in Evidence & provenance.
- Exact edit and narration alignment: logs/live-v2-edit.json.
- The prior Manim and invented visual scenes remain archived/unused in v2.
