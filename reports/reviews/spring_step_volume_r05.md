# r05 compression spring STEP volume review

Executed 2026-10-12 in isolated FreeCAD 27.1.0 CLI (OCCT-backed), without touching the live session or saving native geometry. Reproducer: `src/spring_step_check_r05.py`; optional environment `SPRING_SURFACES=1` selects spline comparison, `SPRING_READ_RESULT=1` prints the last full diagnostic JSON from the application's private temporary directory.

## Conclusion

Evidence strongly supports a volume-integration sensitivity associated with STEP trim/seam representation, rather than loss of a significant section of wire. This is an inference, not a certified global geometric equivalence proof. The existing volume gate remains failed; no tolerance or source geometry was changed.

The checked definition is `LEG_r02_foreL_COMPRESSION_WIRE_L24p73863375` from `cad/flexor_r05_robot.FCStd`, compared to its existing STEP under `reports/tmp/step_part_diagnostics/`. This run does not independently check the right-hand duplicate or its placed full-assembly STEP instance.

## Executed evidence

Native BRep volume: **29.89795182629611 mm³**. Reimported STEP: **29.840730826609672 mm³**. Both valid, three faces, with one BSplineSurface and two Toroid surfaces. Native has nine edges/four vertices; STEP has ten edges/five vertices. STEP includes an additional edge of length **1.4232889e-6 mm** and subdivides a torus circular boundary. Native area is 235.68393306172 mm², STEP area 235.70384489660 mm²; these kernel integrals also differ.

The underlying helical B-spline has the same degrees (6,9), a 6×137 pole array, and identical U/V knot multiplicities. Maximum pole separation is **7.9273e-13 mm**; maximum U/V knot differences are **4.1389e-13 / 4.6896e-13**, and maximum rational weight difference is **4.9960e-13**. Therefore STEP preserved this supporting surface to file numerical precision. Trimmed domains require separate checks.

Bidirectional checks use tessellation vertices at 0.01 mm deflection, selecting 1501 points per direction and measuring exact point-to-opposite-BRep distance:

| Direction | Maximum distance, mm | RMS distance, mm |
|---|---:|---:|
| Native → STEP | 4.2783273e-13 | 8.3386900e-14 |
| STEP → native | 2.2888685e-6 | 7.0772301e-8 |

These are sampled distances, not Hausdorff bounds. The tiny STEP edge and micrometre-fraction sampled discrepancy are consistent with a seam/trim change. They do not account geometrically for a 0.05722 mm³ volume deficit at the sampled locations.

Independent signed triangle volumes were summed with `math.fsum`, from MeshPart meshes at angular deflection 0.08 rad. All six meshes report solid:

| Linear deflection, mm | Native triangles | STEP triangles | Native signed volume, mm³ | STEP signed volume, mm³ |
|---|---:|---:|---:|---:|
| .02 | 383162 | 388144 | 29.74977374044 | 29.74960173926 |
| .005 | 384540 | 391294 | 29.75222138419 | 29.75208582434 |
| .001 | 489050 | 501064 | 29.73632409189 | 29.73663381244 |

The paired meshes agree far more closely than the BRep volume integrals, but absolute mesh volumes do **not** converge. This sequence cannot establish an accurate independent volume or replace the acceptance gate. Mesh.Volume uses a different numerical summation and was also recorded in temporary JSON.

## Recommended bounded acceptance method

Keep volume differences reported. Before approving an exception, define a separate component-level geometry criterion with an explicit engineering distance tolerance, supporting-surface identity checks, trimmed-boundary checks, topology/validity and solid-count checks, and bidirectional surface coverage. Apply it to every discrepant definition and its assembly placements; an aggregate assembly volume alone can conceal local losses.

For a rigorously bounded surface-distance criterion, use a certified surface covering radius `h` together with exact point-to-opposite-shape samples: the distance function is 1-Lipschitz, hence `max(sample distance) + h` bounds the directed distance if every source-surface point lies within `h` of a sample. A mesher's requested deflection alone is not that covering-radius certificate. Alternatively, establish equivalent supporting surfaces and bound all trimming-curve/domain deviations using their spline control data. No such certificate has been established in this review. A finite sampling criterion may be adopted explicitly as sampled engineering evidence, but must not be described as a rigorous global bound.

No source fix is justified by these results alone. Compression is built by `spring_shape` in `src/build_leg_r02.py`; `spring_wire_r03.py` supplies extension springs only. If export-stable topology is required, investigate the helical wire/end-torus fusion and trim/seam cleanup in an isolated prototype, retaining the current physical dimensions and proving valid geometry and round-trip integrity before integration. Merely loosening the 1e-6 aggregate-volume tolerance would not resolve the stated integrity question.
