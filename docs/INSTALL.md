# Clean installation

This guide reproduces the supported local Zephyr development environment from a clean checkout. The validated path is native Windows on an NVIDIA CUDA GPU. Linux and macOS are not currently qualified for the DoMINO runtime.

## 1. Prerequisites

Install these before cloning:

- 64-bit Windows and PowerShell 7 or Windows PowerShell 5.1.
- An NVIDIA GPU with a current driver and enough VRAM for the selected DoMINO workflow. The recorded gate used an RTX 4070 Ti SUPER with 16 GB VRAM.
- Git.
- [`uv`](https://docs.astral.sh/uv/) available on `PATH`.
- Node.js 22.14 or newer with npm.
- Internet access and several gigabytes of free disk space for Python, CUDA packages, checkpoints, upstream code, and optional vehicle sources.

Zephyr does not require a cloud GPU. Nebius credentials are needed only for the optional language-model copilot.

## 2. Clone and bootstrap the local DoMINO runtime

From the directory where the project should live:

```powershell
git clone https://github.com/ASH1998/zephyr.git
cd zephyr
.\scripts\setup-domino-windows.ps1
```

The repository is private, so GitHub must already recognize your HTTPS or SSH credentials.

The setup script:

- creates a workspace Python 3.12 environment at `..\.venv`;
- installs CUDA-enabled PyTorch and Zephyr;
- checks out the pinned PhysicsNeMo-CFD commit under `.local`;
- downloads and SHA-256 verifies the required surface-model bundle; and
- verifies CUDA and the DoMINO import.

It stops if the local PhysicsNeMo-CFD checkout contains changes. Preserve or remove those changes deliberately before rerunning setup.

Install the frontend from the lockfile:

```powershell
npm --prefix frontend ci
```

## 3. Configure the optional Nemotron copilot

Copy the template:

```powershell
Copy-Item .env.example .env
```

For local-only use, leave the Nebius values empty and start the backend without `--enable-llm`.

For the copilot, set these values in `.env`:

```dotenv
NEBIUS_API_KEY=<private-token>
NEBIUS_AI_PROJECT_ID=<project-id>
ZEPHYR_ACTIVE_MODEL=nvidia/Nemotron-3-Ultra-550b-a55b
ZEPHYR_NEMOTRON_MODEL=nvidia/Nemotron-3-Ultra-550b-a55b
```

Model availability is account-specific. Confirm the exact NVIDIA Nemotron ID with the authenticated Token Factory catalog instead of substituting a similar name. Never commit `.env` or paste a token into evidence files.

Run the sanitized capability probe:

```powershell
& ..\.venv\Scripts\zephyr-day0.exe --live-models --structured-model $env:ZEPHYR_NEMOTRON_MODEL --strict --output build\evidence\day0.json
```

The report records presence and results, not secret values.

## 4. Prepare the complete vehicle and airflow catalog

The repository includes the frontend assets needed to inspect the current catalog. To rebuild the licensed source conversions and local inference surfaces from their pinned sources, first add the conversion dependencies:

```powershell
& uv pip install --python ..\.venv\Scripts\python.exe trimesh Pillow scipy pyvista DracoPy==2.1.0
```

Then run:

```powershell
& ..\.venv\Scripts\python.exe scripts\download-vehicle-sources.py
& ..\.venv\Scripts\python.exe scripts\import-vehicles.py
& ..\.venv\Scripts\python.exe scripts\import-aircraft.py
& ..\.venv\Scripts\python.exe scripts\prepare-vehicle-surfaces.py hatchback wagon suv coupe sports van x57 global-hawk
```

The separate volume checkpoint is required for fresh NVIDIA-predicted airflow:

```powershell
& ..\.venv\Scripts\python.exe scripts\download-volume.py
& ..\.venv\Scripts\python.exe scripts\prepare-airflow.py
```

`prepare-airflow.py` runs sequential GPU inference for the catalog and can take time. Saved airflow JSON is sufficient for viewing existing previews; a fresh comparison requires the local checkpoint bundle.

## 5. Start Zephyr

Terminal 1 — backend with Nemotron enabled:

```powershell
& ..\.venv\Scripts\python.exe -m zephyr.local.server --enable-llm --port 8766
```

For a local-only session, omit `--enable-llm`. The explicit preset `Reduce drag. Keep the cabin unchanged.` remains available without a model call.

Terminal 2 — frontend:

```powershell
npm --prefix frontend run dev
```

Open <http://127.0.0.1:5173>. The Vite server binds to `127.0.0.1:5173` and proxies `/api` to the backend at `127.0.0.1:8766`.

Do not replace port 8766 with 8765 on the recorded development machine; 8765 belongs to an unrelated local service.

## 6. Verify the checkout

Run the deterministic test suites and production build:

```powershell
& ..\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm --prefix frontend test
npm --prefix frontend run build
```

In the browser:

1. Select a car and confirm that the saved airflow preview loads.
2. Run **baseline analysis only** before a shape study if you want a lower-risk GPU smoke test.
3. Select NASA X-57 or NASA Global Hawk and confirm the interface labels the result experimental and offers baseline analysis only.
4. If Nemotron is enabled, interpret a supported brief and confirm the response names the exact configured model.

Do not report an accepted surrogate result as validated drag reduction. Preserve the run evidence and send accepted candidates to independent CFD or physical testing.

## Troubleshooting

### The frontend cannot start

- Confirm Node.js is at least 22.14 and rerun `npm --prefix frontend ci`.
- Check that port 5173 is free; Vite uses a strict port and will not silently move.

### The UI reports that brief interpretation is unavailable

Start the backend with `--enable-llm`, confirm `.env` contains valid Nebius values, or use the exact local preset without the copilot.

### CUDA is unavailable

Confirm the NVIDIA driver can see the GPU, then rerun `.\scripts\setup-domino-windows.ps1`. The setup script deliberately fails if `torch.cuda.is_available()` is false.

### A second run returns HTTP 409

Only one GPU job may hold the local lock. Wait for, cancel, or diagnose the active job before starting another.

### Setup refuses to update PhysicsNeMo-CFD

The pinned checkout under `.local\physicsnemo-cfd` has modified or untracked files. Preserve any intentional work elsewhere, restore a clean checkout, and rerun setup.

### A run succeeds but remains refused

That is expected when repeatability, probe linearity, geometry, intersection, disagreement, or scope checks fail. Zephyr records the refusal instead of weakening the gate.
