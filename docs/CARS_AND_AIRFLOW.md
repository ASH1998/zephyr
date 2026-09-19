# Detailed cars, aircraft, and NVIDIA airflow

The live selector has seven cars and two aircraft. The original DrivAer sedan is unchanged. The former rounded blockouts are replaced with licensed, detailed car bodies, lights, glass, trim, and wheels: Impreza hatchback, Hummer SUV, an adapted touring wagon, M3 coupe, Veneno sports car, and Sprinter van. The wagon is an extended derivative of the hatchback; it is not presented as a production model.

NASA's X-57 and Global Hawk are separate aircraft choices. Both are uniformly scaled to 3.3 m wingspan to fit the existing inference domain. Their output is prominently labeled **experimental aircraft flow**. The model was trained on cars. Aircraft cannot use the car rear-taper deformation handle; the API rejects those iteration requests, including compiled requests. A baseline-only experimental analysis remains available and runs directly through the validated measurement path, without a language-model design interpretation.

## Geometry and rendering

- Detailed GLBs preserve material boundaries, UVs, texture maps, normals, and wheels.
- `scripts/prepare-vehicle-surfaces.py` voxelizes each visual mesh at 35 mm, closes small gaps, smooths, and extracts a closed surface for inference. Simplification is retained only if it stays closed. This is a geometry approximation, not independent CFD.
- The inference surface has a SHA-256 binding to its saved airflow. The detailed visual GLB shares the same center/ground transform; its offset is recorded in the preview JSON.
- Live shape changes are projected from the evaluated surface to nearby visual vertices for display. Detailed materials are shown in Airflow; Pressure, Sensitivity, Change, and Mesh expose the evaluated simplified surface.
- The 120× enlargement applies only to Change. Airflow uses actual evaluated coordinates (scaled coordinates for aircraft).
- Switching models clears earlier force results. Stale results cannot be substituted for a different mesh.

## Airflow

NVIDIA's separate volume checkpoint predicts velocity at 96 × 40 × 36 = 138,240 points. Streamlines are integrated through that field. Moving streaks follow recorded travel time at 0.055× playback speed; they trace a steady prediction, not a time-resolved turbulence simulation. At most 48 paths near the body are drawn to keep the model readable. The speed scale is 0–60+ m/s.

The surface model still supplies drag, pressure, and sensitivity. A bounded car test evaluates original and candidate surfaces, then predicts separate volume fields. Source bundle hashes are in `config/domino-volume-artifacts.json`. Raw fields remain in `.local/airflow-cache` and `.local/runs`.

## Sources and reproduction

[Full model credits](../frontend/public/models/VEHICLE_CREDITS.md) are also linked inside the page's Evidence & provenance dialog. `config/vehicle-source-artifacts.json` pins 104 source files by URL and SHA-256. Converted S8 assets and the wagon derivative retain CC BY-SA 3.0. Other assets retain their upstream terms.

Use the existing local NVIDIA environment, plus trimesh, Pillow, scipy, pyvista, and DracoPy 2.1.0:

```powershell
& ..\.venv\Scripts\python.exe scripts/download-vehicle-sources.py
& ..\.venv\Scripts\python.exe scripts/import-vehicles.py
& ..\.venv\Scripts\python.exe scripts/import-aircraft.py
& ..\.venv\Scripts\python.exe scripts/prepare-vehicle-surfaces.py hatchback wagon suv coupe sports van x57 global-hawk
& ..\.venv\Scripts\python.exe scripts/download-volume.py
& ..\.venv\Scripts\python.exe scripts/prepare-airflow.py
& ..\.venv\Scripts\python.exe -m zephyr.local.server --enable-llm
```

The backend now defaults to **127.0.0.1:8766**, and Vite's `/api` proxy points there. Port 8765 was also used by an unrelated local file server, causing API requests to return file-not-found pages. The UI remains at **127.0.0.1:5173**. No cloud GPU is started.

## Verification

- 32 backend tests, 29 frontend tests, and the production build pass. The existing large bundle warning remains.
- All nine saved geometry/flow identities match. The eight added inference surfaces are closed, with unique hashes. Aircraft iteration rejection is tested at both request validators.
- All six detailed cars and both aircraft were inspected in the live browser.
- A complete detailed hatchback test finished in about 22 seconds, with predicted drag 474.92 → 473.50 N (−0.299%), 3.60 mm maximum movement, and protected coordinates unchanged. Both shapes received fresh NVIDIA volume predictions. Engineering acceptance remains refused because calibration/intersection checks are incomplete.
- The earlier `seven-cars-volume-smoke.json` records the retired blockouts and must not be cited as evidence for the detailed assets. Current evidence is in `detailed-vehicles-aircraft-smoke.json`.

The Global Hawk also completed a real baseline-only GPU analysis in 14 seconds, with fresh surface and volume output and no candidate geometry. Its values apply only to the scaled experimental model.


## Airflow presentation modes

The live viewer defaults to **Flow illustration**. These authored paths follow
an envelope of the selected original geometry. Blue trails bend around the body;
orange trails explain the wake behind it. They have no physical velocity values,
are not CFD, and do not imply a candidate improved the flow. Numerical run results
remain separate. Aircraft use spanwise roof sections rather than car side paths.

**NVIDIA prediction** retains the mesh-bound, saved or freshly computed volume
paths and travel times. Moving streaks replace square particles. Linear segments
avoid spline overshoot; ring samples retain their original timing. Paths remote
from the body are omitted for readability, with at most 48 paths displayed. The
underlying exported field and metrics are unchanged. Blue means slower and orange
means faster, on a 0–60+ m/s color scale. Playback is slowed by the field metadata.

Both views obey Pause/Resume and reduced-motion preferences.


The aircraft illustration now includes two counter-rotating orange wake tubes
anchored near each wing's outboard trailing edge, with a gentle downward drift.
Three animated filaments per tube make rotation visible. These illustrate the
[wingtip-vortex mechanism described by the FAA](https://www.faa.gov/air_traffic/publications/atpubs/aim_html/chap7_section_4.html);
their radius, length, and strength are authored for presentation, not inferred.
Car illustrations have three lateral bands on each side and span over twice the
body width. These additions do not alter NVIDIA field data or numerical results.
