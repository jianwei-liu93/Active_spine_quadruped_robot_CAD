# Current r07 center-frame reconciliation against Movie S1

Reviewed 2026-10-12. Bounded independent reviewer role requested: Sol/high; actual service routing is not independently observable. Owned outputs are this report and images under `reports/views/source_fidelity_r07/`. No live FreeCAD/MCP calls, canonical or source/schema writes, or collision tests were performed.

**Finding: a substantial face-orientation mismatch remains.** Movie S1's broad upright rectangular window is on a crosswall adjoining the narrower sagittal horn cheek along a long tilted corner. The lower round horn opening belongs to the adjacent side cheek. Current r07 puts the broad rectangular window and lower round opening into the same sagittal plate on both sides and has no corresponding broad windowed crosswall spanning the motor pack. A rectangular exterior alone did not recover this structure. This is a source-fidelity correction, not a reason to move the S9 axes or rescale motors.

This supersedes the relevant acceptance language in `center_frame_r07.md` and the earlier r06 review. Those reviews correctly identified the lower exterior and A/C topology but did not correctly distinguish the broad window face from its adjacent horn-cheek face. The previously fixed 1.5 mm sill and r07 shaft relief are not reopened by this finding.

## Inspected evidence

- Current `src/spine_frame_r07.py`, `parameters/assembly_r07.json` (`lumbar_frame_r07`), previous review and its lead resolution.
- Current `reports/views/r07_bare_lumbar.png` and `r07_spine_source_facing.png`. Their SHA256 values are respectively `7487e5be7a9677d03a6518b4a310d7dfc9d56ddd8e2d03519bc37d94d8e0b6a8` and `f01c33e5fc0a21a02b8ccd6bec405992333b9b8062623c634aeb1fed06babe3e`.
- The current native file identity was checked read-only: `cad/flexor_r07_robot.FCStd`, SHA256 `cea39190bd1265a7a9be2eddcd061a4abc85e19076e15e1514aa318cdffbb227`. Native solids were not independently reopened or measured.
- User still `/tmp/codex-clipboard-17794a29-f3c1-4e2e-86a4-4495146f791f.png`; saved source frames `references/visual/movie_s1/frame_052s.png`, `frame_060s.png`, `frame_076s.png`; the previously inspected 54/57/69/80 s frames and S9 crop.
- **Fresh original-video extraction** at 51.3, 51.5, 51.7, 51.9, 52.3, 52.7, 53.3 and 53.8 s from `/home/jianwei/freeCAD_projects/active_spine_robot_paper/sciadv.aed5603_movies_s1_to_s14/aed5603_movie_s1.mp4`, using installed `/opt/hfs20.5.278/bin/hffmpeg`. These unmodified frames are saved in `reports/views/source_fidelity_r07/`.

Comparison artifacts:

- `reports/views/source_fidelity_r07/face_ownership_comparison.png`: cropped original frames before and after motor insertion, with labels/arrows only.
- `reports/views/source_fidelity_r07/source_vs_current_r07_face_planes.png`: source/current comparison explicitly labeled as **not camera matched**.

## Why this is geometry rather than shading or a camera reversal

At 51.5/51.7 s the frame is already present while the motor pack is absent. The broad rectangular window face meets a narrow dark face at a sharp, continuous tilted highlight/corner. The narrow face continues into the curved lower opening and has a small upper screw hole. The broad window is not a hole in that same narrow face. This corner and surface separation exist before the motor arrives, so the dark strip cannot be dismissed as the bought motor case.

At 52.3 s the motor pack is visible approaching **from above**. By 52.7 s its connector is visible through the broad window, while its round horn/output is visible on the adjacent lower side face. At 53.3/53.8 s the additional crank/horn parts arrive at that side output. This temporal evidence establishes different face ownership more strongly than interpreting one shaded still.

The sources support adjacent faces and an approximately orthogonal channel/cage interpretation with high confidence. Exact dihedral angle, profile thickness, panel seams and manufactured part count are not recoverable from this perspective sequence; choosing 90° is a reasonable explicit reconstruction assumption.

## Specific corrections, ranked

| Severity | Difference | Required direction |
|---|---|---|
| **Major source-fidelity mismatch** | r07 `annulus` cuts both `lower_opening_radius_mm` and `upper_window_mm` from the same rotated case-local XY face, which maps to sagittal XZ. Both assembly instances therefore carry the broad window in the horn plane. The source window is on the adjoining crossface. | Add broad windowed crosswall geometry spanning Y between the two existing side cheeks. Fill the present upper rectangular cheek cuts to make solid upper sagittal cheeks as the bounded starting geometry; the broad window belongs on the crosswall. Do not merely add a crosswall over the current full windowed sagittal plates and claim the face ownership has been corrected. |
| **Assembly condition, not a required cheek cutout** | Source motors descend into the cradle from above. This establishes an open cavity top but does not establish a void in either sagittal cheek. | Preserve a clear case-local +Z insertion path by avoiding a horizontal cap across the cavity. Solid upper cheeks outside the case-pair Y envelope do not obstruct this path. Keep their top rails and tie/screw bosses unless an actual interference requires local relief. |
| **Medium confidence source detail** | A second, smaller/partly occluded rectangular opening is visible through the primary window at 51.5–52.3 s, on another frame surface behind it. | Prefer two opposing windowed crosswalls rather than one U-backwall alone. The exact second opening outline and whether its panel is full height are partly hidden; retain these as assumptions and show both sides in the revised view. |
| **Unresolved cheek outline detail** | The source exposes a solid dark upper cheek region with an upper screw hole and a blended transition toward the curved lower output opening. Some far surfaces are hidden. | A solid upper cheek is better supported than a required upper void. Retain its material initially; refine shoulders only where the source or revised clearances establish a concrete need. Keep the broad lower outside perimeter rather than reverting to r06's circular external foot. |

## Concrete bounded r08 starting proposal

Use the current **case-local** frame before its existing 30° XZ rotation. Preserve the two motor envelopes, their back-to-back Y spacing, O/A/E and all C tracks, current shelf/guide locations, tie datums and output rigid-body ownership.

1. Keep sagittal side cheeks on the current Y planes. Retain the lower radius-9 opening and lower exterior foot as a provisional starting profile. **Remove the upper rectangular window cut from each sagittal cheek**, retaining solid upper cheek material and the existing upper tie-hole locations X=±11.4, Z=28.4. The cheek plates lie outside the case-pair Y envelope; they therefore permit the motor pack to enter along case-local −Z without requiring an upper cheek void. Keep the cavity top open between cheeks/crosswalls: add no horizontal roof panel. This preserves a continuous grounded connection for the crosswalls, including after required C-shaft reliefs. This is a face-profile change, not a motor-axis change.

2. Connect those cheeks with windowed crosswalls near case-local **X=−14 and X=+14**, spanning the present Y separation. The sources establish the broad primary crossface and suggest its opposing counterpart. Using both avoids relying on uncertain front/rear labeling or choosing a single wall on the wrong end. Their normals are case-local ±X; the lower horn-cheek normals remain ±Y. A panel at only one X end is a less source-complete provisional option if later matched views disprove the second wall.

3. Provisional first geometry: crosswall thickness **1.6 mm**, upright Z approximately **0…31 mm**, broad window centered at Y=0 with width about **36 mm** and height **17 mm**, Z=10.5…27.5 mm. These values are engineering choices compatible with the frozen envelope and the visible proportion ranges below, **not recovered film dimensions**. Use a 3 mm panel only if separately justified for fit/stiffness, with its location chosen to clear the frozen case pack. A crosswall must connect to the cheeks/shelves by positive material rather than visual contact.

4. Preserve the existing tie bosses/bores and original journals initially. Keep the distinct outer C1/A2 and C2/A1 guide ears, copper liners and fixed shelves. The windowed crosswall is a grounded printed support; it adds no moving A–C or E–D link. Retain the engineering C-shaft relief only where the actual revised solids require it, and rerun the changed-material sweep.

5. Treat existing inward collar, case bands and shim as provisional restraint features. Reconcile them with the new insertion path and crosswalls; no hidden clamp/retention surfaces are certified by these frames. Do not silently use a permanently closed zero-clearance cage or claim the movie establishes preload.

The proposed crosswall dimensions need native clearance/insertion review by the lead; this report has not established that they fit the actual horns, C-shaft paths or connectors. The source-fidelity result justifies replacing r07's frame architecture and invalidating its geometric-fidelity completion claim before export acceptance.

## Follow-up resolution: upper sagittal cheeks

The initial version of this report recommended narrow upper sagittal stiles and removal of their central top rail, based on the motor insertion sequence. **That inference was too strong and is withdrawn.** A plate lying on either outside Y face does not block insertion along case-local Z; only a roof across the cavity, obstructing restraint, or insufficient cavity clearance would do so.

The visible dark horn-side surface above the lower circle appears solid around its upper screw hole. The partially occluded grey/far-surface gap does not uniquely establish a hole in that same cheek plane and must not be used to require one. Hidden upper cheek extent remains uncertain. Consequently the preferred bounded reconstruction is the lead's proposal: solid upper sagittal cheeks, two Y-spanning windowed crosswalls, an open cavity top, and unchanged motor/S9/tie datums. Narrow stiles are an optional later engineering relief only if an actual interference or clearer source view justifies them. A full-axis C-shaft clearance can otherwise sever a narrow stile/crosswall junction, so preserving positive material continuity is a concrete reason to start with solid cheeks.

The major face-ownership correction remains: relocate the broad window feature onto crosswalls. The source does not justify retaining the same broad upper window in both sagittal cheeks. No updated CAD or clearance pass is claimed by this report change.

## Proportions and their limits

For the primary broad window face in fresh 51.5/51.7 s frames, comparing opening and outer edges in that **same visible face** gives a rough opening width of **0.65–0.75 of the crosswall span**. Opening height is approximately **0.5–0.65 of the upright height above the shelf region**. These deliberately wide ranges include perspective, rounded edges and partly occluded lower boundaries. They support a broad Y-spanning window, not a 17 mm window copied into an X-spanning horn cheek. They do not establish millimetres, exact orthogonality, overall case depth or manufacturing thickness.

## Correspondences and things that do not require redesign

The source/current views both show the low-slot/high-ear end and the opposite high-slot/low-ear end, the local axial shelves, rounded A journals, paired left/right physical support, and lower curved output clearance. S9 still supports C1/A2 and C2/A1 fixed ear ownership. No evidence here calls for changing fore/hind assignment, motor count, the shared input, output pivot locations, slider heights or leg direction.

Whether the existing CAD camera is on the opposite Y side is a **hypothesis**, not an established explanation. Front/right labels and apparent lean alone are insufficient. A matched pair of both ±Y oblique views, with a strict bare frame and then frame+motors+liners, will resolve projection/occlusion and the second crosswall details. It will not make the current same-plane window/circle construction equivalent to the source's adjacent-face arrangement.

The 60/69 s moving slotted end plates and the 76 s edge views concern the separate moving output bodies; they must not be fused into the grounded crosswalls. Red anatomy graphics, absent parts in an assembly animation, and changing output pose are not missing fixed-frame material. Hidden fits, panel seams, exact screw patterns, motor seating surfaces and connector keepouts remain explicit unknowns.

## Bounded review of the proposed two-half r08 cage

Lead proposal reviewed statically: retain the two existing native sagittal frame bodies/instances and their datums; fill their upper windows; add each body's half of two 1.6 mm transverse windowed walls at case-local X=[−14,−12.4] and [12.4,14], Z=0…31, extending from its outside Y=±28.4 face toward Y=0. The broad openings total Y=[−18,18], Z=10.5…27.5. Keep the cavity top open. Existing four transverse tie tubes/screws and collars retain the two grounded halves; there are no proposed seam screws, bond, or other hidden joint. This is a **manufacturing adaptation**, not a source-established split.

**Assessment:** suitable for a reviewable candidate after the two bounded details below are handled. It preserves the actual source-body/placement structure and permits the halves to close around the motor pack rather than relying exclusively on top insertion past all collars/bands. Neither this report nor the current nominal geometry establishes stiffness, preload, tolerances or fabrication readiness.

1. **Required upper tie passage:** the frozen upper tubes have OD2.4 mm and case-local axes at X=±11.4, Z=28.4. Their radial extents reach X=±12.6, while the proposed crosswall inner surfaces start at X=±12.4. Thus there is **0.2 mm nominal intrusion** of each tube into the corresponding wall along its Y span. This is not a source-supported intentional press fit. Cut a native tube passage/edge relief through the new material. The existing Ø2.6 collar-recess convention is a reasonable provisional starting diameter, providing 0.1 mm nominal radial allowance; it is still an unverified fit. A cylinder centered outside the 1.6 mm wall will produce a shallow edge groove rather than a fully enclosed round hole. Keep the remaining wall continuous and verify it after all shaft reliefs. The lower tubes at Z=−8.4 do not intersect a wall whose Z range begins at 0, by this simple axial-envelope check.

2. **Recommended controlled midplane seam clearance:** exact flat Y=0 butt faces are nominally consistent with the tube-defined spacing, but they introduce a competing physical stop. Four tubes set the inner-cheek separation to 53.6 mm; outer plate faces are 56.8 mm apart including the two 1.6 mm cheeks. Crosswall half lengths, tube length, frame thickness and print shrinkage will not all be exact. Proud butt faces could prevent the frames from seating onto the tubes or bow the new panels; short faces would leave a gap anyway. Use an explicit small seam allowance, for example **0.2 mm total nominal gap** with halves ending at Y=±0.1, as a `DESIGN_ASSUMPTION`, or document an adjustable mating allowance. Keep the tube-defined datum as the locating authority. No fake seam fastener is needed for the candidate.

The split seam is not equivalent structurally to a one-piece crosswall. Each half's window top/bottom rails become cantilevers from its own cheek; a plain butt seam has no reliable tensile or bending capacity. Compression or friction transfer depends on actual contact/preload and must not be assumed, especially because the spacer tubes stop further closure. Existing ties provide a real restraint path, but their bending, screw engagement and frame boss stiffness have not been assessed for the new lateral/racking loads. Compared with a one-piece cage, expect lower crosswall bending/torsional stiffness and more seam motion until demonstrated otherwise.

For this bounded candidate, preserve the simple split and label that structural limitation rather than inventing new purchased seam hardware. If subsequent load/deflection screening shows excessive racking, add a real manufacturable register/lap/bridge or choose a one-piece cage with a verified insertion sequence. A thin cosmetic tongue on a 1.6 mm edge should not be credited as a structural joint without dimensions and analysis. New features must not mask separation or obstruct motor/connector service access.

Assembly review should explicitly show that the two halves, motors/shim, four tubes and outer screws can be brought together without passing a closed crosswall through an already installed horn/shaft or trapping inaccessible screw heads. Open top is helpful but alone does not prove clearance past the inward collars and capture bands. Recheck full C-shaft travel reliefs against crosswall/cheek connectivity: a valid single solid is necessary, and an extremely thin surviving ligament remains a structural limitation. No model topology count, native validity, clearance or strength result is asserted by this static review.

## Review of the measured carrier-clearance adaptation

The lead reports actual r08 neutral native intersections limited to new crosswalls versus the controller carrier (9.98 mm³ per half) and its four clamp bolts (2.45 mm³ each). Reported case-local intersection bounds are X=12.10…14.84, Z=26.90…30.90, Y=17.95…22.05 and the negative-Y counterpart. These are **lead-run measurements supplied to this reviewer**, not tests independently rerun here.

Proposed correction: raise cheek/crosswall top Z from 31 to **33 mm**, keep the broad window at Z=10.5…27.5, and cut two through-thickness pockets **only in the positive-case-X crosswall**, at Y=±[17.75,22.25], Z=[26.65,31.15]. Keep the carrier, tie passages, motor/S9 datums and half-cage split unchanged. The pockets overlap the broad window slightly, creating stepped extensions rather than isolated holes. These dimensions are a measured-clearance engineering adaptation; the movie does not provide the 2 mm height change or pocket pattern.

**Assessment: a reasonable bounded correction.** Each pocket provides 0.20 mm nominal allowance beyond the measured intersection on both Y ends and 0.25 mm on both Z ends. Since the offending material crosses the crosswall thickness, the pockets must be genuine through-cuts in that new wall, not blind cosmetic recesses. The nominal remaining upper rail is **33−31.15=1.85 mm** high; the outer stile width is **28.4−22.25=6.15 mm**. Keeping the negative-X wall free of unnecessary pockets is appropriate. Raising both cheek and crosswall top together preserves their connected upper corner.

Remaining specific risks and checks:

- **Narrow rail strength:** a 1.85 mm high × 1.6 mm thick rail remains geometrically continuous, but continuity does not establish adequate printed stiffness or fatigue resistance. Its corners and adjoining split-panel cantilever remain local stress concentrations. Retain this as a structural limitation; no additional height or thickness is mandated without loads or deformation evidence.
- **Nominal allowance versus manufactured fit:** 0.20/0.25 mm is positive CAD clearance, not a verified tolerance allowance for printed warp, clamp placement, fastener eccentricity or thread-major geometry. Confirm the changed neutral model uses actual carrier/bolt envelopes and record the available minimum gap. Do not add inward corner fillets that consume the small clearance; any blend must keep the measured keepout envelope clear.
- **New material in motion:** Z=31…33 adds grounded material to both cheeks/crosswalls. It needs a fresh moving-link/shaft/cap clearance check, despite the carrier itself being fixed. Earlier neutral or motion results for Z≤31 cannot validate that addition. The existing C reliefs and upper tie passages should also be checked for surviving positive wall continuity after the merged pockets.
- **Assembly and tool access:** these dimensions establish material clearance for the reported clamp/bolt bounds. They do not certify a screwdriver envelope or the sequence for installing/removing the carrier clamps. The clamp bolt axes are world-X directed in `controller_carrier_r07.py`, while the crosswalls use rotated case-local X, so a tool-access claim needs the real axis/path view. Describe the features as **carrier-clearance pockets** until that access is shown.

The face-ownership correction remains intact: the broad window stays on the transverse crosswall and the horn opening stays on the sagittal cheek. The small measured pocket/height adaptation is not a reason to move the controller or mechanism datums. No new source-fidelity metric dimension, native pass, motion pass or fabrication approval is asserted by this report update.
