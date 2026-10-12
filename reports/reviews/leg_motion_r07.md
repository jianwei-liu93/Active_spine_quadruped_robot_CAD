# Prescribed leg and tendon motion adapter, r07

Status: geometric motion implementation with explicit candidate limits; **not a fabrication release or passive-response simulation**. Only `src/leg_motion_r07.py` and this review are owned by this worker. Runtime artifacts remain isolated in `reports/tmp/leg_motion_r07/`. No FreeCAD MCP, canonical document mutation or document save was performed by this worker. Supplemental command processes opened the frozen native r06 file and operated on copied shapes.

## Reference and range interpretation

Read docs03 and the existing leg/spring/tendon generators. `parameters/assembly_r06.json` is authoritative for routing dimensions and frozen leg geometry. The adapter rejects unsupported source/schema length, neutral-angle, cable-diameter, guide-radius or pitch-radius discrepancies. Both fore/hind legs use the corrected shared forward/down thigh/toe convention, with rearward/down shank and dependent ankle `qa=-qk`. Left/right hardware reflection does not reverse the sagittal angle.

The reference notes identify three segments, hind parallelogram, one common hind motor and separate springs, but do not supply measured proximal/passive-knee operational intervals. Original PDFs and full videos are absent from this repository; the local stills do not establish angular extrema. Therefore these intervals are **DESIGN_ASSUMPTION review excursions**, never PAPER_REPORTED motor limits:

| Coordinate | Fore | Hind |
|---|---:|---:|
| qh | -65°..-35° | -55°..-25° |
| qk | -105°..-75° | -115°..-85° |
| qa | -qk | -qk |
| common wheel | 0°..90° | 0°..90° |

Wheel 0..90° retains the existing fixed-guide CW-winding branch. Negative wheel motion stays diagnostic in `tendon_r03`; it is rejected by this assembled adapter because it would move the shell guide. Seven physical motors and the two-XL plus five-XC topology remain unchanged. qh and common wheel are commands; four qk values are independently prescribed passive coordinates, not additional motor commands.

## APIs for lead integration

All radians/mm; actual leg tags are `foreL`, `foreR`, `hindL`, `hindR`.

- `pose_states(leg_angles=None, wheel_angle=0, config=None, enforce_candidates=True)`: pure full FK, closure, spring spans and bilateral cable state. Partial angle maps retain neutral defaults.
- `descriptor(doc, theta=0, leg_angles=None, wheel_angle=None, config=None)`: all native link placements plus source regeneration requests. Partial angle maps retain recorded document angles. Every removed tendon descriptor is handled explicitly or rejected.
- `regenerate_sources(plan, cache=None)`: private **LOCAL** source shapes for each spring/cable request. Source shapes can be assigned to per-instance private sources; matching `plan['placements']` go on the corresponding links. Do not also transform these local shapes to world.
- `copied_shapes(doc, theta=0, leg_angles=None, wheel_angle=None, config=None, cache=None)`: private **WORLD** native TopoShapes and descriptor, for read-only checks.
- `sample_states(step_deg=1, excursion_deg=15)`: inclusive individual-coordinate trajectories, wheel sweep, coordinated directions and asymmetric hind trajectories; 464 states at defaults. `excursion_deg=10` or 5 supplies narrower candidates.
- `math_grid(step_deg=1, config=None)`: exhaustive independent 2D fore/hind mathematical grids and both cable sides at wheel0/45/90.
- `validate_native(doc, samples=None, phases=(0,), step_deg=1, output=None)`: native copied-source broadphase and OCC common-volume checks, including same-torso pairs. Explicit sample definitions and spine phases are recorded. Incomplete/error runs never pass. This is finite coverage of declared trajectories, not the Cartesian product of all robot coordinates.
- `apply_prescribed_pose(doc, theta=0, leg_angles=None, wheel_angle=None, config=None)`: **lead-only live mutation API; not executed by this worker**. Prepares valid shapes, then transactionally assigns private per-instance sources/placements and records `LegAnglesR03`, `WheelAngleR07`, configuration and spine phase. Never saves. Shared source geometry and neutral MotionMap attachment datums remain unchanged. Lead must validate execution on a disposable document before canonical use.

The old r03 fixed-neutral/wheel guard is unchanged. Its rigid torso/spine/leg placement implementation is reused through a private read-only facade which excludes only the newly handled tendon members. Dynamic members include wheel, keyed shaft and retention, actual cable sweeps, and ankle eye/spacer/grub attachments. Their captured neutral local frames are transformed from ankle position and incoming cable direction; captured axial Y/side rotations are preserved. This supports revised outboard eye thickness/base and radius passed by `config`, without inferring their dimensions from bounds.

No return value predicts loaded knees from wheel angle. Two separately secured branch lengths remain neutral geometric path plus0.5mm slack. The existing 2N/mm cable law is provisional; no spring stiffness, initial tension, friction, motor torque or external load has been certified.

## Checks actually performed

`math_grid.json`: one-degree 2D per-leg grids, 1922 geometric states, both cable sides and wheel0/45/90. PASS:

- maximum parallelogram residual 1.07e-14mm; reduced/full FK difference1.59e-14mm;
- maximum tangent residual1.27e-13 (mixed mm/mm² diagnostics); exact primitive endpoint joins;
- `d(length)/du=+5.5mm/rad` error2.67e-14: winding already counted once;
- analytic cable moment arms `-dlength/d(qh,qk)` agree with central differences to2.06e-8mm/rad;
- compression anchor-span minima23.1832mm fore/27.9975mm hind; after7.2mm seat insets the minimum coil gaps remain15.9832/20.7975mm, above the assumed8mm solid+margin;
- extension span minima16.0718mm fore/24.0458mm hind, above assumed free lengths13/18mm.

The 464 one-degree trajectory descriptors also passed pure validation and invalid wheel states failed closed. These are mathematical/geometric checks, not native shape or collision certification.

Actual native neutral copied reprojection covered all464 r06 instances with maximum bounds difference3.55e-14mm. The first coarse native run requested44 states from `sample_states(15)`, completed16, then failed in the pre-existing compression generator. The old run's header originally inherited a1° default; it is explicitly corrected/annotated to15° in `native_15deg.json`.

### Concrete fore collision

At fore qh=-35°, qk=-90°, theta=0, both sides have0.028221mm³ interference between `Torso_fore` and `foreL_O1_Clip0` / `foreR_O1_Clip1`. Intersection bounds in torso coordinates: X35.31518..36, positive Y43.15..43.2 (mirrored side negative), Z-9..-7.75743. This rejects clearance qualification of the full candidate interval.

`fore_relief.log` identifies source `TORSO_FORE_TRANSVERSE_FRAME_r06`, outer hip panels generated by `torso_frame_r06.py`: outer rectangle(12,-9,24,38). A **lead-review-only** corner relief X>=34.65,Z<=-7.4 through the outer panel would remove this observed corner overlap with about0.3mm local margin. Whole-motion clearance after a relief still requires rerun; no relief was made by this worker.

### Compression geometry failure and guarded replacement

At hind qk=-115°, installed coil gap20.7974539159mm, the existing compression helix/tori union raises invalid-single-solid. `compression_reproducer.log` shows that a23° seam rotation on each complete end torus, with identical occupied geometry and the same12-turn helix/OD4/wire0.5/seat locations, yields one valid solid. Other seam choices can produce two solids and are rejected.

`_spring_source` first calls the existing generator, then permits only bounded geometry-preserving seam retries for failed compression unions; all returns must remain one valid solid. There is no shortened coil, scaled spring, shifted seat, cylinder proxy or skipped validation.

`compression_fix.log` shows unconditional `Shape.fix(1e-7,1e-9,1e-6)` is insufficient at this length and can corrupt the valid23°-seam result. It is therefore not used to overwrite valid wire geometry in this adapter. Native endpoint/geometry validation remains mandatory.

Narrow ±10° native run completed47/47 declared samples (individual leg coordinates at -10/0/+10°, wheel0..90° in10° steps, coordinated and asymmetric directions) at theta0: **COLLISIONS_FOUND**, two known fore O1 clip/torso pairs, each worst0.0158323mm³ at foreqh=-40°. All generated/copy shapes remained valid single solids; no errors or guide warnings. It performed9592 OCC checks in587.1s. Native document MotionMap and placements were unchanged. Baseline raw overlaps were empty. This validates geometric regeneration at these samples, but rejects collision clearance of the unrelieved r06 candidate. The raw results are `native_10deg_excursion.json`; new clamp geometry and relieved panels must be rechecked by the lead.


## Final r07 clamp handoff contract

The adapter consumes `cable_clamps_r07.terminated_route` automatically when **both** installed cable `route_local` dictionaries contain `r07_positive_terminals`; inconsistent branch topology fails closed. Pure `pose_states(..., positive_terminals=True)` is also available. The terminal tail/R0.3 bend is added before cable generation, ankle radius is2.1mm, and available secured lengths use the corresponding terminated neutral path+0.5mm. `positive_terminal_math.json` covers all464 one-degree trajectory descriptors: exact primitive joins and wheel derivative error8.9e-15mm/rad.

New rigid component labels `wheel_clamp`, `wheel_anchor_bolt`, `wheel_clamp_grub` rotate both base about captured `wheel_center` and orientation about+X. Centered D-shaft/retention only rotate orientation. Ankle eye/spacer/grub transform their captured positions and rotations using captured ankle/incoming direction, preserving actual axial Y and mirrored source definitions. This contract was coordinated with the clamp worker. New positive clamp CAD topology and clearances require the lead's integration checks; the r06 native probes do not verify the new hardware.

With `wheel_angle=None`, document APIs preserve recorded `WheelAngleR07` (otherwise0). Configuration omitted after a live adapter application uses recorded `PrescribedMotionConfigR07`; the lead should pass the reviewed new configuration on first use. Explicit `wheel_angle=0` restores neutral wheel. The legacy fixed-state API remains guarded.

`fore_clip_range.json` additionally measures the exact r06 fore pair at each integer qh=-65..-35°, theta0/qk=-90: no volume overlap through-43°, first overlap-42°, peak0.0293263mm³ at-36°. Aggregate interfering X reaches34.98624mm, hence the relief candidate uses34.65mm rather than35.0. The fore clip pair alone accepts the±5° neutral excursion at theta0; this is not whole-robot clearance qualification.

Existing pure regressions also passed: `test_tendon_r03.py`10 tests and `test_leg_geometry_r02.py`8 tests. The assigned module compiles with Python. No new tests were added outside the assigned isolated runtime directory.
