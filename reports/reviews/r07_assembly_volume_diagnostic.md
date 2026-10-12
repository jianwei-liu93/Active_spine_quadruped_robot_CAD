# r07 assembly volume diagnostic

Isolated FreeCAD CLI investigation and approved measurement-source implementation, 2026-10-12. The initial diagnostic used canonical SHA`8d0d363add856115761ac767c5b3948d62360c36a5b4d80d76a8de87b9162ca5`; final verification uses the lead's frozen SHA`cea39190bd1265a7a9be2eddcd061a4abc85e19076e15e1514aa318cdffbb227`. This worker edits only the approved C++/Python measurement helpers and exporter measurement/per-instance validation portions. No canonical-document or live MCP writes were performed; temporary exports remain under `reports/tmp/r07_assembly_volume/`.

**Final isolated assembly result: PASS for all486 unchanged actual native↔STEP solid pairs**, using the frozen canonical SHA`cea39190…`. Maximum local difference including numerical margin3.30225617e-7 remains below1e-6. This result concerns the independent diagnostic STEP; the lead performs the complete package export through MCP.

Current implementation preserves strict volume1e-6, placed bounds1e-5mm,486 instances and complete one-to-one imported-solid consumption. Aggregate agreement alone never authorizes a failed local part. The sections below record the investigation; the final current-source result is at the end.

## Consistent aggregate measurement is necessary but insufficient

| Measurement | Native mm³ | STEP mm³ |
|---|---:|---:|
| Compound `.Volume` |171465.05926078145|171465.1803944208|
| `math.fsum(s.Volume for s in shape.Solids)` |171465.62961962415|171465.56707743846|

Native per-solid sum equals the sum of all physical link `.Volume` values. Comparing imported compound volume to native per-link sum mixes two numerically different evaluations. Consistent per-solid sums differ by3.647508e-7 relative and satisfy1e-6, but this **cannot establish package acceptance**: four placed parts fail individually, including a fore compression spring by0.2078%. Centering each solid at its own CenterOfMass changes none of these discrepancies materially.

`probe.py` uniquely consumes every imported solid while matching native placements by six `optimalBoundingBox(False,False)` extrema. All486 matches satisfy1e-5mm bounds. The four individual strict1e-6 volume failures are:

| Physical link | Native mm³ | STEP mm³ | Relative error | Max bounds error mm |
|---|---:|---:|---:|---:|
|hindR_compression_Spring|30.06844868767653|30.068567921524178|3.965414009e-6|9.86944e-12|
|foreL_compression_Spring|29.897951826296136|29.835818915313858|.002078166135|3.44258e-12|
|HindTendon_R_AnkleEye|58.09785214883652|58.097581429837334|4.659707531e-6|8.97415e-12|
|HindTendon_L_AnkleEye|58.097852332081935|58.09758092567241|4.671539457e-6|8.97415e-12|

The other482 placed solids satisfy the existing relative volume gate. The failed spring sources are `LEG_r02_hindR_COMPRESSION_WIRE_L29p55480766_PoseR07` and `LEG_r02_foreL_COMPRESSION_WIRE_L24p73863375_PoseR07`. The fore source retains the previously observed unnormalized original volume; the canonical/native state therefore does not support a claim that every placed neutral spring source has retained the approved normalization.

## Bounded normalization experiment

`repair_probe.py` copies the four source shapes and applies `fix(1e-7,1e-9,1e-6)`, exports explicit-pcurve STEP, and reloads it. No source is modified.

- hindR spring: source kernel volume changes6.994242006e-6 relative; fixed-source STEP roundtrip2.271380569e-12. Maximum bidirectional sampled geometry difference2.17146e-6mm.
- foreL spring: source kernel volume changes.00202938182 relative; fixed-source STEP roundtrip7.561755185e-12. Both directed samples ≤7.43e-15mm in this run.
- Both ankle eyes: `fix` leaves the source volume/topology unchanged and fails to repair the STEP volume discrepancy (same4.66e-6/4.67e-6 errors). Supporting surfaces remain cylinders/planes, and sampled native/fixed geometry agrees to≤3.65e-15mm.

The spring normalization issue should be addressed in lead-owned pose source generation/cache handling. Reapplying the existing normalization to actual installed private pose sources is an explicit native repair; it must not be hidden in the exporter. The eyes need a different measurement or geometry investigation.

## Installed volume API evidence

Installed `/snap/freecad/current/usr/include/opencascade/BRepGProp.hxx` declares a separate adaptive overload `VolumeProperties(shape, GProps, Eps, OnlyClosed, SkipShared)`, where Eps controls per-face adaptive integration and the return is an estimated aggregate relative error. The installed Part.so imports the non-Eps overload `VolumeProperties(shape,GProps,bool,bool,bool)`; disassembly of `Part::TopoShapePy::getVolume` passes three false booleans. Therefore describing the observed default `.Volume` discrepancy specifically as adaptive integration is not established by this binary; report it as numerical nonadditivity unless a more precise mechanism is shown.

An isolated C++ helper `accurate_volume.cpp` calls the explicit adaptive overload on diagnostic BRep copies. `adaptive_probe.py` compares the four discrepant native/STEP placed solids at Eps1e-8 and1e-10. This experiment changes the measurement algorithm, preserves geometry and the strict1e-6 acceptance tolerance, and records kernel error estimates and precision convergence. Results follow when complete.

## Final measurement choice and safeguards

The first explicit Gauss result alone was insufficient. All486 Gauss-adaptive scalar comparisons passed (max7.436024478e-7), but the foreL spring fails the independent span-aware Gauss-Kronrod evaluation: native29.79001162548132, STEP29.790079964259377, relative2.294016495e-6. Selecting the favorable Gauss result would hide this local failure. The two fore foot pads also produce unexpectedly large Gauss error estimates despite stable volumes; Gauss-Kronrod converges to the same foot volume with estimated error≈1.1e-14.

The implementation therefore consistently selects **span-aware adaptive Gauss-Kronrod** for every solid. It evaluates both algorithms at Eps1e-8 and1e-10, records their absolute values, requires selected GK relative precision convergence≤1e-8 (Gauss precision change is separately recorded and included in the numerical margin), and adds selected GK error estimates, precision changes and disagreement between the algorithms' **native-minus-STEP differences** to an estimated numerical margin. Absolute algorithm bias is disclosed rather than added twice to a paired same-geometry comparison. The strict1e-6 gate applies to the volume difference including this estimated margin, independently for every matched physical solid. These kernel estimates and convergence checks are numerical evidence, **not certified mathematical error bounds**.

The copied explicit fore normalization passes GK: native29.79003298875209 versus exported29.7900329892465, relative1.66e-11; GK error estimates≈5.8e-8 and Eps precision change≈5.2e-9 relative. Native geometry samples for the existing approved normalization remain as recorded above (≤~2.2e-6mm at checked points); no hidden exporter repair is introduced.

## Reproducible implementation/API and dependencies

Owned source files are `src/occt_adaptive_volume_r07.cpp`, `src/adaptive_volume_r07.py` and the volume/per-instance validation portions of `src/export_robot_r07.py`. The C++ backend batch-reads diagnostic BRep copies and measures their closed solids; it never repairs a shape or accesses a document.

Runtime discovery inspects the actual Part installation, `FREECAD_OCCT_ROOT`, the installed snap and standard prefixes. It requires matching OCCT headers/libraries and exact OCCT version. A C++17 compiler is a build dependency. The installed snap CLI does not expose a compiler internally, so use the tested host preparation command from the repository:

```sh
python src/adaptive_volume_r07.py --prepare /home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD --occt-root /snap/freecad/current/usr
```

This compiles under `reports/tmp/adaptive_volume_r07/` and writes a manifest with source/header/binary SHA-256, compiler command/version, installed header/library paths and algorithm settings. The FreeCAD runtime loads the verified cache without requiring an internal compiler. Missing dependencies, version/hash mismatch, compiler failure, invalid/open BRep, failed/nonfinite numerical integration, failed convergence, unmatched solids or any failed local gate stop validation. No binary is committed or substituted for the reproducible source.

Public API:

- `measure_shapes(shapes, root, labels=None)`: batch one-solid measurements, both algorithms/two Eps values, selected volume and numerical diagnostics.
- `measure_shape(shape, root, label='shape')`: consistent sum of the shape's physical solids.
- `compare_measurements(actual_record, expected_record, tolerance=1e-6)`: strict selected-volume comparison including the estimated paired numerical margin.
- `validate_solids(actual_shape, expected_shapes, root, labels=None, volume_rel_tol=1e-6, bbox_abs_tol_mm=1e-5)`: complete one-to-one matching using exact placed extrema and independent local volume gates. Bipartite matching consumes every imported solid exactly once; aggregate cancellation cannot authorize a failed local pair.

The exporter compiles/verifies its backend before export, uses this validation for assembly, every unique part STEP and clean-document copy, and records raw `.Shape.Volume` only as a diagnostic. STEP bounds1e-5mm, volume1e-6, validity and solid-count gates are unchanged. Lead final integration: explicitly normalize/install actual intended native spring sources, save the new canonical file through MCP, reload `adaptive_volume_r07` and `export_robot_r07`, then call `export_robot_r07.run(doc, ROOT)`.

## Actual module tests

`module_test.py` / `.json` runs the source-backed implementation inside isolated snap FreeCAD using the host-prepared cache:

| Test | Relative selected volume difference | Difference including estimated numerical margin |
|---|---:|---:|
| exact analytic box |0|1.38161e-15|
| explicitly normalized fore spring STEP |1.65973e-11|1.15572e-7|
| curved foot copy |3.42686e-16|2.42718e-14|
| native ankle eye STEP |1.34671e-11|1.59087e-10|

A meaningful negative test changes two bore radii in opposite directions, preserving aggregate volume and all outer bounds. Both local parts are wrong; the implementation rejects the first at5.07091e-6. The original unnormalized canonical fore spring is also correctly rejected: selected relative2.29402e-6, with estimated numerical margin4.12675e-6. `python -m py_compile` passes for both Python modules.

A complete486-solid integrated check follows using a diagnostic STEP exported from private explicitly normalized CLI copies; canonical and existing package exports remain untouched by this worker.


## Integrated 486-solid diagnostic and remaining uncertainty

The complete isolated normalized assembly test initially stopped on the ancillary Gauss precision change for `hindR_extension_Spring`: Gauss Eps1e-8→1e-10 changes by2.57853e-8 relative, whereas the selected GK changes by4.64548e-10. The implementation now applies its provisional1e-8 convergence budget to the selected GK scalar, records Gauss convergence separately, and still includes the full Gauss change in the paired numerical margin. The frozen volume1e-6 acceptance gate is unchanged.

An explicitly marked diagnostic-only run bypassed convergence to collect every value (`all_measurements.py/json`, `all_pair_diagnostics.json`). No relaxed acceptance was reported. Among486 normalized native↔STEP pairs,484 pass the strict estimated-margin comparison. Both hind extension spring scalar differences are1.96271e-8, but their estimated-margin upper differences are1.14314e-6: **FAIL**. The native GK estimated relative error≈5.6539e-7 and imported error≈5.5788e-7 dominate this failure. All486 scalar differences alone are below1e-6; aggregate cancellation does not resolve the two local uncertainty failures.

Tightening GK Eps to1e-12/1e-14 (`extension_precision.py/json`) converges native volume64.82481887318626→64.82481887304272, but its error estimate plateaus≈5.6538e-7. A materially different documented reference-plane GK overload (`plane_volume.cpp`, `plane_test.py/json`) was also tested with X/Y/Z reference-plane normals through exact bounding-box center. It produces larger extension error estimates≈1.3e-6–1.05e-5, so it is rejected. No measurement selection or geometry repair is hidden in the exporter.

Current limitation: conservative local estimated-margin gating remains unresolved for the two hind extension springs. Canonical/exports have not been altered by this diagnostic. The lead must either qualify a better measurement method or explicitly repair/reconstruct those native spring surfaces and rerun the independent local gate. Stable scalar agreement suggests numerical uncertainty rather than established physical volume error; it does not justify claiming strict PASS. C++ source and helper API are ready for inspection, and the exporter fails closed on these pairs.


Final selected-GK convergence rerun (`module_all_normalized.json`) also exposes `hindR_compression_Spring`: GK eps1e-8→1e-10 change2.23489e-8 relative exceeds the implementation's provisional1e-8 precision budget. Its estimated native↔STEP margin is only1.50e-7. This is an additional numerical convergence stop, despite acceptable paired volume evidence. A bounded eps1e-12 refinement has been proposed; no threshold change or acceptance is assumed. The failure diagnostic now includes label, BRep hash and all four quadrature outputs.


## Bounded precision refinement implemented

The lead approved preserving the1e-8 selected-GK convergence budget with a bounded finer integration. Only selected-GK eps8→eps10 convergence failures receive an additional eps1e-12 evaluation; the last eps10→eps12 change must pass1e-8. The numerical margin retains the entire original eps8→eps10 variation, the final change, the Gauss variation and the larger eps10/eps12 GK error estimate. Neither the1e-6 volume tolerance nor uncertainty margin is relaxed. All evaluations and the selected epsilon are recorded. Isolated `compression_precision.json` establishes the mechanism on both hind compression pairs: final precision change≈1.93e-10 and native↔STEP difference≈3.4e-13. Further obsolete native diagnosis stops here; final full verification must use the lead's newly regenerated actual neutral native wires.


Current-source module tests (`module_current_test.py/json`) after the lead's regenerated native freeze pass with the bounded refinement implementation: analytic box upper1.38161e-15, actual current fore compression source STEP upper3.30671e-7, curved foot self-copy upper2.42718e-14, native ankle eye STEP upper1.59087e-10. The opposing-bore aggregate-cancellation fixture remains correctly rejected locally at5.07091e-6. Retained obsolete spring BReps also reject on placed bounds. The earlier `module_test.py` hardcodes a stale old fixed STEP and is superseded for current geometry; rerunning it after native regeneration correctly detects that mismatch.


Actual frozen canonical SHA`cea39190bd1265a7a9be2eddcd061a4abc85e19076e15e1514aa318cdffbb227` was opened read-only and its unchanged486 instances separately exported to `actual_native_assembly.step`. `actual_native_assembly.py/json` confirms the bounded precision refinement avoids numerical convergence stops, then correctly rejects `hindR_extension_Spring` at selected difference1.96270724e-8 / estimated-margin upper1.14313585e-6. No fix/normalization was applied in this current-source test. Original-domain quadrature escalation is being qualified separately; no complete export PASS is claimed at this stage.


## Qualified unchanged-domain quadrature

Astra's `reports/reviews/extension_volume_precision_r07.md` and `reports/tmp/spring_volume_precision/remedy_evidence.json` qualify a materially different measurement refinement using public OCCT `BRepGProp_Face`, `BRepGProp_Domain`, `BRepGProp_TFunction` and Kronrod quadrature. Original oriented faces, trim curves, surfaces and domain knots remain unchanged. Numerical integration subdivides each original boundary-parameter knot interval; it does not split or repair topology. Analytic box/cylinder/torus/sphere controls agree within1.70e-15 relative.

The production rule is deterministic per shape: when the selected coarse GK estimated error exceeds2.5e-7 (one quarter of the strict volume budget), evaluate unchanged-domain integration with8 subdivisions/order31 and16 subdivisions/order61 at eps1e-10. The refined scalar is the latter; both values must converge within1e-8 relative. Its numerical margin includes the larger refined error estimate, domain convergence shift, every original precision variation, and absolute differences between the refined scalar and **all** original Gauss/GK evaluations (including eps1e-12 if evaluated). The coarse plateau estimate remains disclosed; a qualified finer integration replaces it, rather than simply discarding uncertainty. Matching comparisons continue to add both local margins and paired-algorithm difference spread before the frozen1e-6 gate.

The C++ helper now includes the exact final guarded domain implementation (worker source SHA`dde52212e2afc6ebf2aa3c72bf324be3fdf82c66a273fbabeae7ecab4902a130`, before symbol renaming/inclusion). It rejects invalid/multiple/open solids, missing boundaries, unsupported orientations, failed quadrature or nonfinite results. Build links matching TKMath in addition to TKBRep/TKTopAlgo. Host compilation was rerun from source and runtime source/header/binary hashes remain verified. Python metadata also records the measurement-source SHA and all refinement rules.

On the qualified hind extension fixtures, refined native/STEP difference≈1.96905e-8 and conservative comparison upper≈3.00530e-7 pass without geometry changes or tolerance relaxation. The actual frozen486-instance integration check follows below.


## Final current-native 486-solid result

`reports/tmp/r07_assembly_volume/actual_native_assembly.py/json` opens the frozen canonical SHA`cea39190bd1265a7a9be2eddcd061a4abc85e19076e15e1514aa318cdffbb227` read-only, uses all actual native source shapes unchanged, exports a separate diagnostic STEP, imports it independently and calls the final exporter checker. **PASS**:

| Check | Actual result | Frozen gate |
|---|---:|---:|
| valid physical/imported solids |486 /486|486|
| distinct consumed STEP indices |486|486, one-to-one|
| maximum individual volume difference |1.96905052e-8|1e-6|
| maximum individual difference including numerical margin |3.30225617e-7|1e-6|
| hindR/L extension margin upper difference |3.00530081e-7|1e-6|
| maximum whole-assembly bounds difference |1.35003120e-12mm|1e-5mm|
| aggregate consistent adaptive volume difference |9.68750135e-12|1e-6|
| sum absolute individual volume differences |5.14550177e-6mm³|diagnostic|

Both hind extension native measurements trigger deterministic unchanged-domain refinement; the other shapes use their recorded standard GK path or bounded eps12 precision refinement. Aggregate cancellation is excluded by all486 independent local comparisons and complete matching. No native normalization, topology repair or geometry alteration occurs in this final check. Runtime121.47s under concurrent load.

Integration is ready: the host-prepared exact-source backend cache is verified; lead reloads `adaptive_volume_r07` and `export_robot_r07` in the actual GUI, then calls `export_robot_r07.run(doc, ROOT)`. The exporter freezes486 instances, validates assembly/each unique part/clean-document roundtrip with the same helper, preserves strict gates, writes dependency README and includes complete per-solid evidence and build metadata in the package manifest. This worker does not claim the complete package export has finished; the lead's actual MCP run is the remaining integration step.


Final source/backend regression rerun `module_current_test.json` is DONE: current spring/analytic box/curved foot/native eye controls pass, and the opposing-bore aggregate-cancellation fixture is still rejected locally at5.07091e-6. Python compilation passes.
