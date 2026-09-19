# Car Concept

Copyright 2024 Darmstadt Graphics Group GmbH. Model and textures by Eric Chadwick.

Licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

Source: https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CarConcept

Downloaded file: https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb

Local file: `car-concept.glb`

SHA-256: `c272098089d78c5cd9fd9f24ff50ee8acf8d932c55f2d55fc10adb6c8998966b`

License was verified against the source README Legal section and the GLB's embedded `asset.copyright` metadata on 2026-09-18. Source model originated with Unity Fan's CC0 concept car; this optimized asset and textures carry the attribution license above.

The original file also contains Khronos and 3D Commerce marks (Khronos Group, 2015 and 2017). Trademark rights are not conveyed by the content license. No endorsement is implied. The viewer omits the license plate and emblem meshes and replaces exterior paint materials.

Zephyr modifications at runtime: world-transform baking; coordinate rotation to +X streamwise; uniform 4.65 m display length; silver paint and dark glass; omission of wipers, plate and emblem meshes; analytic illustrative fields on exterior surface parts; bounded demo rear-surface deformation. The original GLB bytes remain unchanged.

This concept vehicle is a visualization asset, not a validated DoMINO input or a claim of membership in the checkpoint's training distribution. It is not a watertight solver mesh. The UI and exported provenance identify all physics values as illustrative.
`khronos-car-concept-2024-zephyr-cabin-v4` applies a smooth baseline-only cabin lift of up to 0.28 m above the 0.98 m beltline, reaching the actual normalized source roof at approximately 1.26 m. Its roof now reaches approximately 1.54 m. Authored normals are transformed through the deformation Jacobian. This is an aesthetic display adaptation, not an optimization result; the resulting baseline cabin is fixed during all demo iterations. This replaces the ineffective v3 height window, which extended above the original roof.

No additional assets were downloaded for this revision. Sedan and SUV catalog entries are unavailable placeholders until a licensed asset, per-asset preparation, surface mapping, and visual/contract QA are supplied.


# DrivAerML geometry preview

`drivaer-preview.json` is a geometry-only reduction of the installed official
DrivAerML sample 1 used by the local NVIDIA DoMINO workflow. It was derived from
run `local-5dc4b61d4d8848bca486eb963108f2c1` baseline display geometry using VTK
DecimatePro (reduction 0.86, topology preserved, splitting and boundary deletion
disabled). Coordinates are rounded to 0.00001 m in the existing viewer frame.
15,373 vertices and 30,918 triangles; 899,793 bytes. Source mesh hash is embedded.
SHA-256: `40f3f745baf3c6920aa759ce805e5b353e7c153a5c288a1c222285868389342c`.

Source sample: the installed `drivaer_1.stl` in NVIDIA PhysicsNeMo-CFD's pinned
`workflows/domino_design_sensitivities/geometries` directory. This preview
contains no pressure, velocity, force or sensitivity results. Its purpose is
an immediate view of the input shape before local GPU inference. Animated
streamlines are authored illustrations and are identical for both comparisons.
