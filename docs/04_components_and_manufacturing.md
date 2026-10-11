# Components and manufacturing specification

**Status: DESIGN_SPEC_ONLY.** This is a specification for a manufacturing-oriented prototype candidate. No completed CAD, supplier selection, strength verification, or fabrication release is claimed. Source IDs refer to the [reference evidence registry](01_reference_evidence.md). Follow the [development plan](07_development_plan.md), with geometry from [spine kinematics](02_spine_kinematics.md) and [leg/cable/spring kinematics](03_leg_cable_spring_kinematics.md).

## 1. Component candidates and interfaces

The table defines the FLEXOR-F candidate. Quantities are design inputs or paper evidence, not an order list. Do not invent availability, prices, supplier part numbers, or delivery times.

| Component | Candidate/quantity | Established information | Required before its interface is released |
|---|---|---|---|
| Spine motors | XL330-M077-T ×2 | Manufacturer nominal body 20 ×34 ×26 mm; mass 18 g each [MX]. Two redundant spine motors reported [P], p. 16 | Pin drawing/CAD revision, body axes, output-center location, mounting pattern, horn, connectors, screw engagement, mirrored calibration |
| Shoulder/hip and knee motors | XC330-M181-T ×5: four limb swings plus one bilateral knee wheel | Manufacturer nominal body 20 ×34 ×26 mm; mass 23 g each [MC]; functional count [P], p. 16 | Same interface checks; distinguish the knee wheel and four limb attachments |
| Controller | OpenRB-150 ×1 candidate | Controller reported [P], p. 16; [S], Table S1 | Verified board outline, holes, connector/cable volumes, mounting insulation, service access |
| Miniature bearings | Reported 2 mm bore/4 mm OD; count and exact type pending | [S], pp. 16–17 | Width, flange/seal type, ratings, fit, lubrication, retention, location-specific quantity |
| Pins and shafts | Metal; exact catalog sizes/materials pending | Crank pin diameter 1.9 mm ×8 mm reported [S], pp. 16–17 | Full journal/shoulder geometry, finish, tolerances, bending/shear checks, axial retention |
| Guide interfaces | Copper-lined/ring interfaces and bearings, or a documented redesign | Reported copper rings at inner/outer faces of sliding joints [S], p. 16 | Which surfaces roll/slide, strip thickness, contact width, alignment, clearance, retention, replaceability |
| Leg springs | Tension and compression spring for each of four legs | Eight spring elements follow the reported arrangement [S], p. 17 | Exact spring specifications and verified anchor/stroke geometry |
| Hind tendon/wheel | Fiber cable; one centrally actuated nylon wheel | Bilateral routing; 13 mm wheel OD [S], pp. 15–17 | Actual cable, termination, pitch radius, guides, adjustment, routing and wear limits |
| Frames/linkages/feet | Process-specific polymer parts; metal inserts/pins as needed | Mainly nylon in [P], p. 16; nylon/resin in [S], p. 16 | Process/material grade, sections, tolerances, orientation, foot contact material and attachment |
| Fasteners/spacers | Standard hardware selected during detailing | Retaining rings and locking nuts reported [S], p. 17 | Thread, length, washer, spacer, locking method, tool access and assembly sequence |

Import verified manufacturer geometry when available through the manuals' Drawings sections [MX, MC]. Simplified purchased-part models may omit internal gears, but must preserve all external mounting and keep-out geometry. A 20 ×34 ×26 mm box alone is not a motor mounting interface. Treat the candidate mapping from the paper's shortened motor names as documented in the evidence registry.

Power packaging must identify the chosen supply arrangement, connector ratings, wiring, strain relief, and service access. A battery is not specified by the paper's 5 V table entry; do not add a fictitious battery and claim the reported mass is retained.

## 2. Fits, retention, and guide clearances

For a shaft diameter $d_s$ in a bore $D_h$, define diametral clearance limits:

$$
C_{d,\min}=D_{h,\min}-d_{s,\max},\qquad
C_{d,\max}=D_{h,\max}-d_{s,\min}.
$$

Radial clearance is half the diametral value. State whether the intended interface is clearance, transition, or interference, and allocate limits using the selected material/process and bearing supplier's guidance. The reported 1.9 mm pin versus 2 mm bearing bore has a nominal 0.1 mm diametral difference **if those items mate**; neither their mating relationship nor a suitable operating fit is established by these two numbers alone.

For available axial space $A$ and a stack of component thicknesses $t_i$, endplay is

$$
e=A-\sum_i t_i,
\quad e_{\min}=A_{\min}-\sum_i t_{i,\max},
\quad e_{\max}=A_{\max}-\sum_i t_{i,\min}.
$$

Set permissible endplay separately for each joint. Include bearing width tolerances, washers, spacers, shoulders, retaining-ring grooves, and nut seating. Provide a clamping path through the intended races/spacers; tightening a fastener must not unpredictably squeeze moving polymer links against stationary parts. Confirm positive shaft capture and a feasible installation/removal sequence.

Each guide needs its own min/max clearance calculation, including rail/slot geometry, bearing or carriage size, parallelism and mounting error. Check the entire stroke, retained engagement and mechanical stops. Define friction and lateral-play consequences explicitly; do not apply one unexplained clearance to every printed hole and rail. Model left/right linkage layer offsets, shaft spans and fastener heads so the nominal planar mechanism can physically occupy three dimensions.

## 3. Manufacturing process and detailing priorities

Select a prototype process and material grade before locking wall thicknesses or fits. Printed nylon is the source reference; SLS/MJF nylon, another suitable nylon process, or a documented alternative remain design choices until selected. Resin can be useful for geometry trials, but its suitability for loaded impact/cyclic parts requires the selected grade's data. Do not transfer properties from a generic material name into strength calculations.

Prioritize:

1. Datum-based motor mounts, bearing pockets, through-shafts and guide alignment.
2. Bearing-seat finishing allowances and replaceable pins/spacers. Decide which holes are printed, drilled, reamed, or machined after printing.
3. Load-bearing sections around pivots, spring anchors, cable anchors and thin guide walls; provide radii and adequate edge distance.
4. Real screw heads, nut capture or inserts, thread engagement, tightening access and removable covers.
5. Cable threading, spring installation, motor replacement, lubrication and inspection access.
6. Lightweight noncritical features only after the functional stack-ups and load paths are credible.

The reported metal-printed crank [S, pp. 16–17] may be reconstructed that way or redesigned for a feasible machining/plate-and-pin process. Any alternative must retain the center-to-center geometry, shaft support and required out-of-plane offsets; record it as a redesign. Provide orientation/support/finishing notes for printed parts and actual dimensional drawings for machined shafts and inserts. Avoid ornamental threads and highly detailed spring coils where they make recomputation costly without improving fit checks.

## 4. Preliminary load and actuator screening

Create a small, explicit load-case table before sizing critical sections. It must include gravity support, hind-leg push-off, asymmetric landing/foreleg touchdown, spring preload, and spine/limb reversal. Record the selected pose, contact points, supported masses, force directions, duration or frequency, and assumptions. A practical parameterization is

$$
F_{z,i}=\lambda_i\alpha m g,\qquad \sum_i\lambda_i=1,
$$

where $\alpha=1$ describes total static vertical support and dynamic $\alpha$ values and load shares are declared design assumptions. Add horizontal forces and inertial torques where relevant. Do not infer a landing load multiplier from appearance or treat one published force peak as a maximum possible load. Use the developing mass estimate; 338 g is a reference value [S, Table S1].

For a solid circular pin, using **N, mm, N·mm**, useful first-pass relations are

$$
\sigma_b=\frac{32M}{\pi d^3},\qquad
\tau_{\mathrm{avg}}=\frac{4V}{n\pi d^2},\qquad
\tau_t=\frac{16T}{\pi d^3},\qquad
p_{\mathrm{lug}}=\frac{F}{d\,t}.
$$

Here $n$ is the number of effective shear planes, $M$ is bending moment, $V$ transverse force, $T$ torsion, and $t$ loaded lug thickness. Results are N/mm² = MPa. Average transverse shear is not its local maximum; unequal double-shear load sharing and real support spans require the corresponding beam/joint model. Projected lug pressure is not a rolling-bearing load rating.

For a genuinely cantilevered pin with end load, also check

$$
\delta_{\mathrm{tip}}=\frac{F\ell^3}{3EI},\qquad
I=\frac{\pi d^4}{64}.
$$

Use the actual support condition when it differs. Check deflection against available clearance as well as stress against material allowables, with explicit safety factors and cyclic/impact limitations. Include fastener pull-out, polymer bearing pressure, and bearing capacity where they govern. Focus detailed analysis on identified critical parts; a speculative full-robot FEA campaign is not required at this stage.

Evaluate motor demand at the **same operating torque and speed**, including transmission Jacobians, inertia, spring loads and losses. Stall torque is not a continuous operating rating, and no-load speed cannot be combined with stall torque as one achievable operating point. Do not resolve inconsistent manufacturer speed tables by guessing. Pin voltage, control mode, exact motor variant and datasheet before the numerical assessment.

The approximately 1.2 A trial peak and plotted current limits in [S], p. 48, Fig. S27, are paper-reported observations. They do not independently establish continuous thermal margin for this reconstruction. For the redundant spine pair, define mirrored zero offsets, synchronization and load-sharing assumptions; two motors on a common mechanism cannot be assigned conflicting position commands.

## 5. Springs and tendons

For every spring record free length, initial tension/preload, rate, usable stroke, solid length or maximum extension, wire/coil geometry, material, fatigue information and anchor loads. Within its verified linear working range, a spring can be represented by

$$
F_s=\max(0,F_0+kx),
$$

with $x$ explicitly defined relative to the chosen reference state and positive in its loading direction. Avoid double-counting installed preload as both an initial deflection and an independent force offset. The separate extension/compression laws and disengagement states in [03](03_leg_cable_spring_kinematics.md) govern the implementation. Apply physical travel limits separately; the equation does not permit coil bind or indefinite extension. Prefer a verified catalog part, or a dimensioned custom spring specification. Include spring installation access and containment/retention at both anchors.

Define cable diameter, minimum bend radius, termination/adjustment method, strength allowance, stretch and creep assumptions, and allowable wear. Use the actual guide tangencies and wheel pitch radius; 13 mm OD does not fix cable take-up. The 317 mm source route is a symmetric bilateral total before this reconstruction's termination allowances [S, S38–S39].

For an ideal inextensible tendon, the slack gap $s=L_{\mathrm{free}}-L_{\mathrm{path}}$ and tension $T$ obey

$$
s\ge0,\qquad T\ge0,\qquad sT=0.
$$

An elastic cable requires a constitutive extension model instead. Establish whether each branch is anchored without slip or can redistribute through the central wheel; preserve the single commanded knee-winding angle. Check routing, wrap transitions, spring travel, slack management and clearance over the full motion, following [the kinematic model](03_leg_cable_spring_kinematics.md).

## 6. Mass, center of mass, and release records

Assign manufactured solids a material density with a source and confidence level. With $\rho_i$ in kg/m³ and CAD volume $V_i$ in mm³,

$$
m_i=\rho_i V_i\,10^{-9}\ \mathrm{kg},\qquad
r_G=\frac{\sum_i m_i r_i}{\sum_i m_i}.
$$

Use one coordinate system and consistent length units. Override simplified purchased-component solid density with verified component mass: the candidate motors contribute $2(18)+5(23)=151$ g before resolving which accessories are included in those manufacturer mass specifications [MX, MC]. Do not double-count imported geometry, horns, screws, cable or motor internals. Add estimates for wiring, controller, inserts and fasteners rather than silently omitting them.

For aggregate inertia use rotated component tensors and the parallel-axis theorem:

$$
I_G=\sum_i\left[R_i I_i R_i^T+
m_i\big((d_i^Td_i)\mathbf I-d_id_i^T\big)\right],\qquad d_i=r_i-r_G.
$$

Use kg and metres here. Convert kg·mm² to kg·m² by multiplying by $10^{-6}$; raw geometric inertia must first receive the correct density conversion. Record the assembly pose because the active spine and legs change aggregate CoM/inertia.

Before **fabrication release**, every manufactured interface must have dimensions/tolerances, every purchased part an exact variant and verified mating geometry, and every provisional spring/cable/guide/retention choice a resolved specification. Until then, continue useful parametric modeling but mark affected parts `PROVISIONAL`; do not label their drawings fabrication-ready. Deliver BOM, per-part process/finishing notes, stack-up records, load-screening assumptions and remaining risks through the [FreeCAD workflow](05_freecad_mcp_workflow.md) and [verification requirements](06_verification_and_acceptance.md).
