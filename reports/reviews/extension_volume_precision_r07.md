# r07 extension-spring volume precision escalation

## Scope

Read-only numerical diagnosis of the hind-left/right extension native/STEP pairs. The strict relative-volume tolerance remains **1e−6**. No canonical assembly, live MCP session, shared source file, spring geometry or final export was modified by this worker.

Input BReps supplied by the export-verification owner are recorded by SHA-256 in `reports/tmp/spring_volume_precision/remedy_evidence.json`. The owner confirmed that the newly regenerated canonical assembly retains the same extension-spring issue, so these isolated pairs remain relevant. Final acceptance still belongs to the lead's actual-current-native/export verification.

## Outcome

**Both isolated hind extension native/STEP pairs PASS** the unchanged strict gate. Relative volume difference is 1.96905e−8; the conservative estimated-margin upper relative difference is **3.00531e−7**, including absolute disagreement with every coarse Gauss/GK result at eps1e−8 and eps1e−10. Four analytic controls (box, cylinder, torus, sphere) all pass, with maximum relative error 1.70e−15. Final diagnostic runtime was 61.57 seconds, including the deliberately expensive eps1e−12 convergence runs.

The refined 16-subdivision/order-61 primary reports estimated relative quadrature error about 6e−11. The retained coarse algorithm disagreement makes the final margin substantially larger than this estimate; it is not discarded to obtain PASS.

## Cause and executable remedy

The installed OCCT 7.8 Gauss–Kronrod volume calculation reports an estimated relative integration error around 5.6e−7 **per shape**, despite stable scalars. Summing both independent numerical margins exceeds the pair's 1e−6 budget. Simply requesting tighter tolerance does not cure that estimate.

`reports/tmp/spring_volume_precision/domain_volume.cpp` integrates the **original, unchanged oriented face-boundary integrand** through public `BRepGProp_Face`, `BRepGProp_Domain`, `BRepGProp_TFunction` and `math_KronrodSingleIntegration` APIs. It divides each existing boundary-curve knot interval into equal subintervals and uses a higher initial Kronrod order. This changes only numerical quadrature domains; it does not split, heal, approximate or replace the BRep.

The volume is the sum of oriented face contributions using one common reference origin (the mean of vertex occurrences). For every subinterval, the estimated absolute error retains both the outer quadrature estimate and the inner integral estimate multiplied by the subinterval width. Contributions and estimated errors are accumulated with long-double sums. This follows the same error-accounting structure as the [OCCT 7.8 implementation](https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_8_0/src/BRepGProp/BRepGProp_VinertGK.cxx), with finer quadrature intervals and higher order.

The helper rejects invalid inputs, non-single-solid inputs, open shells, unsupported faces without a boundary, invalid arguments and quadrature failures. `BRepGProp_Face.Load` retains each face's orientation. The reference origin is shared across all faces; individual face origins must not be substituted without the corresponding flux correction.

Exported C API:

```cpp
int domain_volume(const char* brep_path, int subdivisions, int order,
                  double eps, double* volume, double* relative_error,
                  int* integrated_subinterval_count);
```

Use a deterministic refinement trigger based on a shape's reported uncertainty, independent of whether a native/STEP pair would pass. The export owner proposes `selected_GK_error > 2.5e−7`, then 8 subdivisions/order 31 followed by 16 subdivisions/order 61. Require refinement convergence ≤1e−8. The final margin must retain:

- the refined quadrature error;
- coarse precision variation;
- variation between refined subdivision/order/precision results;
- the coarse-GK to refined-GK difference;
- the **absolute** coarse-Gauss to refined-GK disagreement.

The coarse plateau estimate is superseded by the independently checked finer quadrature estimate, but its scalar disagreement is retained. The original strict pair comparison and tolerance remain unchanged. These are conservative numerical estimates and convergence evidence, not certified interval-arithmetic bounds.

## Verification and rejected alternatives

`domain_convergence.json` records all four inputs at subdivisions 4, 8 and 16, orders 31 and 61. `verify_remedy.py` performs the final conservative pair comparison with all coarse algorithm/precision disagreements retained, and checks box, cylinder, torus and sphere volumes against analytic formulae. Exact results and source/binary hashes are in `remedy_evidence.json`. The final C++ source SHA-256 is `dde52212e2afc6ebf2aa3c72bf324be3fdf82c66a273fbabeae7ecab4902a130`.

`ShapeUpgrade_ShapeDivideArea` lowered the estimate but produced invalid diagnostic topology. That route is **rejected** and is not part of the remedy. No acceptance relies on its volumes.

## Reproduce

Compile the diagnostic from the host (the snap runtime has no compiler):

```sh
g++ -std=c++17 -O2 -shared -fPIC \
  -I/snap/freecad/2830/usr/include/opencascade \
  reports/tmp/spring_volume_precision/domain_volume.cpp \
  -L/snap/freecad/2830/usr/lib -lTKBRep -lTKTopAlgo -lTKMath -lTKernel \
  -o reports/tmp/spring_volume_precision/domain_volume.so
/snap/bin/freecad.cmd reports/tmp/spring_volume_precision/verify_remedy.py
```

The diagnostic files and compiled helper remain under ignored `reports/tmp/spring_volume_precision/`. Integration into source-backed production verification is handed to the export-verification owner; this worker does not edit the shared helper.
