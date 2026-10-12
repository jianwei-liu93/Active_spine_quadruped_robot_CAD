# r10 STEP volume validation dependencies

Validation uses src/adaptive_volume_r07.py and src/occt_adaptive_volume_r07.cpp. Build requires a C++17 compiler and OCCT development headers/libraries matching the FreeCAD runtime exactly.

Prepare on the host (the snap runtime may lack a compiler):

```sh
python src/adaptive_volume_r07.py --prepare . --occt-root /snap/freecad/current/usr
```

The helper is reproducibly compiled under reports/tmp/adaptive_volume_r07; source/header/binary hashes and kernel version are verified at runtime. Missing dependencies fail closed. No compiled helper is included as a source replacement.

Every physical solid must independently pass one-to-one placed bounds (1e-5 mm) and adaptive volume with qualified GK/domain refinement including estimated numerical margin (1e-6 relative). Both GK and Gauss run at eps1e-8 and1e-10; GK refines to1e-12 when needed for convergence. Coarse GK error above2.5e-7 triggers quadrature on unchanged original boundary domains at8/order31 and16/order61, requiring1e-8 convergence and retaining all coarse algorithm deviations in its numerical margin. Raw Shape.Volume is diagnostic only. Kernel error estimates are numerical evidence, not certified mathematical bounds.

This dependency note does not certify export success; inspect reports/package_manifest_r10.json and the current export diagnostics. Details: reports/reviews/r07_assembly_volume_diagnostic.md.
