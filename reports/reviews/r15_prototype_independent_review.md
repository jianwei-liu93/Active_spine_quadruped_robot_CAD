# r15 lumbar root prototype — independent bounded review

2026-10-16. Static review under docs/08, before assembly integration. Scope is the separate R1 mm lumbar prototype, its two source modules, parameters, local geometry/section reports, saved FCStd metadata, source morphology audit, and actual matched images. No FreeCAD/Blender calls, native edits, source edits, or new geometry execution were performed by this reviewer. Model/effort inherited from the lead; no distinct model override is claimed.

**Decision: accept the local prototype for controlled r15 integration at the reviewed R1 mm radii, with motion/interface/native/export acceptance still pending.** No P0/P1 defect was identified in the bounded static evidence. This accepts a functional geometry improvement with qualitative source support; it does not establish that source radii were reproduced or that the assembly remains clear throughout motion. Do not expand the geometry family or radius range on the strength of this review.

## Findings requiring bounded follow-up

| Severity | Finding | Specific disposition |
|---|---|---|
| P2 — evidence provenance, before final acceptance | `r15_prototype_integrated_roots.json` and `r15_prototype_sections.json` contain no native/configuration/module hashes. Their volumes agree, and the saved native has the reported two R1 mm fillets, but those numerical JSON files alone cannot distinguish a later prototype or module revision. The capture manifest hashes pixels but also omits the native input hash. | Bind the prototype native, r14 native, parameters, both modules, numerical JSON and capture manifest to a revision-specific integration/evidence manifest. The hashes observed below permit binding this exact reviewed snapshot. If geometry/code changes materially, regenerate the relevant numerical result rather than merely rehashing an old report. This does not block construction of the controlled integration candidate. |
| P2 — visual evidence, before final visual acceptance | In `r14_root_matched_close.png` and `r15_root_matched_close.png`, the near outer guide hides much of the short-ear-to-shelf root. A small blend behind it is visible, but the comparison does not clearly expose both refined root families. The full lumbar image gives context, with the same occlusion. | Add a matched reverse/underside FreeCAD view with unchanged camera/scale between r14/r15, explicitly exposing one short-ear root and one guide root. Preserve actual geometry and record the new capture provenance. Existing views justify the localized direction; they are incomplete evidence for the final presentation. |

## Evidence supporting integration

- The saved prototype ZIP contains a real native `PartDesign::Fillet` chain: `RootBlendShortEarR15` after the retained `C2TravelRelief` tip, then `RootBlendGuidesR15`. Their stored radii are 1 mm, Base edge counts are four/eight, neither is suppressed, and the second is the Body tip. The 96 baseline Body members remain in exact order before the two appended fillets. Source placement is identity. The isolated prototype has no physical `LumbarIntegrated1` App::Link; the report's instance name is the intended integration target, not proof of an existing prototype assembly.
- The runtime report records one valid solid, +27.459101625678468 mm³, zero removed material, unchanged source frame/history, and valid features. The section report independently lists matching old/new volumes (floating-point difference in the volume delta only), exactly unchanged bounding extents, 12 root regions × 9 stations = 108 sections, and minimum area/principal-moment ratio 0.9999999999994166. This minute deficit is numerical noise at the stated scale, not evidence of a lost section. Assumed mass increment is 0.0274591 g at 1000 kg/m³.
- All four recorded A1/A2 windows at source Z=0.8/56 mm have zero material difference. Their centers are A1=(30,8.66), A2=(-30,-8.66) mm in source XY. These are A support ears: the legacy `ShortEarE*` feature names do not make them the separate central-E supports. The corrected morphology audit now makes this distinction explicitly.
- The selector derives current edge references from straight X-oriented edge geometry at the frozen root planes, then requires exact family counts. It does not reuse stale edge indices. The reported selections match the intended four short-ear and eight guide locations. For this SHA-pinned baseline and fixed radius, the count guard, shape validity, strictly additive Boolean check and preserved placement are a reasonable local contract. The broad X/length predicates are not a general selector contract for arbitrary future frame changes; revalidate geometric centers/counts after any upstream geometry edit.
- The actual clipped-face section implementation handles holes, aggregates face centroidal inertia by parallel-axis shifts, and diagonalizes the resulting in-plane tensor. The XZ and XY mappings are consistent. The executed translated 2×3 mm rectangle probe verifies the centroidal convention, preventing a normal-offset subtraction error. Areas/moments are finite and empty sections fail closed. This is valid local section screening; it does not infer material or loaded stiffness from the bounding box.
- Movie S1 at 53 s supports tapered bearing ears growing into a shelf and compact guide supports. The prototype retains this arrangement and adds small concave transitions without changing the lightweight external span. The film does not resolve the back roots or establish a 1 mm radius. `FUNCTIONAL_GEOMETRY_IMPROVEMENT` with `DESIGN_ASSUMPTION` dimensions is the appropriate classification.

Archive comparisons also show tiny last-digit recompute/serialization changes in some retained placements, directions, sketch geometry and BRep text. Inspected examples are approximately 1e-16 to 1e-14 in coordinates, including signed-zero changes. Byte equality of recomputed FCStd members is therefore not a substitute for the planned strict geometric/datums comparison; no substantive retained-profile edit was identified in the inspected differences.

## Integration boundary and reuse

The plan in `r15_verification_reuse_plan.md` is appropriate: preserve the r14 checkpoint, change only the lumbar source and its `LumbarIntegrated1` instance, retain 455 instances/108 sources, and derive the changed set from actual linked-source identity/BRep comparison. Additive roots can consume neighboring free space even when overall bounding extents are unchanged; local Boolean/section results do not close the assembly-compatibility gate.

Before candidate acceptance, execute the new r15 changed-versus-all finite screen (454 unique pairs per phase for exactly one changed instance), the declared coordinated leg/cable samples with regenerated procedural shapes, critical datum/interface equality, saved-file reopen/recompute, and radius edit/restore probes on a disposable copy. Bind those results to the saved r15 native. Then round-trip the new STEP and regenerate AX0/AX1 and the changed Blender mesh under stable source/instance frames. Reuse unchanged r14 evidence only after those identity/kinematic inputs are proven unchanged. The planned 91-phase plus bounded coordinated screen is proportionate; this review requests no historical full rebuild or broad rerun.

Existing research-candidate limits on supplier fits, central support loads, strength/fatigue and fabrication remain as already documented. The additive geometry and finite section comparison introduce no basis to promote those limits into verified performance.

## Snapshot reviewed

| Artifact | SHA-256 |
|---|---|
| `cad/flexor_r14_robot.FCStd` | `7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87` |
| `cad/prototypes/r15_lumbar_root.FCStd` | `c60fdd5d5f64841f8491ee10f9b8222f8e29d4288f0ccfd8092def9d26e60d03` |
| `parameters/assembly_r15.json` | `bedb045030d2f3879c7226010658d225b38e0e787b0beb27d1689df2f1b48a64` |
| `src/sculpted_frame_r15.py` | `3d35b6583047632bf327a75ef7d704fd5ed36b762e4dea51aeff098d83deb0a1` |
| `src/section_compare_r15.py` | `e9c438e36774fb1794a9ae47631edef9afd62db1c2a64840491e3449c74bb17f` |
| `reports/verification/r15_prototype_integrated_roots.json` | `2065895e1ecc66ff07f977b4e217787093a5839761ee2c0f31b7a89dabb0ed92` |
| `reports/verification/r15_prototype_sections.json` | `3faf1ffdfe8f15b0c081868d766a861a0be4dbaa6106b97f03901acad62f92c9` |
| `reports/views/r15_prototype_capture_manifest.json` | `0a3a33116a511d81f7121b3a1f731e08664f4a9f64fb226927185798a6459d49` |

All four capture hashes in that manifest were checked against the actual PNGs and match. The single-edge `r15_prototype_trial.json` is only the earlier pilot (+2.3152082 mm³), not the integrated 12-edge result; the review bases its decision on the integrated report and saved two-feature prototype.

## 2026-10-16 — new user steering: shelf-to-motor-mount material

The user supplied a source assembly image (`/tmp/codex-clipboard-91f44fa6-cf6a-4698-bf83-be7e1e344bf7.png`) and the isolated CAD image (`/tmp/codex-clipboard-a82e4bef-930a-4cac-b9f5-5c81af689065.png`), identifying missing material between the motor mount and linkage mount. This is an additional source-fidelity concern; the earlier acceptance of a localized R1 mm fillet prototype does **not** close it. This addendum is a static interpretation and proposed geometry bound, not an executed CAD result.

The source image shows a broad, continuous horizontal shoulder between the outer linkage support and motor housing near the output-disc level. The CAD image visibly narrows that connection close to the motor cheek. The code and saved r14 sketch metadata provide a specific, limited candidate for the discrepancy: each `LocalEndPlatform` extends from |X|=10 to 35.5 mm but is only 1.6 mm thick along source Z; each `BroadShelf` starts at |X|=16 mm and adds 9.4 mm of axial depth. Consequently the 6 mm inner shoulder between |X|=10 and 16 lacks the broad shelf's outboard depth. It is connected by the thin cheek/platform, not topologically disconnected. The source supports investigating a more continuous shelf there, with medium confidence in morphology and no metric confidence in the unseen depth.

**Recommended first bounded additive trial:** retain the entire accepted r14 body and add native datum-based shelf pads with these source-local limits, mirrored in X and at both ends of the transverse stack:

| Bounds | Near end | Far end |
|---|---|---|
| X | [10,16] and [-16,-10] mm | same |
| Y | [-2.5,2.5] mm | same |
| Z | [-9.4,0] mm | [56.8,66.2] mm |

These four nominal 6×5×9.4 mm regions extend the shelf footprint to match the existing inner platform. Dimensions are a new reconstruction assumption, not recovered film measurements. Generate the pads from their sketches against the retained platform faces and check positive-area connection to the platform and neighboring broad shelf in the actual BRep; do not rely on the image for contact. A small integration overlap or later local blend is an implementation detail for the lead to verify without changing preserved interfaces. The nominal envelope lies outside the motor bodies' transverse source-Z range of approximately [2,54.8] mm, and does not increase the source stack extrema [-11,67.8] mm or the 78.8 mm span. That is a useful packaging bound, not a completed motor-clearance check.

Do not fill all visible openings between housing and linkage supports. Preserve the radius9 mm central lower motor/output opening; the proposed |X|≥10 band stays outside that circle. Preserve the upper orthogonal motor/access windows, open top, carrier access pockets, A1/A2 bearing openings, guide slots and C1/C2 full-stack travel reliefs. The stored C1 travel capsule begins at source Y=6.51 mm, comfortably outside the proposed |Y|≤2.5 strip. Preserve central-E windowed crossmembers and bearing lugs: a source image with installed hardware is not evidence to turn their current open load path into a solid block or restore retired outer E supports. The actual moving bars, clips and motor output structures still require changed-pair screening around any new pad.

The original 108 section probes cover |X|=22..37 mm and therefore do not assess these inner |X|=10..16 shoulders. Retain those probes for the R1 roots and add a bounded set of actual source-X-normal YZ sections through the new connections, for example at |X|=10.5,13,15.5 mm at both ends. Record connectivity, area/moment change, unchanged critical voids/datums and actual added volume. Use a matched source-facing view that makes the inner shoulder visible before deciding whether this fills the user's identified region; if the lead's live BRep inspection locates a different gap, revise these bounds before modeling beyond this trial. Re-run the same proportionate changed-instance motion/native/export gates against the final selected geometry, with refreshed hashes and section/capture reports.

## 2026-10-16 — executed shoulder prototype follow-up

**Decision: accept the four-pad shoulder geometry as the bounded response to the user's missing-material concern, pending the remaining revision gates.** The actual matched `r14/r15_shoulder_matched_close.png` and `r14/r15_lumbar_under_matched.png` views now clearly expose the inner shelf connection. The r15 shelf reaches the motor cheek with full depth, while the motor/output opening, guide slots and central windowed beams remain visible. The underside pair makes the four repeated bridges and retained local root blends assessable. This resolves the earlier visual-evidence finding for this prototype; no additional broad geometry redesign is requested. Exact source depth and radius remain assumptions.

`r15_shoulder_prototype.json` records the four proposed native pads in the reviewed limits, 1128 mm³ added, zero removed, one valid solid and final frame volume 16600.454665213394 mm³. The added volume agrees exactly with four nominal 6×5×9.4 mm pads. The saved assembly ZIP confirms their profile links, 9.4 mm lengths, Body membership and final tip `ShelfShoulderNegativeFarR15`. Combined with the prior root addition, the frame gains 1155.4591016 mm³ over r14, approximately 7.481% of the r14 frame volume, or 1.1554591 g at the explicitly assumed 1000 kg/m³ density. This remains a local frame mass estimate, not an assembled-robot mass measurement.

The 12 new actual YZ section records at X=±10.5/13/15.5 mm resolve the previously uncovered shoulder region. All show one connected clipped face, 8→55 mm² area and 6.875 area ratio. The moment values also match the expected 5×1.6→5×11 mm local rectangles within numerical precision. The section script correctly rotates each YZ face by +90° about source Y before calling the XY helper.

**P2 reporting clarification, before stiffness claims:** the JSON's `centroid_xy_mm`/tensor axes are the rotated section coordinates X'=source Z, Y'=source Y, not original source X/Y. Its reported minimum principal-moment ratio 33.275 compares sorted eigenvalues; the principal directions swap rank between the thin and thick section. It is not a lower bound on improvement about every fixed source axis. For the recorded rectangles the fixed-axis second-moment ratios are approximately 324.951 about source Y and 6.875 about source Z. Document that mapping/ranking explicitly if reporting these numbers, or publish the fixed-axis ratios. No geometry or section-calculation repair is needed for this clarification, and no loaded stiffness multiplier is established.

The hash-bound `r15_identity.json` records exactly one changed source/instance, no new/retired IDs, 455 instances/108 definitions, 107 strictly unchanged sources, equal motion/pose parameters and zero placement-matrix error. `r15_integration.json` pins the same saved native and current configuration. The lead additionally reports a neutral changed-versus-all screen of 454 unique pairs, 157 OCC checks and 297 bounding exclusions, without overlap; this reviewer did not inspect a persisted neutral pair ledger and does not count that report as completed cycle evidence. Saved-native edit/recompute, full prescribed finite motion, STEP and AX gates remain pending at this review snapshot.

The new integration manifest partially resolves the original provenance finding. Bind the shoulder section helper/report, current eight-view capture manifest and final candidate results in the final evidence manifest. The prior 15472.4546652 mm³ root reports describe the fillet-only predecessor; retain that lineage explicitly rather than presenting their smaller volume as the final candidate. The four shoulder pads lie outside the original root ROIs, so retaining those root checks as local predecessor evidence is reasonable alongside the new shoulder checks and final geometry/datums proof.

| Follow-up snapshot artifact | SHA-256 |
|---|---|
| `cad/flexor_r15_robot.FCStd` | `56126360d99fc6019a0e95f0c0d036ebed607cc50c4a16333c6f9c70aa34b4c4` |
| `reports/verification/r15_integration.json` | `bc20cde9c4db639e488d3af9cace76aff35f4989f734b7d27386d4b8373a1559` |
| `reports/verification/r15_identity.json` | `71ca268b5151dcefeb2d41313883eb7085ab0ef148a7ca02c1c6fe926fab3b30` |
| `reports/verification/r15_shoulder_prototype.json` | `7b526c3cf880e5d264f838a5aade828c04511624f76d142fa612ef238acdfe70` |
| `reports/verification/r15_shoulder_sections.json` | `cb30e663b308a1c625d8fb1c5e2b72e9a54e846dec6bf2db0b4797466fac46e4` |
| `src/shoulder_sections_r15.py` | `f90bd87b182130e05bfdf212b6e5a3b54533da9219f66f2277f0d5feb6ac9969` |
| `reports/views/r15_prototype_capture_manifest.json` | `238389212db15c7cc51327f35f0aeb37903d6c99267a9f5da6f8e5b486f2469f` |

All eight current PNG hashes match their updated capture manifest. The earlier four-image snapshot/hash table remains historical and is superseded for current captures by this follow-up. No app calls or source/native edits were made for this review.
