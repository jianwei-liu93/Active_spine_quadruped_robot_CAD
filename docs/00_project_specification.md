# 00 — Project specification

**Status:** `DESIGN_SPEC_ONLY`  
**Specification revision:** 2026-10-11, initial development baseline  
**Evidence:** [01 — Reference evidence](01_reference_evidence.md)  
**Execution order:** [07 — Development plan](07_development_plan.md)

## 1. Objective and intended use

Develop an editable, reproducible FreeCAD model of a manufacturing-oriented FLEXOR-F-inspired quadruped. The first use is a small laboratory research prototype for studying coupled spine/leg mechanics. The design should expose parameters and physical interfaces so local Codex agents can refine it without repeatedly reconstructing the research context.

The deliverable is a reviewable mechanical design candidate with explicit evidence and limitations. A CAD candidate, fabrication release, assembled mechanism, and validated running robot are distinct completion states. No model, numerical verification run, manufacturing release, or hardware result is established by this specification alone.

The original paper's experiments are references, not acceptance evidence for our design. There is no assumed 0.784 m/s speed, 3.5 Hz operating capability, endurance, or terrain capability for the eventual prototype.

## 2. Baseline scope

| Requirement | Baseline | Interpretation |
|---|---|---|
| Architecture | FLEXOR-F-inspired | Coupled spine and common bilateral hind-knee winding actuator |
| Scale | Approximately 110 mm length, 99 mm width, 84 mm height | Paper reference envelope; declare CAD pose and bounding convention |
| Mass | 338 g reference | Calculate actual onboard mass; do not force an artificial CAD mass |
| Primary fabrication | Printed structural parts with metal joint hardware | Select actual process/material and bearing/shaft fits |
| Electrical reference | 5 V; OpenRB-150 controller arrangement to investigate | Mechanical packaging and connection provisions; no complete electrical design implied |
| Development environment | User's Ubuntu 22.04 with installed FreeCAD MCP | Inspect the actual versions and tools; no presumed server variant |
| Primary CAD interface | Installed FreeCAD MCP | Mandatory for local CAD execution; see [05](05_freecad_mcp_workflow.md) |
| Deliverable type | Native editable assembly plus reproducible sources and exports | Geometry, motion, manufacturing details, and review evidence |

The initial electrical assumption is a laboratory prototype with explicit external power/host connections where selected. Record the location and mass of each onboard item. A battery or onboard compute upgrade is a separately specified configuration, not an invisible addition to the 338 g target.

Scope excludes autonomous locomotion software, a robot-training campaign, exhaustive dynamics/FEA optimization, manufacturing orders, and physical actuation. Parameter and interface exports may support these later.

## 3. System architecture

### 3.1 Torso and spine

The central lumbar frame carries fixed linkage pivots, linear guides, and two synchronized spine servos. The thorax and pelvis rotate about two separate transverse axes. Both output motions arise from one closed linkage system's cyclic input; they are not independently actuated pitch joints.

The planar mechanism contains a common crank, upper/lower crank–rocker branches, slider intermediates, and rocker torso outputs. Physical left/right duplicates, cross-shafts, bearings, lateral offsets, and fastener stacks realize that planar graph in three dimensions. These support features must be modeled without adding unintended kinematic restrictions.

The source's approximate 1:3:1 torso centerline ratio is a reference for kinematic segmentation. It does not assign manufactured frame lengths of 22/66/22 mm from the external 110 mm envelope.

### 3.2 Leg modules

Use separate fore- and hind-leg module designs. Each has three main leg segments and elastic behavior appropriate to the source. The hind leg includes knee/ankle coupling and the shared winding-wheel cable drive; the foreleg retains its passive buffering joints. Provide actual springs, joints, anchors, and guided routes.

The main paper distinguishes a 90 mm sum of hind-leg segments from a 60 mm standing height. Define segment center distances and foot-contact offsets explicitly. Obtain or design individual lengths with provenance.

### 3.3 Actuator and coordinate count

| Command | Physical motor count | Mechanism behavior |
|---|---:|---|
| Spine phase | 2 | Mirrored redundant drives of one mechanical input |
| Left/right fore shoulders | 2 | Individually driven proximal coordinates |
| Left/right hind hips | 2 | Individually driven proximal coordinates |
| Hind-knee winding wheel | 1 | One command with bilateral cable routing |
| **Total** | **7** | **6 nominal independent commanded coordinates** |

The six commanded coordinates do not eliminate passive spring, cable-slack, or load-dependent joint deflections. Account for those coordinates explicitly in pose generation and future simulation. A common knee command does not prove equal left/right loaded angles.

### 3.4 Frames and units

Use a right-handed robot frame with `+X` forward, `+Y` left, and `+Z` upward. Sagittal pitch axes are parallel to local `Y`; the source's planar `X/Y` diagram must be mapped explicitly to the CAD `X/Z` plane. State the sign convention for front/rear outputs and mirrored motor phases.

Use millimetres for FreeCAD geometry and radians for numerical kinematics. Engineering loads use SI or explicitly stated N/mm formulations. Every schema field must encode units or carry a unit field. Conversion occurs at named boundaries, not scattered trigonometric calls.

A neutral configuration must define the central frame, crank phase, torso output offsets, four leg commands, wheel angle, passive deflections, and ground/foot reference. The external envelope is measured in that configuration and separately over the tested motion range.

## 4. Requirement categories

- **R-SOURCE:** Each significant dimension, material, component, or limit has a value, unit, source, and provenance category.
- **R-KIN:** Physical link closure and assembly branches remain consistent through the intended crank cycle. Symmetry is measured independently.
- **R-LEG:** Leg geometry, coupling, cable route, and elastic assumptions match the declared mechanism.
- **R-DFM:** Custom parts have a stated process; critical fits, support, retention, tool access, and assembly order are credible.
- **R-CAD:** Custom parts remain editable and separate; reproducible sources regenerate the approved geometry.
- **R-MCP:** CAD tasks operate and inspect the user's actual FreeCAD through its installed MCP server.
- **R-VERIFY:** Results are backed by actual logs and exported/native checks, with sampled coverage disclosed.
- **R-DELIVER:** Native CAD, reproducible source, manufacturing exports, BOM, drawings, and reports agree on the same revision.

Detailed acceptance is in [06](06_verification_and_acceptance.md). A paper datum cannot pass a runtime requirement, and a runtime pass cannot establish an unknown supplier fit.

## 5. Parameter and interface contract

Before independent component implementation, freeze a versioned parameter snapshot. The snapshot may evolve through recorded decisions; it is not a claim of manufacturing release.

Minimum groups:

| Group | Required fields |
|---|---|
| Identity | Revision, source versions, dimensional unit, angle unit |
| Frame geometry | Central-frame datums, fixed pivots, guide lines, torso offsets, transverse support planes |
| Spine | L1–L11, geometric input-phase convention, output-angle definitions, slider usable limits |
| Legs | Segment center distances, joint offsets, coupling lengths, foot-contact geometry, allowed pose domain |
| Tendons | Anchors, wheel pitch geometry, guide radii, branch attachment/slip rules, installed lengths |
| Springs | Type, free length, preload/reference state, rate or force curve, travel, solid height where relevant |
| Components | Exact variant/drawing revision, mount pattern, shaft/horn interfaces, connector keep-outs, mass |
| Manufacturing | Process, material, critical fits/tolerances, retention stacks, printable/machinable limits |
| Evaluation | Numeric tolerances, load cases, motion samples, contact-pair exceptions, acceptance thresholds |

Each parameter records `PAPER_REPORTED`, `MANUFACTURER_VERIFIED`, `DERIVED`, or `DESIGN_ASSUMPTION`. Unknowns stay explicit. A proposed supplier component becomes verified only when its actual drawing/specification is inspected.

Component-generation interfaces must state:

1. Owning source file/module.
2. Input parameter keys and units.
3. Local origin and axis directions.
4. Output FreeCAD object names/types and assembly attachment frames.
5. Mounting patterns and physical keep-outs.
6. Material/mass treatment and verification hooks.

Use stable part identifiers and revision fields. Symmetric parts can share a part number only when they are physically interchangeable; instance names retain left/right/front/rear identity.

## 6. Source gaps and permitted engineering choices

The paper does not give a complete fabrication release. In particular, complete output-link/guide datums, individual leg lengths, bearing widths, fits, spring specifications, and several mounting/retention details must be recovered or selected. See [01](01_reference_evidence.md).

It is permissible to choose coherent values and fabricate-ready interfaces for a paper-inspired prototype. Mark those values as design assumptions or engineering derivations and show their consequences. Preserve known source values where feasible; if changing a sourced value solves a packaging or feasibility issue, record the original value, reason, new value, and resulting checks.

Do not silently rescale purchased components. An unresolved critical interface may use a labeled envelope for independent packaging work, but it remains a fabrication-release blocker.

If missing original PDFs prevent a visual source check, use the available documents for independent work and report that limitation. Do not claim an exact reconstruction from the derivative notes alone.

## 7. Completion levels

| Level | Meaning |
|---|---|
| `DESIGN_SPEC_ONLY` | Requirements and methods exist; no CAD execution claimed |
| `KINEMATIC_CANDIDATE` | Executed mechanism calculations and a valid selected branch exist |
| `CAD_CANDIDATE` | Actual native geometry and assembly exist with documented checks/limitations |
| `CAD_PACKAGE_VERIFIED` | Required native/export round trips and package consistency checks passed |
| `FABRICATION_RELEASE_READY` | Critical component interfaces, processes, drawings, stack-ups, and engineering review are resolved for fabrication |
| Physical validation | Separate evidence of assembly, motion, loads, endurance, and performance |

The local CAD task should progress through the complete candidate/package, continuing around independent blockers. Do not label a package `FABRICATION_RELEASE_READY` while critical assumptions remain unreviewed. No gate is passed merely by documenting its intended method.

## 8. Delivery contract

Deliver native `.FCStd` files and dependencies, reproducible generation/pose/check/export scripts, parameter snapshots, assembly/custom-part STEP, applicable STL/3MF/DXF, dimensioned drawings, BOM, mass/CoM notes, assembly/calibration instructions, motion views, and verification results.

Include a final decision table: source-faithful features; designed deviations; verified supplier interfaces; provisional interfaces; actual check results; limitations; next required physical checks. Keep authoring and runtime evidence separate.
