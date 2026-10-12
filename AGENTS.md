# Project instructions for Codex agents

## Applicability and current state

This repository defines a FreeCAD active-spine quadruped project. Read the task scope before acting. **Documentation-only edits do not require a live FreeCAD connection.** When the user requests CAD creation, modification, inspection, or CAD verification, the MCP requirements below apply.

The initial repository status is `DESIGN_SPEC_ONLY`; all runtime gates are `NOT_RUN`. Do not turn planned scripts, mathematical derivations, source-paper experiments, or the presence of this document into claims that CAD execution has happened.

## Read order and authority

Start with [README.md](README.md), [the project specification](docs/00_project_specification.md), [reference evidence](docs/01_reference_evidence.md), and [the development plan](docs/07_development_plan.md). Read the specialized documents before changing their subsystems.

User instructions take precedence. These documents define project defaults and evidence requirements. If sources disagree, preserve the discrepancy and derive a consistent implementation; never silently replace physical dimensions to satisfy an inconsistent equation.

## Required FreeCAD MCP use for CAD tasks

**Use the user's installed FreeCAD MCP server as the primary interface to the actual FreeCAD application.** Discover its real tools, inspect the connected application, and perform the sanity round trip in [05](docs/05_freecad_mcp_workflow.md) before substantive modeling.

Where the server supports Python execution, write reproducible scripts and execute them through that MCP capability inside FreeCAD. Use supported inspection, screenshot, save, and export operations to verify results. Exact MCP tool names are implementation-dependent; never invent or assume them.

Headless/CLI tools may supplement calculations and verification. Saving an unexecuted script is not completion of a CAD task. If the connection is unavailable, record the precise blocker, continue independent useful work, and report CAD execution as `BLOCKED` or `NOT_RUN`. Do not silently replace the installed integration or claim that a connection/model was verified.

## Mechanical invariants

- Default to the FLEXOR-F-inspired, original-scale architecture in [00](docs/00_project_specification.md).
- Preserve the coupled two-output spine with one input phase and two redundant motors.
- Preserve seven physical motors and six commanded coordinates for the primary design; document passive elastic coordinates separately.
- Solve actual link closure and preserve branch continuity over a full crank revolution.
- Treat output symmetry as a measured design objective, not an additional exact constraint.
- Keep three-segment legs, their coupling, real cable routes, and separate tension/compression spring behavior.
- Record each important value as `PAPER_REPORTED`, `MANUFACTURER_VERIFIED`, `DERIVED`, or `DESIGN_ASSUMPTION`.
- Use manufacturer drawings for critical bought-part interfaces. Mark unresolved geometry explicitly.

## Collaboration and cost

Follow [08](docs/08_agent_orchestration.md). Suggested base: `gpt-6.1-sol` / `high`; routine workers: `gpt-6-luna` / `high`; bounded complex implementation: `gpt-6.1-sol` / `medium`; independent mechanical review: `gpt-6.1-sol` / `high`.

Use at most three concurrent subagents and no recursive delegation. Request the actual model/effort explicitly when supported; defaults may otherwise inherit the parent. Disclose unavailability instead of pretending a cheaper or stronger model was used.

**Only the lead may write to the live FreeCAD session or canonical assembly.** Delegate evidence extraction, supplier research, isolated source modules, and reviews with explicit file ownership. Integrate sequentially. All agents must respect the same restriction even if MCP tools are inherited.

Escalate a bounded routine task after two materially different failed attempts. Use `gpt-6-astra` / `low`, then `medium` only if needed, for a difficult unresolved issue. Higher efforts are exceptional, not default. Do not duplicate a resolved review.

## Implementation and evidence

Custom manufactured components should have meaningful native feature editability, supported by reproducible source scripts and parameters. Preserve separate parts and instances. See [05](docs/05_freecad_mcp_workflow.md).

For all current and future geometry/pose changes, preserve stable physical-instance identities, part-local frames, complete MotionMap coverage, and separately regenerated spring/cable motion. Follow the [CAD-to-animation interface](docs/20_animation_and_visualisation_pipeline.md); it is a cross-cutting export requirement, **not** permission to render videos now or alter accepted mechanism geometry. Use the current read-only motion adapter and never double-apply App::Link transforms.

Use the checks in [06](docs/06_verification_and_acceptance.md). Reopen/recompute native files and round-trip the final STEP export. Keep fit/contact exceptions precise. Finite pose sampling supports only the sampled coverage.

Perform enough verification to resolve concrete risks, then proceed. Maintain short progress updates, a decision log, and links to actual evidence. Keep mathematical assumptions, runtime results, and fabrication-release status distinct.

## Autonomy and task boundary

Complete reversible work authorized by the user and move through documented internal checkpoints without routine permission requests. Use explicit provisional choices where appropriate and continue independent work around blockers. Ask only when a missing decision materially changes the architecture or invalidates substantial work.

CAD development does not authorize purchasing, operating hardware, or releasing a design for fabrication. Complete the reviewable design package first. Preserve unrelated user files and existing local MCP settings.
