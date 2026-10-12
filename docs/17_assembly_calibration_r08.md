# r08 assembly and torque-off calibration record

**Status: complete editable candidate under verification; not a fabrication release.** This record supersedes the r07 assembly instructions. The lead should refresh the generated PDF and this record only after the final native, motion, export, drawing, mass and engineering-screen manifests all refer to the same frozen r08 source SHA. The current prescribed-pose raw-intersection check reports PASS for 486 instances, but motion, export and drawing acceptance are still pending; no final r08 package pass is claimed here.

## Candidate identity and source interpretation

The intended r08 native candidate is `cad/flexor_r08_robot.FCStd`, generated from `src/build_robot_r08.py` and `parameters/assembly_r08.json`. The expected reviewed inventory is 486 physical links, 95 editable bodies, 105 unique part numbers, two XL330-M077-T spine motors and five XC330-M181-T motors. The exact revision identity and hashes must come from the final package and verification manifests, not from this expectation.

The r08 center frame follows the orthogonal arrangement visible in Movie S1 at 51.5 and 52.7 seconds. It replaces the two r07 lumbar perimeter frames with two separate half-cages. Each half has a solid upper sagittal horn cheek and two orthogonal crosswalls with broad windows; the assembly remains open at the top for motor-carrier access. The split is an engineering adaptation: the existing four transverse ties retain the pair, the midplane seam has 0.2 mm total clearance and is nonstructural, and no bond or bending-moment transfer is credited. Existing shaft, liner, tie, shim, motor and S9 joint datums remain in place. The two half-cages have Ø2.6 mm crosswall tie passages. Carrier access pockets add 2 mm provisional upper height while retaining a 1.85 mm top rail. Metric profile dimensions are reconstruction assumptions; Movie S1 establishes visible arrangement and morphology, not manufacturing dimensions.

Both fore and hind leg assemblies retain their distinct geometry and the same modeled sagittal direction. The design retains the S9 linkage topology, seven motors with six commanded coordinates, physical extension and compression springs, and the bilateral hind cable route. The r08 motor case envelopes are 20 × 34 × 26 mm W/H/D for both specified motor families. Case envelope agreement does not establish output centers, case mounting holes, horn spline/pattern, connector volume or cable bend space.

## Build and inspection order

1. **Stage by exact part number.** Use the revision-matched `bom/bom_r08.csv` and `bom/instances_r08.csv` produced from the final document. Record actual vendor code, batch, material, coating, measured dimensions and mass. Keep each unknown mass explicitly unknown.
2. **Assemble the spine mechanism.** Use the native placements for the A/B/C shaft families, links, crank hardware, copper guides/liners and retainers. Preserve the coupled two-output topology and paired XL motors. Check axial capture, free rotation and tool access against the selected physical hardware.
3. **Install both lumbar half-cages.** Orient each cage according to its AppLink placement. Confirm both solid upper cheeks, both perpendicular windowed crosswalls, open-top insertion path, tie passages and carrier access reliefs. Retain the 0.2 mm nonstructural center seam; do not bond it or rely on it to transfer bending moment. Use the four existing ties only after their real dimensions and retention method are confirmed.
4. **Install the fore and hind torso structures.** Preserve distinct front/rear bodies, moving-frame axes and actual S9 graph. Do not mirror a leg's angular convention by hand. Check journal, shaft, bearing and tie stacks in their own saved orientations.
5. **Fit the seven motor cases and output adapters.** The modeled bodies are envelopes. Before fitting real motors, obtain revision-matched case and output drawings or measure actual samples. Verify output center, pilot/spline, horn pattern, fastener engagement, case mounting pattern, connector orientation and cable bend radius independently.
6. **Fit all four legs.** Retain the separate fore/hind modules and the same +X-forward, +Y-left, +Z-up sagittal convention on both sides. Install hip axes, three segment bodies, pins, journals, bearings, spacers, clips and return features in their saved sides. Record real motor sign per installation.
7. **Fit springs and hind cable drive.** Install one extension and one compression spring per leg only after identifying actual free length, rate, end form and preload. Keep hind knees passive and use the modeled bilateral wheel/cable path. Validate cable bend radius, terminal retention, clamp pressure, tension, slip and spring travel using controlled bench coupons before loading the robot.
8. **Fit the controller carrier and board.** The carrier retains edge capture and no fictional PCB mounting holes. The tray/retainer outer wall was expanded to 0.8 mm by moving the envelope to X=[-24.8, 4.8] mm; board geometry and screw positions are unchanged. Confirm the real OpenRB board, populated components, connectors, solder joints, edge support and service access before installation.
9. **Route wiring and perform a torque-off inspection.** Keep TTL communication and external motor power correctly separated, add chassis strain relief and service loops, and clear all shafts, springs, tendons, clips and bearings. With motor torque off and supply disconnected, inspect fasteners, clip seating, free motion by hand where possible, spring seating, cable paths, pinch points, polarity and unplug access. Stop at any binding or mismatch. No physical assembly inspection is represented by this CAD record.

## Proposed motor map and calibration record

| Candidate ID | Motor envelope | Logical coordinate |
|---:|---|---|
| 1 | XL330-M077-T, spine A | Shared spine phase `theta` |
| 2 | XL330-M077-T, spine B | Same `theta`, redundant paired drive |
| 3 | XC330-M181-T, fore left | Fore-left hip/thigh |
| 4 | XC330-M181-T, fore right | Fore-right hip/thigh |
| 5 | XC330-M181-T, hind left | Hind-left hip/thigh |
| 6 | XC330-M181-T, hind right | Hind-right hip/thigh |
| 7 | XC330-M181-T, hind tendon wheel | Bilateral tendon take-up |

This is a candidate map only. No IDs have been written, encoder offsets measured, torque enabled, or hardware moved. IDs 1 and 2 share one logical spine coordinate, leaving six commanded coordinates. Foreleg passive motion and both hind knees remain passive in the model.

Before any separately authorized commissioning, record for each unit its exact model/serial, measured output-to-link orientation, direction sign, constrained mechanical reference, raw encoder reading, offset, software travel limits, current/temperature limits, operator and date. For the spine pair, record both mechanical references and unloaded tracking error, then define safe synchronization and stop limits. Verify wheel winding sign on both cable branches independently. The saved CAD neutral pose is not a measured encoder zero, spline orientation, hard stop, tendon preload or loaded spring equilibrium. Keep offsets unset and torque disabled until actual interfaces and safe restraints are established.

## Nominal interfaces and release boundary

CAD clearances are candidate dimensions, not process tolerances. The existing provisional stacks include a 4.05 mm bearing seat for a 4.00 mm OD bearing, a 1.90 mm journal for a 2.00 mm bore, and a 2.50 mm carrier clamp bore around a nominal 2.40 mm tie. Confirm bearing type, shaft finish, coaxiality, clip geometry, screw engagement, printed/machined size and clamp retention on real parts. The OpenRB footprint/population and connector bounds remain separate unresolved interfaces.

The exact supplier motor mount/output/horn/connector interfaces, OpenRB mounting and population, spring identity/rate/preload, cable grip/slip capacity, material/process allowables, fits, fastener engagement, tool access, continuous motor duty and physical load path remain open. A valid native solid, a passing sampled pose sweep, or a valid STEP/STL round trip cannot close those items. This candidate is not approved for fabrication, energizing, device-ID writes, gait operation, load testing or hardware release.

## Evidence to refresh at finalization

The generated manual must take final link/body/part counts, native SHA, mass, center of mass, point-mass inertia, load-demand values and check status from the revision-matched r08 manifests. The present 105/985 motion pose manifests define finite input coverage only; they do not themselves prove collision checks passed. Final reporting must preserve any raw overlap or documented exception and state its exact scope. Continuous clearance, loaded equilibrium, material strength, fatigue, physical performance and fabrication release remain separate claims.
