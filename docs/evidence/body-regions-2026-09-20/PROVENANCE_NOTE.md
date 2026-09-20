# Runtime source-capture limitation

The original six-case matrix started before the final experimental-envelope
compatibility refinement. Runs retain their own original evidence unchanged.

The final matrix run, `local-914d0053077f4030bbfb5eac70a3f138`, loaded the earlier
worker before a local source edit but captured the worker file hash after its
baseline calculation. Its worker-file hash therefore cannot identify the code
loaded by that process. Do not use this run as exact final-source reproducibility
evidence. Its stored meshes and forces can still be independently audited.

The final worker freezes source hashes before model loading. The separate
`final-runtime.json` focused production check exercises that final implementation.
The input-contract report separately checks the final compatibility helper on
all nine installed surfaces and 70 signed car candidates. Static checks do not
establish model accuracy or full GPU compatibility for every imported model.

Final check: `local-45e62b3e3d754edd856b2bff898d6f6b` completed in 41.3 seconds.
Its recorded worker hash matched the final source and its candidate force matched
the earlier hood run exactly. `verified-final-runtime.json` records the independent
geometry, force-integration and decision audit.
