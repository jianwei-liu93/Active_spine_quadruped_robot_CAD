# r11 — Movie S1 linkage construction review

**Superseded after user review (2026-10-13).** The user rejected the long staggered cheeks. Later steering confirms compact A–B terminal forks in the source; the rejected r11 geometry must not be treated as accepted. See the r12 source review and compact-frame revision. Historical checks below apply only to r11. Fresh-source reproduction passed; the disposable native edit/restore probe failed a bounding-box identity check, and the larger motion run stopped after 664 completed states. No full r11 acceptance or fabrication release is claimed.

The r11 candidate corrects the three-dimensional spine linkage construction. It preserves the r10 one-piece lumbar frame, central E attachments, torso ownership, S9 pivot locations, distinct leg mechanisms, seven motors and six commanded coordinates. It is a reconstructed research CAD candidate, not an exact recovered drawing set or fabrication release.

## Source review

Reviewed the complete requested Movie S1 interval, 51–80 s, including 19 full-resolution extracts and three contact sheets in `references/visual/r11_movie_s1/`. The provenance file records the source hash and requested seek times; exact frame PTS was not independently recovered. Compared native r10 geometry/source assignments and the supplement Fig. S9. Independent reviews are in `reports/reviews/r11/`.

| Feature | Source observation | r11 disposition |
|---|---|---|
| A–B rockers, 54–55 s | Local parallel cheeks and end-opening slits; a connected web, rather than uniform thin plates | Four individually editable, handed native local-clevis sources; retain four existing physical instance IDs |
| B–C bars, 56 s and later views | Broad bounded relieved face, apparently with a floor; backside/depth partly hidden | Wider profile and a blind rounded rectangular recess with retained floor; separately cut through-bearing bores |
| Ternary B joint, 57–58 s | Independent A–B, G–B and B–C members meet at one axis; transverse shaft inserted afterward | Retain all three independent members. Local fork encloses the incident tongue(s), with an added cheek bearing, spacer, longer shaft and moved retainer |
| A grounded joint | Rocker surrounds a dark fixed upstand | Local inboard cheek encloses the existing ground support; added bearing/spacer and shortened central shaft shoulder |
| Cross-shafts, 58 s | Full-width rods/journals and distinct end/collar regions | Retain real separate A/B/C shafts. Revise only A shoulders and B journal length/capture; exact film material, threads and retention remain unknown |
| Black center frame, 53–60 s | Integrated cage, shelves, upright A supports and C slot ears | Retain the r10 single manufactured solid and its central E crossmembers/lugs; do not restore obsolete split frame or extra moving links |
| Torso plates, 59–60 s | Separate output plates fitted after links and shafts | Retain the corrected r10 slotted plates and moving central clevises on existing E axes; metric slot pattern and hidden bearing stack remain assumptions |
| C–D short connector | Short connector visible, but exact end section mostly occluded | Retain current functional connector; do not invent a universal fork from an obscured view |

The film supports local fork morphology strongly at the visible B end. A-end ownership and long-link blind recess are reconstructed interpretations with less complete visibility. It does not establish exact millimetre dimensions, material, bearings, press fits, hidden fasteners, tolerances or load capacity. Red skeletons, arrows, translucent alternate poses and assembly ghosts are explanatory graphics, not extra manufactured links.

## Frozen section and joint assumptions

All new dimensions are `DESIGN_ASSUMPTION`, versioned in `parameters/assembly_r11.json`.

- Physical bar width is 8 mm; the pose frame remains the legacy 6 × 1.2 mm frame. First source-local bore remains (3,3); the second is (length+3,3). This avoids moving either pivot when changing the outline.
- Main and added cheeks are 1.2 mm thick. The fork is clear to 8 mm from each pivot along the link, with a connecting bridge at 8–10 mm. Rounded added-cheek ends extend to 14 mm from the pivot. Each rocker remains one connected manufactured solid; a cheek is not a new linkage.
- Each A added cheek/bearing is centered at |Y|=25.8 mm. The 0.6 mm spacer at 26.7 mm fills 26.4–27.0 mm to the retained ground bearing. The A shaft's center shoulder spans 50.4 mm, tangent to the added bearing inner faces at |Y|=25.2 mm. Overall shaft and outer capture locations remain unchanged.
- Each B added cheek/bearing is centered at |Y|=36.0 mm. A 0.6 mm spacer at 36.9 mm fills 36.6–37.2 mm. The 76.0 mm shaft has centered 60 mm shoulder and clip grooves centered at |Y|=37.5 mm. Retainers occupy 37.2–37.8 mm, with 0.2 mm shaft end land. Existing bearings and intermediate spacers remain separate.
- On branch 1, the B fork surrounds the long-link tongue; the G–B member is adjacent to the main cheek. On branch 2, both G–B and B–C tongues lie inside the B fork. This is a packaging assumption that preserves the two distinct crank-pin layers and planar closure.
- Long-link relief is 0.6 mm deep in a 1.2 mm section, retaining a 0.6 mm floor. Relief width is 3.2 mm with 0.7 mm corner radii, inset 5.5 mm from the bores. The bore ligament is 1.975 mm at the 8 mm ends. Rail width beside the recess is 2.4 mm.

The nominal stack establishes geometric support and capture candidates. Bearing outer-race retention, race-specific thrust paths, floating support allowances, alignment, actual journal/seat fits, clip standard/tool access, fork-root stress, thin-floor stiffness and fatigue remain fabrication blockers. Tangent nominal surfaces and absence of intersection are not fit or capacity validation.

## Actual implementation and checks

Canonical candidate: `cad/flexor_r11_robot.FCStd`; generator: `src/build_robot_r11.py` and `src/spine_link_sections_r11.py`.

The initial integrated checkpoint has 503 physical instances, 110 used sources, 98 native PartDesign Bodies and 344 fully constrained sketches. All 487 existing physical IDs remain; 16 added bearing/spacer IDs are explicit. Sixteen existing instances have changed geometry or axial capture placement. The 471 unaffected instances pass strict source **and** placed-solid identity comparison against frozen r10. All eight bar instance transforms and MotionMap segments retain their pivot datum.

- `reports/verification/r11_integration.json`: exact source/instance migration and section contract.
- `reports/verification/r11_s9_topology.json`: native topology and bore-axis audit PASS, no extra/missing edges; maximum projected axis error about 1.5e-14 mm.
- `reports/verification/r11_bounded_screen.json`: 13 fixed-leg spine phases, 15,568 unique affected pairs per pose, 3,014 OCC checks, no overlaps. This initial report uses the earlier verifier implementation hash, before its later lazy/cache optimization.
- `reports/animation/ax01_r11.json` and `animation/motion/ax01_r11.json`: AX0/AX1 PASS for neutral and two non-neutral poses; all 503 instances covered, separate prescribed knees and regenerated spring/cable state. Source-to-world transforms verified; maximum source vertex reprojection error below 1e-12 mm.
- `reports/views/r11_*`: actual MCP CAD captures, including isolated fork ends, recessed long bar, central attachments, assembled spine and robot. View operations restore geometry/pose and do not overwrite the frozen native file.

The broader revision-specific affected-pair check, native reopen/edit/restore, source reproduction and STEP round trip are tracked separately. Their status must come from their actual reports, not from the initial checks above. Historical r10 clearance/export evidence remains valid for r10. Old Blender scenes/videos stay r10 and must be regenerated deliberately before presenting r11 geometry.

## Runtime recovery

The original FreeCAD GUI stopped dispatching queued tasks; the native r11 edit request never started. Health RPC remained responsive. Preserved recovery data and diagnostics under ignored `reports/tmp/r11/`, restarted only the stalled project session, and reopened the saved r10/r11 files. The corrected native integration then ran successfully through the installed MCP. No headless process wrote the canonical model.
