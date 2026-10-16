# r15 geometry comparison

**Snapshot:** 2026-10-16. The r15 file is an integrated candidate with local geometry and identity evidence; native acceptance, full motion/clearance, STEP, and AX0/AX1 gates remain pending. This is a geometry comparison, not a fabrication release.

## Matched views

The eight-view capture manifest records matching camera and scale for each r14/r15 pair. These are actual saved native geometry views. The underside pair exposes the new shelf-to-motor-shoulder pads; the close view shows their extent beside the retained motor/horn opening.

| r14 baseline | r15 candidate |
|---|---|
| ![r14 lumbar underside](../views/r14_lumbar_under_matched.png) | ![r15 lumbar underside](../views/r15_lumbar_under_matched.png) |
| ![r14 shoulder close-up](../views/r14_shoulder_matched_close.png) | ![r15 shoulder close-up](../views/r15_shoulder_matched_close.png) |

Full matched lumbar views: [r14](../views/r14_lumbar_matched.png) · [r15](../views/r15_lumbar_matched.png). Matched root views: [r14](../views/r14_root_matched_close.png) · [r15](../views/r15_root_matched_close.png). The root close-up is partly occluded by the guide; the matched underside pair supplements it by exposing the repeated shoulder bridges and retained root transitions.

## Changed geometry and measured comparison

| Item | r14 | r15 | Evidence and limits |
|---|---:|---:|---|
| Lumbar root blends | Square/straight root transitions | Twelve native concave R1 mm fillets: four short-ear/A-bearing roots and eight guide roots | `RootBlendShortEarR15` and `RootBlendGuidesR15`; 27.4591 mm³ added, zero removed. R1 mm is an assumed radius, not a source measurement. |
| Shelf-to-motor shoulders | Thin inner platform connection at the motor cheek | Four native 6×5×9.4 mm additive pads | Source X ranges [10,16] and [−16,−10] mm; Y=±2.5 mm; near Z=−9.4–0 mm; far Z=56.8–66.2 mm. 1,128 mm³ added, zero removed. Extents are design assumptions based on qualitative source comparison. |
| Final lumbar frame volume | 15,444.9956 mm³ | 16,600.4547 mm³ | +1,155.4591 mm³ overall; bounding box unchanged. At assumed 1,000 kg/m³, +1.1555 g for this frame alone. |
| Instance/source identity | 455 instances / 108 sources | 455 instances / 108 sources | `r15_identity.json`: only `FRM_LUMBAR_COMPACT_CAGE_r12` and `LumbarIntegrated1` changed; no IDs added/retired; 107 sources strictly unchanged; all link placements and MotionMap/pose parameters equal. |

The selected support ears carry the A1/A2 support bores; they are not the separate central-E bearings. The central-E bearing datum remains source-local X=±33 mm, Y=0, Z=28.4 mm. The r15 candidate retains the 78.8 mm frame span, 28 mm housing, accepted A–B rocker, blind B–C recess with its 0.6 mm floor, guide slots, and other mechanism datums.

## Section screen and independent review

The root-section report covers 108 sampled regions and records a minimum area/principal-moment ratio of 0.9999999999994; all four A1/A2 bore-support windows remain unchanged within the strict comparison tolerance. Those root sections were taken on the root-only prototype before shoulder pads were added. Their ROIs at |X|=22–37 mm do not overlap the shoulder pads at |X|=10–16 mm, and the shoulder operation retained the root geometry. The separate shoulder screen covers 12 actual source-X-normal YZ sections at X=±10.5, 13, and 15.5 mm. Each grows from 8 to 55 mm², an area ratio of 6.875. The reported 33.275 minimum sorted principal-moment ratio compares ranked eigenvalues after the principal directions switch. For these rectangular sections, the fixed-axis second-moment ratios are approximately 324.951 about source Y and 6.875 about source Z. These are local geometric section comparisons; they do not quantify assembled stiffness under load or establish strength, buckling capacity, or fatigue life.

The independent review accepted the additive roots and shoulder pads for the controlled candidate. It found no P0/P1 issue in the bounded static evidence and clarified the fixed-axis interpretation above. The source supports a tapered support silhouette and a continuous shelf; no exact R1 radius or shoulder depth is recovered from the images. The dimensions and material-density estimate remain assumptions.

Evidence is recorded in [`r15_integration.json`](../verification/r15_integration.json), [`r15_identity.json`](../verification/r15_identity.json), [`r15_prototype_integrated_roots.json`](../verification/r15_prototype_integrated_roots.json), [`r15_prototype_sections.json`](../verification/r15_prototype_sections.json), [`r15_shoulder_prototype.json`](../verification/r15_shoulder_prototype.json), [`r15_shoulder_sections.json`](../verification/r15_shoulder_sections.json), and [`r15_prototype_independent_review.md`](r15_prototype_independent_review.md). The capture hashes are in [`r15_prototype_capture_manifest.json`](../views/r15_prototype_capture_manifest.json); input and report hashes are in [`r15_prototype_evidence_binding.json`](../verification/r15_prototype_evidence_binding.json).

## Remaining acceptance gates

- **Native reopen/editability:** unresolved. `r15_native_checks.json` failed when a temporary edit probe did not observe a change to `ShelfShoulderPositiveNearR15`; diagnose and rerun on a disposable copy.
- **Motion and clearance:** no r15 cycle pass. The current motion run stopped with a harness error (`SimpleNamespace` has no `ExpressionEngine`). Complete the changed-instance finite cycle and the declared coordinated leg/cable samples after repairing the harness.
- **STEP round trip and AX0/AX1:** pending. Regenerate from the final r15 file and bind results to its native/configuration hashes.
- **Blender:** the small r15 interoperability preview remains pending. Existing 25-second videos remain immutable r14 outputs.

Until these gates pass, the screenshots and section metrics show only the geometry change. They do not establish motion clearance, editable-native acceptance, exchange correctness, animation compatibility, or fabrication readiness.
