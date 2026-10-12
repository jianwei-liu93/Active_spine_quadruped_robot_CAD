# Active spine quadruped robot CAD

**Current whole-robot work:** [r08 editable robot](cad/flexor_r08_robot.FCStd) and [r08 delivery record](docs/19_candidate_package_r08.md). The center cage now has windowed transverse crosswalls and solid upper horn-side cheeks, matching the face arrangement visible in Movie S1. The 486-part candidate preserves distinct fore/hind mechanisms, the S9 spine topology, real spring wires and positive cable terminals. Native neutral/axis/motor checks pass; final motion, exports and drawings are being regenerated for r08. Fabrication release remains blocked by explicit supplier and engineering assumptions.

A FreeCAD project for a manufacturable, editable active-spine quadruped inspired by **FLEXOR-F** in Wang et al., *Unlocking fast robotic locomotor propulsion through dynamic spine-leg synergy*, Science Advances 12, eaed5603 (2026).

**Current status: REFERENCE_FIDELITY_RECOVERY.** Installed FreeCAD MCP execution and an exploratory editable whole robot exist. The exploratory r01 model is superseded because its spine packaging and output geometry diverge from the source. Recovery is on `fix/flexor-reference-fidelity`; see [the morphology audit](docs/10_reference_morphology_and_recovery.md). Numerical closure is separate from physical clearance and fabrication readiness.

The current corrected spine is [flexor_r02_spine.FCStd](cad/flexor_r02_spine.FCStd), with [STEP exports](exports/step/r02/) and [slider-plate source reconciliation](reports/source_review/slider_plate_reconciliation.md). Its fixed guide plates now connect C1 to A2 and C2 to A1 through tall contoured ears, as shown in the paper and Movie S2. Exact fit, liner retention and manufacturer mounting interfaces remain provisional.

The initial target is a desktop-scale research prototype, approximately **110 × 99 × 84 mm**, with a **338 g reference mass**. These are source-prototype targets, not promised dimensions or performance of the eventual design. See the source definitions in [the reference evidence](docs/01_reference_evidence.md).

## Start here

1. Read [AGENTS.md](AGENTS.md).
2. Read the [project specification](docs/00_project_specification.md) and [reference evidence](docs/01_reference_evidence.md).
3. Follow the [development plan](docs/07_development_plan.md).
4. For local CAD development, connect to the **installed FreeCAD MCP server** and complete its documented sanity round trip before modeling. See the [FreeCAD workflow](docs/05_freecad_mcp_workflow.md).
5. Keep evidence and completion claims aligned with the [acceptance criteria](docs/06_verification_and_acceptance.md).

The lead agent is the sole writer to the live FreeCAD document. Subagents may independently research components, derive/check mathematics, and write assigned source modules, then hand their work to the lead for serial integration.

## Documentation map

| Document | Purpose |
|---|---|
| [00 — Project specification](docs/00_project_specification.md) | Scope, architecture, requirements, parameters, decision ownership, and delivery contract |
| [01 — Reference evidence](docs/01_reference_evidence.md) | Paper facts, exact provenance, source ambiguities, missing dimensions, and apparent equation inconsistencies |
| [02 — Spine kinematics](docs/02_spine_kinematics.md) | Link graph, geometric solver, assembly branches, derivatives, transmission, and redundant drive |
| [03 — Leg, cable, and spring kinematics](docs/03_leg_cable_spring_kinematics.md) | Three-segment legs, coupling, routed cables, unilateral constraints, and elastic elements |
| [04 — Components and manufacturing](docs/04_components_and_manufacturing.md) | Supplier interfaces, process choices, tolerances, load screening, and mass properties |
| [05 — FreeCAD MCP workflow](docs/05_freecad_mcp_workflow.md) | Required MCP use, native editability, assembly implementation, scripts, and exports |
| [06 — Verification and acceptance](docs/06_verification_and_acceptance.md) | Meaningful gates, evidence requirements, tolerances, and completion levels |
| [07 — Development plan](docs/07_development_plan.md) | Dependency order, parallel work, first deliverable, and progress recording |
| [08 — Agent orchestration](docs/08_agent_orchestration.md) | Model/effort defaults, cheaper workers, escalation rules, and live-session ownership |
| [09 — Codex start prompt](docs/09_codex_start_prompt.md) | Ready-to-copy development request that refers to the specifications and requires actual MCP execution |
| [10 — Morphology and recovery](docs/10_reference_morphology_and_recovery.md) | Source comparison, preserved r01 work and spine-first correction controls |
| [Reference files](references/README.md) | Original PDF names, hashes, and local setup after cloning |

## Mechanical baseline

- Three torso segments and two sagittal spine output joints.
- One cyclic spine coordinate realized by a closed linkage/slider mechanism.
- Two synchronized, redundant spine motors.
- Four separately actuated proximal leg joints.
- One common winding-wheel motor for both hind knees.
- Three-segment compliant legs with tension and compression springs.
- **Seven physical servos; six nominal commanded coordinates**, plus passive elastic coordinates.

The angular relation `psi1 + psi2 = pi` is a synthesis objective, not an exact extra assembly constraint. The supplement reports a 9.29-degree maximum symmetry discrepancy. Numerical link closure, manufacturing tolerances, and this symmetry discrepancy must be treated separately.

## Use after cloning

Open Codex in this repository. The local machine's existing FreeCAD MCP configuration remains the connection authority; a repository clone does not install or connect that server.

Paste the [Codex start prompt](docs/09_codex_start_prompt.md) to begin development. Keep detailed requirements in the linked documents as they evolve.

Place your copies of the paper and supplement in `references/` using the names in [references/README.md](references/README.md). The documentation records the reviewed evidence and equations, so work on planning, software structure, and explicitly assumed geometry can proceed before those local copies are available. Source-visual checks must remain incomplete until the PDFs or the corresponding verified source figures have actually been inspected.

Recommended base model: **GPT-6.1 Sol, high reasoning**. Use **GPT-6 Luna, high reasoning** for bounded routine work. Current model availability must be checked in the local client. Detailed rules and optional configuration examples are in [08](docs/08_agent_orchestration.md).

## Expected future outputs

The development plan calls for native `.FCStd` documents, reproducible Python/macros and parameters, STEP assembly and custom parts, applicable print/profile exports, dimensioned drawings, BOM, assembly instructions, and verification evidence. Native exploratory checkpoints and source/verification scripts are present. Corrected CAD, export and drawing acceptance must be established by the revision-specific reports; the exploratory checkpoints are not manufacturing deliverables.

The final CAD candidate should be assessed for manufacturability. Fabrication release, physical operation, endurance, and locomotion performance require their own evidence.
