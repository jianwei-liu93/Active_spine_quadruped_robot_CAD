# r07 positive cable clamps — native module handoff

All dimensions/materials/processes are **DESIGN_ASSUMPTION**. Source: `src/cable_clamps_r07.py`. No live MCP or canonical CAD writes were made by this worker. Isolated tests open r06 and discard every native modification without saving. The worker inherited routing; requested Sol/medium was not independently verified.

## Frozen ankle geometry

Existing `HindTendon_L/R_AnkleEye` links are retained and relinked to distinct mirrored native OD6/ID2.05/T2.4 steel swivel definitions. Physical axial bounds are absY56.4..58.8; cable plane absY57. Radial Ø.4 blind hole runs R3→1.8. Cable ends at R2.1. Outboard M1.4 minorØ1.1 tap intersects the cable; separate flat-tip Ø1.1 minor-core grub starts at absY57.15 and ends58.8, L1.65, with native .6AF socket. Nominal M1.4 thread metadata is explicit; helical thread crests are omitted.

Journal bounds absY44.75..59.8, L15.05, center52.275; outer clip center59.2/T.6. Existing inner clips and spacer are retained without modification. Mirrored journal definitions use source groove-pocket upperZ L(.9,14.85) and R(.8,14.75), width.6, putting clip grooves exactly at absolute centers45.25/59.2 under the existing source+Z→world−Y convention. Using the original journal helper unchanged would misalign the new outer groove by .1mm.

## Frozen wheel terminal adaptation

Drum OD13, D bore and two existing groove dimensions remain. New wheel native source reconstructs its holes, keys and lead-in pockets; obsolete old-angle anchor holes are absent.

Both steel blocks are mounted on the outboard −X axial face, preserving the motor placement. Each steel block has main clamp at radial4.6..6.4 and tangential±1.1; an integral flange extends inward to3.3 for the physical anchor bolt. Axial thickness1.4 starts adjacent to the outboard drum face; both keys and bolt pockets are on this face. Integral key r3.8..4.8/t±.45 protrudes .5 into its matching wheel pocket. A separate M1 Ø.75-core/L2.2 bolt, Ø1.6 head/T.5 with .6AF socket, passes the block's Ø.8 bore into the wheel. M1 thread crests are omitted. Each separate transverse M1.4 minor-core grub has Ø1.1/L.95, flat tip tangent to the cable and .6AF socket. Aligned axial cable passages are Ø.4. Face lead-in reliefs permit the real bend, with all geometry represented by native Pads/Pockets.

Both full through-wheel axial cable bores are Ø.4, at the new angular/radial datums. The positive-groove branch tail passes through its bore across the negative groove plane to its own positive groove. A real R.3 quarter-circle cable bend connects the axial terminal to the original groove contact and its clockwise tangent. Let original captured neutral groove-contact angle be θ, R=5.5, ρ=.3:

- axial-hole/tail phase θ+δ, where δ=atan(ρ/R);
- axial-hole/tail radius sqrt(R²+ρ²);
- the quarter bend ends at exact original contact θ; both bends use outward normal−X, and at wheel phase u, all terminal geometry rotates by u and the existing wheel-wrap primitive still begins at θ+u.

This explicit offset was approved by the lead. It avoids a neutral-only tangent patch and preserves the captured original phase as the groove-contact reference. The .3 centerline bend is extremely tight for Ø.3 wire; strength, fatigue and permissible cable bend radius are unverified.

## Integration contract

Run `cable_clamps_r07.apply(b)` after the existing r06 integration and before lead finalization. It requires existing neutral r05/r06 eye/cable/wheel links and captured local routes. It preserves every existing physical App::Link name, replaces only source links/placements where required, and adds eight links: L/R `AnkleGrub`, `WheelClamp`, `WheelAnchorBolt`, `WheelClampGrub`. It updates `b.motion` route captures and hardware placements. The lead must serialize `b.motion` to PoseController.MotionMap during finalization and save through MCP. Source rebuild must call the same apply stage after r06 construction.

For every subsequent dynamic cable source request, call `terminated_route(baseline_route)` before `build_tendon_r03.cable_shape`. The helper is idempotent using `r07_positive_terminals`, preserves existing wrapped primitives, and enforces ankle radius2.1. All new rigid hardware descriptors retain kind `torso_r04_rigid`, `wheel_angle_rad=0`, `local_placement_json`, side and component. Wheel terminal components additionally capture `wheel_center`: rotate BOTH the captured base about this center and orientation around torso+X by u. Ankle eye/grub placement follows the ankle and incoming cable direction; preserve mirrored captured axial Y and source rotations. The motion worker has incorporated this contract.

## Executed isolated evidence

`reports/tmp/export_repair_r07/clamp_probe.py` / `.json` applies the module to a private opened r06 document. Existing `cad_common.metadata/instance` assume GUI ViewObjects, so the CLI reproducer substitutes test-only equivalents that preserve identities/links and omit GUI colors. Shared source files were not modified.

All nine new native PartDesign body definitions are valid one-solid shapes, and every constituent sketch reports `FullyConstrained=True`. Both cable source rebuilds are valid one-solid wire sweeps.

At neutral for both sides:

- cable-to-ankle-grub exact minimum distance0; cable/eye, cable/grub and eye/grub common volumes0;
- cable-to-wheel-grub distances ≤5.56e-16mm; cable/block, cable/wheel, cable/wheel-grub and block/wheel common volumes0.

Native full continuous cable sweeps for both sides at wheel0°,45°,90° are valid one-solid shapes and every consecutive primitive endpoint joins with error0. These are finite samples, not full interval collision certification.

Additional pose/contact/packaging checks are recorded separately in `clamp_clearance.py` / `.json`. The final outboard-only candidate replaces the failed two-face attempt described below. No complete package or fabrication pass is claimed.

## Executed two-face attempt and rejected packaging

`clamp_clearance.json` completed native Boolean/distance checks at wheel0°,45°,90°. At all six branch/pose samples, cable/block common volume0 and passage clearance≈.04999995mm; cable/grub common volume0 with tip-contact distance≤5.56e-16mm; cable/anchor-bolt common volume0 and clearance≈.69878mm; cable/wheel common volume0. At45°/90° the wound cable contacts its groove (distance0); neutral cable minimum distance≈.01211mm after the intentional lead-in relief.

Both journal/inner-clip and journal/outer-clip pairs have zero common volume and seat contact distance≤1.43e-14mm. Both swivel-to-journal clearances≈.075mm, eye-to-outer-clip gaps≈.1mm, with zero common volumes.

**The original two-face attempt failed against the existing motor envelope and was rejected.** At all three wheel poses, the +face left-branch block intersects `HindTendon_KneeMotor` by6.368095075mm³, its anchor bolt by1.441922666mm³ and transverse grub by.7469306161mm³. There are no terminal-to-opposite-terminal or terminal-to-drive-coupling positive common volumes in these checked pairs. The bolt head reaches W+3.1 while the current motor face starts W+1.4. These are real native overlaps; they are not an allowable contact exception. The lead chose both terminals on the outboard−X face. Possible alternatives: move motor face outward≥1.8mm (and revise adapter/mount), or place both positive terminal blocks on the outboard−X face and extend the positive-groove branch axial tail. The final source implements the approved outboard-only alternative; failed evidence is preserved in `clamp_clearance_twoface_FAILED.json`.

## Final outboard-only native checks

The lead-approved final design puts both clamp blocks on the −X face. Actual `clamp_clearance.json` native tests at0°,45°,90° all complete with valid one-solid cable shapes and no positive material common volume between cable and wheel/block/bolt/grub, between the terminal hardware assemblies, or between either terminal and the drive coupling/motor envelope. Grub contact distances remain ≤1.17e-15mm. The positive-groove tail passes through its explicit Ø.4 through-wheel bore and across the negative groove plane without intersecting the wheel. Both cables clear the D adapter by4.4mm (all three poses, common volume0). Branch-to-branch cable distances are10.4049200mm at0°,7.60591321mm at45°,3.39755509mm at90°, with common volume0.

All nine new native body definitions remain valid single solids and every native sketch is fully constrained. apply() retains all464 original physical links and adds exactly8 links. It returns explicit original/contact and offset/axial anchor angles, bend radius.3, tail radius5.50817574157, phase offset0.0544914562407rad, outward axis−X, and wheel bore diameter.4mm.

`python -m py_compile src/cable_clamps_r07.py` passes. The performed checks establish the specified sample geometry and local packaging; full assembly sampled motion/interference, STEP/STL package validation, structural strength, fastener torque, cable wear and fabrication release remain lead tasks or unresolved engineering validation.
