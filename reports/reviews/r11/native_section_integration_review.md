# r11 native section integration code review

2026-10-13. **Disposition: resolve two reproducibility/runtime hazards before accepting the integration source. The frozen section geometry and nominal hardware stack are otherwise consistent with the proposed local-fork architecture; final native/affected verification remains pending.** Fits, retention, thrust and strength are known release issues, not newly demonstrated geometry failures.

Read-only static review; no live CAD, source change, native write or OCC execution. Only this report was written. Reviewed source SHA-256:

- `src/spine_link_sections_r11.py`: `473a1f1bd498cab0e22611468762dffb17e44ee31cc725ce051b34b82f9f7633`
- `src/build_robot_r11.py`: `480901ecdd889af699bd10669be4d9a2748a5b61065b4fae95c6ce4c1bb69ecb`
- `parameters/assembly_r11.json`: `c99768178b6a111158e964a76c75dde88595d3483550c350a27e22cb8cdb27a0`

Traced the relevant legacy builder, groove, placement and PartDesign source contracts. Both Python files parse successfully. The reported 12-phase/1,216-check prototype result is lead-provided preliminary evidence **before added hardware**, not a new check by this reviewer or final acceptance.

## Concrete source fixes

### NI-01 — Resolve the shoulder Profile link before accessing its Placement (runtime/reproduction blocker)

`_shaft`, line 106, directly accesses `shoulder.Profile.Placement`. The actual r10 shaft shoulder's persisted `Profile` is `App::PropertyLinkSub` (`LinkSub` pointing to the shoulder sketch). That property is exposed through the standard Python link/subelement tuple contract, so direct `.Placement` access can raise `AttributeError` instead of editing the sketch. The repository already handles this case in `torso_attachment_r10.py` by resolving `Profile[0]` when the value is a tuple.

Minimum fix: resolve the actual sketch object from the link/subelement value, validate it is the expected native Sketcher object, then move its Placement.Base.z and edit shoulder Length. This affects both A and B shaft changes. Do not substitute a frozen shape or bypass the native feature.

### NI-02 — Use native object lookup for the reused spacer on both build paths (fresh-build blocker)

`apply`, line 132, assumes `b.sources['SPACER_2mm_L0_6']`. Existing-document `resume()` rebuilds that dictionary by normalized native object Name, so this path works. The fresh `build_robot_r11.build()` path inherits the legacy builder: `build_flexor.pin()` originally indexes the source by raw part string `SPACER_2mm_L0.6`, while FreeCAD normalizes the object Name to `SPACER_2mm_L0_6`. `build_robot_r03.finalize()` filters dictionary **keys** against normalized used object Names and drops that raw-dot key. The later build chain does not repopulate all dictionary entries by native name. Consequently source reproduction can reach a `KeyError` despite the spacer remaining in PartsLibrary.

Minimum fix: retrieve the known native source through `doc.getObject('SPACER_2mm_L0_6')`, validate the Body/part dimensions, and register the normalized key if useful. Apply the same explicit lookup/validation style to the bearing rather than depending on incidental builder-dictionary history. Validate both existing-document integration and fresh build after this bounded fix; a successful resume alone does not prove fresh reproduction.

### NI-03 — Add explicit invariants for the physical links and shaft feature histories (acceptance guard gap)

`apply` snapshots existing LinkPlacements, but its final guard exempts every `changed` item, including all L3/L4 instances whose placements must remain exactly unchanged. The source correctly retains their local pivots and does not intentionally assign new placements; nevertheless the guard would not catch an unexpected transform change during `setLink`. `_shaft` checks final Shape validity but not the State/status of its changed Pads/Pockets/sketches, and it selects first/last Pads without checking the expected history.

Minimum fix: save/restore or explicitly assert exact L3/L4 placements, unchanged segment descriptors and identity source placements; assert exactly four expected L3 and four L4 instances. In `_shaft`, validate the named journal Pad, both groove sketches/Pockets and shoulder sketch/Pad, then fail for any Invalid/Error feature or unconstrained edited sketch after recompute. The broader final native guard can provide this evidence, but do not accept only the cached final shaft Shape. This is a guard deficiency, not a demonstrated transform or solid failure in the current geometry.

## Geometry/frame checks that are supported by static review

- The physical width is 8 mm while the legacy pose frame stays 6×1.2. This is **correct here**: both sources remain centered at local bore coordinates (3,3)/(L+3,3). The widened outline extends to local Y=−1…7 rather than moving the pivot to (4,4). `line_place` continues to place the same bore centers at the original XZ joints and Y center planes.
- Handed fork formula `zc=t/2 + side*(layer−target)` correctly accounts for local +Z mapping to world −Y on **both** sides. Main cheek remains local Z=0…1.2. Added A/B bounds are:

| Branch/side | A cheek local Z, mm | B cheek local Z, mm |
|---|---:|---:|
| 1 positive | 6.6…7.8 | −3.6…−2.4 |
| 1 negative | −6.6…−5.4 | 3.6…4.8 |
| 2 positive | 4.8…6.0 | −5.4…−4.2 |
| 2 negative | −4.8…−3.6 | 5.4…6.6 |

- The reversed/normal bridge Pads extend from the main cheek through the added cheek's axial interval, and the subsequent cheek Pad overlaps that bridge over a full rectangular region. This is a continuous rigid load path, not an ornamental disconnected leaf or zero-area join. Actual native validity remains a runtime gate.
- A bridge is uniformly confined to pivot distance 8…10 mm; B bridge uses the mirrored 8…10 mm interval from B. There is no rounded-slot-root intrusion into the 8 mm opening. The through bore Pocket from local Z=15 down 30 mm spans every frozen fork section (−6.6…7.8).
- **Actual added-cheek extent is longer than the parameter name suggests:** `pill_face(pivot,pivot+reach,width)` uses endpoint centers, not total capsule extents. With reach=10 and width=8, each local added cheek extends 4 mm behind its pivot and **14 mm towards the other pivot**. This does not invalidate the bridge construction: opposite-end added cheeks occupy different axial bands. It should be documented and included in the actual native check, rather than described as a 10 mm total leaf.
- L4 profile reconstruction retains the existing Pad, moves no datum, replaces the old combined bore/through-relief sketch with just two bore circles, and appends a separate 0.6 mm blind Pocket from Z=1.2. Thus its floor is 0.6 mm with the frozen inherited Pad depth. The source supports independent editable bores and relief. Both baseline profile and new relief must still pass final feature-state checks.
- The 8 mm width leaves 1.975 mm nominal radial ligament at a Ø4.05 bore, improving the former 0.975 mm section without establishing strength. L4 has 2.4 mm side rails and a 0.6 mm floor; nominal axial section through the relief is 7.68 mm². These are geometric calculations, not capacity claims.

A supplementary pure-math screen used the unchanged solver at 3,601 phases (0.1 degree increments). For the actual width-8, 8…10 mm bridge and the existing width-6 B2–G rod, the conservative projected margin is **1.493531 mm**, minimum at phase 196.1 degrees. The expression is 8 sin(alpha)−4 cos(alpha)−3 over the existing B→A/B→G angle range. This is an additional projected screen only; it does not replace the reported prototype OCC checks or pending added-hardware/native checks.

## Nominal shaft/spacer stack

The frozen revised stack closes the prior explicit gaps coherently:

| Stack element | Absolute Y interval, mm | Result |
|---|---:|---|
| A Ø3.6 shoulder | 0…25.2 on either side | 50.4 mm full span; shoulder ends at added bearing's near face. |
| Added A bearing / cheek | 25.2…26.4 | New Ø1.9 journal clears assumed Ø2 bearing ID. |
| Added A spacer, center 26.7 | 26.4…27.0 | Meets added bearing and existing ground bearing at 27.0. OD3 fits through the ground Ø4.05 passage where their Y intervals overlap. |
| Added B bearing / cheek | 35.4…36.6 | Separate 0.6 mm gap remains to L4 ending at 34.8. |
| Added B spacer, center 36.9 | 36.6…37.2 | Fills the interval to outer split retainer's inner face. |
| B split retainer, center 37.5 | 37.2…37.8 | Matches revised 0.6 mm groove exactly. |
| B shaft end | 38.0 | Leaves 0.2 mm outer end land; full length 76 mm. |

The `_shaft` algebra correctly centers the B shoulder: after journal length changes to 76, its sketch starts at (76−60)/2=8; updating shaft placement to `hardware_place(B,0,76)` keeps Y center zero. Moving only Groove1 sketch to local Z=75.8 while Groove0 stays at 0.8 gives world groove centers ±37.5. A shaft stays length 85.6; shoulder start becomes 17.6 and yields ±25.2. These equations are correct once NI-01 is fixed and the actual native features successfully recompute.

Existing A outer spacers and B intermediate spacers do not need retirement merely because the forks exist. The old B retainer is intentionally moved away from the newly occupied bearing interval. There are no new independent linkage members or commanded coordinates: four existing L3 IDs acquire handed rigid source geometries, four L4 IDs retain their source identity, A remains fixed and B follows its original joint point.

The added A `point` descriptors evaluate to fixed centers and are geometrically valid for annular bearings/spacers. Added B descriptors translate with B. Whole annular shapes are invariant under rotation about Y; they do not establish whether a real bearing's inner or outer race rotates with the leaf. Preserve that distinction in ownership/retention documentation.

## Known release issues, without expanding this gate

The new spacers close the nominal **inner-axis stack**, but the generic annular bearing solids do not model separate races. OD3 spacer and Ø3.6 shoulder contact cannot yet be claimed to act only on inner races; race face dimensions, tolerance/endplay, outer-race retention in Ø4.05 through seats, leaf fit and clip/groove load capacity are still unresolved. Treat these as declared fabrication-release issues, not reasons to invent more hardware or reinterpret the math graph during this code gate.

The 2 mm-long bridges and 1.2 mm cheeks require slot-root/leaf bending, torsion and fatigue checks for the selected process/loads. Sharp native rectangular bridge roots currently lack a manufacturing root-radius definition. The geometry can remain a provisional candidate; any future fillet must preserve the established clear opening. No load or physical fabrication claim follows from valid solids or collision-free prescribed samples.

## Bounded integration checks and metadata corrections

After the two source fixes, validate only the revised fork/long-bar/shaft histories and their actual placements first, then finish the already-planned affected campaign. Expected change accounting against r10 is 16 existing IDs (4 L3, 4 L4, 2 A shafts, 2 B shafts, 4 B retainers), 16 new hardware IDs (8 bearings, 8 spacers), no retired physical ID: **503 physical instances**, nominal **110 used source definitions**. A complete 32-affected pair ledger against 503 instances has **15,568 unordered pairs**. These are expectations derived from code, not observed final native counts.

Refresh AX/source-to-world checks with both added leaf bores and all new hardware. Compare transformed source-local shape to actual placed shape at neutral and two non-neutral states, using the documented one-placement rule. Do not infer correct Y stacking from S9 XZ projection alone. The preliminary prototype excluded added hardware, so it cannot clear the final bearing/spacer/retainer stack.

Before final metadata freeze, resolve stale fields: `assembly_r11.limits` still describes r10; `spine_frame.B_shaft_length_mm` still says 72 while the r11 section says 76; inherited `bar_profile_r10` still says forks deferred. These are historical entries, but current consumers need an explicit override/supersession statement. The changed B PartNumber also inherits `L72` from the stable source Name even though its actual length becomes 76; preserve the source identity, but make the current manufacturing label/dimension unambiguous.

Finally, `pivot_local_xy_mm`, pose-frame dimensions, bearing/spacer length fields and `long_floor_mm` are currently descriptive configuration values while the implementation hard-codes several equivalent frozen values or relies on inherited Pad length. Add assertions tying them to the actual source contract, or parameterize them coherently. Do not let a later JSON edit silently advertise a floor or datum the native model did not build.


Lead integration resolution: both implementation blockers were corrected before successful MCP integration: resolve LinkSub tuples for shoulder Profile; retrieve the normalized spacer definition from the native document on both resume/fresh-build paths. Actual integrated inventory is503 instances/110sources,98Bodies,344fully constrainedsketches. NativeS9 and initial13-pose affected collision checks passed. The review's earlier source hashes identify the reviewed draft; actual run hashes are in the revision verification reports.
