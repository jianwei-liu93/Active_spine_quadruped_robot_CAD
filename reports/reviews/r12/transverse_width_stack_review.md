# r12 transverse center-frame stack review

2026-10-13. Independent static review against frozen r10 sources/parameters and BOM; no FreeCAD/Blender session, geometry edit, CAD collision test, or physical validation. All proposed metric changes below are **DESIGN_ASSUMPTION**. User rejection of the r11 fork takes precedence. This review does not introduce a new mechanism edge or alter S9 X/Z datums.

## Recommendation

Freeze **guide centers Y=±38.6 mm**, 1.6 mm guide thickness, giving the grounded frame **Y=±39.4 mm / 78.8 mm span**, versus r09/r10 ±41 / 82. This is a modest 3.2 mm reduction that preserves the existing four independent link layers and actual motor envelopes. Apply the lead-selected central-E-only ownership, remove the orphaned D outer bearing, and shorten D retention and A/C shaft/capture stacks together. Do not obtain a nominally narrower frame by leaving the original projecting hardware in place.

Do **not** freeze guide centers ±37.8 / frame span77.2 with the retained bearing/clip design. Its inner guide face is |Y|37.0; even the shortened D clip proposed below extends to37.4. D's sagittal center passes close to the guide aperture, so axial overlap cannot be dismissed as harmless. A lower width would require another explicit retention/guide design and new clearance evidence.

## Evidence and ownership

- `parameters/candidate_r02.json`, `src/build_flexor.py`: two actual motor envelopes are20×26×34 at Y=±13.4, hence occupied Y bands±[0.4,26.4]. Their26 mm transverse depth cannot be treated as20 mm. Existing case cheeks are±[26.8,28.4], keeping0.4 nominal clearance from each case. Preserve these cheeks and56.8 mm housing span.
- `src/build_flexor.py`: L2/L3 centers30.6/32.4 swap between branches; L4=34.2 and L5=36.0, each1.2 thick. The0.6 gaps between neighboring layers remain intact. No new half-length rocker cheeks or offset link layer is needed for this reduction.
- `src/build_torso_r03.py`: deletes the four original L6 links when the torso becomes the E–D output member, but leaves their old D bearings at37.8 and D spacers at36.9. The actual D load path is the L5 bearing at36 and torso bearing at15.2. The37.8 bearing has no remaining bearing seat/owning L6 body and should not be approved as a floating bearing.
- `src/spine_frame_r09.py`: outer guide plates and E tube/boss pads reach±41. `src/spine_frame_r10.py` plus `src/central_joint_hardware_r10.py` adds grounded central E bearings at±1 and a moving clevis at±2.8, pin and capture, while retaining the complete older outer E system. Parameter `central_attachment_r10.outer_E_supports` explicitly records that retention; retiring it requires a deliberate revision record.
- `bom/instances_r10.csv` supplies the static world Y bounds quoted here. `reports/reviews/r12/source_part_ownership_and_shapes.md` supports simpler independent bars and reassessment of inherited outer E tubes; it does not establish hidden bearing dimensions.

## Proposed frozen positive-Y stack (negative side mirrored)

| Axis/component | Proposed Y extent or center, mm | Required ownership |
|---|---:|---|
| Motor body |0.4…26.4|Unchanged real26 mm depth|
| Case cheek / inner A bearing |26.8…28.4 /27.0…28.2|Existing frame seat|
| L2 / L3 / L4 / L5 |30.0…31.2 /31.8…33.0 /33.6…34.8 /35.4…36.6|Existing independent links; L2/L3 order swaps by branch|
| Guide plate |37.8…39.4, center38.6|Integral frame; shorten shelf reach11→9.4|
| Guide liners |37.8…38.1 and39.1…39.4|Shift both original liner bands inward1.6|
| Outer A bearing / C guide roller |38.0…39.2, center38.6|A bearing seated in plate; C roller translates in guide slot|
| A1/A2 outer spacer |33.0…38.0 L5.0 /31.2…38.0 L6.8|Bridge actual link bearing to outer A bearing|
| C spacer between L5 and roller |36.6…38.0, L1.4|Replace original L3.0; retain L4–L5 spacer34.8…35.4|
| A/C crossshafts |−41.2…41.2, L82.4|Shorten original85.6 by3.2; keep center shoulders54.0(A),67.2(C)|
| A/C outer clips |40.4…41.0, center40.7|Regenerate matching end grooves|
| A/C capture caps |39.6…42.0, center40.8|Keep recessed clip capture;0.2 nominal gap from guide outer face|
| D torso bearing / long inner spacer |14.6…15.8 /16.0…35.4|Existing torso ear / separate spacer|
| D L5 bearing |35.4…36.6, center36.0|Existing L5 seat; retain|
| D outer clip |36.8…37.4, center37.1|Regrooved shortened pin;0.2 gap to L5 bearing,0.4 to guide inner face|
| D pin |13.6…37.6, L24.0|Keep inner clip center14.1; replace shared legacy D/E source for D instances only|
| E |Central r10 stack unchanged; pin±4.6|Retain central bearings, lug, moving clevis, washers and clips; retire complete older outer E stack|

The guide cap envelope becomes **84.0 mm**, from87.2; the ground-frame-only span is78.8. Whole-robot width remains governed by other assemblies; neither number is a whole-robot envelope claim. The existing case cheeks, central E beam span56.8 and central E joint stack stay fixed.

## Hard risks and lead checks

1. **D versus guide:** retaining original D pin to39.4/clip38.6…39.2 conflicts axially with the narrowed guide. Removing only Bearing1 is insufficient. A Python-only3601-phase evaluation of the existing planar solver found |D.z−C.z|=0.4625…2.3400 mm for both branches. This calculation identifies a concrete guide-aperture risk; it is not a CAD sweep. The proposed D capture lies fully inboard of the38.6 guide, avoiding that axial overlap without relying on aperture coincidence.
2. **Orphan supports:** remove the D37.8 bearing and adjacent36.6…37.2 spacer together. Remove E pin, three bearings, two spacers and both clips per old side stack together with inherited outer E tube material; never leave an old bearing behind after deleting its seat or shaft. Preserve the existing central E lug seats and clevis connection. Remove all four older torso E ears at±15.2 with that hardware. Retain all four D ears, the two central clevis ears per torso at±2.8, and all14 central E hardware instances. This leaves a single physical support scheme about each existing E axis.
3. **Central E stiffness and assembly:** central E is an already modeled coaxial alternative, so retiring outer E does not invent kinematics. The remaining load path is grounded shelf/crossmember → central lug/bearings → central pin/clevis → transverse torso plate; L5 → D pin → retained D ears drives that torso about E. There is no new pivot or rigid merger of independent links. Two grounded E bearings at±1 support one coaxial journal, rather than a second commanded joint. Removing outer E support concentrates loads at the narrow central lug and places the long D journal between bearing centers15.2 and36.0 (20.8 mm separation). Actual shaft bending, bearing reactions, lug/clevis/plate stiffness, bearing fits, pin axial retention, and insertion access remain unresolved. Recompute the complete torso solids after removing E ears: their deletion must not detach a retained plate/motor support, and the retained central clevis stems must remain united with the plate. Native one-solid checks, sampled motion checks and unchanged solver coordinates address geometry/topology only; they cannot qualify this load path for fabrication.
4. **A/C whole stack:** a moved guide requires matching A spacer lengths, C spacer length, roller/outer-bearing positions, both liners, groove locations, caps and MotionMap values. Preserve C shoulder ends±33.6 so its large center shaft still stops at the L4 bearings. Preserve the A center shoulder ends±27.0. Shorten shaft end portions only.
5. **Geometry construction:** source-local frame transform remains(X,Y,Z)=(worldX,worldZ,28.4−worldY). New whole-stack cut limits become local Z=−11.0…67.8 (depth78.8). Shorten broad shelves to9.4 and place guide thicknesses against those shelves; do not merely move disconnected plates. Remove/trim `ShelfJournalBossE*` exterior extensions, otherwise frame width stays82 despite moved guides. Preserve sufficient connected shelf root and the central beam. Regenerate then check native connectedness, seated bearings, intended contact pairs, full affected motion, and export/animation identity coverage through the lead.

## Exact affected identities

Retain all unaffected physical IDs. The following names use literal r10 FreeCAD names, including double underscores on the negative side.

- Frame physical ID: `LumbarIntegrated1`. Its source is `FRM_LUMBAR_MONOLITHIC_CAGE_r09`; revise `LeftBroadShelf0/1`, `RightBroadShelf0/1`, `LeftOuterGuide0/1`, `RightOuterGuide0/1`, `LeftShelfJournalBossE1/E2`, `RightShelfJournalBossE1/E2`, `WholeStackJournalClearances`, `C1TravelRelief`, `C2TravelRelief` features (each preceded by the source name plus `_`). Central E beam/lug/seat dimensions are retained.
- Shaft IDs: `ThroughA1`, `ThroughA2`, `ThroughC1`, `ThroughC2`.
- A spacer IDs: `A1_1_OuterSpacer`, `A1__1_OuterSpacer`, `A2_1_OuterSpacer`, `A2__1_OuterSpacer`.
- A outer-bearing IDs: `A1_1_OuterBearing`, `A1__1_OuterBearing`, `A2_1_OuterBearing`, `A2__1_OuterBearing`.
- C roller IDs: `C1_1_Bearing2`, `C1__1_Bearing2`, `C2_1_Bearing2`, `C2__1_Bearing2`.
- C spacer IDs: `C1_1_Spacer1`, `C1__1_Spacer1`, `C2_1_Spacer1`, `C2__1_Spacer1`.
- A/C cap IDs: `A1_1_CaptureCap`, `A1__1_CaptureCap`, `A2_1_CaptureCap`, `A2__1_CaptureCap`, `C1_1_CaptureWasher`, `C1__1_CaptureWasher`, `C2_1_CaptureWasher`, `C2__1_CaptureWasher`.
- A/C outer-clip IDs: `A1_1_Retainer1`, `A1__1_Retainer0`, `A2_1_Retainer1`, `A2__1_Retainer0`, `C1_1_Retainer1`, `C1__1_Retainer0`, `C2_1_Retainer1`, `C2__1_Retainer0`.
- Liner IDs: `GuideLiner1_1_0_65`, `GuideLiner1_1__0_65`, `GuideLiner1__1_0_65`, `GuideLiner1__1__0_65`, `GuideLiner2_1_0_65`, `GuideLiner2_1__0_65`, `GuideLiner2__1_0_65`, `GuideLiner2__1__0_65`.
- D pin IDs: `D1_1_Pin`, `D1__1_Pin`, `D2_1_Pin`, `D2__1_Pin`; outer-clip IDs: `D1_1_Retainer1`, `D1__1_Retainer0`, `D2_1_Retainer1`, `D2__1_Retainer0`. Retire `D1_1_Bearing1`, `D1__1_Bearing1`, `D2_1_Bearing1`, `D2__1_Bearing1`, `D1_1_Spacer0`, `D1__1_Spacer0`, `D2_1_Spacer0`, `D2__1_Spacer0`.
- Torso physical IDs `Torso_fore`, `Torso_hind`: remove native features `TORSO_FORE_TRANSVERSE_FRAME_r06_EarE0`, `TORSO_FORE_TRANSVERSE_FRAME_r06_EarE1`, `TORSO_HIND_TRANSVERSE_FRAME_r06_EarE0`, `TORSO_HIND_TRANSVERSE_FRAME_r06_EarE1` and their owned profiles during coherent source rebuilding. Preserve `EarD0/1`, each source's `CentralClevisEar0_r10` and `CentralClevisEar1_r10`, source-local frames and link placement.
- Retire older E hardware: for each exact prefix `E1_1`, `E1__1`, `E2_1`, `E2__1`, remove all eight exact suffixes `_Pin`, `_Bearing0`, `_Bearing1`, `_TorsoBearing`, `_Spacer0`, `_TorsoSpacer`, `_Retainer0`, `_Retainer1` (32 physical IDs). Preserve every `CentralE1_*` and `CentralE2_*` physical ID.

Stable part-local frames and updated MotionMap entries are required for moved C/D parts; remove only explicitly retired IDs from those maps and BOMs. This document recommends a reviewable stack; lead execution and verification remain pending.

## 2026-10-14 addendum — organic A–B, single A eye and B-only fork

Bounded static geometry follow-up requested by the lead. The current `src/spine_bars_r12.py` replaces the earlier rocker interpretation with an organic four-arc A–B outline, **single A eye and terminal fork only at B**. This addendum evaluates that actual source footprint; it does not restore the rejected long alternating fork. No CAD execution or source/parameter edits were performed by this reviewer.

**Recommend opening depth8 mm / maximum inward reach10 mm**, preserving the rounded root and organic outline. The present3.5/5.5 mm settings necessarily intersect the B–C end eye, and also intersect the branch2 G–B bar. A much shorter6/8 mm option has only0.224 mm nominal planar separation from G–B in this sampled calculation;8/10 provides1.977 mm and is the more credible provisional selection before lead OCC checks. These are selected design dimensions, not measurements recovered from the imagery.

Coordinate `d` runs from B toward A; transverse planar coordinate `v` is perpendicular to B→A. The source bridge is precisely the intersection of:

- the organic A–B outline (length24.1215, end radius4, minimum waist width6);
- a width8 capsule whose root center is `d=reach−4` and whose other center is B;
- `depth≤d≤reach`.

Thus8/10 uses a capsule center atd6 and a rounded tip atd10, not a rectangular bridge with arbitrary full-width corners. Its organic half-width at bridge entryd8 is3.11919 mm; the rounded root further narrows towardd10. The added cheek remains confined to this terminal region and A remains a single eye.

Pure Python evaluated the frozen `candidate_r02.json` planar solver at361 phases,0…360° in1° increments. For each phase it expressed B→C (radius4 capsule, both branches) and B→G (radius3 capsule, branch2 only) in this coordinate frame. Branch2 G–B lies inside the axial span between its A–B base at|Y|30.6 and added cheek36; branch1 G–B at30.6 lies inboard of its A–B base32.4, so it is not the corresponding bridge interference. B–C at34.2 lies inside both bridges. The B bore radius2.025 cannot remove an intersection atd≥3.5, because every such bridge point is already outside that bore.

| Opening depth / reach, mm | Minimum bridge-to-BC capsule signed separation, mm | Minimum bridge-to-branch2-GB capsule signed separation, mm |
|---|---:|---:|
|3.5 /5.5|−0.50000|−1.97457|
|5.5 /7.5|1.50000|−0.21882|
|5.7 /7.7|1.70000|−0.04133|
|5.8 /7.8|1.80000|0.04730|
|6 /8|2.00000|0.22431|
|8 /10|4.00000|1.97682|

Here signed separation is the minimum Euclidean distance from bridge material to the opposing link center segment, minus that link's capsule radius. A negative value denotes overlap of the planar envelopes; it is not an OCC intersection volume. B–C recesses do not excuse the current overlap: the3.5 mm bridge entry crosses its solid B end-eye annulus between radii2.025 and4. This occurs independently of link angle and therefore at every sampled pose (indeed, the fixed shared B eye alone establishes it).

The sampled B→A / B→C angles are91.3425…126.4182°. As the C segment lies in the negative-d half-plane, its nearest point to the bridge at(d,0) is B and the exact minimum capsule margin is `depth−4`. The sampled branch2 B→A / B→G angle reaches its minimum **56.72346° at phase196°**. For these bridge ranges the half-width `h(d)` decreases toward the rounded root and the nearest G–B point lies within its finite segment. Its minimum margin therefore occurs at bridge entry and equals `depth·sin(angle)−h(depth)·cos(angle)−3`. Solving that expression at the sampled worst angle gives a **zero-margin threshold5.74662 mm** for the family `reach=depth+2`. This is a mathematical nominal threshold, not a recommended clearance or tolerance allowance.

The lead still owns actual native/OCC checks of the full base/bridge/leaf, all four physical rocker copies, bearings/spacers/retainers, adjacent links, and the requested motion domain. The margins above cover only the two specified sagittal capsule families and sampled solver angles; they do not establish fabrication fit, strength, unsampled global clearance, or the absence of other interference. No physical ID, S9 datum, source-local frame, motor geometry, or parameter file was changed for this analysis.
