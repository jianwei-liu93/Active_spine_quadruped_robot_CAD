# r15 sculpted geometry refinement

## Purpose and baseline

r15 is a controlled refinement of the accepted r14 assembly. It modifies one source definition, `FRM_LUMBAR_COMPACT_CAGE_r12`, used by the physical instance `LumbarIntegrated1`. It adds material at lumbar support roots and at the shelf-to-motor-mount shoulders. The S9 mechanism, all pivot and guide datums, instance placements, and MotionMap are retained.

The protected r14 baseline is `cad/flexor_r14_robot.FCStd`, SHA-256 `7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87`. The saved r15 candidate is `cad/flexor_r15_robot.FCStd`, SHA-256 `56126360d99fc6019a0e95f0c0d036ebed607cc50c4a16333c6f9c70aa34b4c4`; its parameter file is `parameters/assembly_r15.json`. The recorded integration status is `INTEGRATED_PENDING_REVISION_GATES`.

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

The r15 geometry candidate is **not yet fully accepted**. At the current evidence snapshot:

- Local root/shoulder geometry and section comparisons: passed for their bounded scopes.
- Saved-native reopen/recompute and editability: unresolved. `reports/verification/r15_native_checks.json` failed when its temporary edit probe did not observe a change to `ShelfShoulderPositiveNearR15`; investigate the probe on a disposable copy and rerun before making an editability claim.
- Full prescribed motion and clearance: not passed. The current `reports/verification/r15_motion_error.json` records a harness error (`SimpleNamespace` has no `ExpressionEngine`), so no cycle result was established. The changed-instance finite screen and declared coordinated leg/cable samples remain to be completed.
- STEP round trip and AX0/AX1: pending. Regenerate these against the final native file; r14 exports and animation manifests do not certify r15.
- Small Blender interoperability preview: pending and separate from the immutable r14 videos. The existing 25-second video remains an r14 result.

The candidate remains a research CAD model, not a strength-qualified design or fabrication release. Supplier fits, load assumptions, central support capacity, fastener retention, process tolerances, and fatigue remain unresolved.

## Reproduction and evidence

Build from a disposable copy of the SHA-verified r14 native file, using the lead-owned installed FreeCAD MCP integration flow. `src/build_robot_r15.py:integrate(doc)` validates the r14 checkpoint hash, applies the r15 native features to the copied document, and saves a separate `cad/flexor_r15_robot.FCStd`. It refuses to overwrite existing r15 progress. Do not rebuild r14 or treat prototype files as the integrated candidate.

The matched native captures and their SHA-256 records are listed in `reports/views/r15_prototype_capture_manifest.json`. The prototype input and numerical evidence are bound in `reports/verification/r15_prototype_evidence_binding.json`. The actual before/after images and comparison measurements are summarized in [the r15 geometry comparison](../reports/reviews/r15_geometry_comparison.md). All dimensions introduced by this refinement remain assumptions unless independently identified as source-reported or manufacturer-verified.
