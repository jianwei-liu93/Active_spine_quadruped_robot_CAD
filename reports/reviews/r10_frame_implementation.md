# r10 central frame crossmember/lug implementation

Owned implementation: `src/spine_frame_r10.py`. Configuration reads only lead-owned `parameters/assembly_r10.json` / `central_attachment_r10`. Interpretation follows `reports/reviews/r10_center_attachment_source_review.md` and the lead's bounded geometry contract. No parameter schema, frozen motion helper, other source, installed MCP document, or canonical native file was edited.

## Native implementation

`apply(b)` appends features to the existing fixed frame Body `FRM_LUMBAR_MONOLITHIC_CAGE_r09`, retaining its source Name, physical `LumbarIntegrated1` AppLink identity, LinkPlacement, MotionMap and original 40 native features. It updates only the frame PartNumber to `FRM_LUMBAR_MONOLITHIC_CAGE_r10`, Revision to `r10`, and its process/assumption metadata. It performs no saves, exports, GUI launch or physical-instance creation.

At both frozen E axes, E1=(−33,0) and E2=(+33,0), a full transverse beam occupies inward X offsets4..8 mm, worldZ ±2.5 mm and worldY ±28.4 mm. Its first Pad overlaps the original near/far shelf material within the same Body. Two transverse windows occupy worldY [−26.8,−3] and [3,26.8], worldZ ±1.2; each pair is cut by one Pocket along worldX through the 4 mm beam thickness. The remaining roof/floor strips, end walls and center web provide a connected open-box load path.

The central sagittal lug spans worldY ±1.6, with radius3.5 round end centered exactly at E and a stem extending8 mm inward. Following the lead's correction, **the stem uses worldZ ±2.5**, matching the beam height; the round end retains radius3.5. The lug has a diameter2.2 through bore and diameter4.05 bearing-seat Pockets, each1.2 mm deep from opposite faces. These seat intervals center bearings at worldY ±1.0. All added bearing/pin axes remain parallel worldY at the existing E revolute joint; no datum or DOF is added.

Each new Pad/Pocket has its own fully constrained native sketch. Temporary fused/section shapes are used solely to derive a connected lug sketch contour, with no opaque Part::Feature or PartDesign::Feature result. Every feature recompute checks a valid single connected solid. The original40 features remain the unchanged prefix of the native feature tree.

Added per E: beam Pad, lug Pad, paired-window Pocket, through-bore Pocket, and two bearing-seat Pockets. Total additions: **4 Pads +8 Pockets =12 features**. Resulting frame: **38 Pads,14 Pockets,52 fully constrained sketches**.

## Supplemental isolated validation actually run

The lead authorized isolated CLI validation. Input was the frozen canonical r09 native model; the only native save was the separate temporary copy `reports/tmp/central_attachment_r10/r10_frame_append.FCStd`. The runner, logs and machine-readable results are in that directory.

The first native execution passed construction, all per-feature connected-solid checks, native feature counts and all sketch constraints. An additional harness-only byte-identical BREP assertion for intermediate old features failed after recompute. This was not a native topology failure. The first-attempt report/log is preserved; the second harness compared detached old shapes with actual post-append intermediate shapes. All40 old features had exactly zero bidirectional Boolean difference and zero bbox difference, preserving their actual geometry and IDs. The implementation source needed no geometry repair.

The final supplemental run passed construction and separate-copy save/reopen/recompute:

- One valid connected frame solid; no opaque frame features.
- 38 Pads,14 Pockets,52 fully constrained frame sketches.
- 473 physical AppLinks, unchanged by this fixed-source append.
- Original40 feature identities/order preserved; each old feature had zero bidirectional geometric difference and zero bbox difference.
- Frame volume15907.31469821606 mm³ before and after save/reopen.
- Source-local bbox unchanged: X ±38.30736611867309; Y [−15.977241335952169,35.57883832488649]; Z [−12.6,69.4] mm.
- Frozen canonical r09 SHA-256 stayed `765bb3b9a32365e1c005ff16a246ac284d2e0544d3648d4e4be3f436a58e1b57`.

Final detailed record: `reports/tmp/central_attachment_r10/validation.json`; successful log: `validate_retry.log`. `python -m py_compile src/spine_frame_r10.py` passed.

## Limits and integration handoff

This module implements only the fixed integral crossmember/lug. The moving central clevis/carrier, real pin, bearing and retention instances are separate lead-owned work; this geometry alone does not complete the user's mechanical attachment request. It preserves the existing outer E support material without declaring its eventual load sharing or fit verified.

This isolated exercise establishes native construction/editability and readback, not whole-robot collision clearance. Lead integration must check moving E–D bars, torso plates, central clevis/pin stacks, C-shaft envelopes, insertion access, and relevant poses against the new material. Film-derived dimensions, bearing count/retention, supplier fits, structural capacity and fabrication release remain assumptions. No stopped r09 partial campaign evidence is promoted to r10 acceptance.
