# r08 engineering demand screen

**Status: provisional r08 calculation available; final SHA-matched verification set is pending.** No r08 stress, load, strength, mass-target or fabrication pass is claimed by this preparation record. The current prescribed-pose `r08_neutral.json` reports `PASS`, while export, drawing and full-motion acceptance are still pending. The values below are read from the current r08 mass and engineering-screen JSON; refresh them after the lead freezes the final native SHA.

## What the screen will report

The r08 screen is a reduced, read-only engineering calculation from actual r08 placements and B-rep geometry. It should include known mass, center of mass, point-mass inertia, a separate controller/harness sensitivity case where its assumptions remain appropriate, actual assembly envelope, and quasi-static demand cases. Geometry mass estimates must use the revision-specific mass report, explicit material-class density assumptions and nominal purchased mass metadata. Unknown controller mass must remain unknown in the BOM and be reported separately. The inertia calculation must state that each solid's own centroidal inertia is omitted.

Demand cases should state the assumed support distribution, gravity multiplier, horizontal-to-vertical load ratio, contact estimate, measured CAD lever arms, pin shear/bending model, bearing-seat projected-pressure model and spine-shaft span/support model. These are calculated demands only. Compare hip moments to the cited motor stall value only as context; stall torque is not a continuous-duty limit. Do not infer strength without material/process allowables, actual load distribution, contact, dynamics and safety factors.

## r08 mass and envelope

Current provisional r08 values from `reports/verification/r08_mass_envelope.json` and `reports/verification/r08_engineering_screen.json`:

| Quantity | Final r08 result |
|---|---|
| Physical links / mass-bearing links / unknown-mass instances | 486 / 485 / 1 |
| Known mass and center of mass | 273.0556 g; (−8.6923, −0.0007, 3.3258) mm |
| Point-mass inertia diagonal Ixx/Iyy/Izz | 221638.57 / 635315.74 / 777813.54 g·mm²; solid centroidal inertia omitted |
| Separate controller/harness sensitivity | 291.0556 g, adding assumed 10 g controller + 8 g wiring at the board envelope center; not BOM mass |
| Actual B-rep envelope versus 110 × 99 × 84 mm reference | 164.3376 × 119.6000 × 104.0254 mm; +54.3376 / +20.6000 / +20.0254 mm |

The currently available files identify the r08 native path and report 105 part numbers. Final mass output is density-based and is not a weighing. The package manifest and refreshed engineering calculation must bind these values to the final frozen native SHA before delivery. Do not publish r07 values as r08.

## Structural demand model and limitations

The screen may estimate hip moment at a selected saved or neutral pose, ankle pin single-shear and nominal overhang bending, projected pressure at the provisional bearing seat, and nominal bending of the Ø3.6 mm spine B shaft under an explicitly assumed support span. It must identify the actual geometric centers/lever arms and loads used. Results are not resolved contact stresses, joint reactions or gait loads. No yield, fatigue, creep, bearing-pressure, cable-terminal, spring-life, motor-duty or safety-factor pass follows from those estimates.

The r08 center structure is a pair of half-cages held by the existing four transverse ties. Its 0.2 mm midplane seam is nonstructural and carries no credited moment. The two upper sagittal cheeks and two perpendicular windowed crosswalls follow Movie S1 at 51.5/52.7 seconds, while numeric wall, window, pocket and fit dimensions remain reconstruction or engineering-adaptation assumptions. The 0.8 mm controller retainer wall is a manufacturability repair; it does not verify the PCB interface. Exact motor mounts/horns/connectors, controller population, bearing/shaft/clip fits, fasteners, spring catalog data, cable grip, process allowables and physical load paths remain unresolved.

## Verification status that must accompany values

The final report must bind every PASS to the r08 SHA and exact scope recorded by the source manifest. At preparation time:

- The current neutral raw-intersection report covers 486 instances and reports `PASS` (95 editable bodies, fully constrained sketches, 1,207 narrowphase tests). This is only the saved prescribed pose.
- The coarse and full motion pose manifests define 105 and 985 target states respectively. These are input coverage manifests, not execution results. The full path has a maximum coordinate increment of about 1 degree; continuous clearance and loaded equilibrium remain outside its scope.
- The capture manifest says images were captured and restored, while its source-fidelity visual review is still `NOT_RUN`.
- Export, drawing, profile and engineering-screen acceptance must be taken from their final r08 manifests. Do not infer them from r07 outputs or from the existence of r08 source scripts.

After the lead completes source-hash freeze and reruns all checks, replace this preparation record with actual numeric results, scoped outcomes, report paths, source hashes and limitations. Fabrication release remains blocked until supplier interfaces, manufacturing process, allowable loads, tolerances, physical fit and build inspection are separately established.
