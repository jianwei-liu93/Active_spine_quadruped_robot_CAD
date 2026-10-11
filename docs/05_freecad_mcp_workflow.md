# FreeCAD MCP implementation workflow

## Purpose and present status

This document specifies work to execute on the user's Ubuntu machine with the already installed FreeCAD MCP connection. Repository documentation is not evidence that FreeCAD has been contacted or a CAD model generated. At this documentation baseline, environment checks and CAD acceptance gates are **NOT_RUN**.

Use [00_project_specification.md](00_project_specification.md) for requirements, [01_reference_evidence.md](01_reference_evidence.md) for evidence, [02_spine_kinematics.md](02_spine_kinematics.md) and [03_leg_cable_spring_kinematics.md](03_leg_cable_spring_kinematics.md) for mechanisms, and [04_components_and_manufacturing.md](04_components_and_manufacturing.md) for physical interfaces. The execution order and ownership rules are in [07_development_plan.md](07_development_plan.md) and [08_agent_orchestration.md](08_agent_orchestration.md). Acceptance is defined in [06_verification_and_acceptance.md](06_verification_and_acceptance.md).

## 1. Establish a real MCP round trip early

Before substantial modeling, the lead agent **must connect to the installed FreeCAD MCP server** and inspect its actual tool schemas. Record the server identity/version if available, FreeCAD version, Python version, available workbenches, document inventory, and output paths. State when a version cannot be determined. Different servers expose different execution, inspection and screenshot tools; no particular tool name is universal.

Use the discovered tools to complete this small sanity sequence:

1. Inspect open documents and their saved/unsaved state without modifying or closing the user's work.
2. Create a uniquely named temporary diagnostic document containing a small box and cylinder as separate objects. Use known dimensions and placements.
3. Recompute and read back the object names, dimensions, positive volumes and validity. Retrieve an actual FreeCAD view snapshot showing both objects.
4. Save the diagnostic document in a temporary project area and confirm the saved path. Then create or open the intended project document and save an identifiable initial project checkpoint.

The sanity document is disposable diagnostic geometry, not the robot deliverable. Do not overwrite an existing file or close an unsaved user document to complete this check.

Prefer FreeCAD Python executed **through the installed MCP** for repeatable feature creation and inspection when that server provides execution. If only object-level tools are available, use their documented capabilities and record limitations. Discover executables and packaging paths instead of assuming a particular Snap, AppImage or system installation.

If connection, execution or image retrieval is blocked, record the exact unsuccessful operation and evidence. Continue independent source extraction, interface design, kinematics and useful script preparation. Mark the connection or capability **BLOCKED**; a scripts-only result does not complete this workflow and must not be described as a generated or inspected CAD model. Do not install another server or reconfigure the user's setup merely to hide the blockage.

## 2. Keep one writer and one canonical model

The lead is the sole writer to the live FreeCAD MCP session and canonical CAD files. Subagents produce isolated modules, calculations, source tables or reviews. They do not mutate the shared document, GUI, Python namespace, assembly schema or output files.

Before a live write, establish an advisory project lock identifying owner, document, canonical file, run identifier and start time. All agents must respect that same-document lock. Verify that a former owner is inactive before reclaiming a stale lock. This coordination does not prevent a user from editing the GUI; recheck document identity and unexpected changes before integrating each module.

Integrate modules sequentially. Save a checkpoint before major integration and after a verified subsystem. Use document transactions when supported, inspect failures and avoid silently continuing after an unsuccessful feature. Recompute at meaningful dependency boundaries.

Use CLI/headless processes only for independent checks or isolated experiments against separate files. They must not write a file open in the live session. Do not replace the required MCP build-and-inspection workflow with an unexecuted script. Async APIs, if present, must follow that server's thread and document-mutation rules; do not assume a background thread can safely change FreeCAD documents or views.

## 3. Model editable manufactured parts

Maintain one authoritative parameter schema with units, names, defaults, allowed ranges and evidence references. Do not independently maintain divergent spreadsheet and script values. If both are used, specify which is authoritative and generate the other. Mechanical-interface decisions belong in the shared schema, not hidden literals inside component modules.

Normally represent each custom manufactured part as a separate `PartDesign::Body` with constrained Sketcher geometry and meaningful Pad, Pocket, Hole, Fillet or Chamfer features. Use named parameters and expressions where supported. Prefer datum planes and explicit local coordinate systems over incidental face or edge numbering. Sketches defining fixed manufactured geometry should be fully constrained without redundant constraints; document intentionally free construction geometry.

Each component needs a stable part identifier, material, manufacturing route, part-local frame and mating-interface definitions. Repeated identical components should share a source definition and use instances where supported. Handed or mirrored components need correct manufacturing identities and right-handed local frames.

Permitted exceptions include imported supplier STEP components, purchased-part envelopes and an explicitly justified scripted feature where native features are unsuitable. Mark envelopes as provisional, retain their source dimensions and expose their parameters. A block labeled as a motor is not a verified mounting interface. An opaque final shape and a rebuild script alone do not satisfy native editability for ordinary custom machined parts.

Fillets and cosmetic details follow functional geometry. Avoid explicit helical fastener threads unless they serve a concrete clearance or fabrication need; conventional thread annotations and simplified hardware geometry are sufficient for most assembly work.

## 4. Assemble from verified mechanism coordinates

Choose one available assembly approach and use it consistently. Ground the designated chassis reference, define joint axes and actuator zero conventions, and group rigid hardware into subassemblies. Verify the ground placement after solving.

Build the spine and one complete leg against the kinematic contracts before replication. Preserve every physical link, shaft, bearing and passive pivot. A drawn cylinder cannot stand in for an unspecified bearing arrangement or an unsupported load path.

Closed chains need an explicit link graph, active/passive coordinates, loop-closure equations and assembly-branch convention. Initialize components from the verified forward-kinematic solution. Do not add redundant fixed/revolute constraints to force a superficially stable pose. Check the loop residuals independently of the assembly solver's success message.

If the installed solver cannot reliably express or drive the mechanism, retain the complete assembly and use verified scripted placements driven by the same mechanism parameters. Label this a **scripted kinematic assembly**, record the limitation, and validate its motion. Do not delete the closing link, fuse moving components or claim native constraints exist when they do not. An available native constraint representation remains preferable when reliable.

## 5. Rebuild, inspect and deliver

Verify a bounded parameter change, recompute and inspect the affected part and assembly; restore the original value and verify the original configuration again. Use a meaningful interface-safe change rather than a cosmetic color change. Save, reopen and recompute the native project to establish that dependencies and scripted features survive a fresh session. Document any module installation or loading needed for reopening.

Export final bodies or intended assembly instances, not every object in the tree. Selecting all objects can include hidden intermediate features and duplicate solids. Produce the native assembly, assembly and custom-part STEP files, essential TechDraw drawings, applicable plate-profile DXFs, BOM, source scripts, parameters and verification evidence. Include actual screenshots of assembled, orthographic, section and exploded views as appropriate. Render and inspect drawing exports for legibility and completeness.

Suggested future paths include `src/build_robot.py`, `src/verify_kinematics.py`, `src/verify_cad.py`, `cad/active_spine_quadruped.FCStd`, and `reports/verification/`. These are proposed implementation paths, **not assertions that files already exist**; reconcile them with the project specification before implementation.

## Primary implementation references

- FreeCAD: [PartDesign Body](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_Body.md), [Sketcher scripting](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Sketcher_scripting.md), [Assembly](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Assembly.md), [Assembly Workbench](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Assembly_Workbench.md), [Export](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_Export.md).
- MCP interface examples: [neka-nat tools](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md), [ahelja FreeCAD-MCP](https://github.com/ahelja/FreeCAD-MCP), [bonninr freecad_mcp](https://github.com/bonninr/freecad_mcp). These illustrate variation; they do not identify the installed server.

The FreeCAD documentation mirror is archived. Verify exact APIs against the installed version and implementation source.
