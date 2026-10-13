# r11 bounded local-fork stack review

2026-10-13. **Disposition: mechanically plausible candidate, with a 7 mm opening preferred; no fundamental projected bridge/upstand or bridge/rod collision found in the bounded numerical screening.** This is not OCC clearance, native-solid validity, fit or strength approval. All new millimetre values are `DESIGN_ASSUMPTION`.

Read-only review of the proposed local L3 forks against current r10 generator/parameters, `spine_frame_r09.py`, `spine_shafts_r04.py`, `retain_flexor.py`, the saved r10 XML and previously inspected S1 54–60/66/74 s frames. No live CAD operation or source/native/schema edit. Only this report was written. The source supports local fork morphology; it does not establish the proposed cheek planes, 7/10 mm extents or bearing layout.

## Proposed axial section and necessary corrections

Use absolute Y below; negative-side geometry is its handed counterpart. Main L3 plate and its current segment MotionMap stay unchanged.

| Location | Proposed occupied interval, mm | Consequence |
|---|---|---|
| Added A cheek, center 25.8, thickness 1.2 | 25.2…26.4 | 0.4 mm nominal gap to the ground upstand starting at 26.8. The existing inner journal boss/upstand at 26.8…28.4 fits within the opening. |
| Branch 1 existing main L3 cheek | 31.8…33.0 | A clear internal fork span 26.4…31.8. Existing A spacer spans 28.2…31.8. |
| Branch 2 existing main L3 cheek | 30.0…31.2 | A clear internal fork span 26.4…30.0. Existing A spacer spans 28.2…30.0. |
| Added B cheek, center 36.0, thickness 1.2 | 35.4…36.6 | 0.6 mm nominal gap to L4 ending at 34.8; requires an additional bearing and revised outer capture. |
| Branch 1 B fork opening | 33.0…35.4 | Contains L4 at 33.6…34.8, with 0.6 mm nominal gap each side. L2 at 30.0…31.2 remains outside this local fork; all three rods remain independent at B. |
| Branch 2 B fork opening | 31.2…35.4 | Contains L2 at 31.8…33.0 and L4 at 33.6…34.8, with the existing 0.6 mm layer gaps. |

The existing A **outer** spacer is farther out: branch 1 33.0…39.6; branch 2 31.2…39.6. It does not intersect the proposed inboard cheek at 25.2…26.4. Its radius is only 1.5 mm about A, so a bridge starting 7 mm from A is also clear in projection. Keep these outer spacers unless actual native geometry demonstrates another issue.

Likewise, the existing two B spacers at 31.2…31.8 and 33.0…33.6 are about the pin within the still-open region; a bridge beginning 7 mm radially from B does not hit those OD3 rings. There is no reason from this screening to retire them simply because a fork has been added.

However, the existing B outer split retainer at center 35.5 occupies 35.2…35.8. It overlaps the proposed new bearing's 35.4…36.6 axial interval by 0.4 mm. Its OD3.6 lies inside the leaf's Ø4.05 bore, so inspecting the leaf alone could miss the conflict: **the bearing is the mandatory interfering part**. Move the retainer and groove, not merely the visible leaf. A bearing in the added leaf also needs deliberate outer-race retention; a 1.2 mm-deep flush through seat is not positive retention by itself.

## Pure numerical projected sweep

Computed the existing exact solver at **3,601 phases, 0…360 degrees in 0.1-degree steps**, preserving candidate_r02 lengths/branch. No FreeCAD, geometry kernel, native shape or OCC operation was invoked.

For a conservative screening envelope, each bridge was a 6 mm-wide planar rectangle from 7 to 10 mm along the rocker, measured from its pivot towards the other rocker pivot. The added A leaf was bounded by a rectangle from −3 to +10 mm, width 6. A ground upstand used the source trapezoid plus radius-3.5 mm boss; its rotated cage comparison used the complete source outer bounding rectangle, before windows/collar cuts. Rods were capsules of radius 3 around the existing B–C/B–G center segments. Distances used point/segment and convex-polygon separation; results are finite sampled projected distances, not 3D guarantees.

| Screen | Minimum projected separation | Interpretation |
|---|---:|---|
| A bridge vs its actual pedestal/boss | 3.500 mm, both branches | Bridge beginning at 7 mm lies beyond the radius-3.5 boss and away from the pedestal. |
| Added A leaf bounding rectangle vs full rotated cage outer envelope | 9.459 mm | At 245.4 degrees, branch 1; 65.4 degrees, branch 2. This also conservatively separates the nearby case collar/crosswall envelope. |
| A bridge vs local broad shelf | 7.807 mm | Both branches. |
| B bridge vs local broad shelf | 11.961 mm | Both branches. |
| B bridge vs B–C capsule | 4.000 mm | Both branches; no end-bridge/L4 collision indicated. |
| B bridge vs B–G capsule, start at 7 mm | 1.206 mm | Minimum at 16.1 degrees, branch 1, and 196.1 degrees, branch 2. Branch 2 is the relevant axial overlap; branch 1's L2 is outside the bridge's axial span. |
| Same B–G screen, start at 6 mm | 0.370 mm | Too little margin to prefer once fillets, print error, deflection and unspecified transition material are included. |

The B→A versus B→G included angle ranges 56.723…83.270 degrees; B→A versus B→C ranges 91.342…126.419 degrees. These ranges explain why the 7 mm bridge clears the inserted rods and why shortening the opening materially reduces the L2 margin.

**Minimum geometric recommendation:** keep the opening clear for at least 7 mm measured from the pivot along the rocker. Round the slot root without allowing a fillet or blend to intrude towards the pivot inside that envelope. If a native sketch uses a rounded slot cap, distinguish its *total opening extent* from its straight portion: a slot ending at center 7 mm with a round cap can start the bridge earlier at its sides. The numerical rectangle began uniformly at 7 mm across the whole 6 mm width. A root shape intruding to 6 mm inherits only the 0.370 mm screen, not the 1.206 mm screen.

Leaves extending about 10 mm at both ends of the 24.1215 mm rocker leave about 4.1215 mm between those local sections. Retaining the uninterrupted main cheek provides a continuous rigid load path without thickening the complete bar axially. Each added leaf must connect through a bridge with positive overlap; avoid a construction that joins only along a coincident edge or creates a disconnected PartDesign solid.

## Minimum shaft and capture requirements

**A shaft:** shortening the Ø3.6 central shoulder from 54 to 50.4 mm places its ends at |Y|=25.2. The new 2×4×1.2 bearing at 25.8 then occupies 25.2…26.4 on the Ø1.9 journal rather than colliding radially with the shoulder. This is the correct nominal boundary. Preserve overall A shaft length and existing outer captures unless another check requires alteration. Exact tangency provides no tolerance allowance; a chosen shoulder relief or axial clearance must be explicit. Its thrust contact must be checked against the actual bearing inner-race face: Ø3.6 shoulder versus Ø4 bearing OD does not establish race-specific clearance/retention. A slight setback can avoid an unintended shoulder contact, but then axial location/endplay still needs a declared contact stack.

**B shaft:** retain the central Ø3.6 shoulder span of 60 mm unless another load/stack requirement changes it. Extend the journal ends and relocate the grooves. The legacy `grooves` construction places a 0.6 mm groove at absolute Y=(L/2−0.8)…(L/2−0.2), center L/2−0.5. For L=76.8 mm, the positive groove is 37.6…38.2, center **37.9 mm**; move the corresponding retainer to 37.9, with the opposite sign on the other side. This leaves a **1.0 mm gap** from outer leaf/bearing face 36.6 to retainer inner face 37.6. Either fill this deliberately with an appropriate spacer/washer arrangement or declare and justify the endfloat; do not label that gap a completed positive capture.

If an explicitly selected 0.2 mm nominal gap is sufficient, an overall shaft length **75.2 mm** puts the existing-style groove at 36.8…37.4 and retainer center 37.1. The geometric lower-bound formula is L ≥ 74.8 + 2c, where c is the desired gap beyond the outer leaf face. This is a packaging alternative, not a tolerance or strength recommendation. 76.8 mm is a reasonable provisional choice if its 1.0 mm capture interval is resolved.

Do not change an arbitrary `Tip.Length` on the stepped source: the Tip is the shoulder Pad, and `HasEndGrooves` prevents automatic groove regeneration. Explicitly rebuild/edit the journal length, both groove stations and shoulder centering, preserving the physical shaft ID. If the B source still starts at its end, updating overall length also requires the hardware `point.length` descriptor/placement to keep the shaft center at Y=0. Keeping the **bar** MotionMap unchanged does not mean the old 72 mm shaft placement is valid for a new end-anchored 76.8 mm source. Alternatively preserve the old reference origin and symmetrically extend the source past it, with that frame convention explicitly documented.

## Native frames, load path and acceptance boundary

Four handed L3 source variants are appropriate because the two branches have different main cheek planes and the opposite side needs opposite axial extensions. Keep each source's existing main cheek at local Z=0…1.2 and preserve current local X/Y bore centers. In the current `line_place`, local +Z maps world −Y for **both** sides; geometry must be handed around source midplane Z=0.6, not mirrored with a negative instance scale. Reuse the current proper rotation and segment transform.

Added A/B leaf bearings remain separate physical hardware with explicit IDs; their geometry is axisymmetric but their fixed/moving ownership and axial capture still need declaration. The fixed A shaft passes through both moving rocker leaves around the grounded upstand; the B shaft remains at the existing shared B point and allows independent incident rods to rotate. Do not fuse L2/L4 into the clevis or add independent fork-leaf motion. The longer/asymmetric fork bridge transmits leaf bending and torsion into the retained 1.2 mm main cheek; thin cheek ligament, slot-root fatigue, bearing retention and joint thrust remain load/process questions. Geometric plausibility does not qualify that load path.

Lead validation must include all four fork sources, eight added leaf bearings, both modified A shoulders/B shafts, moved B retainers and any chosen new capture spacers in the actual affected-pair ledger. Check the full native assembly, including both chain copies, outer guide/caps, other rods, torso/frame and all same-joint hardware at the accepted multi-coordinate states. Refresh source-local-to-world/AX checks with both fork-leaf bores, not just their projected XZ centers. This review establishes only a favorable bounded projected screen and the explicit shaft/capture requirements above.
