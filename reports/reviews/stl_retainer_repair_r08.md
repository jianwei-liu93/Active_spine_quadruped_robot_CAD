# r08 retainer STL repair — isolated supplemental evidence

The r07 failure is reproduced from `cad/flexor_r07_robot.FCStd` in an isolated FreeCADCmd process. No MCP session, canonical CAD, or shared schema was changed by this worker. The saved native file SHA-256 remained unchanged.

## Diagnosis and design decision

The left native retainer is a valid, closed, single BRep solid (8 faces; raw volume 102.38300912272375 mm³), but its hole radius 0.8 mm and centre X=-23.2 place the hole exactly tangent to the outer strip X=-24. The generated mesh has 436 facets, 216 points, and two edges with incidence four at X=-24, Y=±29, Z=41.2…42. This is nonmanifold geometry before serialization, rather than an STL reader failure. `removeSplitter()` was tried once and produces the identical failure; no hole filling or proxy geometry was used.

The lead approved a minimum 0.8 mm outer wall: tray X=[-24.8,4.8], left strip X=[-24.8,-22], right strip X=[2,4.8]. Hole centres/radii, PCB datum, tie attachments, feature bodies, part numbers and physical links remain unchanged. `controller_carrier_r07.repair_existing(builder)` rebuilds only the three base-pad sketches using fully constrained Block line geometry and marks the three bodies r08. Repeated application is idempotent. `apply(builder, revision='r08')` uses the same repair; the default remains the historical r07 build.

Binary STL also exposes an independent FreeCAD `Mesh.Volume` numerical issue: identical triangle coordinates read back with raw API volume 102.38150787353516 versus generated 102.38314056396484 mm³. Stable signed tetrahedral summation around one mesh vertex gives identical geometric volume 102.39073354515838 mm³ for those two triangle sets. Raw API volume therefore remains diagnostic only. The exporter uses translated triangle integration with `math.fsum`, preserves the existing relative volume tolerance 1e-6, and uses ASCII STL. It requires each generated and readback mesh to have no boundary edges, no nonmanifold edges, consistent edge orientation, nondegenerate triangles and `Mesh.isSolid()`. Each serialized triangle's vertex positions are checked with the existing 1e-5 mm tolerance, permitting cyclic vertex ordering while retaining orientation. Facet count and bounds gates remain strict. STEP checks and adaptive helpers are unchanged.

## Checks actually executed

`reports/tmp/stl_retainer_repair_r08/verify.py` opens the saved r07 file, applies the approved native repair twice without saving, exports and independently reads all 25 used PA12 definitions, and runs existing adaptive STEP round trips on the three changed bodies. FreeCADCmd finished successfully. Results: `reports/tmp/stl_retainer_repair_r08/verify.json` (ignored supplemental evidence).

- All 25 PA12 STL readbacks passed closed oriented manifold, triangle correspondence, facet count, geometric volume and bounds checks.
- Maximum serialized STL geometric volume relative error: 7.243921455717925e-8.
- Maximum serialized STL bounding-box absolute error: 4.76837158203125e-7 mm.
- Maximum serialized triangle vertex displacement: 1.0662402999400094e-6 mm.
- Repaired tray STL: 2420 facets; each retainer STL: 428 facets.
- Tray STEP adaptive volume relative error: 3.179068497406712e-12; maximum bounds error: 5.684341886080802e-14 mm.
- Left/right retainer STEP volume errors: 2.5547955670160177e-15 / 2.3582728310917096e-15; bounds errors zero.
- Native file SHA-256 unchanged; all three repaired sketches fully constrained and all three bodies one valid solid after both repair calls.
- Python compilation and `git diff --check` passed for both changed source modules.

## Lead integration

Call `controller_carrier_r07.repair_existing(builder)` in the lead-owned application before final r08 verification/save. It returns changed body/sketch names. Export with `export_robot_r07.run(doc, ROOT, revision='r08', expected_instances=485)` when 485 is the declared final physical instance count. Defaults remain `revision='r07', expected_instances=486`. Revision selects assembly/part/STL output directories, filenames, manifest, diagnostics, BOM and mass reports. Adaptive backend filenames remain r07 because that unchanged implementation is shared.

This worker did not execute a final r08 assembly export, whole-package manifest, collision/motion checks, live-MCP verification, or fabrication release. The widened tray/strips require the lead's assembly clearance checks. Supplemental STL evidence covers the repaired r07 assembly's 25 PA12 definitions, and does not cover a subsequently introduced r08 cage definition.
