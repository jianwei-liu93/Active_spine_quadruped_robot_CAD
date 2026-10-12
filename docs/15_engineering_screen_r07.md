# r07 engineering demand screen

**Status: calculated screening evidence, not strength validation or fabrication release.** The calculation reads actual placements and solid volumes from `cad/flexor_r07_robot.FCStd` and source metadata from its 486 physical App::Links. It does not modify the native document. Geometry-derived masses use the explicit densities in `reports/verification/r07_mass_envelope.json`; purchased masses use `PurchasedMass_g`. Each actual solid's own centroidal inertia is omitted from the reported point-mass inertia tensor.

## Mass, center of mass, and point-mass inertia

| Quantity | Known-mass case | Separate controller/harness sensitivity case |
|---|---:|---:|
| Included mass | 268.3758 g | 286.3758 g |
| CoM, world X/Y/Z | (-8.6965, -0.0006, 3.1116) mm | (-8.7784, -0.0006, 5.4554) mm |
| Point-mass inertia about that CoM, rows/columns X,Y,Z | `[[220317.59, -25.51, -19292.68], [-25.51, 634978.84, -4.77], [-19292.68, -4.77, 777068.56]]` g·mm² | `[[243772.09, -25.49, -18472.76], [-25.49, 658462.01, -5.17], [-18472.76, -5.17, 777097.22]]` g·mm² |

The known case contains 485 mass-bearing links among the 486 physical links. `OPENRB150_PCB_ENVELOPE_r07` remains the one mass-unknown line in the BOM and is excluded from 268.3758 g. The sensitivity case adds the old parameter-file assumptions of 10 g controller and 8 g wiring, both lumped at the actual PCB envelope's B-rep center (−10, 0, 40.4) mm. This changes no PCB mass metadata or BOM value. These 18 g are not supplier or weighing evidence. The mass report's envelope is 164.3376 ×119.6 ×104.0254 mm against the 110×99×84 mm reference; the deltas are +54.3376, +20.6000, and +20.0254 mm. Neither the candidate mass target nor the reference envelope is demonstrated by this estimate.

## Quasi-static cases and calculation assumptions

The assumed loaded sensitivity mass (286.3758 g) is multiplied by gravity and alpha = 1, 3, or 6. The two-leg case assigns one half of the entire robot weight to each of two contacts; the one-leg case assigns the full weight to one contact. Both use horizontal load `Fx = 0.30 Fz`; resultant force is `sqrt(Fz²+Fx²)`. The worst hip moment uses actual saved-pose hip-journal B-rep centers and an estimated foot contact: the mean X/Y of lowest foot vertices and the lowest Z of that foot solid. This is a neutral-pose geometric lever estimate, not a contact patch model or a prediction of gait force distribution.

| Alpha | Support | Fore hip moment | Hind hip moment | Ankle 1.9 mm pin single-shear demand | Pin overhang bending demand | 4.0×1.2 mm bearing-seat projected pressure | Ø3.6 mm spine B-shaft nominal bending demand |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | two legs, equal | 0.0323 N·m | 0.0378 N·m | 0.52 MPa | 8.55 MPa | 0.31 MPa | 4.60 MPa |
| 1 | one leg | 0.0646 N·m | 0.0756 N·m | 1.03 MPa | 17.10 MPa | 0.61 MPa | 9.20 MPa |
| 3 | two legs, equal | 0.0969 N·m | 0.1134 N·m | 1.55 MPa | 25.64 MPa | 0.92 MPa | 13.80 MPa |
| 3 | one leg | 0.1939 N·m | 0.2269 N·m | 3.10 MPa | 51.29 MPa | 1.83 MPa | 27.60 MPa |
| 6 | two legs, equal | 0.1939 N·m | 0.2269 N·m | 3.10 MPa | 51.29 MPa | 1.83 MPa | 27.60 MPa |
| 6 | one leg | 0.3878 N·m | 0.4537 N·m | 6.21 MPa | 102.58 MPa | 3.67 MPa | 55.20 MPa |

For each ankle journal the B-rep bearing center is 3.925 mm axially from the journal's loaded plane. Pin shear uses the full circular 1.9 mm section as a conservative single-shear area; the double-shear comparison is half the single-shear value. Pin bending uses a circular-beam nominal stress, `32 F e/(π d³)`, with the resultant load and that measured 3.925 mm overhang. This is a simplified overhang model; the bearing/clip/journal contact distribution is not solved. The PA12 seat figure is projected pressure `F/(4.0×1.2 mm²)` using the candidate bearing OD and width; local contact, wall bending, creep and print orientation are unmodeled. The spine shaft figure uses `M=F L/4` for a simply-supported central point load, Ø3.6 mm, and the requested 60 mm maximum-span assumption. Actual support reactions, distributed masses and torque transmission are not solved.

Compare the hip moments only with the published XC330-M181-T **stall** value 0.60 N·m at 5 V: at alpha 6 one-leg, the neutral-state moment is 65% (fore) and 76% (hind) of stall. At alpha 6 equal-two-leg it is 32% and 38%. The stall comparison is not an allowable continuous load; no continuous motor torque, gearbox efficiency under these loads, thermal limit, acceleration, impact, or life margin is established. XL330 stall torque is not compared because the spine kinematic transmission/load path for motor torque is outside this reduced calculation.

The report contains demand values only. **No yield, fatigue, creep, bearing-pressure, motor-duty, cable-termination, or safety-factor pass is claimed.** PA12/steel grades, print direction, joints, notch effects, bearing retention, and safety factors remain unqualified. The r07 cable clamps provide modeled positive terminal geometry, but required cable holding force, surface preparation, clamping torque and friction remain unknown. The leg spring lengths/rates (extension 14 mm free/0.25 N·mm⁻¹; compression 18 mm free/0.4 N·mm⁻¹; compression solid 6 mm plus 1 mm bind margin) are parameter-file assumptions; catalogue identity, preload, rates, fatigue, end form and measured free lengths are unverified.

## Nominal fit stackups to verify on real components

| Interface in candidate | Nominal stack | Diametral result | Evidence / unresolved item |
|---|---|---:|---|
| Frame bearing seat to provisional 4.00 mm OD bearing | Seat 4.05 mm; bearing OD 4.00 mm | 0.05 mm clearance | Candidate geometry, not a process/tolerance specification; bearing OD/type and printed/machined size unverified. Radial wall on Ø7.00 boss is 1.475 mm. |
| 1.90 mm shaft/journal to provisional 2.00 mm bearing bore | Bore 2.00 mm; shaft 1.90 mm | 0.10 mm clearance | Nominal envelope only; shaft OD, finish, bearing bore, coaxiality and running fit unverified. |
| Fixed tie through controller split clamp | Clamp bore 2.50 mm; nominal tie OD 2.40 mm | 0.10 mm clearance | Seating/clamp preload and retention have not been physically established; model fit is an adaptation assumption. |
| Controller PCB inside carrier edges | Board envelope 25×66×1.6 mm; tray 28×70 mm | 1.5 mm nominal per side | Board thickness and component-free edges are assumptions; no supplier mounting holes are asserted. Connector/component population clearance is a separate nonphysical reserve. |

Retaining clips, screw fits, motor-output spline/horn, case mounting, OpenRB connector clearances, tie friction, cable-end retention and spring seating require supplier drawings or physical metrology. Nominal overlaps or clearances in the CAD are not manufacturing tolerances.

## Executed evidence and status boundary

The primary-MCP read-only calculation against the saved native r07 document found 486 physical links, 485 mass-bearing links, and one unknown PCB mass. `reports/verification/r07_engineering_screen.json` is the source of the mass/CoM/point-mass inertia and load-demand values above; `reports/verification/r07_mass_envelope.json` supplies the BBox and mass assumptions. The reported inertia omits each solid’s own centroidal inertia.

A separate primary-MCP C1/C2 moving-frame pair check against two frame pieces sampled 361 states and reported PASS with a 0.35 mm minimum gap. This is a scoped pairwise clearance result; it is not whole-assembly G3. Full whole-robot motion remains unqualified. `reports/verification/r07_frame_clamps_neutral.json` remains an earlier **472-link partial integration**, not verification of the current 486-link candidate. No G3/G4/G5 pass is inferred. Supplier datums, whole-robot motion clearance, assembled-candidate collision status, loaded equilibrium, final drawing/export checks and load allowables remain open. Fabrication release is not established.
