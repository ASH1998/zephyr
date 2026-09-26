# Synthetic sedan dent demonstration

This is a prescribed geometric dent on the original DrivAer sedan hood. It is
separate from the selected 3.33% research candidate. It is not a crash simulation,
damage detector, photo inspection service, structural analysis, repair estimate,
or a safe-to-drive assessment. A lower aerodynamic force does not make damage safe.

The fixed preset is chosen before observing model forces: centre (0, 0.22, 0.74)
metres in upstream coordinates, ellipsoid radii (0.34, 0.30, 0.25) metres, inward
Z displacement with a 12 mm ceiling and a compact cubic profile. Discrete surface
vertices produce a maximum actual movement of about 11.3 mm. All protected
coordinates, topology and the cabin remain fixed. The usual research geometry
checks, including exact intersections, apply with a tighter 12 mm displacement
ceiling. A failed geometry gate stops the scenario before inference.

The original and dented shapes receive separate fresh NVIDIA DoMINO surface,
sensitivity and volume predictions at 38.889 m/s and density 1.205 kg/m³. The
scenario receipt is written before force evaluation; original numerical study
records are not modified. The result always retains unverified training-domain,
structural and roadworthiness status, regardless of the drag direction.

Generate with the existing local CUDA environment:

```powershell
& ..\.venv\Scripts\python.exe scripts/publish-sedan-replay.py --directory .local/research/sedan-2026-09-25-v2 --synthetic-dent --live
```

Open the returned replay URL. Use **Compare Original / Changed**, **Change**,
**Pressure**, **Sensitivity**, and **NVIDIA airflow**. Both views use their own
fields and shared scales. Movement opens at true scale; any optional enlargement
is display only. The original UI, aircraft and interactive 4 mm design controls
are preserved. The dent is available through the existing **Previous runs** list.

The deployment packager accepts `--additional-run-id <dent-run-id>` alongside
the selected sedan's `--run-id`, so both comparisons appear in the same recorded
demo's history. The package needs no GPU or credentials; fresh computation and
LLM Q&A remain available in the local workstation application.
