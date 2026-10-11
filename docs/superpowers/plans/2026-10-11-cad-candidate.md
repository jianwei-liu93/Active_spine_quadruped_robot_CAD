# Active spine CAD candidate implementation plan

> **For agentic workers:** Use superpowers:executing-plans for lead integration. Supplier and review work is bounded delegation; only the lead uses FreeCAD.

**Goal:** Generate the complete editable FLEXOR-F-inspired candidate and auditable review package in this repository.

**Architecture:** One authoritative JSON parameter snapshot drives a pure-Python closure solver and scripted FreeCAD placements. Custom parts use constrained sketches, pads and pockets; purchased envelopes remain explicitly provisional where drawings are missing. Seven motors implement six commands with passive leg states.

**Tech Stack:** Installed FreeCAD MCP, FreeCAD Python/PartDesign/Sketcher/TechDraw, Python numerical checks, native/STEP/STL/DXF exports.

**Spec:** docs/00_project_specification.md through docs/08_agent_orchestration.md; user-pasted execution brief.

## Global constraints

X forward, Y left, Z up; geometry mm, numerical angles rad. Preserve reported spine lengths. Never enforce exact output symmetry. Only lead mutates canonical schema/CAD. Unknown supplier interfaces block fabrication release. No hardware operation/purchasing. Work in the requested clone and commit/push meaningful checkpoints.

## Review focus

- Full crank closure, branch signs and near-tangent configurations: independent length residuals and finite-difference derivatives.
- Wrong handed transforms: actual CAD pivot/axis reconstruction.
- Cable slack/extension and spring bind: explicit laws, asymmetric prescribed poses; no claim of loaded equilibrium.
- Layer and motor interference: exact solid checks after broad-phase rejection, explicit pair exceptions.
- Native dependency loss/duplicate STEP solids: reopen, reversible parameter edit, reimport inventory/volume/bounds.

## A0: environment and diagnostic

- [ ] Read baseline, inspect sources and discover actual MCP/version/document inventory.
- [ ] Write src/diagnostic.py; create box 10x20x30 and cylinder r5 h20 separated by 30 mm through MCP.
- [ ] Recompute, inspect volumes/validity, save/reopen, capture actual view; record reports/verification/environment.json.
- [ ] Save identifiable initial robot document and commit/push checkpoint.

## A1–A2: spine

Files: parameters/candidate_r01.json, src/kinematics.py, src/verify_kinematics.py, tests/test_kinematics.py, src/cad_common.py, src/build_robot.py.
Interface: load_parameters(path)->dict, spine(theta,p)->named planar points/branch metrics; build(root)->document, pose(document,theta,...)->placements.

- [ ] Test impossible intersections, full-cycle rigid lengths, branch continuity and periodic closure before solver implementation.
- [ ] Adopt explicit reversible missing output-link/guide dimensions; record source gaps and decisions.
- [ ] Sweep >=720 intervals; report residuals, travel, symmetry (project convention), conditioning and derivatives.
- [ ] Build separate native links, crank, sliders, guides, output frames, bearings/pins/retention; save cad/checkpoints/spine_r01.FCStd and views.
- [ ] Independent mechanical review; resolve concrete failures; commit/push.

## B1–B2: legs and integration

Files: src/leg_mechanics.py, src/build_robot.py, parameters/candidate_r01.json, reports/verification/legs.json.
Interface: leg_pose(qh,qk,qa,p)->joint centers and coupling vertices; routed_tendon(...)->segments/arcs/length; elastic_state(...)->spring/cable forces and travel.

- [ ] Test full 3-segment FK, parallelogram closure, tangent radii, unilateral force signs and travel.
- [ ] Build one foreleg and one hind leg, separate pivots/coupler, springs, seats, guides and anchors; inspect neutral/extreme poses.
- [ ] Instantiate all legs, seven motor envelopes/interfaces, controller/connector provisions, spine redundancy synchronization.
- [ ] Check CAD centers, shape validity, sampled interference, mass/CoM, tolerance stacks and bounded load/actuator screening; record failed/unrun checks honestly.
- [ ] Save whole robot checkpoint; commit/push.

## C: delivery

Files: src/verify_cad.py, src/export_package.py, bom/*, drawings/*, reports/verification/*, reports/assembly.md, reports/status.md, reports/manifest.json.

- [ ] Export assembly and custom-part STEP, applicable STL/DXF, native part documents and dimensioned TechDraw review drawings.
- [ ] Reopen/recompute native CAD; change/restore structural thickness; independently reimport STEP and compare counts/volumes/bounds.
- [ ] Inspect actual views and drawing PDFs; prepare BOM, assembly/calibration notes, engineering screening and manifest.
- [ ] Independent final package review; resolve material discrepancies, leave explicit gates and release blockers.
- [ ] Verify repository/package consistency, commit/push final package and report actual completion level.

Execution is authorized by the user's detailed brief; internal checkpoints require no routine approvals. Unavailable original PDFs remain BLOCKED for source-visual verification.
