# r15b symmetric-depth rocker — independent source review

**Scope:** bounded static review of `src/symmetric_rocker_r15b.py`, its parameters, the retained profile/pose helpers, the r15 saved XML, and `r15b_symmetric_rocker_source.md`. No FreeCAD, OCCT, Blender, native recompute, collision execution, or export validation was performed by this reviewer. Runtime gates remain the lead's responsibility. Repository AGENTS and docs 08/20 were read; only this review file is owned here.

**Disposition:** no concrete implementation blocker found in this source review. The construction is consistent with a centered single A eye/web and balanced B-only fork while preserving the established source frame and sagittal pivots. Acceptance remains conditional on native feature validity, source/instance checks, finite changed-pair clearance, and motion/export readback.

## Geometry and transforms

`organic_face()` retains A=(3,3), B=(L3+3,3), the 8 mm end outline and 6 mm waist. The blank spans the two retained B-cheek envelopes. The opposed reliefs use the same section about `mid`; their two equal-radius arcs have zero slope at both plateaus and matching tangents at their join. The reflected lower relief is algebraically symmetric, rather than a separately tuned profile. The A bore's outward extent, x=5.025 mm, precedes the ramp start x=7.1215 mm, so the whole A eye retains the centered 1.2 mm section under the current dimensions.

The section sketch rotates XY into source XZ at source Y=-2. Its normal is source -Y; the ordinary Pocket direction is consequently +Y. A 12 mm cut covers the organic outline's source-Y range -1…7 mm. Through bores start above the full depth envelope and cut through both cheeks. These are construction-direction checks from source, not runtime confirmation of the resulting solids.

`cad_common.plane_placement()` maps source +Z to world -Y for both sides using proper rotations. The retained 6×1.2 placement frame therefore requires exactly the side-dependent source offsets used in `build_section()`. The branch-1 web center is |Y|=34.2 mm, between B-cheek centers 32.4 and 36 mm; branch 2 is |Y|=33.3 mm, between 30.6 and 36 mm. The four rocker LinkPlacements and bore coordinates need no change. Sharing a single handed rocker source would be incorrect; the existing four distinct sources avoid that issue.

| Quantity, mm | Branch 1 | Branch 2 |
|---|---:|---:|
| Total depth envelope | 4.8 | 6.6 |
| Centered web/cheek thickness | 1.2 | 1.2 |
| B gap | 2.4 | 4.2 |
| Depth-ramp arc radius | 9.338889 | 6.600926 |
| Rounded slot-root radius | 1.2 | 2.1 |
| Maximum slot reach inward from B | 9.2 | 10.1 |
| Full-depth bridge before slot root | 2.8 | 1.9 |

The rounded slot starts its straight open zone 8 mm inward from B; its semicircular root extends farther inward by the gap radius. In particular, branch 2 reaches 10.1 mm, slightly beyond the prior source review's nominal 10 mm reach. This is an explicit consequence of the current gap, not a disconnected cheek or an inferred source measurement. The current ramp reaches full depth 12 mm inward, leaving a positive 1.9 mm full-depth bridge before that root. Neither this arithmetic nor the film establishes sufficient ligament strength.

## A stack, source ownership, and motion

The A-bearing and spacer arithmetic closes without nominal axial gaps: branch 1 inner spacer 28.2…33.6 mm, bearing 33.6…34.8 mm, outer spacer 34.8…38.0 mm; branch 2 inner spacer 28.2…32.7 mm, bearing 32.7…33.9 mm, outer spacer 33.9…38.0 mm. Negative-Y placements correctly mirror these ranges because `hardware_place()` places the source's axial midpoint at the supplied signed center. Bearing source length remains 1.2 mm; each spacer source's pad length is revised together with its placement.

The integration guards each revised spacer source's exact two-user set before changing it. Under this frozen baseline, revising the existing four unique sources is sufficient; the earlier recommendation to create new inner sources was intended to prevent collateral edits to shared definitions. No additional sources are needed once that sharing condition is disproved.

An initial possible MotionMap concern was checked and withdrawn. Static inspection of `cad/flexor_r15_robot.FCStd` confirmed all 12 moved A hardware links exist and are absent from its 409-entry MotionMap. `robot_pose_r03._plan()` first copies all current App::Link placements, then overrides mapped dynamic parts; `leg_motion_r07.descriptor()` delegates to that plan. Thus these grounded hardware placements survive pose replay, while the four dynamic rocker segment descriptors correctly remain unchanged. Adding point descriptors solely to encode the new A planes is unnecessary here. The lead should still confirm all 455 adapter placements against the saved candidate and retain explicit grounded-instance coverage.

The reviewed baseline SHA-256 is `56126360d99fc6019a0e95f0c0d036ebed607cc50c4a16333c6f9c70aa34b4c4`, matching the integration guard. Its saved XML contains 455 LinkPlacement-bearing instances. The integration report's candidate hash/count assertions are not independently established as runtime results by this review.

## Remaining acceptance limits

The wider transition occupies more of the retained B envelope along the web, so full-cycle affected-pair checks are necessary even though B cheek planes are unchanged. Include the four rockers, all users of the four resized spacer sources, the four moved bearings, and their adjacent frame/shaft/incident-link parts. Sampled clearance only supports the actual sampled poses and prescribed leg/wheel configuration.

Check the 0.2 mm axial overlap of the inner spacer's 28.2 mm start with the frame cheek's 28.4 mm end in actual section/clearance evidence. It may be permitted by the through-bore/recess, but stack arithmetic alone cannot prove that. Keep bearing-seat fit, race capture, thrust path, retention, shaft support, printed 1.2 mm sections, and fatigue/load capacity explicitly unqualified. The source evidence supports morphology, not these dimensions or fabrication readiness.

For native acceptance, require all final rocker features to be valid single solids with four fully constrained sketches each, mirrored depth sections about their declared midplanes, coaxial bores at the retained A/B coordinates, and preserved source/instance identities. Reopen/recompute and STEP/AX readback should use the saved r15b hash. The earlier source review, inherited r15 evidence, and this independent code review do not substitute for those gates.
