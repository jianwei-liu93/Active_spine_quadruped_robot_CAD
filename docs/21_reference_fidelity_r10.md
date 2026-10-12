# r10 source-fidelity update: central E attachment, torso plates, and long links

**Status: INTEGRATED r10 CANDIDATE / PACKAGE VERIFICATION PENDING.** The saved, reopened, recomputed native candidate is `cad/flexor_r10_robot.FCStd`, SHA-256 `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`. It contains a central frame beam/lug, moving torso clevises, revised slotted torso plates, and a relieved long B–C link profile. Metric dimensions are reconstruction or engineering assumptions. The initial cached-valid long-bar Pocket failed when recomputed; the lead repaired its boundary sketch with an explicit eight-edge profile. Initial AX and broad pass-scope evidence from before that repair remains archived as diagnostic evidence. Refreshed native, topology, actuator, leg-axis, AX0/AX1, and source-reproduction checks now bind to the stated SHA. Changed-material clearance and full package acceptance remain pending.

This document records source interpretation and the current editable implementation. It does not establish final collision clearance, supplier fit, structural capacity, or fabrication readiness. It does not authorize copying the red schematic into physical parts.

## Source observations and limits

The primary visual evidence is the retained [Movie S1 frame set](../references/visual/movie_s1_attachment/), with decode provenance in its [provenance record](../references/visual/movie_s1_attachment/provenance.json). The source movie SHA-256 is `16b180fa5da669e78e7d2038147e1f09fd8adbb2265341d8c3a14d0093a235a9`; retained frame filenames identify requested seek times and decode 0.1001 s later.

- [51 s](../references/visual/movie_s1_attachment/s1_51.0s.png) shows the red skeletal illustration through the assembled robot. It is schematic anatomy/kinematic explanation; its rods, caps, arrows, colors, and apparent part count are not evidence of physical red components.
- [54 s](../references/visual/movie_s1_attachment/s1_54.0s.png) and [56 s](../references/visual/movie_s1_attachment/s1_56.0s.png) show short broad plain links and longer white linkage members in the assembly sequence. These frames support different short/long link profile families and a broader relief on at least one long member. Oblique overlap does not uniquely assign every visible edge or split end to a named S9 link.
- [58 s](../references/visual/movie_s1_attachment/s1_58.0s.png) and [59 s](../references/visual/movie_s1_attachment/s1_59.0s.png) show the fixed central crossmember region, its round-ended central lug, and a separate moving output/end plate with elongated openings. [64 s](../references/visual/movie_s1_attachment/s1_64.0s.png) shows the plate and linkage from another pose. These establish morphology and moving/fixed ownership more strongly than dimensions.

Movie S1 does not reveal the hidden central bearing stack, bore fits, plate attachment pattern, exact link relief dimensions, wall thicknesses, strength, material, or whether a visible assembly seam is a manufactured joint. Perspective frames must not be scaled into millimetre dimensions. The paper's S9 mechanism keeps the existing E1/E2 output axes grounded and the torso outputs rotating in the sagittal plane; this implementation preserves those axes and adds no command or joint.

## What r10 adds

### Fixed central beam and lug

`src/spine_frame_r10.py` appends native features to the existing `FRM_LUMBAR_MONOLITHIC_CAGE_r09` PartDesign body used by physical instance `LumbarIntegrated1`. The source body name and instance placement remain stable; its r10 PartNumber/revision identify the addition. It keeps the original one-piece open-top center frame and original S9 datums.

The fixed beam spans world Y = −28.4…28.4 mm and world Z = −2.5…2.5 mm. At E1=(−33,0) it occupies world X = −29…−25 mm; at E2=(+33,0) it occupies X = +25…+29 mm. Each beam has two open windows over Y = [−26.8,−3] and [3,26.8] mm and Z = [−1.2,1.2] mm. The remaining roof/floor strips, end walls, and center web form a connected open-box profile. Each beam is native Pad geometry that overlaps existing shelf material inside the same body.

At each existing E center, a central sagittal lug has a round end of radius 3.5 mm and an inward stem 8 mm long. The stem uses the beam's ±2.5 mm world-Z height; the lug spans world Y = ±1.6 mm. A Ø2.2 mm through-bore lies on the existing E axis, parallel to world Y. Opposed Ø4.05 mm bearing seats are 1.2 mm deep, centered at world Y = ±1.0 mm. Two Pads, one window Pocket, one through-bore Pocket, and two seat Pockets are appended per E joint. The lead's refreshed native checks report 95 editable Bodies, 321 fully constrained sketches, no invalid native features, and maximum native joint residual 8.88×10⁻¹⁵ mm for this saved/reopened/recomputed candidate. These validity/axis checks do not establish clearance or capacity.

### Moving torso clevises, revised plate pattern, and hardware

`src/torso_attachment_r10.py` appends features to the existing `TORSO_FORE_TRANSVERSE_FRAME_r06` and `TORSO_HIND_TRANSVERSE_FRAME_r06` sources used by AppLinks `Torso_fore` and `Torso_hind`. It retains the torso output motion and placement. For each body, a full rounded plate-web Pad fills the legacy plate apertures, followed by a Pocket that cuts the revised profile. Two native sagittal clevis-ear Pads then connect the center lug to that same moving torso body.

The existing plate outline remains 36 × 40 mm in its local YZ plane: Y = −18…18 mm, Z = −16…24 mm, corner radius 2 mm, thickness 1.6 mm. The r10 replacement pattern is an assumed interpretation of [Movie S1 at 59 s](../references/visual/movie_s1_attachment/s1_59.0s.png):

| Feature | Current r10 metric choice | Status |
|---|---:|---|
| Two long side slots | Y = ±12 mm; Z bounds −12…20 mm; width 2.2 mm | `DESIGN_ASSUMPTION` |
| Center slot | Z bounds −6…8 mm; width 2.2 mm | `DESIGN_ASSUMPTION` |
| Two curved end slots | Centers Z = −10 and 17 mm; radius 4.5 mm; sweep −35°…+35° from +Y toward +Z; width 2.2 mm | `DESIGN_ASSUMPTION` |
| Adjacent round holes | Ø2.2 mm; Y offset −2.5 mm at each end-slot center | `DESIGN_ASSUMPTION` |

For fore and hind, the sketch reflects the Y coordinate according to the existing plate normal. The pattern is not a manufacturer mounting pattern; no supplier hole specification has been recovered.

Each moving clevis has ears centered at Y = ±2.8 mm, each 1.6 mm thick and 7 mm wide, with a Ø2.0 mm central pin bore and an E-centered R3.5 end. Its stem runs from E through the existing plate thickness to that plate's outer datum. Fourteen separate central hardware instances are added by `src/central_joint_hardware_r10.py`: two Ø1.9 × 9.2 mm grooved pins, four existing provisional Ø4/Ø2 × 1.2 mm bearing instances, four OD3/ID2.05 × 0.2 mm washers, and four OD3.6/ID1.6 × 0.6 mm split retainers. Pin, washer, and retainer instances follow the torso's existing E output; bearings are fixed to the lumbar frame. Nominal stack gaps are 0.2 mm lug-to-washer, 0 mm washer-to-clevis, and 0.1 mm clevis-to-retainer. The insertion/access sequence is unresolved: demonstrate insertion and retainer installation with the outer E journals removed, then install those journals, or provide another feasible sequence with tool/service access evidence.

All clevis, pin, seat, slot, bearing, washer, and retainer dimensions are design assumptions, including the apparent zero-gap contact. The exact source bearing count and retention arrangement are hidden in the film. Supplier verification, printed-bore tolerances, pin/clip fit, load sharing, and strength remain open.

### Long B–C profile

The r09 source `SPN_r02_L4` supplies the four B1–C1 / B2–C2 physical instances: `Link1_L4__1`, `Link2_L4__1`, `Link1_L4_1`, and `Link2_L4_1`. `src/spine_bar_profile_r10.py` changes only this source's relief sketch. It preserves all four instance IDs and placements, source-local bore centers, and MotionMap descriptors.

The original capsule is 6 mm wide, 1.2 mm thick, and 45.7876 mm between Ø4.05 mm bores centered locally at (3,3) and (48.7876,3) mm. The former narrow 2.4 mm axial slot is replaced by a rounded rectangular through-relief 3.2 mm wide, with 0.7 mm corner radius and 5.5 mm end inset from each bore center, leaving 1.4 mm nominal side rails. The dimensions are `DESIGN_ASSUMPTION`; the video supports the broader relieved long-bar morphology but cannot dimension it. L2 drive bars, L3 A–B bars, and L5 C–D bars stay plain. E–D is carried within each torso body; r10 does not add separate L6 physical links. No fork or bevel has been assigned because the visible layers and load path remain ambiguous.

## Repair history and evidence status

The first integrated r10 artifact had a cached-valid long-bar Pocket that failed on recompute. The lead repaired the profile construction to use an explicit eight-edge boundary: four line segments and four quarter-circle arcs, plus the two original bore circles in the sketch. The repaired source is `src/spine_bar_profile_r10.py`. The saved/reopened/recomputed candidate now has a valid repaired link profile, and the current checks below bind to its SHA.

The original integrated document and its initial AX/pass-scope reports were copied under [`reports/diagnostics/r10_pre_bar_recompute_repair/`](../reports/diagnostics/r10_pre_bar_recompute_repair/). Those diagnostics describe the pre-repair artifact and are not current r10 evidence. The refreshed native, S9, actuator, neutral leg-axis, AX0/AX1, and supplemental source-reproduction reports bind to the native SHA in the status paragraph. Neutral leg-axis coincidence is not a neutral-clearance result. No revision-specific changed-pair clearance campaign is claimed here.

The implementation reports [fixed frame](../reports/reviews/r10_frame_implementation.md) and [torso](../reports/reviews/r10_torso_implementation.md) record their bounded feature construction/isolated checks. The current integrated results are in [native checks](../reports/verification/r10_native_checks.json), [S9 topology](../reports/verification/r10_s9_topology.json), [actuator inventory](../reports/verification/r10_actuators.json), [leg-axis checks](../reports/verification/r10_leg_axes.json), [AX0/AX1 summary](../reports/animation/ax01_r10.json), the [AX1 payload](../animation/motion/ax01_r10.json), and [source reproduction](../reports/verification/r10_source_reproduction.json). These checks bind to the stated native SHA. AX0/AX1 covers three prescribed poses only; source reproduction is supplemental isolated CLI evidence. They do not establish assembly-wide clearance or fabrication readiness. The [source-profile review](../reports/reviews/r10_bar_plate_source_review.md) records the retained video comparison and current link mapping.

The lead's [bounded integration review](../reports/reviews/r10_integration_review.md) found the central correction and nominal kinematic ownership supported, with no demonstrated geometry failure, while retaining these release blockers:

- Changed-material clearance remains pending. The new beam/lugs, torso clevises, plate pattern, pin stack, and relieved bar need revision-specific changed-pair checks with exact pose domain, contact policy, and failures. AX0/AX1 three-pose transforms and native validity do not establish this clearance. Do not claim the 1,346-state campaign has passed.
- Center-pin installation order must account for the existing outer E journals on the same Y axis. Demonstrate insertion and retainer fitting with those journals removed, then install the journals, or document another feasible sequence. Show retainer/tool access and service requirements; current static captures do not prove access.
- Bearing outer-race retention and axial thrust are undefined. The nominal Ø4 bearing sits in a Ø4.05 blind seat of matching 1.2 mm depth, without a specified fit or positive outer-race cap. The moving OD3 washer sits 0.2 mm from the lug and does not prove race retention or a thrust path. Select interfaces and define fits, retention, thrust contacts, groove tolerances, endplay, and clip capacity.
- The central bearing pair supplements outer E supports on the same rigid axis. The Ø1.9 pin in the assumed Ø2 clevis bore has 0.1 mm diametral clearance; nominal coaxial CAD geometry does not account for print error or deflection. Define which supports locate radially/axially, whether a support floats, and the alignment/reaming process and allowable error.
- Strength and process are unqualified. The L4 link has two 1.4 mm rails at 1.2 mm thickness (3.36 mm² nominal net area) and 0.975 mm radial ligament at the bore. Beam window roof/floor material is 1.3 mm and the opposed lug seats leave a 0.8 mm web. Select process/material and check fatigue, pin bearing/tear-out, buckling, out-of-plane bending, beam torsion, lug splitting, and the grooved pin root.

Subsequent installed-MCP checks pass the neutral assembly's 1,205 raw intersection tests, native long-bar thickness edit/recompute/restore, and STEP round trips for the 487-solid assembly and all 107 used sources. Three flat-stock profiles pass exact readback. Reports are `r10_neutral.json`, `r10_native_edit_restore.json`, `reports/package_manifest_r10.json`, and `exports/profiles/r10/profile_manifest_r10.json`.

The supplemental `reports/verification/r10_central_pin_access.json` clears E1/E2 insertion from either Y side at 24 stations per path (96 stations and 340 OCC checks). Both center retainers and the entry-side outer E journal and its two retainers must be deferred; structural bodies, bearings, spacers, opposite-side hardware and cables remain included. This resolves the sampled initial pin sequence only. Elastic clip installation, tool/service access, fits, bearing retention/thrust and alignment remain release blockers. It does not prove the continuous swept path.

Final drawing review, assembly manual, changed-pair motion checks and overall package verification remain pending.

## Remaining acceptance and release blockers

The candidate remains unfinished until the remaining revision-matched clearance and delivery gates are complete. Required actions include:

- Complete the changed-material clearance campaign on the stated SHA and report exact coverage, pose inputs, contact policy, and failures.
- Demonstrate center-pin/retainer installation with the existing outer E journals removed, then journal installation and service access.
- Define outer-race retention, thrust path, radial/axial support roles, floating allowance, pin/seat tolerances, coaxial alignment, and endplay.
- Complete material/process load and fatigue checks for the link rails, beam windows, lug seats, pin groove, and retainers.
- Complete final exports, drawings, assembly manual, and package checks if required by the delivery plan. The cited native/AX/source checks do not establish those deliverables.

The source frames support the part classes and arrangement described here, not an exact replica. Millimetre contours, the reconstructed bearing stack, generic slots, and long-bar relief stay assumptions until dimensioned source or supplier evidence supersedes them. Fabrication release and powered hardware testing remain separate gates.
