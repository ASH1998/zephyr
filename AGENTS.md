# Zephyr engineering rules

Zephyr is an evidence-first aerodynamic design copilot. Preserve these invariants:

1. Never describe the open DrivAerML `.mdlus` checkpoint as the Automotive Aerodynamics NIM.
2. Nemotron may compile intent, plan tools and explain evidence. It must not choose raw vertex motion, bypass geometry checks or decide trust thresholds.
3. Every accepted deformation is fixed-topology, bounded, validated and freshly evaluated.
4. Never call surrogate output ground truth. Independent CFD is the trusted comparison and may disagree.
5. Never print or persist credentials. Environment reports record only whether a secret is present.
6. Do not start paid cloud resources from scripts by default. Live calls require an explicit CLI flag.
7. Keep demo claims traceable to versioned evidence. A failed gate changes the claim or stops the build.

The current product and validation specification is in `PROJECT_PLAN.md`.

