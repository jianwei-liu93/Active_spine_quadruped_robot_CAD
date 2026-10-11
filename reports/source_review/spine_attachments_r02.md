# r02 spine attachment candidate

Implemented only `src/spine_attachments_r02.py`; no live FreeCAD execution, canonical CAD writes, parameter-schema edits, or commits were performed by this worker. Requested role/model: inherited Sol/high; actual routing is not observable to the worker. This is a bounded implementation handoff, not fabrication approval.

## Integration contract

Call `spine_attachments_r02.apply(b)` after `slider_plate_flexor.apply(b)` and before the lead's final save/validation. The function returns its provisional parameters and sampled screening results and stores the same dictionary in `PoseController.SpineAttachmentCandidate`. It is idempotent once that property exists. Existing mechanism dimensions, rod layers, corrected fixed slider plates, journals and L6/L11 output geometry are preserved.

The lead must add the new motion case to **every pose and copied-native-shape sweep path**:

```python
elif m['kind'] == 'horn_screw':
    placement = spine_attachments_r02.motion_placement(m, theta, s)
```

Assign `placement` to the instance `LinkPlacement`, or to the copied source shape before Boolean checking, as appropriate to the existing caller. The helper has no document access. Its `points` argument is the current kinematic state dictionary; `theta` is the O→G phase in radians.

Exact new descriptor:

```python
{'kind': 'horn_screw', 'point': 'O', 'offset_perp_mm': -2.5,  # other screw +2.5
 'axis_side': 1,  # opposite side -1
 'tip_abs_y_mm': 27.0, 'underhead_mm': 1.9, 'head_height_mm': 0.8}
```

The screw source tip is local `(0,0,0)` and its head extends along local +Z. Global tip is `(Ox-offset*sin(theta), side*27.0, Oz+offset*cos(theta))`; source +Z maps to global `(0,side,0)`. Screw circular symmetry makes rotation about its own axis irrelevant. `horn_screw_pose_data()` exposes the same contract without importing FreeCAD. New washers use the existing `axialrot` motion kind; fixed ties, their screws and case shim have no moving descriptor.

## Drive geometry and axial stack

All attachment dimensions and fastener patterns below are `DESIGN_ASSUMPTION`. Nothing in this module verifies ROBOTIS horn holes, spline, output datum, center screw or available shaft length.

The native steel crank outline joins a 5 mm-wide O–G capsule to an O-centered radius 4.5 mm disk. Its local O/G coordinates are `(2.5,2.5)` and `(7.5,2.5)`, preserving the existing `line_place` convention. O bore is Ø2.05; G bore is Ø1.9 nominal fixed press fit. Two Ø2.2 clearance bores are perpendicular to O–G at ±2.5 mm from O. Handed native crank sources put Ø3.5 × 0.8 mm counterbores on the outward face on both sides.

| Feature | Absolute Y extent, mm |
|---|---:|
| Candidate horn, OD8, central Ø2.05, two Ø1.7 tap-minor holes | 27.0–28.2 |
| OD8 matching gap washer, Ø2.2 screw clearance | 28.2–28.5 |
| Steel crank | 28.5–29.7 |
| Screw minor core, Ø1.65 | 27.0–28.9 |
| Screw head, Ø3.5 | 28.9–29.7 |
| Adjacent L2 inner face | 30.0 |

Thus the frozen head envelope leaves 0.3 mm nominal axial clearance to L2. A proud head was rejected during implementation because the rotating screw can cross the G→B1 link centerline. The selected 1.9 mm under-head length spans a 0.4 mm crank floor, 0.3 mm washer and 1.2 mm horn engagement. It requires a nonstandard short/trimmed M2 candidate; no catalog availability is claimed. Metadata records nominal major diameter 2 mm, but modeled shafts use the Ø1.65 minor core and no helical threads. A Boolean pass therefore cannot validate thread engagement or thread-major contact.

The Ø3.5 counterbores intersect the central Ø2.05 O bore by 0.275 mm radially. A supplier output shaft or central fastener extending into the head layer needs its own clearance check. The 0.4 mm floors and 0.375 mm ligaments between through bores have unverified strength. Material, machining tolerance, preload, screw drive details and anti-loosening remain release limitations.

## Ground frame restraints

Four fixed metal spacer tubes join the two lumbar ground frames at case-local `(±11.4,-8.4)` and `(±11.4,28.4)`, rotated by the existing case angle. They do not attach to the moving B shafts. Each tube is OD2.4, ID1.7 nominal tap-minor, length 53.6 mm, with endpoints at Y±26.8. Native radius 2.5 frame bosses have Ø2.2 clearance bores; Ø2.6 recesses keep the tube ends clear of added inward collar material. Eight outward-facing M2 screw envelopes span the 1.6 mm frame plus nominal 1.2 mm tube engagement. Their heads end at |Y|29.2.

Native inward collars use the existing outer cradle rectangle `[-12,12] × [-9,29]` and the nominal case rectangle `[-10,10] × [-7,27]`. They project 1.4 mm inward from each ground frame. Top/bottom capture bands fill the nominal 0.4 mm frame-to-case face gap; a 0.8 mm insulating center shim fills the gap between the back-to-back cases. The nominal captive pack is 52 mm of cases + 0.8 mm shim + 0.8 mm face pads = 53.6 mm. These features provide a provisional case-edge/face clamp without inventing motor case holes. Exact tangent surfaces, compression allowance, assembly access, case contact suitability, connector keepouts and clamp preload remain unverified. There is no claim that a rigid zero-clearance CAD pack can be manufactured or assembled without fit adjustment.

## Checks actually run

- Python syntax compilation passed. Importing the module and running its pure helpers did not import FreeCAD.
- Pure screw placement checks passed for both sides, both offsets, a translated O, several phases, full-cycle closure and outward axis signs. Head maximum |Y|29.7 was checked numerically.
- A 721-pose planar screen using the current `candidate_r02.json` closure passed: minimum B-shaft surface clearance to a tie 8.6943 mm, to a mount boss 7.3943 mm, and to a conservative whole-cradle-rectangle bound 7.4285 mm. Tube-to-nominal-motor-corner clearance is 0.7799 mm. This screen checks finite samples, not continuous motion or native solids.
- Source/API review checked `cad_common.py`, `build_flexor.py`, `refine_flexor.py`, `slider_plate_flexor.py` and the current parameter file. No CAD Boolean, native reopen, screenshot or export verification was run by this worker.

## Required lead checks before accepting the candidate

1. Integrate the motion handler in build/pose and each sweep runner; execute the module through the live FreeCAD workflow, verify every final native Body is one valid solid and every sketch is fully constrained, and inspect both handed counterbores and frame collar/recess directions.
2. Save/reopen/recompute, inspect the actual axial stack, and run the full copied-native-shape motion sweep with the new screw motion. Keep intended contacts precise: G press fit, head/counterbore seating, simplified screw/tapped-bore engagement, tube/frame seats, and nominal case/shim/collar contacts. No new sweep pass is claimed here.
3. Check supplier output/horn drawings and the central output retention path; resolve the provisional hole pattern, spline, shaft extent and center-fastener clearance. Check crank-floor/ligament strength and feasible screw selection before release.
4. Validate case clamp fit, preload, connector/access clearances and tube-end engagement; retain the exact unresolved items in the fabrication gate. Conditional dependent body development may proceed with these frozen outer envelopes after native/motion checks, while supplier-interface and strength release blockers remain explicit.
