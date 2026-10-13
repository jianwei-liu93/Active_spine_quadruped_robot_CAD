# r14 — compact center frame and clearance-corrected organic rocker

2026-10-14. Source-facing CAD refinement follows the user's successive close-up corrections. This is a research CAD candidate, not an exact recovered drawing set or fabrication release. Drawings/manual and new Blender rendering remain deferred.

## Source interpretation and superseded trials

Movie S1 at 54–55 s isolates the short A–B rocker before the independent B–C and G–B members arrive. The latest user crop resolves the desired construction: **B-end fork only, A-end single eye**, with a smooth contoured web. The rejected r11 long staggered cheeks and r12 two-ended trial are preserved as historical native checkpoints. Earlier review language suggesting two forks is explicitly superseded by this user instruction. See the [source review](../reports/reviews/r12/source_part_ownership_and_shapes.md) and original extracted frames in `references/visual/r11_movie_s1/`.

The r14 assembly reuses corrected component factories named r12. Assembly and component revisions are distinct; these names do not imply that the saved rejected r12 trial was overwritten. A separate native assembly is built from the SHA-verified saved r10 checkpoint through the installed FreeCAD MCP, executing the changed component factories and preserving earlier saved models and animations. A full historical source rebuild stalled at r04 in this runtime; it was stopped after recovery data preservation. Full historical rebuild reproduction remains incomplete.

## Actual changes

| Feature | Reconstruction |
|---|---|
| Center frame transverse span | 82.0 → 78.8 mm (3.2 mm / 3.9% reduction); guide centers 40.2 → 38.6 mm per side |
| Case housing transverse span | 56.8 mm retained around the two 26 mm-deep XL330 envelopes; no motor rescaling |
| Full A/C cap span | 87.2 → 84.0 mm; shaft lengths 85.6 → 82.4 mm with coordinated clips, liners, rollers and spacers |
| Housing sagittal width | Original 28 mm retained to preserve controller-mount clearances; requested transverse reduction is independent |
| Ground frame | One native connected body with orthogonal windows, low shelves, guide ears and central E crossmembers/lugs; inherited outer E tubes removed |
| E output support | Existing central bearing/clevis system exclusively owns E; retire 32 obsolete outer E hardware instances and replace lateral E ears with plate-connected stubs |
| D output support | Retire four unsupported L6-era bearings and four adjacent spacers; shorten pins to 24 mm and outer clips to 37.1 mm absolute Y |
| A–B rocker | Four handed native one-piece bodies; 8 mm round eyes, 6 mm waist, tangent circular side arcs, continuous web and B-only compact fork |
| Fork detail | 1.2 mm leaves, 8 mm opening depth, 10 mm maximum inward reach; rounded added-leaf root; eight separate B bearing/spacer instances |
| B–C member | Broad native bar with rounded blind recess retaining 0.6 mm floor; bores cut separately |
| Fore/hind mounting frames | Rounded panel/window outlines, open 2 mm pan rails and compact old-E stubs; retain distinct motor arrangements, D/H, central clevis and knee/cable owners |

These metric sections, clearances, materials, bearing and retention arrangements are **DESIGN_ASSUMPTION**. They are not dimensions measured from video pixels. Published motor envelopes stay unchanged. The whole-robot width is governed by the leg/cable assemblies; 78.8 mm is the ground-frame span only.

The central-E-only load path is intentional: ground shelf/crossmember → central lug/bearings → pin/clevis → torso plate. L5 drives the retained D journal and torso ears. Removing the supplementary outer E supports concentrates loads at the central lug; shaft bending, bearing reactions and frame/clevis stiffness remain unresolved. See the [independent stack review](../reports/reviews/r12/transverse_width_stack_review.md).

## Identity, kinematics and animation

The candidate has 455 physical instances: 487 r10 instances minus 40 explicitly retired legacy parts plus 8 B-fork bearing/spacer instances. Every surviving physical instance keeps its stable ID. There are no new planar linkage edges, pivots, motors or commanded coordinates. The S9 branch solver and one-phase/two-motor spine coupling remain the source of motion, with seven physical motors, six commands and separate prescribed/passive knee coordinates. Springs and cables retain anchor/route-dependent regeneration.

The source-local ground frame remains `(X,Y,Z)=(worldX,worldZ,28.4-worldY)`. Bars retain the legacy 6×1.2 placement frame and first bore (3,3); their changed physical outline must never be substituted into the pose-frame origin calculation. New B fork hardware uses the existing B point. A/C/D stack changes update the actual MotionMap axial coordinates. AX0/AX1 must consume the native geometry and transforms, not define another mechanism.

## Verification record

The following results were actually executed against native SHA `7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87`:

| Gate | Result and evidence |
|---|---|
| Installed MCP construction | PASS — saved separate r14 from verified r10 plus executed changed factories; [integration](../reports/verification/r14_integration.json) |
| Physical/source identity | PASS — 455 physical instances, 378 unaffected instances strictly unchanged including actual motor solids; 69 changed existing and 8 new; [identity](../reports/verification/r14_identity.json) |
| Local sections and S9 axes | PASS — one-ended forks, tangent organic contours, frame/stack sections and actual neutral cylindrical axes; maximum axis error 7.46e-14 mm; [probes](../reports/verification/r14_sections_s9.json) |
| Native recompute/editability | PASS — disposable saved-file reopen/forced recompute of all 455 instances and three parameter edit-and-restore probes; [native checks](../reports/verification/r14_native_checks.json) |
| STEP assembly exchange | PASS — 455 valid closed solids matched one-to-one; per-solid bounds tolerance 1e-5 mm and adaptive volume tolerance 1e-6 relative including numerical margin; [round trip](../reports/verification/r14_assembly_export.json) |
| AX0/AX1 | PASS — 455 individually mapped instances, 108 source definitions, neutral plus two non-neutral poses, proper rotations, mm conventions and source-to-world transforms; maximum vertex reprojection error 9.78e-14 mm; [report](../reports/animation/ax01_r14.json), [versioned pose manifest](../animation/motion/ax01_r14.json) |
| Source-facing visual review | Lead reviewed actual isolated/assembled views against extracted Movie S1 frames and latest user crop; qualitative morphology with explicit limits, not dimensional identity; [view manifest](../reports/views/r14_reference_capture_manifest.json) |
| Affected finite-motion screen | RUNNING — 91 inclusive phases at 4-degree intervals, neutral legs/wheel; final acceptance requires the complete merged report in `reports/verification/r14_motion_91.json` |

The first native edit probe exposed inconsistent display triangulation in bounding-box comparisons. Copying **both** comparison operands without their display meshes resolves it while retaining the strict geometric gates; [initial failure](../reports/verification/r14_native_checks_initial_bbox_failure.json) and [BRep diagnostic](../reports/verification/r14_native_bounds_diagnostic.json) are preserved. The first STEP wrapper omitted the established explicit-pcurve export setting and failed a spring volume comparison. Applying the same `write.surfacecurve.mode=1` prerequisite as the r07 exporter passes with unchanged source solids and tolerances; [initial STEP failure](../reports/verification/r14_assembly_export_initial_failure.json) remains recorded.

The animation interface uses the existing read-only adapter, current MotionMap and kinematic APIs. Six commanded coordinates and four separately prescribed knees remain explicit; ten deforming spring/cable instances use procedural anchor/route metadata and shape regeneration. Loaded passive response is not solved. Native geometry is not flattened or altered for Blender. New r14 meshes, a Blender scene/import and updated videos remain separate future work; existing r10 videos depict r10 geometry.

Runtime evidence pins the native and relevant source/parameter hashes. The finite screen addresses the affected pairs only and does not qualify continuous clearance, all coordinated leg states, loaded cable behavior, strength or fabrication fits. Older r10/r11 clearance reports do not certify changed r14 shapes. Full historical source rebuild reproduction remains incomplete as stated above.

## Review findings and metadata precedence

The independent final evidence review confirmed the selected 78.8 mm frame and 8 mm opening / 10 mm reach across all four B-only forks, and checked actual native, STEP and AX hashes. Two findings remain explicit:

- `central_attachment_r10.outer_E_supports` is **superseded historical metadata** inherited for the earlier build stage. The final `center_frame_r12.E_support_ownership` and executed compact-stack migration define the r14 central-E-only support system. The old text is not a second current load path. Frozen configuration/native bytes are preserved during verification; a later controlled metadata cleanup must retain this precedence and re-pin dependent evidence.
- The B–C bearing spans absolute Y 33.6–34.8 mm and the outer fork bearing spans 35.4–36.6 mm. The 0.6 mm axial gap has no intermediate spacer. An intentional axial-float/race-capture and thrust/retention decision is required before fabrication; absence of an interference is not a fit qualification.

Outstanding fabrication blockers remain: exact supplier mounting/output datums, bearing fits/retention/thrust, clip/groove standards, strength/fatigue, central support stiffness, insertion/tool access and physical cable/spring characterization. Existing r10 videos depict r10 geometry and remain clearly versioned. Regenerating Blender assets and videos from the accepted newer CAD is a separate task.


## Clearance correction from the r13 trial

The original 3.5 mm opening intersected the radius4 mm B–C eye. Independent planar analysis across 361 phases also found branch2 G–B clearance controls the opening: minimum mathematical tangency occurs near 5.75 mm. The chosen 8 mm opening / 10 mm rounded-root reach has nominal planar separation 4.0 mm to B–C and 1.977 mm to branch2 G–B; actual three-dimensional CAD screening is required separately. It remains forked only at B, with a single A eye and smooth 6 mm waist. Restoring the 28 mm sagittal housing avoids the four actual controller clamp-bolt intersections caused by the unrequested inward wall shift. These corrections preserve all S9 axes and the requested transverse narrowing.
