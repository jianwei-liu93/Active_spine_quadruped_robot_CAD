# Verification and acceptance

## Evidence and status rules

These gates govern the CAD work defined in [00_project_specification.md](00_project_specification.md). This repository's initial documentation does not establish an installed connection or a built model: every gate starts **NOT_RUN**.

Each check has exactly one execution status: **NOT_RUN**, **PASS**, **FAIL**, or **BLOCKED**. Record its requirement, input revision/parameter set, method, numerical result where applicable, artifact path and remaining limitation. A plan is NOT_RUN; a missing tool or source dependency is BLOCKED; an executed check that violates its criterion is FAIL. Never convert missing evidence into PASS.

Apply the reference classifications in [01_reference_evidence.md](01_reference_evidence.md) and the mechanism contracts in [02_spine_kinematics.md](02_spine_kinematics.md) and [03_leg_cable_spring_kinematics.md](03_leg_cable_spring_kinematics.md). Physical interfaces and load assumptions follow [04_components_and_manufacturing.md](04_components_and_manufacturing.md). Execution and ownership follow [05_freecad_mcp_workflow.md](05_freecad_mcp_workflow.md), [07_development_plan.md](07_development_plan.md) and [08_agent_orchestration.md](08_agent_orchestration.md).

## Gate sequence

| Gate | Required evidence for PASS | Initial status |
| --- | --- | --- |
| G0 — Environment | Actual installed MCP tool inventory; FreeCAD version; diagnostic geometry created, inspected, captured and saved through the discovered tools; identifiable project checkpoint. | NOT_RUN |
| G1 — Evidence and interfaces | Source/assumption table, parameter schema, frames, link graph, actuator conventions, hardware-interface records and unresolved items with owners. Any provisional choice is explicit. | NOT_RUN |
| G2 — Mechanism cycle | Full intended input-cycle closure, branch continuity, extrema, permissible travel, singularity assessment, and cable/spring state checks against the mechanism equations. | NOT_RUN |
| G3 — Foreleg and hind-leg modules | One complete foreleg and one complete hind leg with editable custom parts; complete pivots, bearings and fasteners; motor mounting checked against the declared interface; verified neutral/extreme/intermediate poses; assembly and service access; no unexplained interference. | NOT_RUN |
| G4 — Whole robot and DFM | Complete articulated assembly, supported spine load path, replicated-leg consistency, moving clearances, cable routing, packaging, practical assembly order and bounded engineering calculations. | NOT_RUN |
| G5 — Delivery | Native reopen/recompute and reversible parameter-edit checks; validated STEP exports; inspected drawings; BOM and source traceability; verification report and limitations. | NOT_RUN |

Useful independent work may continue around a blocked gate. Do not promote a dependent check as verified before its required input is established.

## Numerical closure is separate from manufacturing accuracy

Use millimetres for geometry and radians for kinematic calculations unless the authoritative schema states otherwise. Convert explicitly at API boundaries. Define a recorded characteristic mechanism length $L_{ref}$, such as the longest rigid link, and report positional closure as an actual Euclidean distance, not a squared-distance residual mislabeled as length.

Default computational thresholds, adjustable only with recorded justification before acceptance, are:

$$
\epsilon_{kin}=10^{-8}\max(L_{ref},1\,\mathrm{mm}),\qquad
\epsilon_{CAD}=\max(10^{-4}\,\mathrm{mm},10^{-6}L_{ref}).
$$

Use $\epsilon_{kin}$ for independent numerical loop equations and $\epsilon_{CAD}$ for reconstructed joint-center positions in the CAD assembly. A default axis/orientation consistency threshold is $10^{-6}$ rad. Record measured residuals and thresholds. Avoid a blanket condition-number threshold without stating the Jacobian, its scaling and the physical implication of its singularities.

These are computational consistency criteria, not bearing fits, machining tolerances, backlash allowances or predicted robot accuracy. Manufacturing dimensions, tolerance stacks and minimum running clearances must be assigned separately to actual interfaces. An unspecified critical fit remains unresolved even when closure is numerically exact.

## G2: full-cycle checks

Evaluate the full **intended** actuation or gait cycle, including its closing transition. For the spine, verify a complete unidirectional crank revolution and both resulting output phases (flexion and extension); this does not require reversing the input motor. Other limb and wheel coordinates use their declared operating ranges. Do not assume every rotary actuator has unrestricted 360-degree travel. Verify:

- Constant rigid-link lengths, coincident intended pivots and the declared branch of each closed chain.
- Continuous placements and angles after unwrapping, with no branch jumps or hidden resets.
- Actual mechanism extrema and actuator/passive-joint limits; intended and unintended singularities identified separately.
- Cable path length, routing, spring extension limits and tension/slack states using the equations and unilateral behavior specified in the mechanism design. A spring or cable drawn in a single pose is insufficient.

Use independent equations or geometric reconstruction to verify implementation outputs rather than asserting that an assembly solver returned success. A native solver fallback may pass geometric/kinematic checks when explicitly documented and independently verified; it does not establish unsupported native-constraint functionality.

## G3–G4: motion, geometry and physical interfaces

Start with inexpensive kinematic placements sampled at no more than **1 degree of change per driven rotary coordinate**, plus exact endpoints and analytically known critical poses. Adapt time sampling to satisfy this angular criterion. For multiple independently driven coordinates, record the tested coordinated motions, adverse phase offsets and range combinations; one nominal gait is not coverage of the entire configuration space.

Use transformed bounding boxes as broad-phase rejection before expensive shape checks. Evaluate candidate interference pairs using valid solids, Boolean intersection volume and minimum shape distance as appropriate. Refine samples near small clearances, sign changes, singularity neighborhoods and suspected contact, for example to 0.25 then 0.1 degree increments. Record a refinement-convergence criterion and observed result; do not treat those example increments as proof of a global minimum.

Finite sampling establishes clearance only for the tested samples and documented envelope. Claim continuous guarantees only with an additional justified bounding method. Report the smallest observed clearance, its pose and the required minimum rather than reporting only “collision-free.”

Maintain a narrow intended-contact register identifying the exact component pair, interface region and permitted contact or overlap. Bearings, shaft fits, fastener engagement and bonded interfaces may need such treatment. Do not exempt entire legs, motor assemblies or broad categories of pairs; an allowed shaft fit must not hide a nearby housing collision. Bounding-box overlap alone is not a collision failure.

Inspect each custom part for a non-null valid shape, intended solid count and positive volume. Use the more detailed geometry/BOP checks when warranted by Boolean operations or suspicious shapes. Visually inspect assembly, sections and joint extremes for errors numerical checks may miss.

Physical review covers bearing seats and retention, shaft shoulders, axial spacing, fastener engagement and tool access, moving-joint clamping, mechanical stops, cable bend/service loops, motor connectors and replaceable wear parts. Check battery restraint only if an onboard battery is selected; otherwise check external-power connector protection and strain relief. Check a plausible assembly/disassembly sequence. Apply the bounded mass, load-path and actuator-envelope calculations specified in the component document; no simulation or FEA campaign is required for these CAD gates, and no such result may be implied without execution.

## G5: native and export integrity

Close/reopen the saved project without overwriting unsaved user work, recompute and verify the part inventory and dependencies. Change and restore a meaningful parameter, checking geometry and interface propagation in both directions. Check that feature-tree editability and any required scripted-feature dependencies persist after reopening.

Reimport STEP into a clean document and compare units, overall dimensions, expected component/solid counts and representative volumes within declared export tolerances. Inspect placement, missing parts and duplicate intermediate solids. Preserve the native file as the editable deliverable; STEP does not substitute for its feature history. Check individual-part STEP files against their BOM identifiers.

Inspect TechDraw PDFs and applicable profile DXFs for units, scale, dimensions, material, revision, critical fits and readable section/detail views. A screenshot of a drawing is not a fabrication drawing. The final report must identify files actually generated and checks actually run.

## Animation interface readiness (separate from G0–G5)

Maintain exportable stable physical-instance identifiers, part-local frames, the complete pose-controller/motion-map contract, and separate length/route-dependent springs and cables as specified in [20 — CAD-to-animation interface](20_animation_and_visualisation_pipeline.md). That document defines independent AX0–AX4 readiness gates. A read-only AX0/AX1 smoke is useful during CAD development, but **final Blender videos are not a prerequisite for G5 CAD candidate or fabrication-release assessment**. These checks must not mutate or replace the canonical assembly and must not mask missing G0–G5 evidence.

## Candidate acceptance and fabrication release

A **CAD candidate** can pass the staged criteria while containing explicitly declared provisional components or assumptions, provided their envelopes/interfaces are sufficient for the stated geometric checks and those limitations appear in the delivered model, BOM and report. A record of a provisional assumption is evidence of traceability, not verification of that assumption.

**Fabrication release remains BLOCKED** when any critical mounting dimension, bearing/shaft fit, material/process choice, structural load assumption, actuator interface or other build-critical requirement remains unverified. Enumerate those items precisely. Do not stamp drawings as released or describe the robot as ready to manufacture merely because G0–G5 produced a useful CAD candidate.

## Primary verification references

FreeCAD documents [shape validity, detailed checks, intersections and distances](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TopoShape_API.md), [Part CheckGeometry and BOP checks](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Part_CheckGeometry.md), [export selection](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_Export.md), and [TechDraw outputs](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TechDraw_Workbench.md). Verify precise APIs against the installed FreeCAD version.
