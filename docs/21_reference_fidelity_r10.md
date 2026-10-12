# r10 source-fidelity update: central E attachment, torso plates, and long links

**Status: INTEGRATED CANDIDATE INCOMPLETE.** The r10 native candidate contains a proposed central frame beam/lug, moving torso clevises, revised slotted torso plates, and a relieved long B–C link profile. Metric dimensions are reconstruction or engineering assumptions. The initial cached-valid long-bar Pocket failed when recomputed; the lead repaired its boundary sketch with an explicit eight-edge profile. All initial AX and broad pass-scope evidence was captured before that repair and is archived as diagnostic evidence. Refreshed validation is pending. The latest native SHA is intentionally not pinned until the repaired artifact and its evidence are frozen together.

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

At each existing E center, a central sagittal lug has a round end of radius 3.5 mm and an inward stem 8 mm long. The stem uses the beam's ±2.5 mm world-Z height; the lug spans world Y = ±1.6 mm. A Ø2.2 mm through-bore lies on the existing E axis, parallel to world Y. Opposed Ø4.05 mm bearing seats are 1.2 mm deep, centered at world Y = ±1.0 mm. Two Pads, one window Pocket, one through-bore Pocket, and two seat Pockets are appended per E joint. The complete fixed-frame addition is 4 Pads and 8 Pockets with fully constrained sketches, subject to refreshed integrated checks after the long-bar repair.

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

Each moving clevis has ears centered at Y = ±2.8 mm, each 1.6 mm thick and 7 mm wide, with a Ø2.0 mm central pin bore and an E-centered R3.5 end. Its stem runs from E through the existing plate thickness to that plate's outer datum. Fourteen separate central hardware instances are added by `src/central_joint_hardware_r10.py`: two Ø1.9 × 9.2 mm grooved pins, four existing provisional Ø4/Ø2 × 1.2 mm bearing instances, four OD3/ID2.05 × 0.2 mm washers, and four OD3.6/ID1.6 × 0.6 mm split retainers. Pin, washer, and retainer instances follow the torso's existing E output; bearings are fixed to the lumbar frame. Nominal stack gaps are 0.2 mm lug-to-washer, 0 mm washer-to-clevis, and 0.1 mm clevis-to-retainer. Axial insertion is planned along Y before motors/cables are installed; service access is not yet checked.

All clevis, pin, seat, slot, bearing, washer, and retainer dimensions are design assumptions, including the apparent zero-gap contact. The exact source bearing count and retention arrangement are hidden in the film. Supplier verification, printed-bore tolerances, pin/clip fit, load sharing, and strength remain open.

### Long B–C profile

The r09 source `SPN_r02_L4` supplies the four B1–C1 / B2–C2 physical instances: `Link1_L4__1`, `Link2_L4__1`, `Link1_L4_1`, and `Link2_L4_1`. `src/spine_bar_profile_r10.py` changes only this source's relief sketch. It preserves all four instance IDs and placements, source-local bore centers, and MotionMap descriptors.

The original capsule is 6 mm wide, 1.2 mm thick, and 45.7876 mm between Ø4.05 mm bores centered locally at (3,3) and (48.7876,3) mm. The former narrow 2.4 mm axial slot is replaced by a rounded rectangular through-relief 3.2 mm wide, with 0.7 mm corner radius and 5.5 mm end inset from each bore center, leaving 1.4 mm nominal side rails. The dimensions are `DESIGN_ASSUMPTION`; the video supports the broader relieved long-bar morphology but cannot dimension it. L2 drive bars, L3 A–B bars, and L5 C–D bars stay plain. E–D is carried within each torso body; r10 does not add separate L6 physical links. No fork or bevel has been assigned because the visible layers and load path remain ambiguous.

## Repair history and evidence status

The first integrated r10 artifact had a cached-valid long-bar Pocket that failed on recompute. The lead repaired the profile construction to use an explicit eight-edge boundary: four line segments and four quarter-circle arcs, plus the two original bore circles in the sketch. The repaired source is `src/spine_bar_profile_r10.py`. This addresses the boundary/recompute defect in source; the repaired integrated native artifact still needs a fresh freeze and checks.

The original integrated document and its initial AX/pass-scope reports were copied under [`reports/diagnostics/r10_pre_bar_recompute_repair/`](../reports/diagnostics/r10_pre_bar_recompute_repair/). Those diagnostics describe the pre-repair artifact and are not current r10 acceptance evidence. Existing root-level reports such as `reports/verification/r10_integration_mcp.json`, `r10_native_initial.json`, `r10_native_checks.json`, `r10_neutral_initial.json`, and the initial r10 AX payloads must not be presented as refreshed passes for the repaired artifact. A new native SHA, AX exports, native recompute, pose/topology, neutral-clearance, changed-pair checks, and visual evidence must be bound to the same post-repair file before acceptance.

The implementation reports [fixed frame](../reports/reviews/r10_frame_implementation.md) and [torso](../reports/reviews/r10_torso_implementation.md) record their bounded feature construction/isolated checks. Those checks do not prove current integrated motion clearance. The [source-profile review](../reports/reviews/r10_bar_plate_source_review.md) records the retained video comparison and current link mapping.

## Remaining acceptance and release blockers

The candidate remains unfinished until the lead regenerates a post-repair native document and revision-matched evidence. Required checks include:

- Reopen/recompute the exact repaired native candidate and verify all appended PartDesign bodies/features and fully constrained sketches remain valid connected solids.
- Regenerate AX identity/pose evidence and confirm stable AppLink identities, source-local frames, unchanged E1/E2 axes, torso motion, and the four L4 placements after the relief repair.
- Recheck the central pin/bearing/washer/clevis/retainer stack, insertion and tool access, plate and link clearances, neutral intersections, and sampled spine motion. Existing pre-repair neutral and motion evidence does not transfer.
- Re-render bare central-frame, fore/hind plate, long-bar, and assembled views from the post-repair file and review them against the retained source frames.
- Resolve or keep explicit the supplier bearing, shaft, pin/clip, motor output/mount, and connector interfaces; establish tolerances, material/process allowables, printed-hole accuracy, load distribution, and strength. No strength, fatigue, endurance, or fabrication-release evidence exists.

The source frames support the part classes and arrangement described here, not an exact replica. Millimetre contours, the reconstructed bearing stack, generic slots, and long-bar relief stay assumptions until dimensioned source or supplier evidence supersedes them. Fabrication release and powered hardware testing remain separate gates.
