# Bounded r07 center-frame source review

Reviewed 2026-10-12. Requested reviewer routing: Sol/high; actual service routing is not independently observable. Only this report is owned by this reviewer. No live FreeCAD/MCP calls, source/schema edits, canonical writes, or new CAD checks were performed.

**Disposition:** the user's renewed objection to r06 is supported. The source's lower cradle has a broadly rectangular exterior surrounding a curved opening; the r06 circular external foot was a real profile difference. The corrected two-instance r07 view resolves that particular difference and improves the broad upper window and tapered pedestal ears. One concrete local design correction remains: the current lower circular opening and upper window are exactly tangent, leaving a zero-thickness sill point. Repair that profile before accepting r07. The source supports the paired cradle/ear/shelf architecture, but does not establish the candidate's internal motor capture bands or clamp fit.

This supersedes the r06 review's suggestion that all further cradle profile changes were optional. A circular **opening** does not establish a circular **outer foot**.

## Evidence actually inspected

- Repo `AGENTS.md`, documents 00/01/07/08, prior r06 frame review and Movie S1 attachment review, slider-plate reconciliation, `src/spine_frame_r07.py`, relevant `src/spine_attachments_r02.py`, and `parameters/assembly_r07.json`.
- User still `/tmp/codex-clipboard-52667344-bb06-4b32-876d-0504f8b9d4e1.png`; timestamped Movie S1 frames at 51, 52, 54, 57, 60, 69, 76 and 80 s. The 52 s source is `references/visual/movie_s1/frame_052s.png`; the other inspected timed frames are in `/tmp/flexor_movie_s1_frames/`. The source video is `/home/jianwei/freeCAD_projects/active_spine_robot_paper/sciadv.aed5603_movies_s1_to_s14/aed5603_movie_s1.mp4`. Existing extracted frames were inspected, not a new continuous video analysis.
- Existing Fig. S9 crop `/tmp/spine-source-review/s9-crop.png`, for graph identities rather than manufactured dimensions.
- Actual corrected `reports/views/r07_bare_lumbar.png`, compared with `reports/views/r06_bare_lumbar.png`. The corrected r07 image shows two assembly instances; the earlier image with source definitions also visible was excluded.
- Read-only ZIP/XML inspection of `cad/checkpoints/r07_center_frame.FCStd`. Its SHA256 at inspection was `3b3efd12d378b2afeac08f7438156289ca4f153c18f5d2ca910bb46dec3eebb8`; the corrected view SHA256 was `93f7b9656b4ef8f35c4c8bd715b8f6e979142dd23ee685ca5075cee57d8eb33a`.

No metric dimensions were recovered from perspective pixels.

## Morphology and axial ownership

| Feature | Source observation and r07 assessment |
|---|---|
| Two parallel tilted cradle walls | Both walls are visibly present at 52–57 s. They are part of the fixed central support, rather than duplicate moving links or an exploded copy of one wall. Keeping two walls is correct. Their exact separation, thickness, tilt and manufacture are not dimensioned by this sequence. |
| Lower exterior and opening | At 52/54 s the outer lower foot continues the broad straight-sided cradle perimeter, with modest corner transitions; the inner opening is curved around the crank/output region. r06's disk-shaped exterior is the mismatch. r07's rounded rectangular perimeter plus circular opening is materially closer. The exact inner curve and transitions remain reconstruction assumptions. |
| Upper window | A broad rectangular opening is clear at 52/54 s. r07's wider window is an appropriate feature-type correction. The source does not certify its selected 17 × 17 mm dimensions or a tangent connection to the lower opening. |
| Shelves and pedestals | The source has substantial short horizontal end shelves with tapered round-ended ears, not a full exposed beam across the entire central opening. r07's local platforms, axial shelves and tapered inner pedestals match this arrangement. Exact widths, blends and seams remain provisional. |
| A/C identity and reversed heights | S9 puts C1 above E1 with A2 below, and C2 below E2 with A1 above. The source shows the corresponding upper-slot/lower-ear end and lower-slot/upper-ear end. r07 explicitly pairs C1/A2 and C2/A1; no swap or new planar A–C linkage is needed. The web joining A and C is grounded support. |
| Axial order | The source's white A–B rocker lies inward of the outer black A/slot ear; the shelf joins the inner cradle/pedestal region to that outer ear. r07 retains that architectural order. With the saved placements and code, the positive-side inner plate occupies Y=26.8…28.4 mm and outer guide ear Y=39.4…41.0 mm; the negative side mirrors it. These are candidate stack dimensions, not source measurements. A matched view with links/hardware is still needed to verify the final visible stack after integration. |
| E journal and moving output | The shelf-level journal supports the E-axis output body. At 60/69 s the separate slotted end plate changes inclination while the shelves/guide ears remain fixed; 76 s shows that plate almost edge-on. Preserve the separate E–D output body and Y-directed E/D axes. Do not add an extra moving planar link or ground the end plate to the shelf. |
| Perimeter motor collar and internal bands | The source supports a cradle around a motor region and some visible edge depth, but these views do not expose a complete inward collar or prove the candidate's two internal capture bands, back-to-back shim, preload or restraint method. They are plausible engineering additions with explicit `DESIGN_ASSUMPTION` status; they cannot be claimed as recovered original geometry. Their presence alone is not a demonstrated source-fidelity error requiring deletion. |

Native XML confirms `LumbarIntegrated1` and `LumbarIntegrated_1` reference `FRM_LUMBAR_ROUNDED_CRADLE_L_r07` and `_R_r07`, at unchanged Y=+28.4/−26.8 mm placements with unit scale. The source module reads A/E/track datums from the existing solver and preserves those placements. This supports intended ground ownership and datum preservation by construction, but does not replace native bore-axis measurement.

## Required local correction and verification

1. **Remove the zero-thickness aperture junction.** Current case-local lower radius is 9 mm and upper-window bottom is z=9 mm. The circle's top therefore touches the window bottom at exactly one point; the rotation preserves that tangency. The inward collar void and remote capture bands do not provide a sill at this point. A positive provisional sill/web, or one deliberately merged aperture with a continuous manufacturable boundary, is required. The source supports two recognizable opening regions but does not establish a zero-ligament cusp. Choose the dimension as an explicit engineering assumption; do not infer a thickness from the source pixels. A valid single native solid alone is insufficient evidence for this local detail.

2. **Verify the changed profile against actual nearby parts.** The enlarged rectangular perimeter and upper-window/collar material need revision-specific clearance checks against crank/horn hardware, rods, ties, motor cases and connectors. Inspect a section of the aperture junction and case capture surfaces, then run the intended sampled spine cycle. The prior r06 pass does not validate r07 material additions. No new collision, axis, strength or fit pass is claimed here.

3. **Show a matching source-oriented view after integration.** Keep a strict bare-frame view and a view with motors, copper liners, A–B links and C caps so the perimeter and rod-behind-ear order can both be judged. This is an evidence requirement, not justification to move any frozen datums. The existing corrected r07 bare view already establishes the outer-foot improvement.

## Camera/assembly differences and unresolved dimensions

The two walls look widely separated in the saved bare view because their ties, motors and linkage are hidden and the view direction differs from the source. That appearance is not evidence for deleting one wall, narrowing the motor pack, or changing axes. Source 54/57 s shows links and shafts arriving in an assembly animation; absent white links or caps in the bare CAD view are expected. Red anatomical rods and skeletons are explanatory graphics, not extra manufactured frame members. Source 60/69 s output-angle differences are motion, rather than a change in fixed shelf orientation.

Manufacturer output/horn location, spline and retention details; acceptable case contact/preload; connector keepouts; bearing/liner fits and retention; hidden washer/bearing counts; and structural adequacy remain separate unresolved interfaces. Lead-reported motor envelopes of 20 × 26 × 34 mm were not rescaled in this review and are not a reason to distort the source morphology. This review makes no fabrication-release claim.

## Lead resolution

The upper window was moved to case-local Z=10.5..26 mm, leaving a positive 1.5 mm sill above the radius9 lower opening. Native final sources are FRM_LUMBAR_ROUNDED_CRADLE_L/R_r07_final. The partial-integration native neutral check passed for all472 physical links, with zero raw material overlaps (r07_frame_clamps_neutral.json). Full revised motion remains pending; the successful neutral check alone does not close that requirement.
