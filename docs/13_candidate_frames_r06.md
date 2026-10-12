# r06 — Movie S1 lumbar and torso attachment refinement

The editable checkpoint is [flexor_r06_robot.FCStd](../cad/flexor_r06_robot.FCStd). It supersedes r05 frame morphology while retaining the seven-motor mechanism, joint coordinates, leg directions and fixed-neutral hind tendon route.

## Source and design changes

Movie S1 51–80 s establishes a rounded lower lumbar opening, an upper rectangular window, local end shelves and separate moving slotted torso end plates. Retained stills and hashes are in [references/visual/movie_s1](../references/visual/movie_s1/); interpretation is documented in the [source reconciliation](../reports/source_review/movie_s1_frame_attachment_r06.md) and [independent review](../reports/reviews/frame_fidelity_r06.md).

- Replace the rectangular lumbar annulus and uninterrupted middle rail with a rounded lower cradle, distinct upper window and two local end platforms. Retain fixed C1/A2 and C2/A1 guide ears, shelves, E/A journals, ties and transverse shafts.
- Replace both long E–D–H triangular carriers with transverse slotted end plates and independent short E/D bearing ears. Their bearings remain normal to Y; the plate broad faces are approximately normal to X. The plates belong to their moving torso bodies.
- Use different fore/hind motor supports: vertical fore cases, horizontal hind cases. Local pans, outer H bearing panels, capture strips and straps connect the cases to the transverse plate. Rebase the central hind-knee cage and guide supports onto the new hind frame; retain its removable rear lock and separate fasteners.
- Preserve S9's eleven projected edges on each side, two XL330-M077-T spine motors, five XC330-M181-T leg motors, existing H axes, same sagittal leg direction, shafts, springs and cable datums.

Plate dimensions, the five-slot pattern, cradle radii, pans, straps, ear thicknesses and fits are **DESIGN_ASSUMPTION** in [assembly_r06.json](../parameters/assembly_r06.json). The source animation supports their arrangement and general profiles; perspective frames do not establish millimetre dimensions or vendor hole patterns. Manufacturer output/mount geometry and detailed source bracket contours remain unresolved.

## Executed checks

| Check | Actual result |
|---|---|
| Saved native reopen/recompute and neutral intersections | PASS: 464 valid single-solid instances; 80 editable bodies; all sketches fully constrained; 1,129 narrowphase checks; no overlaps above 1e-5 mm³. |
| S9 topology and native E/D axes | PASS: no missing/extra edges; maximum native axis error 8.56e-14 mm. |
| Leg native axes and orientation | PASS: 315 checks; both fore/hind retain the corrected direction. |
| Motor inventory | PASS: 2 XL330-M077-T + 5 XC330-M181-T. |
| Fresh current-source rebuild through installed MCP | PASS: all 464 instance bounds/volumes match the saved native within 1e-6 mm / mm³. |
| Native edit/recompute/restore | PASS: fore transverse plate Pad length 1.6 → 1.7 → 1.6 mm; valid connected solid and exactly restored volume. |
| Sampled spine cycle | PASS: 25 distinct poses at 15° intervals including 0°/360°; no raw overlaps; three validated read-only partitions share native/motion hashes and inventory. Fixed saved leg/wheel states. |
| Pure software checks | 43 tests pass. |

Evidence is in `reports/verification/r06_*.json` and `r06_coarse_partitions/`. The 25-pose result is finite sampled evidence, not a continuous-clearance certificate or a one-degree sweep. Independent leg actuation, moving tendon regeneration and loaded equilibrium are not certified.

[Bare lumbar](../reports/views/r06_bare_lumbar.png), [fore attachment](../reports/views/r06_bare_fore_attachment.png), [hind attachment](../reports/views/r06_bare_hind_attachment.png), [frame assembly](../reports/views/r06_spine_torso_frames.png), [whole robot](../reports/views/r06_robot_assembled.png), and [side view](../reports/views/r06_robot_side.png) are actual FreeCAD captures. Motor boxes in the whole-robot view are purchased envelopes, not solid frame walls.

The revised nominal/volume-derived installed mass estimate is 262.81 g; purchased motor portion 151 g. The prescribed-pose envelope remains 163.54 × 117.60 × 94.12 mm. Controller and harness are uninstalled; these values do not reproduce the paper's mass/envelope. See [BOM](../bom/bom_r06.csv) and [mass report](../reports/verification/r06_mass_envelope.json).

## Reproduction and remaining work

The lead executes `build_robot_r06.build(save=True, doc_name='FlexorR06')` from [build_robot_r06.py](../src/build_robot_r06.py) through the installed FreeCAD MCP. Frame modules create constrained sketches and native Pad/Pocket features. [render_robot_r06.py](../src/render_robot_r06.py) captures views without saving geometry.

FreeCAD crashed in the first combined integration. Saved r05 survived. The recovered build used separate staged saves and name-based cleanup of obsolete bodies; the precise crash cause is unproven. Stages are retained under `cad/checkpoints/r06_*.FCStd`, with [recovery evidence](../reports/diagnostics/r06_freecad_recovery.json). The successful complete fresh build validates the final scripts against the saved r06 geometry.

Final supplier interfaces, positive cable-end securing, controller/harness packaging, fits/load/access review and export/drawing acceptance remain open. Failed r05 STEP files are isolated under `reports/diagnostics/r05_failed_step_export/`; their volume-gate failure was not waived. Interrupted r05 full-degree progress is likewise diagnostic, not a motion pass. The native r06 checkpoint is a reviewable reconstruction candidate, not a fabrication release.
