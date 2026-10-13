# r13 — compact center frame and single-ended organic rocker

**Superseded trial: actual neutral interference FAIL.** The3.5 mm fork opening intersected the B–C eye on all four rockers, and the additional24 mm sagittal housing-width change intersected four controller clamp bolts. See `reports/verification/r13_motion_91.json` (one fully evaluated neutral state, stopped on failure) and the isolated local joint probe. R14 retains the requested78.8 mm transverse span, restores the original28 mm sagittal housing and uses a deeper B-only fork. The r13 native and its actual reports remain preserved.

2026-10-13. Source-facing CAD refinement follows the user's successive close-up corrections. This is a research CAD candidate, not an exact recovered drawing set or fabrication release. Drawings/manual and new Blender rendering remain deferred.

## Source interpretation and superseded trials

Movie S1 at 54–55 s isolates the short A–B rocker before the independent B–C and G–B members arrive. The latest user crop resolves the desired construction: **B-end fork only, A-end single eye**, with a smooth contoured web. The rejected r11 long staggered cheeks and r12 two-ended trial are preserved as historical native checkpoints. Earlier review language suggesting two forks is explicitly superseded by this user instruction. See the [source review](../reports/reviews/r12/source_part_ownership_and_shapes.md) and original extracted frames in `references/visual/r11_movie_s1/`.

The r13 assembly reuses corrected component factories named r12. Assembly and component revisions are distinct; these names do not imply that the saved rejected r12 trial was overwritten. A separate native assembly is built from the SHA-verified saved r10 checkpoint through the installed FreeCAD MCP, executing the changed component factories and preserving earlier saved models and animations. A full historical source rebuild stalled at r04 in this runtime; it was stopped after recovery data preservation. Full historical rebuild reproduction remains incomplete.

## Actual changes

| Feature | Reconstruction |
|---|---|
| Center frame transverse span | 82.0 → 78.8 mm (3.2 mm / 3.9% reduction); guide centers 40.2 → 38.6 mm per side |
| Case housing transverse span | 56.8 mm retained around the two 26 mm-deep XL330 envelopes; no motor rescaling |
| Full A/C cap span | 87.2 → 84.0 mm; shaft lengths 85.6 → 82.4 mm with coordinated clips, liners, rollers and spacers |
| Housing sagittal width | 28 → 24 mm; 1.6 mm crosswalls leave 0.4 mm nominal lateral clearance about the unchanged 20 mm motor face |
| Ground frame | One native connected body with orthogonal windows, low shelves, guide ears and central E crossmembers/lugs; inherited outer E tubes removed |
| E output support | Existing central bearing/clevis system exclusively owns E; retire 32 obsolete outer E hardware instances and replace lateral E ears with plate-connected stubs |
| D output support | Retire four unsupported L6-era bearings and four adjacent spacers; shorten pins to24 mm and outer clips to37.1 mm absolute Y |
| A–B rocker | Four handed native one-piece bodies; 8 mm round eyes, 6 mm waist, tangent circular side arcs, continuous web and B-only compact fork |
| Fork detail | 1.2 mm leaves, 3.5 mm opening depth, 5.5 mm maximum inward reach; rounded added-leaf root; eight separate B bearing/spacer instances |
| B–C member | Broad native bar with rounded blind recess retaining0.6 mm floor; bores cut separately |
| Fore/hind mounting frames | Rounded panel/window outlines, open2 mm pan rails and compact old-E stubs; retain distinct motor arrangements, D/H, central clevis and knee/cable owners |

These metric sections, clearances, materials, bearing and retention arrangements are **DESIGN_ASSUMPTION**. They are not dimensions measured from video pixels. Published motor envelopes stay unchanged. The whole-robot width is governed by the leg/cable assemblies;78.8 mm is the ground-frame span only.

The central-E-only load path is intentional: ground shelf/crossmember → central lug/bearings → pin/clevis → torso plate. L5 drives the retained D journal and torso ears. Removing the supplementary outer E supports concentrates loads at the central lug; shaft bending, bearing reactions and frame/clevis stiffness remain unresolved. See the [independent stack review](../reports/reviews/r12/transverse_width_stack_review.md).

## Identity, kinematics and animation

The candidate has455 physical instances:487 r10 instances minus40 explicitly retired legacy parts plus8 B-fork bearing/spacer instances. Every surviving physical instance keeps its stable ID. There are no new planar linkage edges, pivots, motors or commanded coordinates. The S9 branch solver and one-phase/two-motor spine coupling remain the source of motion, with seven physical motors, six commands and separate prescribed/passive knee coordinates. Springs and cables retain anchor/route-dependent regeneration.

The source-local ground frame remains `(X,Y,Z)=(worldX,worldZ,28.4-worldY)`. Bars retain the legacy6×1.2 placement frame and first bore(3,3); their changed physical outline must never be substituted into the pose-frame origin calculation. New B fork hardware uses the existing B point. A/C/D stack changes update the actual MotionMap axial coordinates. AX0/AX1 must consume the native geometry and transforms, not define another mechanism.

## Verification record

Initial actual r13 native/source identity, local section/organic tangency and neutral S9-axis checks passed. The identity comparison proves378 unaffected instances strictly unchanged, including the motor envelopes. All77 affected/new instances receive separate checks. Motion and final packaging results are recorded only when the corresponding report completes.

Runtime evidence and final source/native hashes are recorded in `reports/verification/r13_*`, `reports/views/r13_*` and the animation manifest. Planned verification is not a PASS. The finite changed-pair screen covers the actual affected pairs over a documented spine-cycle sample; it does not qualify continuous clearance, loaded cable behavior, strength or fabrication fits. Older r10/r11 clearance reports do not certify changed r13 shapes.

Outstanding fabrication blockers remain: exact supplier mounting/output datums, bearing fits/retention/thrust, clip/groove standards, strength/fatigue, central support stiffness, insertion/tool access and physical cable/spring characterization. Existing r10 videos depict r10 geometry and remain clearly versioned. Regenerating Blender assets and videos from the accepted newer CAD is a separate task.
