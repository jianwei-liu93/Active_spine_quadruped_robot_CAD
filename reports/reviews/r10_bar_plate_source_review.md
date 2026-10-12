# r10 spine-link and output-plate profile review

Review date: 2026-10-12. Scope: bounded, read-only comparison of the retained Movie S1 frames and current r09 source generators. No live FreeCAD session, CAD document, native geometry, parameter file, or canonical assembly was changed. This is a morphology/profile review, not a dimensional or fabrication approval.

## Evidence inspected

- Retained Movie S1 extracts `references/visual/movie_s1_attachment/s1_54.0s.png`, `s1_56.0s.png`, `s1_58.0s.png`, `s1_59.0s.png`, and `s1_64.0s.png`. Their common source and decode provenance are recorded in `references/visual/movie_s1_attachment/provenance.json` (source movie SHA-256 `16b180fa5da669e78e7d2038147e1f09fd8adbb2265341d8c3a14d0093a235a9`). The visual files are timestamped extracts, not dimensioned drawings.
- Current generation chain: `src/build_robot_r09.py` → `build_robot_r07`/`build_robot_r06` → `build_robot_r05`/`build_robot_r04`/`build_robot_r03` and `src/build_flexor.py`; plus `src/spine_attachments_r02.py`, `src/torso_frame_r06.py`, `src/spine_frame_r09.py`, `src/refine_flexor.py`, and `parameters/candidate_r02.json` / `parameters/assembly_r09.json`.
- Existing source context: `reports/source_review/movie_s1_frame_attachment_r06.md`, `docs/13_candidate_frames_r06.md`, `docs/02_spine_kinematics.md`, and `reports/source_review/spine_reconciliation.md`.

## Supported visual differences

At 54–56 s, the mechanism is shown with distinct links over a fixed frame. The short members read as broad, plain flat bars with rounded bearing ends. Longer white members show more profile treatment: a recessed or open narrow center panel/slot on at least one long member, edge transitions that appear beveled, and forked or split lug-like regions around some end pivots. The frames support preserving distinct short and long profile families. They do not resolve which precise S9 edge owns every visible pocket, bevel, or fork, because the views are oblique, links overlap, and the assembly sequence includes translucent transition geometry.

At 58–59 s, a separate dark, broad rectangular end plate appears across the output assembly with several elongated openings. At 64 s, the plate is still distinct from the narrow sagittal links and is seen at another angle. This supports a transverse slotted output/end plate as a separate moving torso-frame feature. It does not establish its millimetre dimensions, exact angle, exact number/orientation of openings, mounting pattern, or vendor interface.

The r09 native inventory and AX01 manifest identify the actual moving plate instances as `Torso_fore` / `Torso_hind`, sourced from `TORSO_FORE_TRANSVERSE_FRAME_r06` / `TORSO_HIND_TRANSVERSE_FRAME_r06`. Their inherited plate is a rounded rectangle, local bounds Y = −18…18 mm and Z = −16…24 mm (36 × 40 mm), corner radius 2 mm, thickness 1.6 mm. The original source cuts five vertical capsule slots: one 14 mm long at local center and four 6 mm long at (Y,Z) = (±12, ±10) mm, all 2.2 mm wide. These are explicitly `DESIGN_ASSUMPTION` geometry. The plate’s class and moving-body ownership are visually supported; the precise original five-slot pattern is not recovered from the video.

The current r10 torso source revises that assumed pattern on the same plate: two long 2.2 mm-wide side slots at Y=±12 mm spanning Z=−12…20 mm; a center slot spanning Z=−6…8 mm; and two short curved end slots centered at Z=−10 and 17 mm, with 4.5 mm arc radius and ±35° sweep, each paired with a Ø2.2 mm round hole offset Y=−2.5 mm. The same source appends two central clevis ears per torso at Y=±2.8 mm; each ear is 1.6 mm thick, 7 mm wide, and has a Ø2.0 mm pin bore. These are all explicit r10 `DESIGN_ASSUMPTION` metric reconstructions, not measured source or vendor interfaces.

The fixed r09 center frame should not be confused with these moving plates: `src/spine_frame_r09.py` builds a one-piece open-top lumbar cage and its orthogonal crosswalls. It does not build the A–B–C–D moving bars or the transverse torso plates.

## Current link source/profile and interfaces

The r09 native inventory and AX01 manifest list the physical spine members as `Link1_L2_*`, `Link2_L2_*`, … through `L5`; suffixes `_1` and `__1` distinguish the positive/negative axial copies. `L2` is the OG0/OB2 drive family; `L3` maps A1–B1 and A2–B2; `L4` maps B1–C1 and B2–C2; `L5` maps C1–D1 and C2–D2. There is no physical L6 link in r09: E–D is incorporated into each moving `Torso_fore` / `Torso_hind` body. Do not use the older `build_flexor.py` segment labels as a complete physical inventory.

The r09 inherited `src/build_flexor.py::profile_part` sketches a capsule outline and pads it as a single flat plate. `add_link` adds two through bores and optionally one narrow central capsule cut. The original profile family has no bevel/chamfer feature or forked clevis ends. Current r02 inherited dimensions remain in the r09 robot:

| Family / physical instances per side | Current profile | Local bore centers / diameter | Axial thickness | Assessment |
|---|---|---|---:|---|
| `SPN_r02_L2`; `Link1_L2_1`, `Link1_L2__1`, `Link2_L2_1`, `Link2_L2__1` (O/G drive family) | Plain capsule; 30 mm center spacing, 6 mm width, 36 mm overall end-to-end | (3,3) and (33,3) mm; Ø4.05 mm | 1.2 mm | Broad, plain member family; exact width/end profile remains an assumption. |
| `SPN_r02_L3`; `Link1_L3_*`, `Link2_L3_*` (A1–B1 / A2–B2) | Plain capsule; 24.1215 mm center spacing, 6 mm width, 30.1215 mm overall | (3,3) and (27.1215,3) mm; Ø4.05 mm | 1.2 mm | Plain member family; video does not establish dimensions. |
| `SPN_r02_L4`; `Link1_L4_1`, `Link1_L4__1`, `Link2_L4_1`, `Link2_L4__1` (B1–C1 / B2–C2) | r09: capsule, 45.7876 mm center spacing, 6 mm width, 51.7876 mm overall; narrow 2.4 mm-wide, 35.7876 mm-long axial through-slot. r10 source: rounded-rectangle through-relief, 3.2 mm wide with 0.7 mm corner radius and 5.5 mm inset from each bore | (3,3) and (48.7876,3) mm; Ø4.05 mm | 1.2 mm | These are the four long bars targeted by `spine_bar_profile_r10.py`. r10 profile keeps bore centers, source-local frame, and placements; side rails are 1.4 mm each. Metric relief remains `DESIGN_ASSUMPTION`; bevel and fork features are not added. |
| `SPN_r02_L5`; `Link1_L5_*`, `Link2_L5_*` (C1–D1 / C2–D2) | Plain capsule; 6 mm center spacing, 5 mm width, 11 mm overall | (2.5,2.5) and (8.5,2.5) mm; Ø4.05 mm | 1.2 mm | Very short links; preserve simple broad end-lug form. |
| E–D output connection | No physical L6 source or `Link*_L6_*` instances in r09; carried by `Torso_fore` / `Torso_hind` | E/D axes remain in torso body/motion frames | Native torso features | Do not recreate old r02 L6 bars as separate physical parts. r10 adds a central clevis feature to each existing torso body. |

The segment placements are motion descriptors with endpoint frames, axial layer, width, and thickness. Preserve AX01 IDs/object names, endpoint coordinates, source-local frames, bore center spacing/diameter, axial layers, and `MotionMap` descriptors during profile changes. E–D is a torso connection in r09 and the r10 clevis must stay on that same torso motion body. The separate motor crank remains constructed in `src/spine_attachments_r02.py`: a 5 mm-wide capsule, 1.2 mm thick, with O/G bores plus two clamp-screw holes and counterbores. It also lacks visible bevel/fork details; its interfaces are provisional.

## Bounded native-edit recommendations

1. Keep L2/L3 drive and A–B bars and L5 C–D bars plain as the source-supported baseline. Do not add L6 members; E–D belongs to the moving torso bodies. Preserve existing pivots, bore diameters, member lengths, layer positions, IDs, and link placements.
2. `src/spine_bar_profile_r10.py` targets the four long L4 B–C instances and replaces only the narrow legacy cut with a broad rounded-rectangle through-relief. The source module uses the assumed 3.2 mm relief width, 5.5 mm bore inset, and 0.7 mm corner radius, while retaining 1.2 mm thickness, 4.05 mm bores, local bore centers, source body, physical instances, and MotionMap placements. This matches the broad relief category more closely. Bevels and forks remain unresolved and are not added without clear member layering and load-path evidence.
3. `src/torso_attachment_r10.py` updates the plate pattern on existing `Torso_fore` / `Torso_hind` bodies with paired side slots, a center slot, curved short end slots and adjacent round holes, then adds native central clevis ears. It keeps the output plate/torso body moving together. Slot profile and clevis dimensions remain `DESIGN_ASSUMPTION`; preserve E-axis / torso motion and check pin stack, clearance, and strength before acceptance.
4. Keep the exact plate supplier mounting status `UNKNOWN`; do not label generic slots as verified vendor holes. Keep the change local to profile construction and torso plate/clevis features. Do not change S9 pivots, link-center distances, branch, fore/hind leg direction, interfaces, or center-frame correction.

## Code hooks

- r09 physical source inventory and stable instance IDs: `animation/motion/ax01_r09.json` and `reports/verification/r09_inventory.json`. The AX01 manifest confirms four physical instances each for L2–L5, both torso bodies, and no separate L6 instance.
- r09 link definition plus r10 long-link profile: `src/build_flexor.py::profile_part` / `add_link` are historical generator hooks; `src/spine_bar_profile_r10.py::apply` is the current targeted native edit. It locates `SPN_r02_L4` and checks exactly four B–C AppLinks before changing the relief sketch.
- E–D/output carrier and plate pattern: `src/torso_attachment_r10.py::apply` adds the native web/pocket and central clevis to existing torso bodies. `parameters/assembly_r10.json` holds the relief, slot, and clevis assumptions. Leave the torso `MotionMap` and AppLink placements intact.
- Crank: `src/spine_attachments_r02.py::apply`, `outline` and `crank_bores`; edit separately if a clearer reference supports it.
- Transverse fore/hind plate: `src/torso_frame_r06.py::apply`, local rounded `plate`, `slots`, and `pad(..., 'TransverseSlottedPlate', ...)`. Parameter values live in `parameters/assembly_r09.json` under `attachment_frame`. `spine_frame_r09.py` is the fixed center frame and is not the hook for this plate or moving-link morphology.

## Checks actually performed and limits

- Read `AGENTS.md` and `docs/08_agent_orchestration.md`, repository reference/morphology guidance, current source generators, and the plate/link parameter entries.
- Visually inspected the five timestamped Movie S1 extracts listed above and checked their recorded decode/hash provenance.
- Traced r09 physical names/mappings against `reports/verification/r09_inventory.json` and `animation/motion/ax01_r09.json`, and reviewed the r10 profile/attachment source and parameters. Read-only review only: no source execution, test run, native-shape recompute, screenshot comparison against the CAD model, collision check, or live FreeCAD operation was performed.
- The frames justify profile categories and part separation only. Exact feature assignments, plate slot details, all thicknesses, fit, strength, manufacturing process, and vendor patterns remain unresolved or provisional.
