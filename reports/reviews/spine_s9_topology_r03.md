# Independent Fig. S9 topology audit — r03

**Conclusion:** the pre-existing r02 spine moving graph matches SI Fig. S9. No nonmatching moving rod was identified. In r03 the rigid torso cheek must replace each E–D output rocker rather than coexist as another independently pinned E–D link. The saved r03 snapshot inspected here already implements that replacement: there are no instantiated `Link*_L6_*` bars. This supports continued dependent body development, subject to the lead's native joint-axis, gap and interference checks.

Scope: read-only source/static-native audit, with only this report written. No live FreeCAD, CAD mutation or verification of `spine_attachments_r02.py` was performed. Requested reviewer routing was inherited Sol/high; actual model routing is not observable.

## Evidence inspected

- User attachment `/tmp/codex-clipboard-1f81d810-c3cb-495a-aff3-3c1e0c49f881.png` and full rendered SI Fig. S9 at `/tmp/spine-source-review/sm-30.png`, inspected as images.
- Local SI PDF `2026_Unlocking fast robotic locomotor propulsion throughdynamic spine-leg synergy_sm.pdf`: PDF page 7, “Mathematical modeling of the spinal mechanism / Kinematics”; PDF page 30, full Fig. S9 and caption. Page 7 explicitly enumerates the rods, identifies C1/C2 as sliders on fixed tracks, and identifies E1/E2 as fixed output pivots. The caption identifies transparent rods as alternate maximum flexion/extension poses.
- `src/build_flexor.py`, `src/refine_flexor.py`, `src/kinematics.py`, `src/build_torso_r03.py`, `parameters/candidate_r02.json`.
- ZIP `Document.xml` in saved `cad/flexor_r03_robot.FCStd`, read without FreeCAD. Snapshot SHA256 `9f28142cf0a4d78282d91e2d7b9348d2ce6de02d9d998ccc4bce409d24e85131`, 1,048,734 bytes, read at 2026-10-11 23:05:12 UTC. The lead was actively integrating; conclusions refer to this exact snapshot.

## Moving-link correspondence

`G` in the CAD corresponds to `G0` in S9. CAD planar coordinates are X/Z; source diagram coordinates are X/Y. Shaft axes are CAD Y. Shared r02 dimensions reuse the same L2–L6 names on both branches, whereas the SI names the second branch L7–L11.

| S9 physical member | SI length | CAD segment / implementation |
|---|---|---|
| O–G0 | L1 | `DirectCrank_1`, `DirectCrank1`: O–G |
| G0–B1 | L2 | `Link1_L2__1`, `Link1_L2_1` |
| G0–B2 | L7 (=L2) | `Link2_L2__1`, `Link2_L2_1` |
| A1–B1 | L3 | `Link1_L3__1`, `Link1_L3_1` |
| A2–B2 | L8 (=L3) | `Link2_L3__1`, `Link2_L3_1` |
| B1–C1 | L4 | `Link1_L4__1`, `Link1_L4_1` |
| B2–C2 | L9 (=L4) | `Link2_L4__1`, `Link2_L4_1` |
| C1–D1 | L5 | `Link1_L5__1`, `Link1_L5_1` |
| C2–D2 | L10 (=L5) | `Link2_L5__1`, `Link2_L5_1` |
| E1–D1 | L6 | r02 separate L6 bars; r03 `Torso_hind` rigid cheek pair |
| E2–D2 | L11 (=L6) | r02 separate L6 bars; r03 `Torso_fore` rigid cheek pair |

Before torso substitution there are 11 moving rod members per planar mechanism, including the shared input crank, plus two slider bodies. In the inspected r03 XML there are 18 `segment` MotionMap entries: nine remaining members in each Y-side copy. `Torso_hind` and `Torso_fore` each link to a monolithic cage containing both cheeks, replacing the four separate bilateral output bars. These are physical instance counts, not extra kinematic coordinates.

The E1–A1–E2–A2 bars belong to the single fixed `LumbarIntegrated` ground body. S9 depicts separated ground symbols at its fixed pivots; it does not require a disconnected physical ground frame. The tall C1/A2 and C2/A1 guide ears also belong to ground. They are not moving A–C rods. Removing these structural frame members merely because they are absent as bars in the kinematic diagram would remove support while leaving the abstract graph unchanged.

Likewise, black C1–D1 and C2–D2 are genuine short moving links, even when partly hidden by slider blocks. Gray transparent poses in panel A must not be instantiated as additional rods. Bilateral copies and shaft synchronization are spatial construction of the same mechanism; the SI's construction discussion also describes left/right synchronization shafts. They do not supply another commanded spine phase.

## Torso substitution

`build_torso_r03.build_torso()` creates a rigid E–D–H cheek with the neutral D coordinate measured from E. Its pose contract uses `beta(theta) - beta(0)`. Therefore the cheek's E–D vector is the same output rocker as S9, while E–H and D–H are rigid load-carrying structure on that output body. H is a future hip/shoulder coordinate on the output frame, not another spine joint connected to lumbar ground.

The source now removes `Link1_L6_*` for the hind cage and `Link2_L6_*` for the fore cage, including their MotionMap entries. The inspected native XML agrees: no App::Link instantiates `SPN_r02_L6`, and no separate physical L6 bar remains. Its unused native library Body and profile/pad/pocket features remain saved. They are not extra moving instances; remove that unused definition during normal final package cleanup to avoid BOM/export ambiguity.

The substitution is topologically correct only while the cage pivots at fixed E and its D bore follows the C–D link endpoint, with a common physical joint axis and suitable axial support. This audit verifies source coordinates and declared motion, not native bore-axis coincidence or shaft load paths. Those checks remain with the lead's actual-native report.

## Degree of freedom and numerical checks actually run

For one ideal planar mechanism: 11 moving rods + 2 sliders + ground gives N=14 bodies. Equivalent revolute pair count is 17: O(1), G(2), A1/A2(2), B1/B2(4), C1/C2(4), D1/D2(2), E1/E2(2). There are two prismatic slider-to-ground pairs. Thus the planar mobility count is `3*(14-1) - 2*(17+2) = 1`. Ternary pin joints count as two equivalent lower pairs. Replacing E–D rods by rigid torso output bodies does not change that count. Prescribing the crank phase removes the remaining coordinate.

A pure-Python 721-pose check at 0.5° spacing over 0–360° used the current r02 parameters and actual `kinematics.spine()` closure. The reduced coordinates were theta, B1/B2 X/Z, C1/C2 X and D1/D2 X/Z (11 coordinates). Ten rod-length constraints gave finite-difference Jacobian rank 10 at every sample; fixing theta also gave rank 10 in the resulting 10×10 Jacobian. Central difference step was 1e-5, elimination threshold 1e-8, and minimum retained pivot 0.001246. Maximum link-length residual was 1.42e-14 mm. Independently rotating each neutral torso E–D vector by beta−beta0 reproduced D within 8.88e-15 mm.

These checks support one local mechanism coordinate throughout sampled poses and the intended rigid torso replacement. They do not establish continuous nonsingularity, structural stiffness, fit, interference-free native motion or that a scripted animation is a solved FreeCAD joint assembly. FreeCAD was not imported. An initial NumPy attempt could not run because NumPy was absent in the default Python; the reported rank check used pure-Python pivoted elimination instead.

## Concrete disposition

- **No link deletion is warranted for G–B, A–B, B–C or C–D.** All match S9 and its accompanying text.
- **Keep the r03 E–D torso replacement and keep separate physical L6 bars removed.** This change is present in the inspected native snapshot and source. Do not remove the E/D pivots, C–D rods or kinematic L6 dimension.
- **Keep fixed frame/guide support identified as ground.** Distinguish fixed-frame geometry, bilateral copies and alternate source poses when explaining an apparently crowded view.
- **Clean up the uninstantiated L6 library definition at final packaging.** This is a minor inventory ambiguity, not a mobility defect.
- **Require native axis/gap and collision evidence separately.** No claim is made here about supplier horn interfaces, frame attachment strength, the new attachment module, or complete robot acceptance.
