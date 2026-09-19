> Historical research plan, superseded by ../../PROJECT_PLAN.md on 2026-09-19. Targets and competition details below are not a record of implemented or reverified capabilities.

# Zephyr — Hackathon Project Plan

**Status:** Research-backed implementation specification; local scaffold started, paid infrastructure not yet approved\
**Hackathon:** Nebius x NVIDIA Global AI Hackathon\
**Track:** Best Apps and Agents\
**Submission deadline:** October 30, 2026, 10:00 PDT\
**Primary tagline:** *Shape the flow.*

## 1. Executive decision

Zephyr is an agentic aerodynamic design copilot for small automotive and EV engineering teams. The user provides a passenger-car surface, a design brief and bounded rules. Nemotron compiles the language into an executable constraint graph. NVIDIA's open PhysicsNeMo-CFD DoMINO checkpoint evaluates surface pressure, wall shear, total aerodynamic force and local drag sensitivity. A deterministic controller makes small, mesh-safe changes and re-evaluates each one. The system refuses changes that violate geometry constraints or leave its empirically calibrated trust region.

> **Zephyr helps engineers reshape vehicles for lower drag—with AI-guided changes and simulation-backed proof.**

The winning mechanism is:

```text
engineering intent
→ executable constraint graph
→ aerodynamic fields and drag sensitivity
→ bounded fixed-topology deformation
→ fresh evaluation
→ accept, shrink or refuse
→ independent CFD validation of finalists
```

This is not a general CAD generator and not a replacement for trusted CFD. It is a fast design-exploration system that helps engineers decide which candidates deserve expensive validation.

## 2. Official competition fit

The Best Apps and Agents track asks for an application people would use, powered by Nemotron on Nebius through Token Factory. Nebius Serverless Endpoints and Jobs are encouraged. The project requirements define a valid Nebius runtime as either a Token Factory inference call or deployment on AI Cloud compute.

**Stage-One defense:**

> Zephyr is an engineering application in which Nemotron on Nebius Token Factory turns unstructured requirements and rule excerpts into an executable constraint graph and orchestrates domain tools. NVIDIA's open DoMINO checkpoint runs on Nebius AI Cloud and supplies the aerodynamic fields and local drag gradients used by a deterministic, safety-bounded optimizer.

Do not submit this to Physical AI. It does not sense and act in the physical world.

Submission obligations planned from the start:

- public working demo or test build;
- public open-source repository with visible license and reproducible README;
- public YouTube demonstration under three minutes;
- explicit evidence of runtime Nebius and NVIDIA-model use;
- free judge access through the judging period;
- project must behave as depicted;
- every third-party dataset, solver and model must be used under its applicable terms.

Judging implications:

- Stage One is pass/fail for genuine theme and API/model fit.
- Stage Two equally weights technological implementation, design, potential impact and quality of idea.
- Technological implementation is the first tie-break criterion.
- Judges may never test the app and may judge solely from the video, images and description.

## 3. User and painful moment

**Hero user:** an aerodynamics or energy engineer at a small EV company, retrofit shop or student automotive team working on a passenger-car-shaped body.

**Pain:** the team has many useful design questions but can afford to send only a few geometries through a trusted CFD workflow. The bottleneck is not that CFD is impossible; it is that slow or expensive iteration suppresses exploration.

**Job to be done:** turn a design brief into several legal, ranked, explainable candidates before spending limited trusted-solver time.

Formula Student, open-wheel vehicles, wings, SUVs and arbitrary uploads are not part of the hero claim until out-of-distribution testing supports them.

### 3.1 Identity and visual system

The identity makes an invisible force visible. **Zephyr** suggests air that is light, fluid and controllable without making a claim about the engineering result. The primary pairing is:

> **Zephyr — Shape the flow.**

Visual direction:

- midnight-blue environment with crisp white typography;
- fine cyan airflow and sensitivity lines as the active visual language;
- a restrained curved stroke forming a subtle `Z`, like air bending around a surface;
- precise, calm interface chrome so the vehicle, flow field and measured change remain dominant;
- motion follows streamlines and pressure transitions rather than generic glowing-AI effects.

Supporting lines may be used selectively—**Small changes. Less resistance.**, **Every curve counts.**, and **Find the shape that flows.**—but only *Shape the flow.* appears as the primary brand tagline.

## 4. Correct technical foundation

### 4.1 Core artifact

Use NVIDIA's public `domino_drivaerml_surface_checkpoint`, particularly:

- `DoMINO.0.501.mdlus`;
- matching `scaling_factors.pkl`;
- matching training configuration and bounding boxes;
- NVIDIA's published `domino_design_sensitivities` workflow.

The workflow returns:

- geometry coordinates;
- `d(-drag)/dX` geometry sensitivity;
- surface pressure;
- surface wall-shear vector;
- integrated aerodynamic force `[Fx, Fy, Fz]`;
- normal-projected and smoothed sensitivity fields;
- finite-difference gradient-checking utilities.

### 4.2 Do not conflate checkpoint and NIM

The open DrivAerML checkpoint and the DoMINO Automotive Aero NIM must not be described as the same artifact. The public sensitivity workflow establishes gradient access for the `.mdlus` checkpoint. The Automotive NIM documentation describes a separate RANS-trained model and does not establish the same optimization-gradient interface.

The film and README must attribute every latency, model envelope and validation result to the exact artifact actually used. Do not reuse the NIM's published latency numbers.

### 4.3 Honest operating envelope

The checkpoint is associated with parametrically morphed DrivAer-like notchback vehicles. The product therefore enforces:

- passenger-car-like hero geometry;
- fixed surface connectivity;
- watertight input;
- small, smooth deformation;
- no topology creation or removal;
- hard displacement and angle bounds;
- symmetry rules where applicable;
- self-intersection, normal and triangle-quality checks;
- fresh DoMINO evaluation after every accepted step;
- visible predicted-versus-evaluated error;
- refusal outside the calibrated trust region.

Large mesh warps may be used only as clearly labelled visual magnification. Actual displacement must always be displayed.

## 5. Product scope

### 5.1 MVP input

- one prevalidated DrivAer/DrivAerML-style notchback STL;
- one fixed flow condition until velocity generalization is tested;
- plain-English design brief;
- optional text or PDF excerpt containing rules;
- 6–10 predefined manufacturable geometry handles.

### 5.2 MVP output

- surface-pressure map;
- drag-sensitivity overlay;
- protected-region envelope;
- compiled constraint graph with quoted source clauses;
- ranked legal candidate steps;
- predicted and freshly evaluated force change;
- visible trust error and step history;
- accepted/rejected/refused audit trail;
- downloadable candidate STL;
- independent-CFD evidence for the final candidate.

### 5.3 Initial geometry handles

Prefer handles close to the published DrivAerML morphing space:

- hood angle;
- windscreen angle;
- greenhouse taper;
- backlight angle;
- decklid height;
- rear-end taper;
- rear-diffuser angle;
- ride height;
- vehicle pitch;
- front plan-view adjustment.

The MVP should activate only the 6–8 handles that survive early geometry and trust testing. Each handle must be manufacturable by construction rather than merely visually smooth.

## 6. Load-bearing Nemotron role

Nemotron must own real language and planning work while deterministic software owns numerical safety.

### Nemotron responsibilities

1. Parse the design brief and rule excerpt.
2. Map source clauses to named regions and available handles.
3. Produce a schema-validated constraint graph:
   - objective;
   - protected regions;
   - allowed handles;
   - per-handle bounds;
   - hard and soft constraints;
   - quoted evidence;
   - unresolved ambiguity.
4. Select the next appropriate domain tool from summarized results.
5. Explain accepted, rejected and refused steps using measured fields.
6. Produce a final evidence report linking claims to artifacts.

### Nemotron must not control

- raw vertex movement;
- numerical step size;
- mesh validity;
- trust thresholds;
- hard-constraint enforcement;
- acceptance of invalid candidates.

### Candidate tool contract

```text
inspect_geometry()
compile_constraints()
lock_region()
set_handle_bounds()
evaluate_domino()
propose_handle()
apply_bounded_deformation()
validate_mesh()
compare_evaluations()
run_trusted_cfd()
accept_candidate()
```

At project start, query the real Token Factory model catalog and record the exact working model IDs. Use the strongest available Nemotron for initial rule interpretation and a faster model for iteration explanations only if both are demonstrably available and schema-reliable.

## 7. Geometry and optimizer design

### 7.1 Morphing

Use constrained free-form deformation or radial-basis-function morphing over the original vertex array. Preserve face connectivity by moving vertices instead of rebuilding surface topology.

Each semantic handle defines:

- region or control cage;
- permitted direction;
- minimum and maximum value;
- maximum step;
- fixed boundary points;
- symmetry behavior;
- continuity/manufacturability checks.

PyGeM is a candidate implementation because it supports FFD/RBF and mesh formats under an MIT license, but the 48-hour gate must prove it can preserve the exact geometry invariants required here.

### 7.2 Primary optimization loop

1. Project smoothed sensitivity onto each handle basis.
2. Rank handles by predicted drag reduction.
3. Select one legal bounded step.
4. Reject geometrically invalid output.
5. Run a fresh DoMINO forward evaluation.
6. Compare predicted and evaluated change.
7. Accept, shrink or refuse.
8. Update trust evidence and repeat.

Do not optimize raw vertex coordinates directly.

### 7.3 Built-in fallback

Implement derivative-free bounded search over the same handles from the beginning:

- Latin-hypercube or random warm start;
- Bayesian optimization or CMA-ES over a small parameter space;
- batched DoMINO forward evaluation;
- identical geometry verifier;
- sensitivity map retained for diagnosis and explanation.

If local gradients fail but forward ranking works, narrow the product claim to:

> Explore many legal variants quickly and reserve trusted CFD for the best few.

## 8. Validation and evidence design

Validation has three distinct jobs. They must not be conflated.

### Layer A — checkpoint evaluation on public CFD

Use selective DrivAerML downloads rather than the roughly 31 TB full dataset. Fetch only the required STL, surface fields, force values and geometry metadata.

Metrics:

- integrated drag-force MAE;
- rank correlation across selected cases;
- area-weighted surface-pressure error;
- wall-shear error;
- performance on high- and low-drag cases when the verified split supports it.

Do not claim specific case IDs are held out for this checkpoint until the exact checkpoint split is verified. The public checkpoint materials mention training and test counts, but the precise IDs must be established before publishing held-out results.

### Layer B — gradient implementation

First reproduce NVIDIA's finite-difference notebook unchanged. Then test every custom deformation handle.

Metrics:

- sign agreement between gradient-predicted and fresh-forward drag change;
- relative magnitude error;
- usable displacement radius;
- accepted-step monotonicity;
- prediction-error growth with step size.

This validates local surrogate behavior, not physical truth.

### Layer C — independent CFD

Adapt a pinned OpenFOAM DrivAer external-aerodynamics tutorial:

1. baseline and candidate use identical meshing and solver settings;
2. remesh both from STL;
3. require `checkMesh` success;
4. monitor residual and force convergence;
5. perform at least one coarse/medium consistency comparison;
6. compare direction and ranking before claiming absolute agreement.

A practical hackathon solve is likely steady RANS while the open checkpoint is associated with HRLES-derived DrivAerML data. Therefore independent CFD should validate direction and candidate ranking rather than be called exact ground truth.

Pre-register the disagreement branch as carefully as the success branch. If the independent solver disagrees in direction for a separation-dominated change, show the disagreement, remove the unsupported improvement claim and explain the model-fidelity boundary. A transparent disagreement is acceptable evidence about where the copilot must stop; concealing it is not.

### Negative control — surrogate level, N = 20

Evaluate 20 random legal deformations at the same displacement budget using DoMINO fresh-forward evaluations. Report the complete drag-change distribution and the optimized candidate's percentile, with an interval. The preregistered target is at or above the 95th percentile: it must beat at least 19 of 20 random candidates.

### Trusted-solver set — N = 6

Run OpenFOAM only for the baseline, three optimizer finalists and two random candidates drawn from the control set. Use identical meshing and solver settings. Report Spearman rank agreement across the six cases. Blind labels during trusted-solver evaluation where practical and write thresholds before observing results.

## 9. Preregistered success metrics

- **Constraint validity:** zero accepted hard-constraint violations.
- **Mesh validity:** every accepted candidate passes connectivity, normal, self-intersection and quality checks.
- **Gradient direction:** at least 90% sign agreement across N >= 30 perturbations (three handles by ten steps) inside the selected trust radius, with a 95% interval.
- **Evaluation noise:** define the noise floor as the standard deviation of predicted drag across N >= 10 null or sub-threshold deformations. If deterministic inference makes that effectively zero, substitute the measured Layer-A drag MAE and say so.
- **Optimization:** final fresh-forward drag reduction exceeds 3× the declared noise floor.
- **Negative control:** optimized candidate beats at least 19 of 20 equal-budget random legal deformations.
- **Independent validation:** report rank agreement, direction and discrepancy across the six-case trusted-solver set. If direction disagrees, remove the physical-improvement claim and present the trust-boundary finding.
- **Constraint compiler:** N = 30 labelled briefs; 30/30 schema-valid and at least 24/30 semantically correct; ambiguity must trigger clarification or refusal.
- **Runtime:** report p50 and p95 for parsing, inference and full iterations.
- **Trust behavior:** every forced illegal or out-of-range test is refused.
- **User outcome:** report viable candidate iterations per hour; do not claim solver runs avoided unless directly demonstrated.

Convert aerodynamic improvement only into transparent quantities. Aerodynamic power equals drag force multiplied by velocity. Show every input. Avoid speculative range, fuel, battery-life or CO₂ claims.

## 10. Proposed Nebius architecture

```text
Browser / 3D viewer
        |
        v
Web API + deterministic controller
        |
        +--> Nemotron via Token Factory
        |      constraint compilation, tool planning, explanation
        |
        +--> DoMINO GPU service on Nebius AI Cloud
        |      pressure, shear, force, sensitivity
        |
        +--> Object Storage
        |      STL, VTK and evidence artifacts
        |
        +--> OpenFOAM Serverless Job
               asynchronous independent validation
```

Deployment policy:

- prototype from a pinned PhysicsNeMo-CFD commit;
- package pinned dependencies and checkpoint in a custom container;
- use a Nebius GPU Endpoint or persistent GPU deployment for DoMINO;
- use asynchronous Jobs for independent CFD;
- store only required artifacts;
- keep credentials behind the backend;
- preload one public demo case so judges can succeed immediately;
- keep the final demo available through the judging period.

PhysicsNeMo-CFD describes itself as workflow-oriented experimental software rather than a stable production API. Pin exact versions and record hashes.

## 11. Forty-eight-hour falsification plan

This plan is designed now and should be executed only after approval.

### Gate A — account and artifacts

- query the real Token Factory account;
- record a working Nemotron model ID and runtime call;
- prove structured JSON/tool behavior;
- verify Nebius GPU quota/capacity;
- download the `.mdlus`, scaler and matching configuration.

**Kill:** no qualifying Nemotron runtime path or no Nebius compute access.

### Gate B1 — publisher workflow as shipped

Run NVIDIA's sample sensitivity workflow unmodified on Nebius, using the checkpoint and configuration it ships with.

- **Pass:** stable repeatable pressure, force and gradient outputs.
- **Downgrade:** 90–180 second iterations become asynchronous.
- **Kill interactive story:** median over 300 seconds at acceptable fidelity or unstable results.

### Gate B2 — intended artifact

Re-run the workflow against `DoMINO.0.501.mdlus` with its matching `scaling_factors.pkl`, training configuration and bounding boxes.

- **Pass:** the same stability plus physically plausible force values for the hero body.
- **Kill sensitivity claim:** B1 passes but B2 fails. The sensitivity interface is not established for the artifact we intend to ship, so no downstream result may rely on it.

### Gate C — finite-difference check

Run the supplied gradient check with positive and negative perturbations.

- **Pass:** a stable local interval has consistent predicted and fresh-forward direction.
- **Fail:** after excluding integration defects, abandon gradient control and use derivative-free search.

### Gate D — three real handles

Implement three FFD/RBF handles at several millimetre or equivalent angular steps.

- fixed connectivity and watertightness retained;
- no self-intersection;
- symmetry preserved where required;
- fresh inference succeeds;
- at least two handles produce repeatable directional response.

### Gate E — independent solver path

Run the stock OpenFOAM DrivAer case, substitute one bounded morphed STL, complete meshing, pass `checkMesh`, start the solve and extract force history.

- **Pass:** baseline and candidate enter one automated validation path.
- **Downgrade:** stable meshing but incomplete convergence moves completion to Week 2.
- **Kill optimization claim:** candidate geometry cannot be meshed reliably by the Week-2 checkpoint.

### Gate F — Nemotron mechanism

Test 30 labelled briefs/rule excerpts.

- 30/30 valid schemas;
- at least 24/30 semantically correct;
- zero accepted hard-constraint violations after deterministic checks;
- at least one ambiguity triggers clarification/refusal.

Failure is a track-fit problem, not a cosmetic defect. Redesign Nemotron's role before any polish; do not silently replace the load-bearing mechanism with a form.

## 12. Execution schedule

### September 18–20 — falsification

After approval, focus portfolio compute on Zephyr Gates A–F. Run one shared account capability probe for model IDs, structured output, GPU quota, dataset/display rights and endpoint behavior. Choose gradient optimizer, derivative-free optimizer, narrowed ranker or kill.

### September 21–27 — physics vertical slice

- pinned Nebius DoMINO image;
- one hero STL;
- three then six handles;
- geometry validator;
- pressure/sensitivity output;
- forward accept/reject loop;
- initial public-case benchmark.

Exit: command line completes one trustworthy iteration.

### September 28–October 4 — independent proof

- automated OpenFOAM job;
- baseline/candidate parity;
- 20 surrogate-level random negative controls and the six-case trusted-solver set;
- trust-radius calibration;
- checkpoint-split verification;
- frozen metric definitions.

Exit: at least one candidate has non-circular evidence.

### October 5–10 — agent vertical slice and rough cut

- constraint schema;
- Token Factory tool loop;
- deterministic verifier;
- ambiguity/refusal UX;
- prompt/rule evaluation set;
- audit trail showing what Nemotron did.
- assemble a complete rough video with placeholder evidence cards by October 10.

Exit: prompt → constraints → evaluated candidate works end to end.

### October 11–17 — coherent product

- browser 3D viewer;
- pressure/sensitivity overlays;
- actual-versus-magnified displacement toggle;
- protected envelopes;
- history and trust plot;
- prepared public case;
- result export.

Exit: an unfamiliar user completes the flow without team intervention.

### October 18–23 — robustness, proof and shooting

- automotive/CFD user review if accessible;
- latency and failure testing;
- deployment recovery;
- metric freeze;
- shoot final product/user footage October 20–23.

Exit: every numerical claim has a versioned evidence artifact.

### October 24–25 — final edit

- edit 2:45–2:55 film;
- replace the placeholder evidence cards with frozen results;
- public repository, license, notices and README;
- public demo and clean login path;
- Devpost description, images and sponsor feedback.

### October 26–29 — judging rehearsal and submission

- test the demo anonymously;
- install from README on a clean machine;
- watch the film muted and confirm the idea remains legible;
- verify endpoints and credentials;
- submit with at least one day of buffer.

## 13. Three-minute film plan

Target runtime: 2:50.

### 0:00–0:10 — proof before explanation

No logo. Begin in near-darkness with the silhouette of the car. Fine cyan airflow lines reveal the body as they bend around it.

Opening line:

> **“You can't see the air holding this car back. Zephyr can.”**

The engineer types:

```text
Reduce drag.
Keep the cabin unchanged.
```

Protected cabin surfaces lock into place. The permitted regions illuminate; the 4 mm maximum appears as a constraint chip. The surface becomes a true-scale displacement colormap in millimetres—blue at 0 mm, red at 4 mm—so the tiny real movement is instantly legible without magnification. Drag-sensitivity arrows appear, the bounded geometry changes, and fresh evaluated drag moves from `[measured X]` to `[measured Y]`.

First line:

> “Four millimetres. Measured, not guessed.”

### 0:10–0:30 — painful moment

A real engineer or student explains:

> “We have dozens of ideas and only a few trusted solver runs.”

### 0:30–1:05 — one complete loop

Rule excerpt → Nemotron constraint graph → sensitivity projected onto legal handles → deterministic bounded step → geometry check → fresh evaluation.

### 1:05–1:30 — signature refusal

Force two failures:

1. a request conflicts with a protected requirement;
2. a larger step leaves the calibrated trust region.

Remembered line:

> “It stops when it stops being trustworthy.”

### 1:30–2:00 — independent proof

Reveal blind labels. Show one scatter: 20 random equal-budget candidates as a cloud near zero, with the optimized candidate as one contrasting point; then add the six trusted-solver ranks. If the trusted solver disagrees, show that instead of narrating a win. Say “trusted validation,” not “ground truth.”

### 2:00–2:25 — relatable consequence

At the exact velocity used by the evaluated checkpoint case—not a rounded marketing speed:

```text
measured drag-force reduction × speed
= measured aerodynamic-power reduction
```

Do not extrapolate to vehicle range.

### 2:25–2:35 — complete product

An unfamiliar user runs a second case, inspects the result and exports a candidate for trusted CFD.

### 2:35–2:50 — close

Return to the single negative-control scatter and the displacement colormap. Overlay only the evaluated drag change, candidate time and trusted-solver rank agreement. These are annotations on the proof image, not a table the judge must read.

Final line:

> “Zephyr helps engineers ask a hundred design questions before spending their one trusted solver run.”

End card: the curved `Z`, **Zephyr — Shape the flow.**, then Nemotron on Token Factory; PhysicsNeMo DoMINO on Nebius AI Cloud; independent CFD on Nebius Jobs.

## 14. Risk register and fallback ladder

| Risk | Earliest evidence | Response |
|---|---|---|
| Gradient is noisy | Publisher and handle finite-difference checks | Derivative-free bounded search |
| Forward model cannot rank variants | Public CFD cases | Kill or narrow to diagnosis |
| Geometry leaves distribution | Domain and plausibility checks | Refuse; keep hero DrivAer-like |
| New STL cannot mesh | OpenFOAM smoke test | Narrow handles; remove validation claim if unresolved |
| Validation is circular | Independent solver | Claim candidate ranking only if independent evidence is incomplete |
| Nemotron feels bolted on | Constraint/tool benchmark | Make rule compilation central and visible |
| Exact Nemotron unavailable | Real `/v1/models` query | Resolve immediately; do not invent model IDs |
| Inference is slow | p50/p95 measurement | Honest asynchronous workflow |
| Framework changes | Pinned image/commit | Never build from floating `main` |
| Visual morph misleads | Actual/magnified toggle | Always label scale |
| Dataset or derivative-display rights are unclear | Audit in Gate A before any public render, STL or demo | Use only permitted assets; downloader scripts and third-party notices; replace the hero geometry if required |
| Independent CFD disagrees in direction | Six-case trusted-solver set | Show the disagreement, remove the improvement claim and frame the finding as a trust boundary |
| Public endpoint is exhausted or cold | Load/rate test | Rate-limit, scale to zero where practical and provide a clearly labelled replay case |

## 15. Ownership and resource assumptions

**Portfolio headcount assumption:** TBD at approval. This schedule assumes at least three active builders allocated to Zephyr plus access to a shared editor. If the total team is fewer than six people with real slack across both submissions, only one project should enter full production.

Minimum ownership areas:

- physics/model/validation;
- application/3D experience;
- agent/backend/infrastructure;
- evidence/presentation.

One person may own two areas. Every critical proof task must have a named owner.

Initial resource hypothesis to validate:

- one Nebius L40S or H100-class GPU deployment for DoMINO;
- CPU Jobs for OpenFOAM;
- selective dataset storage measured in tens of GB, never the full dataset;
- scale-to-zero or otherwise bounded endpoint availability through the verified judging window;
- six primary trusted solves plus limited reruns only if early timing makes them practical.

These are planning estimates, not approved costs.

## 16. Portfolio firewall

Zephyr and Still My Voice must remain substantially different submissions.

May be shared:

- deployment scripts;
- generic observability;
- repository quality checklists;
- video review method.

Must remain separate:

- repositories and public demos;
- product identity and interface;
- user story and evidence;
- model pipeline;
- film and submission copy.

Zephyr should feel like precise, ambitious engineering—not a reskinned general agent.

## 17. Definition of done

Zephyr is submission-ready only when:

- a stranger can use the public demo;
- Nemotron makes visible runtime calls and outputs the executable constraint graph;
- the open DoMINO checkpoint runs on Nebius AI Cloud;
- every accepted deformation is bounded and mesh-valid;
- the system visibly stops outside its trust region;
- equal-budget random changes appear as a negative control;
- at least one independent CFD result supports the final directional claim;
- every film number is reproducible from versioned evidence;
- the public repository installs from its README and carries required licenses/notices;
- the film communicates the idea within ten seconds and remains under three minutes.

## 18. Open questions before approval

1. Which Nemotron IDs and structured/tool capabilities are live in the actual Token Factory account?
2. Which exact cases trained and tested the published `.mdlus` checkpoint?
3. What are real runtime and memory on available Nebius GPUs?
4. Does the checkpoint behave sensibly when velocity varies, or should the demo remain at one condition?
5. What trust radius works for each handle?
6. What OpenFOAM mesh and runtime are sufficient for directional validation?
7. Can an automotive/CFD user participate in product review or the film?
8. Will the organizer confirm that a load-bearing Nemotron planner plus DoMINO on AI Cloud is accepted for Best Apps and Agents?

## 19. Sources

- [Hackathon overview](https://nebiusglobalaihackathon.devpost.com/)
- [Official rules](https://nebiusglobalaihackathon.devpost.com/rules)
- [Token Factory documentation index](https://docs.tokenfactory.nebius.com/llms.txt)
- [Token Factory model-list API](https://docs.tokenfactory.nebius.com/api-reference/models/list-models)
- [Token Factory function calling](https://docs.tokenfactory.nebius.com/ai-models-inference/function-calling)
- [Token Factory structured output](https://docs.tokenfactory.nebius.com/ai-models-inference/json)
- [PhysicsNeMo-CFD](https://github.com/NVIDIA/physicsnemo-cfd)
- [DoMINO design-sensitivity workflow](https://github.com/NVIDIA/physicsnemo-cfd/blob/main/workflows/domino_design_sensitivities/README.md)
- [DoMINO DrivAerML model card](https://huggingface.co/nvidia/domino_drivaerml/blob/main/README.md)
- [Published checkpoint files](https://huggingface.co/nvidia/domino_drivaerml/tree/main/domino_drivaerml_surface_checkpoint)
- [DrivAerML dataset](https://huggingface.co/datasets/neashton/drivaerml)
- [PhysicsNeMo-CFD benchmarking workflow](https://github.com/NVIDIA/physicsnemo-cfd/blob/main/workflows/benchmarking/README.md)
- [Automotive NIM usability guide](https://docs.nvidia.com/nim/physicsnemo/domino-automotive-aero/latest/usability-guide.html)
- [OpenFOAM DrivAer tutorial](https://github.com/OpenFOAM/OpenFOAM-9/tree/master/tutorials/incompressible/simpleFoam/drivaerFastback)
- [OpenFOAM `snappyHexMesh`](https://www.openfoam.com/documentation/user-guide/4-mesh-generation-and-conversion/4.4-mesh-generation-with-the-snappyhexmesh-utility)
- [PyGeM](https://github.com/mathLab/PyGeM)
- [Nebius Serverless AI](https://docs.nebius.com/serverless/overview)
- [Nebius endpoint management](https://docs.nebius.com/serverless/endpoints/manage)
- [Nebius Jobs quickstart](https://docs.nebius.com/serverless/quickstart/jobs)
