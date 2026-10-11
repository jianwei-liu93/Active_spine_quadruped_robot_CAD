# Reference evidence and reconstruction limits

**Status: DESIGN_SPEC_ONLY.** This document records evidence for a FLEXOR-inspired CAD design. It does not establish that CAD has been created, checked, or released for fabrication. The primary candidate is the fully actuated hind-leg configuration, FLEXOR-F. See the [development plan](07_development_plan.md) for the implementation sequence.

## 1. Source registry and identity

Main-paper references use printed article page numbers (matching the first 18 PDF pages). Supplementary references use PDF page numbers, including the cover. Preserve the supplied originals privately as described in [references/README.md](../references/README.md); the PDFs are not committed here.

| ID | Source | Identity or link |
|---|---|---|
| [P] | Wang et al., *Unlocking fast robotic locomotor propulsion through dynamic spine-leg synergy*, Science Advances 12, eaed5603 (2026), main paper | [DOI](https://doi.org/10.1126/sciadv.aed5603); SHA-256 `a922f5a4895ccab1b1af0868c35f9782f20ce1eef32e141c721cd9d856c3b8d4` |
| [S] | Supplementary Materials to [P], 70 PDF pages | SHA-256 `b4cb79060e2f9394ca8cf1fa67cdab2e664d3ff52ee8f78349358a732c6aefa6` |
| [MX] | ROBOTIS XL330-M077 manufacturer documentation | [e-Manual](https://emanual.robotis.com/docs/en/dxl/x/xl330-m077/), including its Drawings section |
| [MC] | ROBOTIS XC330-M181 manufacturer documentation | [e-Manual](https://emanual.robotis.com/docs/en/dxl/x/xc330-m181/), including its Drawings section |
| [MS1], [MS2] | ROBOTIS product listings reviewed with the manuals | [Listing 902-0162-000](https://en.robotis.com/shop_en/item.php?it_id=902-0162-000), [listing 902-0172-000](https://en.robotis.com/shop_en/item.php?it_id=902-0172-000) |

Manufacturer facts above were reviewed during preparation of this specification. Before releasing motor mounts, pin the exact variant and downloaded drawing revision/hash. A web link alone does not freeze a specification. In particular, the XL330 manual and shop listing have differing no-load-speed information; this specification deliberately does not select one unqualified speed number.

Use these provenance labels on parameters, drawings, and BOM rows:

| Label | Meaning |
|---|---|
| `PAPER_REPORTED` | Explicit text, dimension, or quantity in [P]/[S], with page and figure/equation reference |
| `MANUFACTURER_VERIFIED` | Exact manufacturer variant and source; identify which drawing or specification supports the value |
| `DERIVED` | Calculated from identified inputs; retain the equation and coordinate convention |
| `DESIGN_ASSUMPTION` | A proposed choice introduced for this reconstruction; changeable and not attributed to the authors |

`UNKNOWN` is a value-availability status, not a fifth provenance category. An unselected parameter has a null value/provenance and an unknown status. If a provisional value is selected, label it `DESIGN_ASSUMPTION` and retain its unresolved verification status.

## 2. Architecture, scale, and actuator counts

| Item | Evidence | CAD interpretation |
|---|---|---|
| Overall reference dimensions | Length 110 mm, width 99 mm, height 84 mm; 338 g ([S], p. 65, Table S1) | Reference envelope and mass. Record the assembly pose and bounding convention used when comparing a reconstructed model. |
| Hind-leg length | Sum of individual segments 90 mm; standing height 60 mm ([P], p. 4) | These are different quantities. Do not set every segment, or their sum, to 60 mm. |
| Other use of “leg length” | Prototype paragraph calls leg length 60 mm ([P], p. 16) | Preserve the wording difference; use the explicit 90 mm segment-sum/60 mm standing-height distinction for the dimensional model. |
| Leg size comparison | Hip-center-to-foot-end distances of 50, 60, and 70 mm ([S], p. 37, Fig. S16) | Example leg configurations, not individual link dimensions or three mandatory variants. |
| Torso/spine topology | Three torso sections; two coupled spinal joints, driven through crank/rocker/slider motion chains ([P], pp. 2–5, Figs. 1–2; [S], p. 30, Fig. S9) | One independent crank input controls the two spinal outputs. Keep physical hinges, independent coordinates, and motors distinct. |
| Spinal range | Sagittal bending range 120° ([P], p. 4) | Total reported bending range; not ±120° at each hinge. Specify signed CAD angles and neutral offsets separately. |
| Physical motors | Six total, seven for FLEXOR-F; two redundantly drive the spine; four/five drive the legs ([P], p. 16) | This count is explicitly reported, not inferred from Table S1. FLEXOR-F has two spine motors, four shoulder/hip motors, and one knee-winding motor. |
| Independent actuation | P/U: five; F: six actuated DOFs ([S], p. 65, Table S1) | Two spine motors share one mechanical input. The additional F motor controls both hind knees ([P], p. 16; [S], p. 27, Fig. S6). |
| Leg topology | Three-segment legs, coupled knee/ankle parallelogram, tension and compression springs; passive foreleg elbow ([P], p. 4; [S], pp. 27, 38–40) | Reconstruct closed loops and passive coordinates. Do not silently substitute a generic independently actuated 12-DOF quadruped. |
| Controller/power reference | OpenRB-150, 5 V ([S], p. 65); position commands at 250 Hz ([P], p. 16) | Package the electronics and wiring; these facts do not specify a battery, connector capacity, or complete power budget. |

The paper abbreviates motor names as “XL330–077-T” and “XC-M181-T.” The manufacturer-backed candidate mapping is **XL330-M077-T** and **XC330-M181-T**, respectively [MX, MC]. Preserve both spellings in the BOM provenance instead of treating the incomplete paper names as manufacturer part numbers.

## 3. Spine geometry: known values and missing datums

[S], p. 7 defines the following rod lengths. Its optimization vector is

$$
[H_x,H_y,L_1,L_2,L_3,L_4]
=[30,8.66,5,30,24.1215,45.7876]\ \mathrm{mm}
$$

([S], pp. 12–13, S24–S31). Retain the published precision as reference input, without implying that printed parts can achieve it.

| Parameter | Definition | Value/status |
|---|---|---|
| $H_x,H_y$ | Horizontal/vertical offsets between $A_1$ and $O$ | 30, 8.66 mm; coordinate signs must be documented |
| $L_1$ | $OG_0$, input crank | 5 mm |
| $L_2,L_7$ | $G_0B_1,G_0B_2$ | 30 mm |
| $L_3,L_8$ | $A_1B_1,A_2B_2$ | 24.1215 mm |
| $L_4,L_9$ | $B_1C_1,B_2C_2$ | 45.7876 mm |
| $L_5,L_{10}$ | $C_1D_1,C_2D_2$ | Equal by reported symmetry; numerical values unknown |
| $L_6,L_{11}$ | $D_1E_1,D_2E_2$, output rods | Equal by reported symmetry; numerical values unknown |
| Ground/guide datums | $E_1,O,E_2$ collinear; $A_1,A_2$ and $E_1,E_2$ centrally symmetric about $O$ | Relations reported; all required signed coordinates, guide centerlines, offsets, and physical strokes must still be specified |

The opposite-branch equalities are reported in [S], p. 7; assigning their numeric values from the optimized first branch is `DERIVED`. The source requires slider travel of at least 10 mm and $\max X_C\le H_x$ ([S], p. 13, S31). Carriage length, retained engagement, end clearance, and hard-stop geometry are additional manufacturing dimensions.

The optimization seeks complementary output angles, but reports a maximum residual error of **9.29°** over a cycle ([S], p. 13 and Fig. S12, p. 33). Consequently, do not impose $\psi_1+\psi_2=\pi$ as an exact extra closure constraint. Use the [independent spine geometry](02_spine_kinematics.md), measure the resulting output symmetry, and document any redesign.

## 4. Springs, cables, and fabrication evidence

| Item | Reported evidence | Still unresolved |
|---|---|---|
| Passive hind cable | $l_u=31$ mm; uncompressed spring at source-coordinate hip angle 30° ([S], p. 14, S36) | Anchor coordinates, termination allowance, loaded length, slack transition |
| Active hind cable | $l_a=317$ mm from a factor-two bilateral route ([S], p. 15, S38–S39) | Not 317 mm per leg; anchoring/slip conditions and actual half-path equality need explicit reconstruction |
| Active wheel/routing | Nylon winding wheel, 13 mm OD; two direction changes per side via hip-center shaft and shell guide/bearing ([S], p. 17, Fig. S19 p. 40) | Effective pitch radius, groove, cable diameter, tangency, usable rotation, retainers |
| Cable material | Eight-strand fiber fishing cable ([S], p. 17) | Strength, stiffness, diameter, abrasion resistance, creep, minimum bend radius |
| Springs | Tension and compression spring per leg ([S], p. 17; Figs. S17–S19) | Rates, free lengths, preload, stroke, wire size, material, fatigue life |
| Bearing/pin | Bearings: 2 mm bore, 4 mm OD; crank protruding pin: diameter 1.9 mm, length 8 mm ([S], pp. 16–17) | Bearing width/type/rating, mating locations, tolerances, retention |
| Fabrication | Mainly printed nylon ([P], p. 16); nylon/resin frame, copper guide interfaces, metal printed crank and synchronization shafts ([S], pp. 16–17) | Grades, process, orientation, link sections, fasteners, fits, shaft stack-ups |

The [leg/cable/spring model](03_leg_cable_spring_kinematics.md) must respect tension-only cables and real spring travel. The [manufacturing specification](04_components_and_manufacturing.md) converts missing information into explicit component and drawing requirements.

## 5. Apparent source inconsistencies: implementation treatment

These are transcription, indexing, or algebraic concerns observed in the supplied PDFs, **not an assertion that the authors' physical robot or original software is incorrect**. Preserve the printed equations in source notes and verify geometry independently.

| Source | Concern | Required treatment |
|---|---|---|
| [S] p. 9, S10 | Length vector $[L_7,L_1]$ appears inconsistent with columns indexed by $\delta,\gamma_2$ and preceding length definitions | Derive the lower crank loop from point coordinates. |
| [S] p. 9, S14 | RHS uses $\omega_9$, whereas $\dot\theta_2$ was defined as $\omega_8$ | Differentiate the verified position constraint. |
| [S] p. 9, S16 | $[L_{11},L_{10}]$ appears exchanged relative to $\lambda_2,\psi_2$ definitions | Match each vector to its physical rod. |
| [S] p. 12, S29 | Displayed inequality is not satisfied by the reported optimum: its left side is about 72.450 mm and right side about 90.346 mm | Check actual full-revolution feasibility; do not copy the inequality as an acceptance test. |
| [S] p. 14, S34–S35 | S34 omits the distal length present in S32; S35 reintroduces $a_1+a_3$ and does not follow algebraically from displayed S34 | Derive FK from the actual parallelogram, then verify IK against that FK. |
| [S] p. 15, S40–S41 | Cosine-rule product repeats $\lvert O_a\delta_4\rvert$; the intended segment product/wrap convention needs checking | Derive cable tangencies and wrapped lengths from the chosen geometry; test continuity. |

Use the [FreeCAD workflow](05_freecad_mcp_workflow.md) and [acceptance criteria](06_verification_and_acceptance.md) to retain implementation evidence. Published speed, force, and current traces are reference observations; they do not certify a new reconstruction's strength, thermal margin, or locomotion performance.
