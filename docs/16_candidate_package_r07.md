# r07 candidate package — delivery and verification record

Updated 2026-10-12. This is an editable reconstruction candidate. Final package verification is in progress; fabrication release is BLOCKED.

## Geometry and source fidelity

The canonical file is `cad/flexor_r07_robot.FCStd`: 486 physical AppLinks and 105 BOM part numbers. The rectangular lumbar perimeter, separate upper window and curved lower opening follow Movie S1 51–80 s. Tapered pedestal ears, short end platforms and outer slotted guide plates preserve the S9 joint graph. A native C1/C2 travel relief removes material added by the rectangular perimeter; no joint or motor datum was moved.

Both forelegs and hind legs retain the same sagittal direction seen in Movie S2, with distinct module geometry and actuator layout. The model preserves seven physical motors and six commanded coordinates. Cable terminals, a controller carrier, retention details and provisional fits are engineering additions, not claimed recovered paper dimensions.

## Motor size check

Actual native source bounding extents are 20 × 26 × 34 mm X/Y/Z for all seven motor cases. Manufacturer dimensions are 20 × 34 × 26 mm W/H/D for both XL330-M077-T and XC330-M181-T. Inventory is two XL and five XC, including the common hind-leg winding-wheel motor. See `reports/verification/r07_actuators_dimensions.json` and `reports/sources/supplier_completion_r07.md`.

Case size does not verify output-center locations, spline/pilot, horn pattern, housing mounting holes, or connector/cable bend clearances. These remain provisional and block fabrication release.

## Actual mass and envelope

The density-based known mass sum is 268.37577 g, excluding the unknown OpenRB board mass and unmodeled electrical harness. Nominal purchased motor masses contribute 151 g. Separate controller/harness assumptions add 18 g only for a screening sensitivity; they do not change the BOM. Actual neutral envelope is 164.338 × 119.600 × 104.025 mm, larger than the paper reference 110 × 99 × 84 mm. This is an explicit candidate packaging deviation, not an exact original-scale reconstruction claim.

See `bom/bom_r07.csv`, `bom/instances_r07.csv`, `reports/verification/r07_mass_envelope.json` and `reports/verification/r07_engineering_screen.json`. Screening stresses and torque demands have no validated material/process allowable or continuous motor rating; they are not strength passes.

## Completed checks and open work

- Native frame edit/restore: PASS, base thickness 1.6 → 1.7 → 1.6 mm with geometry changing and restoring.
- C1/C2 shafts versus both relieved frames: PASS over 361 integer spine angles, 1,444 pair samples, zero intersection, smallest observed gap 0.35 mm. This is scoped to these four pairs.
- Applicable flat-stock profiles: PASS, three analytic DXFs independently reimported with exact outlines/holes and declared millimetres.
- Native drawing companion: generated and reopened, 67 sheets and 311 checked dimensions. PDF layout review is in progress; numerical dimensions alone do not establish drawing quality.
- Whole-robot motion and final STEP/STL round trips: in progress. Failed earlier source-generation/export attempts remain diagnostic evidence; they are not accepted package outputs.

The final handoff will replace this progress section with revision-specific completed results and file hashes. All finite pose results are limited to their recorded trajectories; no continuous-clearance, loaded-equilibrium, endurance or physical-performance claim is made.

## Fabrication blockers

Exact bought-part output/mounting/connector interfaces; populated OpenRB keepouts; selected spring catalog/rates/preload and limits; cable bend radius, tension and clamp capacity; bearing/shaft/clip fits and tolerances; clamping grip, fastener thread/engagement and tool access; material/process allowables, impact/fatigue and load validation; and final harness/service routing remain unresolved. Drawings and profiles are review candidates, not released manufacturing instructions.
