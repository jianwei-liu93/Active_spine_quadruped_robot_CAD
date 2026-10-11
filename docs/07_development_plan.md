# 07 — Development plan

**Current state:** `DESIGN_SPEC_ONLY`. No FreeCAD application connection, mechanism execution, CAD build, export, or physical test is claimed by this initial documentation commit.

Use [00](00_project_specification.md) for scope, [05](05_freecad_mcp_workflow.md) for execution, and [06](06_verification_and_acceptance.md) for gate definitions. The user may steer the scope; record changes rather than silently changing architecture.

## 1. Dependency order

| Stage | Work | Independent work that may run concurrently | Exit evidence |
|---|---|---|---|
| A0 — Environment and evidence | Inspect local repo/instructions, source files, models, installed MCP and FreeCAD; perform sanity round trip | Paper fact extraction; supplier drawing inventory | Environment/source report; actual MCP result |
| A1 — Mechanism definition | Freeze frames, joint graph, source values, explicit missing-value choices; implement spine closure | Motor/board/bearing interfaces; leg source derivation | Parameter snapshot; full-cycle numerical report |
| A2 — Spine prototype | Build native spine parts/assembly and motion control through MCP | Isolated leg module source; BOM skeleton | Spine `.FCStd`, views, source, closure and initial clearances |
| B1 — Single leg modules | Complete one foreleg and one hind leg with coupling, springs, tendon routing, and retention | Bounded manufacturing review; drawing preparation | Module geometry, route checks, and interface review |
| B2 — Whole robot | Instantiate four legs, integrate torso, support hardware, controller/connection space | Documentation and independent report review | Complete assembly; mass/envelope and engineering screening |
| C — Verified package | Fix concrete failures; reopen/recompute; export and reimport; finish drawings/BOM | Review exported snapshots and package manifest | Consistent native/export package and gate results |

The numerical spine solver should precede expensive detailed solids. Independent work may continue while a supplier interface is unresolved, but it must not establish a false gate pass.

## 2. First local Codex assignment

Connect to the installed FreeCAD MCP and complete A0–A2. Produce the first tangible result: a saved, viewable spine assembly that follows the selected full-cycle branch and has physical link thickness, guides, bearings, and support planes.

Then continue through B and C within the same authorized task, using the staged checkpoints to preserve progress. The checkpoints are internal review steps, not requests for routine user approval.

At the first checkpoint report:

- Actual FreeCAD/MCP versions and tool capability results.
- Source PDFs inspected or missing.
- All source parameters and selected unknowns.
- Closure, branch, travel, and symmetry results, with numeric/physical tolerance distinctions.
- Native file path and screenshot/view evidence.
- Remaining interference or interface issues and the next action.

A plot or unexecuted Python file alone is not the first CAD checkpoint.

## 3. Roles and integration

The lead owns architecture, parameter schema, live MCP, native assembly, and integration. Routine workers own supplier facts, assigned component source files, BOM rows, or documentation. A bounded reviewer checks the actual mechanism package; another bounded review checks final integration. See [08](08_agent_orchestration.md).

Freeze the attachment frames and interface dimensions before delegating component code. If those values change, identify every affected component and invalidate only the relevant downstream results.

Use isolated worktrees where useful for code. They do not provide independent access to the same FreeCAD process: the live-session restriction applies across all worktrees and agents.

## 4. Proposed future layout

The following are proposed output locations, **not files claimed to exist today**:

| Path | Intended content |
|---|---|
| `src/` | Component generation, kinematics, pose, verification, and export modules |
| `parameters/` | Versioned machine-readable parameters and component interfaces |
| `cad/` | Native assembly and any linked native parts |
| `exports/step/` | Final assembly and custom-part STEP |
| `exports/print/` | Approved candidate print meshes |
| `exports/profiles/` | Flat-stock profiles where applicable |
| `drawings/` | Native drawing pages and PDFs |
| `bom/` | BOM data and supplier-reference manifest |
| `reports/` | Gate results, assumptions, checks, screenshots, and package manifest |
| `vendor/` | Locally obtained manufacturer files with provenance and notices |

Avoid tracking large transient meshes, repeated render caches, secrets, or machine-specific MCP connection credentials. Decide repository storage for large reproducible assets and vendor files deliberately; no automatic public redistribution is assumed.

## 5. Progress and decisions

Create a concise progress record during execution with these fields:

`date | revision | stage/gate | status | evidence paths | blocker | next action`

Allowed gate statuses are `NOT_RUN`, `PASS`, `FAIL`, and `BLOCKED`. For candidate-level acceptance, report provisional interfaces alongside the relevant passed geometric checks. Keep fabrication readiness as a separate explicit assessment.

Each design decision should record:

- The ambiguity or failure being resolved.
- Source values and conventions affected.
- Selected assumption/change and reason.
- Consequences for packaging, force transmission, mass, and manufacturing.
- Checks performed and remaining limits.

Where evidence depends on parameters, pin the parameter revision and source/script revision. Use a manifest with file hashes for the final deliverables; do not impose an expensive provenance campaign on every intermediate screenshot.

## 6. Bounded recovery

- **MCP unavailable:** record the actual error; complete independent source, math, and script work. Connection/CAD-execution gates remain blocked. Give the smallest useful local corrective step.
- **Linkage infeasible:** reduce to the planar model, check source conventions/unknown datums/branches, and solve the physical closure. Do not hide failure by stretching links or forcing symmetry.
- **Assembly solver unreliable:** preserve the full mechanism and use verified scripted placements if supported, documenting the implementation.
- **Supplier drawing missing:** use a labeled envelope for packaging and identify the interface as provisional. Continue work unaffected by it.
- **Detailed collision:** inspect the offending part pair and pose, adjust the documented stack/interface, and rerun relevant motion checks.
- **Worker blocked:** follow the bounded escalation in [08](08_agent_orchestration.md), passing a minimal reproducer.

Do not restart a completed stage merely because context was compacted or a session resumed. Inspect the saved state and continue the actual outstanding work.

## 7. Final handoff

Report delivered paths and revision; source-faithful features; engineering changes; actual model dimensions/mass; pass/fail/blocked results; verified and unresolved hardware interfaces; and the specific outstanding requirements for fabrication and physical validation.

The task is complete at the agreed CAD deliverable level when the actual package and its evidence exist. Missing critical fabrication information must remain visible, even if the complete editable CAD candidate is delivered.
