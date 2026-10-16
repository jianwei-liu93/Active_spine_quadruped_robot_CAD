# r15 sculpted geometry refinement

## Purpose and baseline

r15 is a controlled refinement of the accepted r14 assembly. It modifies one source definition, `FRM_LUMBAR_COMPACT_CAGE_r12`, used by the physical instance `LumbarIntegrated1`. It adds material at lumbar support roots and at the shelf-to-motor-mount shoulders. The S9 mechanism, all pivot and guide datums, instance placements, and MotionMap are retained.

The protected r14 baseline is `cad/flexor_r14_robot.FCStd`, SHA-256 `7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87`. The saved r15 candidate is `cad/flexor_r15_robot.FCStd`, SHA-256 `56126360d99fc6019a0e95f0c0d036ebed607cc50c4a16333c6f9c70aa34b4c4`; its parameter file is `parameters/assembly_r15.json`. Final native, exchange, kinematic, finite-motion, and animation-mapping gates now pass for their stated scopes; fabrication qualification remains open.

The model retains the accepted B-only rocker fork, blind B–C recess with 0.6 mm floor, 78.8 mm frame span, 28 mm sagittal housing, orthogonal windows, open top, and central-E support architecture. The ShortEar legacy feature names refer to the A1/A2 support bores; they are not the separate central-E bearings. Central-E bearings remain at source-local X=±33 mm, Y=0, Z=28.4 mm.

## Geometry changes

The one-piece lumbar body receives two native concave R1 mm PartDesign fillets: `RootBlendShortEarR15` at four short-ear roots and `RootBlendGuidesR15` at eight guide roots. The radius is a new design assumption informed by qualitative Movie S1 morphology, not a measured source value. The changed geometry is additive: the root report records 27.4591 mm³ added and zero material removed.

Four native pads extend the shelf toward the motor cheek at the inner shoulder. Their source-local extents are X=10–16 mm and −16 to −10 mm, Y=−2.5 to +2.5 mm, and Z=−9.4–0 mm at the near end and 56.8–66.2 mm at the far end. Each pad is 6×5×9.4 mm; together they add 1,128 mm³ without removing material. These dimensions address a visible source/CAD shoulder difference but remain design assumptions; the source does not provide the exact wall depth.

The final lumbar source volume is 16,600.4547 mm³, compared with 15,444.9956 mm³ in r14, a 1,155.4591 mm³ increase. At the explicitly assumed density of 1,000 kg/m³, that corresponds to about 1.155 g for this frame only. It is not a whole-robot mass result. The final bounding box is unchanged.

## Local geometry evidence

`reports/verification/r15_prototype_integrated_roots.json` records a valid single solid, unchanged source placement and retained r14 feature history for the root fillets. The companion root sections were measured on the root-only prototype, before the shoulder pads; they cover 108 sampled regions. The shoulder pads lie at |X|=10–16 mm, outside those root-section ROIs at |X|=22–37 mm, and retain the root geometry. The minimum root area/principal-moment ratio is 0.9999999999994. Four A1/A2 bore-support windows are unchanged within the recorded strict tolerance. `reports/verification/r15_shoulder_sections.json` contains 12 actual YZ sections through the previously unmeasured shoulder region. Their area ratio is 6.875 (8 to 55 mm²). The reported minimum sorted principal-moment ratio is 33.275; because principal directions switch rank, this is not a bound on improvement about each fixed source axis. For the rectangular shoulder sections, the fixed-axis ratios are about 324.951 about source Y and 6.875 about source Z. These section comparisons describe geometry only; they do not establish loaded stiffness, buckling, strength, or fatigue life.

The independent bounded review accepted the local R1 root geometry and the four-pad shoulder geometry for a controlled r15 candidate. It found no P0/P1 issue in the bounded static evidence. It also requested that the section-axis interpretation remain explicit and that final assembly gates be completed before acceptance. Source morphology is qualitative: Movie S1 and the supplied visual comparison support tapered supports and a continuous shelf, but do not establish the selected radii or pad depth.

## Identity and verification status

The identity comparison in `reports/verification/r15_identity.json` passes for its stated scope: 455 physical instances, 108 source definitions, one changed source and one changed instance (`LumbarIntegrated1`), no added or retired IDs, 107 strictly unchanged sources, zero link-placement matrix error, and equal pose parameters and MotionMap. This is identity evidence, not mechanism or strength qualification.

The final gate snapshot passes for the bounded evidence below. Earlier attempt artifacts remain chronological history; the current reports named here are authoritative.

- **Native document:** `reports/verification/r15_native_checks.json` passes reopen/recompute of all 455 instances and comparison of 108 source definitions. It records 93 bodies, 745 body/member entries, zero invalid/error shapes, 325 fully constrained sketches, and three disposable-copy edit/restore probes. The probes changed and restored `RootBlendShortEarR15.Radius`, `RootBlendGuidesR15.Radius`, and `ShelfShoulderPositiveNearR15.Length`, without modifying either saved native file.
- **Exchange:** `reports/verification/r15_assembly_export.json` passes a one-to-one strict round trip for 455 placed solids. The exporter used detached copies of placed native BReps in a temporary exchange document to avoid source p-curve bookkeeping effects.
- **Animation mapping:** `reports/animation/ax01_r15.json` passes AX0 and AX1 for the final native SHA, covering 455 instances and 108 sources; 409 native motion entries plus 46 explicitly grounded instances give complete 455-instance coverage. Source-to-world convention and regenerated tendons/springs were checked, with no guide warnings.
- **Numerical cycle:** `reports/verification/r15_numeric_cycle.json` passes 361 samples at 1-degree phase increments. Endpoint joint error is 1.776e-15 mm; the maximum all-instance transform-matrix difference is 1.776e-15; maximum adjacent output-angle step is 0.00972447 rad.
- **Finite motion screens:** `reports/verification/r15_motion.json` passes `PASS_BOUNDED_ADDITIVE_DELTA_R15`. Its additive-delta screen samples 91 phases at 4-degree increments and checks all 16 added solids against the other 454 physical instances: 661,024 component-pair decisions, 1,732 exact common checks, no positive-delta intersections, and no guide warnings. The complete changed frame is also checked at nine prescribed paper poses with 1,429 exact OCC checks, all passing. Frozen r14 evidence is reused only for the exactly bound identical native/configuration/profile. These finite screens do not establish continuous-cycle clearance.
- **Identity:** `reports/verification/r15_identity.json` passes for 455 instances and 108 sources: one changed source and instance, 107 unchanged sources, no IDs added or retired, and placements, pose parameters, and MotionMap retained.
- **Whole-robot views:** matched native FreeCAD captures are recorded in `reports/views/r15_robot_capture_manifest.json`; the read-only capture did not save either native file.
- **Blender preview:** the generated scene contains 455 instances and 108 sources; the changed lumbar mesh has 6,251 vertices and 12,598 triangles. A four-pose probe observes both legs and the fore-leg extension spring changing. A 60-frame, 5-second, 640×360 preview was generated at `animation/previews/r15_spine_leg_coordination.mp4` and `.gif`; saved-scene, unit/reprojection, full MP4 decode, GIF timing, articulation, and sampled image checks passed in `reports/animation/r15_preview_qa.json`. Existing full r14 videos remain unchanged.

The candidate remains a research CAD model, not a strength-qualified design or fabrication release. Source imagery supports the broad morphology but gives no exact R1 radius or shoulder depth. The density-derived mass difference is assumed. The checks do not establish loaded equilibrium, continuous clearance, strength, buckling, fatigue, supplier fits, fastener retention, or process capability.

## Reproduction and evidence

Build from a disposable copy of the SHA-verified r14 native file, using the lead-owned installed FreeCAD MCP integration flow. `src/build_robot_r15.py:integrate(doc)` validates the r14 checkpoint hash, applies the r15 native features to the copied document, and saves a separate `cad/flexor_r15_robot.FCStd`. It refuses to overwrite existing r15 progress. Do not rebuild r14 or treat prototype files as the integrated candidate.

The prototype input and numerical evidence are bound in `reports/verification/r15_prototype_evidence_binding.json`. Native candidate captures are listed in `reports/views/r15_robot_capture_manifest.json`. Gate reports are `reports/verification/r15_native_checks.json`, `r15_identity.json`, `r15_assembly_export.json`, `r15_numeric_cycle.json`, `r15_motion.json`, and `reports/animation/ax01_r15.json`. Actual before/after images and measurements are summarized in [the r15 geometry comparison](../reports/reviews/r15_geometry_comparison.md). All introduced dimensions remain assumptions unless independently identified as source-reported or manufacturer-verified.

## Small preview reproduction

The installed Blender MCP constructs the isolated preview with `animation/blender/preview_geometry_r15.py:build(root, r14_library_path)`. The pinned local r14 `.blend` library is required; its SHA-256 is recorded in `animation/motion/geometry_preview_r15.json`. Large scenes and PNG caches remain local/ignored. Package and render only this five-second preview with:

```bash
/snap/bin/blender -b animation/scenes/r15_geometry_interoperability_preview.blend --python animation/blender/render_preview_r15.py
/snap/bin/blender -b animation/scenes/r15_geometry_interoperability_preview.blend --python animation/blender/check_preview_r15.py
python animation/blender/quality_preview_r15.py --encode
```

The standalone scene opens directly to the r15 assembly. These commands consume the existing prescribed trajectory; they do not solve loaded knee motion. The source-definition inventory and all 455 stable instance IDs are also exported in `bom/bom_r15.csv` and `bom/instances_r15.csv`.
