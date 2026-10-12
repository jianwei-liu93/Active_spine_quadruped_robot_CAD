# 09 — Codex start prompt

Open Codex in the cloned repository on the Ubuntu machine that has FreeCAD and the FreeCAD MCP server configured. Select the actual model and effort in the client; mentioning them in a prompt does not change a running model. Recommended launch and configuration are in [08](08_agent_orchestration.md).

Copy the text below as the development request. The repository documents hold the detailed requirements and mathematics; this prompt gives the execution order and task boundary.

---

Work in this cloned repository to create a realistic, editable, manufacturing-oriented FreeCAD CAD candidate for the FLEXOR-F-inspired active-spine quadruped. Complete the whole robot and its review package, using the repository specification as the project baseline.

## Read and establish the baseline

Read `AGENTS.md`, `README.md`, and `docs/00_project_specification.md` through `docs/08_agent_orchestration.md`. Follow their requirements, source definitions, frame conventions, implementation contracts, and acceptance gates. Start with `00`, `01`, and `07`; read the specialized documents before implementing each subsystem.

Inspect the existing repository and preserve prior work. Read `references/README.md` and inspect the locally available paper and supplement, particularly the mechanism diagrams, construction figures, and Table S1. If the PDFs are absent, use the documented evidence for independent work and explicitly leave source-visual checks incomplete. Do not claim to have read unavailable files.

Maintain a single parameter source of truth. Every important value must be classified as `PAPER_REPORTED`, `MANUFACTURER_VERIFIED`, `DERIVED`, or `DESIGN_ASSUMPTION`, with its source or rationale and verification status. Distinguish an unknown value from an adopted provisional value. Reconcile document conflicts before relying on them and record material design changes with their rationale.

## Mandatory FreeCAD MCP execution

Use my **installed FreeCAD MCP server as the primary interface to the actual FreeCAD application**. Discover the server's available tools and the connected FreeCAD version; do not invent tool names or assume a particular server implementation.

Complete the real MCP sanity round trip in `docs/05_freecad_mcp_workflow.md` before substantive modeling: create a diagnostic document with separate simple solids, recompute it, inspect dimensions, volumes and validity, obtain an actual application view, save it, and verify the saved result. Keep this diagnostic separate from the robot assembly and record the evidence under the documented verification structure.

Where supported, write reproducible Python modules/macros and execute them through the MCP's Python capability inside FreeCAD. Use the actual application's inspection, save, screenshot and export capabilities to check the generated model. Supplementary numerical or headless tools are appropriate for calculations and independent checks.

If the installed MCP connection or an essential capability is unavailable, report the exact blocker, continue useful independent work, and leave the affected CAD gates `BLOCKED` or `NOT_RUN`. Do not substitute an unexecuted script or a rendered illustration for an actual CAD deliverable. Preserve the existing MCP configuration.

## Mechanical and manufacturing requirements

Implement the coupled spine mechanism described in the documents: three torso sections, two spine output joints driven by one cyclic mechanism coordinate, and two redundant spine motors. Preserve the primary architecture's seven physical servos and six nominal commanded coordinates, plus its passive elastic states.

Solve geometric loop closure and track assembly branches throughout the intended crank cycle. Treat output symmetry as a measured synthesis objective, not an extra exact linkage constraint. Implement the foreleg and hind-leg distinctions, three-segment geometry, knee/ankle coupling, bilateral tendon routing, slack/taut states, and separate extension/compression spring behavior from `02` and `03`.

Turn the mechanism into physically separate, assemblable parts with realistic motor interfaces, shafts, bearings, spacers, fasteners, joint retention, guides, spring seats and cable anchors. Use manufacturer drawings for critical purchased-part interfaces. Define material/process assumptions, fits, tool access, assembly sequence and replaceable wear parts as specified in `04`.

Use explicit provisional values where source dimensions are missing and a reasonable choice allows reversible progress. Keep unresolved critical interfaces visible in the release status. Check load paths, actuator envelopes, spring travel, mass properties and motion clearance to the documented depth; do not infer continuous motor capability from stall torque.

## Model allocation and subagents

Use the policy in `docs/08_agent_orchestration.md`. The recommended lead is `gpt-6.1-sol` at `high`; bounded routine workers use `gpt-6-luna` at `high`. Use Sol at `medium` for more complex bounded implementation and Sol at `high` for independent mechanical review. Escalate a difficult unresolved issue to `gpt-6-astra` at `low`, then `medium` only when justified.

Verify actual model availability and routing. Request model/effort overrides explicitly when supported; do not claim that a requested model ran if the client used an inherited or different model. If delegation or overrides are unavailable, continue with the available model and report that limitation.

Use at most three concurrent subagents, with no recursive delegation. Delegate bounded evidence extraction, supplier research, BOM work, assigned source modules and reviews. Give each task explicit file ownership, parameter revision, units, interfaces, evidence inputs, output contract and acceptance check. Workers return concise findings, changed paths, checks actually run and blockers.

**Only the lead may operate the live FreeCAD MCP session or modify the canonical assembly and shared parameter schema.** Workers must not call the live CAD tools, even if those tools are inherited. Separate worktrees do not isolate the application. Integrate changes sequentially. Escalate routine tasks after two materially different failed repair attempts and avoid repeated reviews of resolved issues.

## Preserve animation readiness without delaying mechanical CAD

Read `docs/20_animation_and_visualisation_pipeline.md`. From now on keep stable App::Link-instance IDs, body-local geometry frames, explicit native placements, complete PoseController/MotionMap coverage and separate spring/cable shape requests. Reuse existing read-only r03/r07 motion APIs where applicable. When safe, implement the document's bounded AX0/AX1 inventory/pose-export smoke. Preserve correct physical linkage and manufacturing priorities; do not make Blender video rendering or a second pose solver part of this initial CAD task.

## Execute and deliver

Follow `docs/07_development_plan.md`: establish the environment and source/interface contracts, build and verify the spine mechanism, complete one foreleg and one hind-leg module, then integrate and verify the whole robot. The spine is the first reviewable checkpoint; continue through the complete authorized CAD candidate without stopping for routine approvals.

Create the native editable `.FCStd` assembly and custom parts, reproducible source modules/macros, parameter records, STEP assembly and parts, applicable print/profile exports, dimensioned drawings, BOM, assembly instructions, and verification evidence specified in `00`, `05`, and `06`. Use meaningful native features for custom manufactured parts and preserve part identities and instances.

Run the documented checks against the actual generated artifacts: full-cycle mechanism behavior, branch continuity, spring/cable states, relevant motion interference and clearances, assembly/service access, native save/reopen/recompute and parameter editing, and STEP round-trip consistency. Report numerical tolerances and sampled coverage accurately. Maintain `NOT_RUN`, `PASS`, `FAIL`, or `BLOCKED` gate status with links to actual evidence.

Keep concise progress updates and a decision log. Ask only when a missing decision materially changes the architecture or invalidates substantial work; otherwise choose a documented provisional default and proceed. Complete reversible work and prepare a concrete reviewable result.

At completion, identify the files actually generated, the actual model/effort allocation, checks performed and results, remaining assumptions and blockers, and the achieved completion level. Distinguish a verified CAD package from fabrication release or physical validation; the source paper's experiments are not verification of this new design. This task authorizes CAD development and documentation, not purchasing or operating hardware.
