# Public competitor snapshot

Date: 2026-09-20

This is a point-in-time review of publicly discoverable GitHub repositories and Devpost pages for the Nebius x NVIDIA Global AI Hackathon. It is not exhaustive: private repositories, unindexed pages, and unannounced projects are invisible.

## Bottom line

No public contestant found in this search is building the same aerodynamic design loop as Zephyr. The nearest technical baseline is NVIDIA's own [DoMINO design-sensitivity workflow](https://github.com/NVIDIA/physicsnemo-cfd/tree/main/workflows/domino_design_sensitivities), not another hackathon product.

The strongest competition is for the **trustworthy Nemotron application** story. Several teams use the same winning pattern: domain-specific workflows, deterministic gates around model output, replayable evidence, and a polished judge path. Zephyr's defensible difference is that its evidence is not only text provenance—it connects a brief to a bounded geometry, a local GPU surrogate evaluation, a fresh comparison, and an explicit accept/refuse decision.

## Projects worth watching

| Project | Public idea | Strongest signal | Overlap with Zephyr | What to learn |
|---|---|---|---|---|
| [NemoFold](https://github.com/ellmos-ai/NemoFold) | Private document agent with local authority, exact citations, reversible actions, and bounded Nemotron reasoning | Large test suite, committed secret-free paid-run receipt, offline verification, strong failure story | High overlap in evidence-first positioning; no physics or geometry loop | Make one sanitized Nemotron receipt and one local GPU result trivially re-verifiable by judges |
| [Indie App Ops Agent](https://github.com/YK-StudioPM/indie-app-ops-agent-nemotron) | Multi-Nemotron operations agent for reviews, crashes, revenue, and screenshot QA | Clear user pain, deterministic anomaly checks, independent audit, replayable traces, measured cost | Medium overlap in deterministic trust and operator UX | Show the cost/latency and exact role of every model call; keep offline/demo/live modes obvious |
| [MeshCFO Control Tower](https://github.com/Cubiczan/meshcfo-control-tower) | Governed remediation briefs from labeled financial-control signals | Narrow buyer, per-claim provenance, lock states, deterministic playbooks, prepared short demo | Medium overlap in domain-specific gates and refusal language | Keep the buyer and decision moment concrete; make the trust state understandable without reading internals |
| [Nemotron Research Agent](https://github.com/darrenthanawinn-ux/NemotronResearchAgent) | Planner/researcher/critic/synthesizer pipeline with model-tier routing and live progress | Familiar full-stack demo and visible multi-agent timeline | Low product overlap; high judge-attention overlap | Zephyr should not compete on agent count. Demonstrate that one bounded model role unlocks a real physical workflow |
| [Spaghetti Overflow hackathon workspace](https://github.com/Spaghetti-Overflow/nvidia-x-nebius-hack) | Coding-agent R&D, sandboxed runtimes, and developer tooling | Active public build in a broadly popular agent category | Low direct overlap | Zephyr's domain depth and GPU visualization are more distinctive than another general developer agent |

Other public submissions include broad workspaces, finance platforms, and flood-risk tools. They compete for overall polish and impact, but they do not currently appear to duplicate Zephyr's DoMINO-driven aerodynamic design concept.

## Position Zephyr around the closed loop

The pitch should make this sequence unmistakable:

1. A user states a constrained aerodynamic goal.
2. Nemotron compiles only supported intent; it does not control the mesh or the trust decision.
3. A deterministic controller proposes a fixed-topology, millimetre-bounded change while preserving protected regions.
4. NVIDIA DoMINO evaluates the original and candidate locally on the GPU.
5. Numerical and geometry gates accept, shrink, or refuse the candidate.
6. The UI links every result to run identity, hashes, constraints, and limitations.

That is materially different from the dominant public pattern of sending text through several agents and rendering a report.

## Demo recommendations

- Lead with the visual aircraft/car workspace, then switch quickly to the car workflow where bounded changes are valid.
- Show one accepted sedan and one refused hatchback. The refusal is part of the product, not a failed demo.
- Put the Nemotron model ID, local GPU stage, actual displacement, run ID, and trust verdict on screen.
- Say “accepted for further evaluation,” never “aerodynamically proven.”
- Keep the aircraft experience explicitly experimental and baseline-only so visual impact does not blur the scientific boundary.
- Prepare a short recorded result for the expensive run and a clean-start checklist for judges.

## Competitive risks

- **Setup friction:** other projects launch with Docker or one API key. Counter with the clean installation guide, recorded evidence, and a predictable judge path.
- **Dense scientific language:** judges may miss the product. Counter with a five-word verdict and reveal details progressively.
- **Small measured deltas:** do not sell the magnitude. Sell the evidence chain and the system's willingness to refuse.
- **Nemotron appearing ornamental:** show the structured brief it produced and the exact deterministic actions that followed.
- **Aircraft overclaiming:** retain the car-trained-model warning and never present illustrated vortices as calculated performance.

## Search notes

Sources reviewed included the public [Nebius GitHub topic](https://github.com/topics/nebius), current Devpost project pages, their linked repositories, and GitHub searches for the hackathon name, Nemotron, DoMINO, and aerodynamic design. Repeat this check near submission because the field is changing quickly.
