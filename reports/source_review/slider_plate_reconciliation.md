# Fixed slider plate source reconciliation

Reviewed 2026-10-11. **The user's correction is supported: r02 has the right fixed horizontal tracks, but the visible guide-support plates still have the wrong morphology.** They should be tall contoured ears of the ground spine frame, joining a rounded slot lobe to the adjacent fixed A journal and the lumbar rail. The current rounded capsule plus small rectangular central pedestal omits that journal-bearing ear. It is not sufficient to recolor the present capsule or attach it to a rotating torso.

Requested/current reviewer role: inherited Sol/high; actual routing is not independently observable. This is a bounded source/static-code review. Only this report was authored; no CAD, schema or shared source was modified.

## Sources inspected

- User attachments `/tmp/codex-clipboard-463c39bc-3d0f-4dcb-8b91-f4dfb8297e81.png` (whole reference rendering) and `/tmp/codex-clipboard-0558b726-63f4-419a-84eb-746da0926f19.png` (lower-right guide close-up).
- Original main paper, `active_spine_robot_paper/2026_Unlocking fast robotic locomotor propulsion throughdynamic spine-leg synergy.pdf`, printed/PDF p. 5 Fig. 2A, inspected from its existing full-page render `/tmp/spine-source-review/main-05.png`.
- Original supplement, corresponding `_sm.pdf`: PDF p. 30 Fig. S9, inspected in the earlier review and used here for the A/C point map; PDF pp. 16-17, “Design and fabrication of spine and legs,” text re-extracted directly with `pdftotext -layout`.
- Original `active_spine_robot_paper/sciadv.aed5603_movies_s1_to_s14/aed5603_movie_s2.mp4`: freshly extracted and visually inspected frames at **9.5, 11.5 and 12.5 seconds**. Temporary frames are `/tmp/slider_movie_s2_9p5.png`, `_11p5.png`, `_12p5.png`. Also inspected the existing 10.5-second pack frame and `/tmp/flexor_movie2_spine.png`. These are discrete source-frame checks, not exhaustive video motion analysis.
- Current `src/build_flexor.py`, `src/refine_flexor.py`, relevant retained-journal implementation, and saved `reports/views/r02_neutral_side.png`. The previously inspected r02 isometric/extreme views provide axial context.

The PDF skill was used for read-only source inspection. No dimensions were inferred from perspective pixels as manufacturing facts.

## Observed arrangement versus unknown details

| Item | Supported observation / interpretation | Not established by the source |
|---|---|---|
| Fixed or moving plate | The elongated copper-lined slots are features of the central ground spine frame. Movie frames show the fore/hind torso moving beside them while slot supports and A journals retain their relationship to the central spine. SI explicitly integrates servo slots, rotary holes and linear sliding holes in the printed spine frame. | Exact part seams, fastener pattern and whether every visible outer ear is manufactured in the same printed piece as the whole lumbar frame. |
| Right/lower track C2 | Its visible black plate continues **upward** into a rounded/tapered ear carrying fixed **A1**, the endpoint of the white A1-B1 rocker. This is not D2 or the E2 torso pivot. | Exact contour, fillet radii, thickness and journal fit. |
| Left/upper track C1 | Its support continues **downward** toward fixed **A2**, the endpoint of the white A2-B2 rocker, as the centrally symmetric counterpart. | Exact handed manufacturing identity or whether axial offsets differ between copies. |
| Slot lobe | Rounded rectangular outer lobe, rounded rectangular copper liner, dark open track, broad silver moving pin/washer at C. The source ear is more than a slot outline: it has a substantial tapered web to the fixed journal/rail. | End reserve, slot width, liner wall/face thickness, adhesive/press-fit/screw retention and local stiffness. |
| Axial order | At the fixed A journal, the visible outer plate/washer is outside the white A-B rocker; the rod lies inward behind the ear. At C, a visible outer moving washer/head covers the local roller/pin stack. The long slot and copper ring remain stationary. | Exact sequence/count of bearings, washers and spacers hidden behind the plate; pin shoulder/groove dimensions or which race receives clamp load. |
| Bearing and copper interface | SI specifies rounded rectangular copper rings on **both inner and outer faces** and **2 mm ID / 4 mm OD bearings**, with small clearance. | Bearing width/type, material tolerances and a numeric running clearance. The 1.9 mm ×8 mm reported pin belongs to the crank and must not be copied indiscriminately to C/A journals. |

The A1/A2 mapping is supported jointly by S9 graph identities and the movie's visible white rocker endpoints. The perspective close-up alone would not uniquely identify the joint or precise mounting dimensions.

## Concrete correction for the current implementation

`src/refine_flexor.py` currently builds each boss from a horizontal `pill_face(...,8.2)` plus a **6×4 mm rectangular tab** near z=±2.5, then supports it with two 11 mm posts. The result shown in `r02_neutral_side.png` is an obround with a short square pedestal; it lacks the source's tall A-journal ear. The original independent `GuideFrame` capsules in `build_flexor.py` are removed by refinement, so modifying only their initial profiles will not correct the saved result.

Replace that final refined guide-face construction with an editable contoured plate per track and side:

1. Preserve the solved track centers and horizontal directions: C1 at z=+8.66, C2 at z=-8.66. Preserve O/A/E and all rigid link center distances.
2. Extend the **C2** slot plate to **A1=(+30,+8.66)** and the **C1** slot plate to **A2=(-30,-8.66)** with a rounded journal boss and tapered/angular web. Current sampled track midpoints are approximately (+27.7074,-8.66) and (-27.7074,+8.66), so the corresponding A journals are offset by **(±2.2926, ±17.32) mm**. Those offsets derive from this candidate; they are not new paper-reported dimensions.
3. Ground each ear rigidly to its lumbar side structure using a continuous shaped bridge or defined fixed attachment. The A hole locates a fixed rocker axis; bearing-mounting an otherwise free plate on that pin would add an unintended rotational coordinate. Keep the bridge inward toward O and behind the central white links. Do not add a broad beam across their foreground sweep.
4. Retain the visible outer plate layer near y=±40.2 as a candidate stack choice. Extend A journals and add the appropriate outer support/bearing seat, spacers and positive retention so the white A-B rocker turns between supports without being squeezed. Preserve the source-visible rod-behind-ear order. Exact widths, fits and clip dimensions remain engineering assumptions.
5. Keep two stationary copper face liners and the moving C bearing/pin/washer assembly distinct. Relocate neither liner with C nor plate with beta/torso pose. Provide an explicit liner recess/retention interface and enough washer overlap to capture the moving journal while allowing the declared guide endplay.
6. Record contour/bridge/stack dimensions and provenance in the authoritative candidate schema, and implement the same geometry in the fresh-build path. The source does not justify silently moving the tracks or pivots to suit the desired silhouette.

## Checks required after correction

- Save matched side, opposite-side, isometric and section views. Compare the slot lobe, A-journal ear, tapered web and rod-behind-ear order with the attached close-up and Movie S2 frame. Check both symmetric tracks, not only the visible right side.
- Read actual native A/C hole centers and axes; confirm A1/A2 coincide across inner frame, outer guide plate and rocker bearings. Confirm guide lines remain horizontal at ±8.66 for all phases and the support plates have no torso-dependent placement.
- Verify each integrated custom part has one valid solid, with a continuous load path from roller contact to slot plate/web/ground frame. Check bores, liner capture, journal shoulder/clip engagement and a nonbinding axial clamp path in section.
- Rerun the full-cycle copied-native-shape sweep for changed plates, bridges, A pins/clips, C hardware and adjacent L3/L4/L5 links, then refine near any small clearance. Report minimum actual distances and allowances in addition to intersection volume. New A support and bridge material can collide with the rocker despite an unchanged solver.
- Recheck branch/length residuals, schema/source rebuild consistency, native save/reopen and parameter change/restore where supported. Do not reuse the old spine sweep as evidence for the new silhouette and stack.

No CAD clearance or manufacturing pass is claimed by this source reconciliation. Supplier fits and hidden stack details remain unresolved; the observed morphology and fixed-frame ownership are clear enough to implement a reviewable correction without inventing them.

## Implemented correction review — 2026-10-11

**Morphology finding resolved for the reviewable candidate.** The actual `reports/views/r02_slider_plate_side.png` now shows the tall lower-right C2/A1 ear, upper-left C1/A2 counterpart, rounded A journal bosses, tapered webs, stationary copper-lined slot lobes and moving broad C caps. Their locations and visible rod-behind-ear order agree with the supplied close-up and previously inspected Movie S2 frames. Exact outline radii and thickness remain declared engineering assumptions. No new blocking graph or neutral-stack error was found in this bounded static review.

Inspected the updated `src/refine_flexor.py`, `src/slider_plate_flexor.py`, relevant `candidate_r02.json` fields, `build_flexor.build` integration order, neutral report, actual side PNG and selected saved `cad/flexor_r02_spine.FCStd` XML records. The new final guide-face construction uses the appropriate opposite A journal for each C track. The existing integrated axial posts rigidly connect the ears to the inner lumbar frame; they are not free plates supported only on a bearing at A. Fixed A journals/outer bearings have no moving MotionMap entries. C shafts, clips and washers do have C-driven entries. The fresh-build sequence calls refinement, retention and slider-plate recovery in that order.

The saved positive-side stack is internally consistent at nominal dimensions:

- A journal: 15.8 mm long, y=26.0…41.8; outer bearing y=39.6…40.8 and outer clip y=41.0…41.6. That clip occupies the corresponding end groove, leaving a 0.2 mm shaft-end land. The added outer spacers bridge to the existing inner rocker stack. The fixed outer ear occupies y=39.4…41.0.
- C journal: 10.2 mm long, y=32.6…42.8; outer capture washer y=41.2…41.8 and outer clip y=42.0…42.6, likewise aligned with its end groove. The 6 mm washer overlaps the 4.2 mm slot by **0.9 mm nominal radial margin** at the straight slot edges. Its inner face has **0.2 mm nominal axial clearance** from the outer plate face. These are designed nominal allowances, not supplier/tolerance verification.

Saved XML confirms these source links and placements and contains 27 native Body definitions. `r02_slider_plate_neutral.json` records **190 instances, zero raw neutral overlaps, 394 narrowphase checks, no exceptions, 1e−5 mm³ volume threshold**. The lead additionally reports valid single solids and fully constrained sketches; those CAD checks were not rerun independently here.

**Remaining local release issue:** the copper liners are seated flush within the 5.2 mm opening but have no specified bonding, interference-fit allowance, flange or other axial retention process. Matching nominal edges does not establish capture or an adequate tolerance fit. Select and document that process/interface, including liner replacement and allowance effects on the 4 mm roller's running clearance. This is a precise fabrication limitation; it does not negate the corrected morphology or require inventing a supplier drawing.

The 361-pose check was still in progress and no final slider-plate sweep report was available at this inspection. Thus neutral overlap PASS is not a full-cycle clearance PASS. Inspect the completed sweep and refine around any offending plate/link/journal pair before promoting motion acceptance. Also regenerate the isometric/opposite-side views with the corrected orientation and final parts so they agree with the inspected side view. Source rebuild/native reopen, full 3D bore-axis extraction, minimum-distance verification, journal/clip strength and tolerance/endplay checks remain separate evidence tasks.

Dependent body geometry can use this corrected plate arrangement, with the E/output attachment reservations and unresolved horn interface preserved. This resolution neither approves fabrication nor certifies hidden supplier interfaces. Only this resolution section was appended; no model, parameter or source changes were made by the reviewer.

### Lead integration evidence after review

The final isolated sweep completed after the independent review:361 poses at1° spacing,76,378 narrowphase checks,zero overlaps above1e-5mm³,without exceptions (`reports/verification/r02_spine_sweep.json`). Actual neutral interface measurements, native thickness edit/restore, fresh source rebuild and native/STEP reopen reports are saved beside it. The liner identity is now copper as stated in the supplement. These are lead-run integration checks, not a claim the reviewer reran CAD or approved fabrication. Liner retention, supplier fits and horn coupling remain open.
