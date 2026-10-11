# Leg S6/S17–S19 anchor and actuator-layout audit

**Disposition:** correct the signs of O1 and A1 in both leg types, preserve the beyond-knee O3 lever and the named spring endpoints, and replace the collinear default O2 horn direction with an explicit noncollinear candidate. The source supports these directions and attachment roles, but not the frozen 6/9 mm offsets or exact ±60° lever angles. The proposed lower common-knee-servo location is a packaging assumption, not a dimension recovered from S6.

This is a bounded read-only source audit. Only this report was written in the repository. No live FreeCAD, CAD/schema changes, native validity, collision verification or fabrication approval was performed. Requested routing: inherited Sol/high; actual routing is not observable.

## Evidence inspected

- User S19 attachment `/tmp/codex-clipboard-04dec99d-3ad2-450b-8b43-120a04531677.png` and S6 attachment `/tmp/codex-clipboard-cd2f35b2-6c65-4cd3-9e53-e117e74f6d2d.png`, visually inspected.
- Original local supplement `2026_Unlocking fast robotic locomotor propulsion throughdynamic spine-leg synergy_sm.pdf`: PDF p27 Fig. S6; pp38–40 Figs. S17–S19; pp13–17 leg kinematics, cable routing and fabrication discussion. Existing full-page renders `sm-38.png`, `sm-39.png`, `sm-40.png` were inspected.
- Original Movie S2 at 16.5 s (labeled hind torso, hip servo, knee servo, wheel, cable and springs) and 26.5 s (fore torso, shoulder servo and springs), extracted to `/tmp/leg_anchor_movie_s2_16p5.png` and `/tmp/leg_anchor_movie_s2_26p5.png` and visually inspected.
- `src/leg_geometry_r02.py`, `src/build_leg_r02.py`, `src/build_torso_r03.py`, `parameters/assembly_r03.json`, `docs/03_leg_cable_spring_kinematics.md` and earlier `reports/source_review/leg_recovery.md`. Source files were read while the lead was correcting the model; findings identify the old expressions explicitly.

## Named anchor directions and ownership

Let H be hip/shoulder, K knee/elbow, A ankle, F foot contact; `e(q)=(cos(q),sin(q))` in project X/Z. The pictured S19 Oh/Ok correspond to H/K, and delta6 is at the distal ankle carrier near A. Source S17 has the same lower parallelogram framework on fore and hind legs, with different proportions.

| Point/member | Source observation | Correct candidate expression / ownership | Status |
|---|---|---|---|
| O1 | Proximal return-rail/compression seat lies from K **toward H** | `K - 6*e(qh)`; thigh local x=`a1-6` | Direction supported; 6 mm assumed |
| A1, second distal rail pivot | Lies from A in the same direction as K→H, opposite the long foot toe | `A - 6*e(qh)`; foot local x=`-6` | Direction supported; ideal equal offset assumed |
| F | Toe extends from A in the same broad direction as H→K | `A + a3*e(qh)` | Parallel-foot idealization; exact contour/contact assumed |
| O3 | Tension anchor is beyond K on the continuation opposite K→A | `K - 6*e(qh+qk)`; shank local x=`-6` | Direction and lever role supported; 6 mm assumed |
| O2 | Hip-side tension anchor is offset from H and visibly **not collinear** with H→K | `H + 9*e(u)` on a declared driven lever/horn-side body | 9 mm, lever angle and hidden keying assumed |
| Return rail | Joins offset proximal and distal pivots | O1–A1, parallel to K–A for the selected uncrossed parallelogram | Physical rail supported; exact parallelogram dimensions assumed |
| Tension spring k1 | O2–O3 | Preserve these named endpoints | Supported topology; eye offsets/rate/free length unknown |
| Compression spring k2 | O1-side seat to distal carrier at A | Preserve O1–A, not O1–A1 | Seat-to-pivot offsets remain assumed |
| Cable end | At delta6 distal carrier | Preserve A/declared near-A carrier attachment | Exact termination fitting unknown |

The old `O1=K+6*e(qh)` and `A1=A+6*e(qh)` place both auxiliary pivots on the wrong side while still closing an algebraic parallelogram. Closure alone therefore failed to detect the source discrepancy. Changing both to minus preserves `A1-O1 = A-K`, so the rail frame can retain angle `qh+qk`, and the selected dependent relation `qa=-qk` remains unchanged.

This also requires matching **native bores and outline** changes. The old thigh profile's pivots `(0,a1,a1+6)` must become `(0,a1,a1-6)` with an outline reaching H–K rather than an unnecessary distal extension. The old foot's +6 mm A1 bore/boss must move to −6 mm, with real material supporting that pivot behind A while the toe still extends +a3. Update attachment metadata and source identities along with the pure point formulas; moving only a rail instance or only a reported point would leave a physical mismatch.

## Horn sign and the unresolved rigid-body decision

S19A places H→O2 upward relative to the down-going H→K vector. S17A shows the corresponding fore spring lever angled away from the fore proximal segment. Thus defaulting `u=qh` is not a faithful neutral lever direction.

With the lead's selected project neutral seeds (`qh=-40°` hind and `qh=-130°` fore), `u=qh+60°` hind and `u=qh-60°` fore give coherent **provisional** side-view directions: hind u=+20°, fore u=−190° (equivalent +170°). These signs depend on the declared project frame. The S19 side image's rear-facing horizontal direction is opposite project +X, so copying image angle signs directly would be wrong. The exact ±60° offsets are not printed or calibrated source values. Mirroring left/right through Y should not reverse the X/Z lever sign; fore/hind differences are separate planar conventions.

A nonzero angle between O2 and H→K does **not** itself prove that horn and thigh rotate independently: a rigid bent proximal part has that geometry too. SI fabrication text says hip/shoulder actuators connect directly to legs; the paper also describes serial elastic behavior. The inspected stills/movie frames do not establish the hidden bearing/keying sufficiently to certify a separate motor-to-thigh passive coordinate. The prior recovery report already kept this conditional. Preserve that distinction: either declare a rigid driven proximal body with fixed `u-qh` offset, or explicitly retain a separate elastic-horn reconstruction and identify it as a design assumption pending rigid-part tracing. Do not label the existing additional proximal deflections source-verified merely because the angles are represented independently in code.

## Pure numerical impact check actually run

Using the old code's frozen lengths and neutral seeds, with the corrected minus offsets and candidate horn angles above:

| Leg | Old compression anchor length | Corrected compression anchor length | Old tension anchor length | Candidate tension anchor length |
|---|---:|---:|---:|---:|
| Hind |31.5993 mm|29.5548 mm|21.8558 mm|25.6114 mm|
| Fore |24.7386 mm|24.7386 mm|16.1555 mm|19.5824 mm|

The fore compression length happens to be unchanged at its 90° knee seed; that coincidence does not validate the old anchor sign. Corrected return-rail length residuals were below 8e-15 mm. With the existing two 3.6 mm seat offsets, candidate physical compression coil lengths are 22.3548 mm hind and 17.5386 mm fore. These are geometry calculations, not valid purchased-spring selections, force predictions or loaded equilibrium. Reevaluate free length, preload, coil-bind/travel and guide engagement over the selected pose range after correcting anchors. No supplier dimensions should be invented to force a pass.

Fore center distances 24/24/30 mm, hind 29/30/31 mm, the ±6 mm offsets, 9 mm horn lever and fore spring free lengths remain `DESIGN_ASSUMPTION`. The source reports the 90 mm hind segment sum and changed fore proportions, not these individual manufactured dimensions.

## S6 common knee-servo arrangement

S6A shows two fore actuators and three hind actuators, with the third hind servo centered between the two hip servos. Movie S2 confirms one knee servo carrying the winding wheel within the hind torso. S19B views the wheel face together with both hind legs; combined with Movie S2 this supports a wheel axis approximately along torso-local longitudinal X, distinct from the transverse Y hip axes. The sign and mounting datum are not dimensioned.

S19B places wheel center Oa approximately level with the horizontal delta4/delta5 cable run and hip region in that view. S6's center case appears offset relative to the two side cases, but the illustration does not define a signed XYZ case permutation or exact vertical position. Therefore a proposed wheel axle at torso E−27 mm, Z−17 mm, with a rolled knee-servo case occupying Z[−27,−7] and 34 mm across Y, is an explicit packaging candidate. It is not a source measurement or confirmed source-equivalent layout. A 90° roll can be useful for fitting a center motor between side cases, but collision avoidance alone cannot certify fidelity. Compare a matched rear/end view against S6/S19B and Movie S2; check actual motor output axis/datum, wheel-to-case attachment, both cable guides and case/frame clearance through torso motion. Do not derive hidden supplier mounting holes from the pictures.

Keep one common wheel command and two physical cable branches. The SI reports a 13 mm wheel OD and two direction changes per branch through shell guide and hip-center smooth screw; it does not establish an arbitrary relocated drum, exact pitch radius or a constant-radius take-up law for all angles. Moving the wheel invalidates old route lengths and guide tangencies, which must be regenerated from the chosen three-dimensional frame.

## Acceptance checks for the lead

1. Compare named native bore centers against the corrected point contract on all four legs; verify O1/A1 are toward the proximal side, O3 is beyond K, and all rail/horn/spring instances attach to those bores.
2. Use source-matched fore/hind side and hind end views to assess proportions, toe direction, distinct O2 lever angles and central servo/wheel layout. Keep unreported center distances, exact angles and lowered-wheel deviations explicit.
3. Check four-bar closure, springs/guide travel, cable routing and native swept clearance after the correction; do not reuse prior neutral spring or cable acceptance evidence unchanged.
4. Resolve or explicitly retain the conditional horn/thigh rigid-body assumption before making mobility or source-certified actuation claims. Keep supplier output/keying and attachment strengths unresolved until supported by actual drawings/checks.
