# Independent r06 frame fidelity review

Reviewed 2026-10-12. Requested routing: inherited Sol/high; actual service routing is not independently observable. Scope is a static source/native-mapping and visual review, with no live MCP calls or CAD edits.

**Disposition: the principal r05 frame architecture differences have been corrected.** The saved r06 view shows a rounded lower lumbar opening, local shelves, short output bearing ears, and distinct transverse rectangular/slotted plates. The long E–D–H triangular webs are absent. Source and native XML preserve the intended fixed lumbar / moving E–D output ownership. No concrete remaining source-fidelity error identified here requires changing the S9 axes, the current H offsets, motor orientations, or leg branches. The candidate can proceed to revision-specific motion/clearance verification; it is not a dimensionally recovered replica or a fabrication-approved assembly.

## Evidence actually examined

- `src/spine_frame_r06.py`, `src/torso_frame_r06.py`, `parameters/assembly_r06.json`, and the integration path in `src/build_robot_r06.py`.
- Actual saved `reports/views/r06_spine_torso_frames.png`, compared with `/tmp/movie_s1_review_extra/52s.png`, `58s.png`, `/tmp/flexor_movie_s1_frames/60s.png` and `76s.png`. These are rendered source views with perspective and animation, not calibrated drawings.
- Read-only ZIP/XML inspection of `cad/flexor_r06_robot.FCStd`, SHA256 `812074066fa3803c865dea3ae7b537d0677246642141e042a9e39912af2a45e8`. Counted 464 App::Links and 80 PartDesign bodies; inspected actual source references, placements and PoseController.MotionMap.
- `reports/verification/r06_robot_neutral.json`: recorded PASS, 80 editable bodies, fully constrained sketches, 1129 narrowphase tests and no raw overlaps above `1e-5 mm³`. This is the lead's prescribed-pose runtime evidence; I read the report and did not independently rerun its Booleans.

## Source fidelity and ownership

| Item | r06 evidence and source comparison | Assessment |
|---|---|---|
| Fixed lumbar cradle | `CaseWindowBase` now combines a rounded lower outline/opening and separate upper rectangular window. Saved view visibly recovers the major 52 s silhouette. | Principal r05 rectangular-foot mismatch resolved. High confidence in feature type; chosen radii, window size and contour transitions remain assumptions. |
| Shelves and guide ears | Full central `HorizontalPlatform` is replaced by local end platforms; substantial axial shelves and C1/A2, C2/A1 guide profiles remain. | Consistent with 52/58 s fixed support arrangement. High confidence. Local platforms tie into the cradle instead of being unsupported decoration. |
| Output/end plate | Native `TransverseSlottedPlate` is an approximately YZ plate with outward ±X normals, short sagittal E/D ears and a slotted broad face. | Recovers the separate rectangular end-face structure visible at 60 s and almost edge-on at 76 s. High confidence in arrangement; source does not prove the exact plate angle, offset, width or thickness. |
| Output rigid body | Independent short E/D ears connect through the common plate; no E–H/D–H triangular carrier bars are generated. E/D bores remain normal to torso Y. | Correct separation of bearing ears from transverse plate. The plate can carry the rigid E–D output relation without an extra physical L6 rod. |
| Fore/hind case mounts | Fore vertical and hind horizontal panels/pans/straps replace the old four-cheek rail cages. | Appropriate distinct mounting architecture; detailed manufactured profiles are still candidate engineering geometry. The 52–76 s spine close-ups do not fully expose the final motor mounts. Motor envelope boxes must not be interpreted as structural walls. |

The saved native lumbar links reference `FRM_LUMBAR_ROUNDED_CRADLE_L/R_r06`, retain their previous placements (Y +28.4 / −26.8 mm), and have no MotionMap entry. They remain ground structure. `Torso_fore/hind` reference the new transverse frame sources and retain original E-based placements: `(33,16,0)` and `(-33,16,0)` mm, with source XY mapped into world XZ. Both retain `torso_r03` motion descriptors. Thus the plate/ears/case supports are part of each moving output body, not newly grounded surfaces.

Static MotionMap inspection retains bilateral O–G, G–B1/B2, A1–B1, A2–B2, B1–C1, B2–C2 and C1/C2–D1/D2 descriptors. No `Link*_L6_*` objects remain; E–D is supplied by the output rigid body. `spine_frame_r06` reads A/E coordinates and C tracks from the same spine solver, preserves the 30° case angle and link placements, and `torso_frame_r06` reads D–E and H from the existing geometry. This supports axis preservation by construction. It does **not** replace a native-cylinder/bore coaxiality measurement or motion check.

`build_robot_r06.integrate` regenerates the hind tendon mounts onto the new hind body using `body_override`; the old cheek-dependent mounts are not simply retained as references to a deleted source. Static review establishes the intended ownership, not strength or clearance over the cycle.

## Remaining deviations and actionable follow-up

1. **The end-plate opening pattern is generic.** Source 60 s shows elongated openings, small round holes and hooked/asymmetric details. r06 uses five straight capsule slots, with no claim of a recovered manufacturer pattern. If closer visual replication is required, model those feature types as separately labeled provisional profile details. Do not move E/D bearings or certify a supplier mounting pattern to match a rendering.

2. **The cradle is a simplified rounded construction.** Its disk-plus-rectangle outline, circular lower opening, straight upper window and sharp local shelf junctions reproduce the major arrangement but not every source transition, rounded corner or apparent rib. The visible r06 opening is appropriate; exact source blend curves and thickness cannot be inferred from 52 s. Further cosmetic/profile refinement is optional until a better drawing or matching view establishes a concrete discrepancy.

3. **Motor mounting panels, pans and top straps remain unmeasured design choices.** Their rectangular windows and broad pan extents in the saved view are not fully recovered from these spine frames. Retain explicit assumptions and review bare side/end views alongside later assembled source frames before describing them as a source-exact mount. Hind H-local −27 mm, fore +24 mm, plate X offsets −11.4/+12.4 mm and the 36 × 40 mm plate are not source measurements. There is no basis here for changing these datums merely to fit one perspective silhouette.

4. **Complete r06 runtime verification before carrying clearance claims forward.** Measure native E/D/H axes and guide locations, then run the sampled spine cycle with the intended fixed leg angles. Focus on the short D ears/plates versus moving C–D links and caps, and new pans/straps versus cases, springs and cable guides. Fresh-build equivalence and supplier interfaces need their own evidence. The earlier r05 sampled clearance results do not validate r06.

Seven motor count remains specified as two XL330-M077-T plus five XC330-M181-T. Both leg chains retain the accepted common directional zigzag and distinct fore/hind proportions. No corrective action in this review calls for changing either invariant.

## Verification limits

Checks actually performed: local source/JSON reads, saved PNG inspection, native XML source/placement/MotionMap/object-count inspection, and reading the neutral verification report. No new FreeCAD process, Boolean test, continuous collision check, native bore-axis measurement, strength calculation or fabrication review was run. Static ownership/profile findings support further development, not a motion pass. Supplier output/horn/mount datums, fits, retention, case preload and load capacity remain unresolved.
