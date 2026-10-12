# 20 — CAD-to-animation interface and visualization pipeline

**Status:** DESIGN SPECIFICATION ONLY. No Blender scene, mesh export, animation, or movie is claimed to have been generated or tested by this document.  
**Scope:** Cross-cutting interface contract for the existing FreeCAD FLEXOR-F candidate; no change to the accepted linkage, actuator count, manufacturing baseline, or current verification evidence.  
**Maintainer:** Lead CAD agent. **Revision:** 2026-10-12 (v0).

Related: [00 project specification](00_project_specification.md), [02 spine kinematics](02_spine_kinematics.md), [03 leg/cable/spring mechanics](03_leg_cable_spring_kinematics.md), [05 FreeCAD MCP](05_freecad_mcp_workflow.md), [06 acceptance](06_verification_and_acceptance.md), [07 plan](07_development_plan.md), [08 agents](08_agent_orchestration.md), and [10 morphology recovery](10_reference_morphology_and_recovery.md).

## 1. Goal and tool boundaries

The CAD and engineering motion model remain authoritative. Build motion exports that can be replayed in **Blender** for:

1. A clean, assembly-order-aware exploded view and reassembly.
2. An isolated demonstration of one continuous spine-crank revolution, the two sliders, coupled torso outputs, and linkage transmission.
3. A synchronized whole-robot spine/leg/hind-knee demonstration, with optional joint/phase overlays.

FreeCAD + the **installed FreeCAD MCP** remain the authoritative CAD editing, mechanism inspection, and export environment. Blender is a downstream visualization consumer, **not a second mechanical model or physics solver**. A future MuJoCo trajectory may supply independently validated dynamic motion; do not label prescribed motion as a running simulation.

**Current-project integration:** The active reference-fidelity branch has saved r08 assembly artifacts, a PoseController/MotionMap, and prior leg-motion machinery. Inspect the actual current revision before implementation; do not assume r08 remains latest. Favor adapters to:

- src/robot_pose_r03.py: rigid source-local-to-world placements and the existing guarded native pose code.
- src/leg_motion_r07.py: read-only descriptor(doc, theta, leg_angles, wheel_angle, config), which yields placements, shape_requests, state, validation information; regenerate_sources(plan) and copied_shapes(...) for legitimate length-dependent springs/cables.
- src/motion_views_r07.py: FreeCAD visual captures; these do not constitute full Blender exports or proof of motion clearance.
- src/build_robot_r08.py and the current MotionMap/PartsLibrary: current instance inventory and motion descriptors.

Use the actual latest API, verify each supported motion kind, and fail closed for an unhandled dynamic part. Do not “fix” a pose failure by silently freezing an articulated part or dropping it from the export. Read-only copied_shapes provides **world** copies, while regenerate_sources produces **local** source shapes: never apply a placement twice.

## 2. Invariants from CAD development onward

Each exported *physical instance*, including left/right copies and small moving hardware, needs:

- A unique stable **instance_id**, independent of presentation label and unrelated object-order changes. Keep a stable mapping from current FreeCAD App::Link Name and the source/BOM part identifier. Preserve existing names when stable; version any mapping correction. Do not force renaming of hundreds of native objects merely to build this mapping.
- A distinct **mesh_id** for its shareable source geometry. Several App::Link instances can use one part mesh but must have different instance IDs and time-varying transforms.
- A defined component-local, right-handed coordinate system and a unique neutral reference pose; state explicit frame origin, axis directions, parent/mounting frame, and units.
- A semantic group (spine frame, input crank, rocker, upper/lower slider, front/rear torso, each leg, spring, cable, servo, shaft, fastener, controller), active/passive/fixed classification, material, source object, part number, and release/provenance status when available.
- A physical geometry flag: rigid; length/route dependent; or static auxiliary. Do not fuse moving links, flatten the assembly into one mesh, or bake shared source solids at world position without reversing that bake.
- Unambiguous visibility: exclude hidden construction/source libraries and duplicated intermediate solids; include every intended visible hardware instance. Do not confuse native feature-body count with physical App::Link instance count.
- A preserved joint/assembly graph with fixed body, parent relationships, revolute/slider axes, commanded coordinates, and passive/dependent constraints. Provide actual attachment/anchor coordinates for procedural components.

This is an **interface requirement**, not a request to redesign correct functional geometry. Native manufactured parts retain editable Sketcher/PartDesign history and separate source parts, even though Blender receives tessellated meshes.

## 3. Coordinate and transform specification

FreeCAD robot world is **+X forward, +Y left, +Z up** and right-handed. Geometric/position values are **millimetres** in FreeCAD and **metres** in Blender. Numerical joint angles are **radians** and unwrapped for cyclic driver state. Blender is also Z-up; **do not add an arbitrary 90-degree rotation**. If a non-identity axis mapping is introduced, encode it explicitly and test it.

Use column vectors and homogeneous transforms. Let W denote the central CAD world frame and i an instance component-local frame. Each motion sample produces

$$
{}^W T_i(t)=\begin{bmatrix}{}^W R_i(t)&{}^W p_i(t)\\0&1\end{bmatrix},
\quad p_i\ {\rm in\ mm},\ R_i\in SO(3).
$$

The Blender-space mapping is determined by the explicit conversion matrix

$$
C=\mathrm{diag}(0.001,0.001,0.001,1),\qquad
{}^{W_B}T_{i_B}=C\,{}^{W}T_i\,C^{-1}.
$$

Apply the same axis/scale conversion to local mesh vertices exactly once. For identical axes this means **same rotation**, position multiplied by 0.001, and local geometry coordinates multiplied by 0.001. If mesh geometry is already in metres, do not rescale again.

Prefer one local mesh per distinct physical part definition. When the available source is a world-space shape at neutral pose t0, reconstruct local vertices using

$$
v_{i,\mathrm{local}}=\left({}^W T_i(t_0)\right)^{-1}v^W(t_0).
$$

For a genuine part-local FreeCAD shape, confirm how its own Shape.Placement, source Placement, LinkPlacement and LinkTransform are composed before exporting; do not blindly apply the inverse link transform again. Prove the choice by reprojecting each exported mesh to the neutral and at least two non-neutral CAD placements.

Use proper rotations (orthonormal R and det R=+1); mirrored left/right parts must not be represented by an undocumented negative-scale reflection. Blender quaternions should be stored as **[w,x,y,z]** when sent directly to mathutils. Normalize and choose sign continuity so adjacent q values have nonnegative dot product. Matrices, if supplied, are row-major JSON nested rows, interpreted as acting on column vectors; validate this convention in the importer.

## 4. Two-layer interchange contract

**Layer A — Immutable part assets and assembly manifest.** Create local-space tessellated meshes for distinct physical parts, plus a deterministic manifest. Preferred format is GLB/glTF *when the installed FreeCAD/export tooling actually preserves the necessary geometry/hierarchy*. Otherwise, per-part OBJ/PLY/STL or equivalent meshes plus the manifest are acceptable. STEP remains the engineering CAD export, not the default Blender animation exchange.

**Layer B — Pose and procedural-shape timeline.** Provide ordered time samples, all rigid-instance transforms, commanded and passive/dependent coordinates, and per-frame changes to springs and tendon routes. Do not use a GLB with only a static neutral assembly and claim that the movement has been exported.

Recommended future paths (do not claim these exist now):

~~~text
animation/
  schema/                       # JSON Schema, schema version and validation
  geometry/                     # Local-space part meshes, immutable per geometry hash
  motion/                       # Frame transforms, actuator/passive states, source hashes
  blender/                      # Scene builder, importer, procedural springs/cables, shots
  scenes/                       # Regenerable .blend file(s)
  output/                       # PNG sequences and encoded videos when authorized
reports/animation/              # Export/readback/pose-validation evidence and thumbnails
~~~

The smallest proposed **manifest** has the structure below; identifiers and paths are illustrative, not an assertion about existing FreeCAD objects.

~~~json
{
  "schema_version": "1.0",
  "cad_revision": "r08-or-later",
  "source": {
    "cad_path": "cad/flexor_r08_robot.FCStd",
    "cad_sha256": "COMPUTE_AT_EXPORT",
    "parameter_files_sha256": {"parameters/assembly_r08.json": "COMPUTE_AT_EXPORT"},
    "motion_map_sha256": "COMPUTE_AT_EXPORT",
    "exporter_revision": "GIT_SHA"
  },
  "conventions": {
    "world_axes": {"x": "forward", "y": "left", "z": "up"},
    "handedness": "right",
    "cad_length_unit": "mm",
    "blender_length_unit": "m",
    "angle_unit": "rad",
    "matrix_layout": "row_major_nested_rows",
    "vectors": "column",
    "quaternion_order": "wxyz",
    "reference_pose_id": "neutral_v1"
  },
  "meshes": [
    {"mesh_id": "mesh:source_part_a", "path": "geometry/source_part_a.glb",
     "sha256": "COMPUTE_AT_EXPORT", "local_frame": "part_a_local",
     "local_units": "m", "tessellation_tolerance_mm": 0.05}
  ],
  "instances": [
    {"instance_id": "instance:front_left_link",
     "freecad_object_name": "EXACT_NAME_FROM_INVENTORY",
     "part_number": "EXACT_PART_NUMBER_FROM_SOURCE",
     "mesh_id": "mesh:source_part_a", "group": "foreL",
     "motion_kind": "rigid", "frame": "front_left_link_local"}
  ],
  "timeline": {
    "timestamps": "motion/timestamps.npy",
    "transforms": "motion/T_world_component_mm.npy",
    "array_layout": "[frame, instance, row, column]",
    "instance_order": ["instance:front_left_link"],
    "actuated_order": ["spine_phase", "foreL_hip", "foreR_hip",
                       "hindL_hip", "hindR_hip", "hind_wheel"],
    "passive_state_path": "motion/passive_states.jsonl",
    "deformable_state_path": "motion/procedural_shapes.jsonl"
  }
}
~~~

Array files are an example, not a required dependency on NumPy inside the installed FreeCAD interpreter. An equivalent versioned JSON/JSONL representation is acceptable, especially for the first adapter. Pick and freeze one **actual** validated format before Blender import. The instance_order array must match the transform axis exactly, or the importer must reject the payload.

Validate schema fields, all paths, geometry hashes, frame counts, monotonically increasing finite timestamps, finite 4×4 matrices, bottom rows [0,0,0,1], and unique instance/mesh IDs. Report source revisions and tessellation settings; reject missing files or a changed source SHA when strict reproduction is requested.

## 5. Commanded, passive and shape-dependent state

The FLEXOR-F reference has **seven physical motors but six commanded coordinates**:

$$
q_a=[\theta_\mathrm{spine},q_{\mathrm{foreL}},q_{\mathrm{foreR}},
q_{\mathrm{hindL}},q_{\mathrm{hindR}},u_\mathrm{wheel}]^T.
$$

Two spine servos redundantly drive one cyclic input; both output torso angles and both sliders follow the validated physical linkage equations, not independent animated curves. Sample the original exact crank-to-link transformations, not a visual sinusoidal substitute.

The current prescribed leg-motion adapter additionally uses knee states for each leg. These are **passive/prescribed mechanical states, not additional actuators**. All legs' three-segment couplings and hind-wheel/cable constraints remain explicit. Cable slack, spring forces and asymmetric knee response do not follow uniquely from the six commands alone; export the provided knee/passive values, and label their provenance as one of:

- **PRESCRIBED_KINEMATIC** — manually specified, consistent with geometry.
- **QUASISTATIC_MODEL** — solved under explicit loads, spring/cable assumptions and constraints.
- **DYNAMIC_SIMULATION** — imported from an actually run and identified simulator with validated mappings.
- **SOURCE_MEASURED** — digitized/measured reference, with source and estimation uncertainty.

Never label PRESCRIBED_KINEMATIC as load-predicted motion. A reference synchronization example may use the published near-optimal hind-backswing delay of pi/10 **only after identifying actual source event times**; it is not an unconditional numerical offset for all limb angles.

For each sampled time supply the complete rigid-instance transform set. Cyclic spine phase remains **unwrapped** (e.g. theta runs 0..2pi over one cycle) so the exporter does not introduce an artificial branch reset. One closed-cycle animation may repeat the neutral pose as the final time step, but it must retain ordered samples and consistent link closure.

## 6. Springs, cables and other deforming geometry

Do not treat a variable-length spring or tendon as a fixed rigid mesh. Current native code has length-dependent **shape_requests** and per-pose route/spring state; preserve this contract and avoid editing the shared PartsLibrary to visualize a different frame.

Export procedural records for each spring/cable with stable instance_id and:

- Named owner bodies and component-local anchors/guide points.
- Ordered world-space anchors/tangent points and pulley/guide radii (CAD mm, converted once in renderer).
- Coil end-seat positions and orientations, centerline axis, current coil length, free length, visually chosen pitch/turn count, and physical travel validity.
- Cable segments and arcs with winding sense, slack/tension state when actually known, and route branch continuity.
- Shape generator type/version, geometric parameter hashes, and frame identifier.

Render coil/tendon geometry downstream from these values **or** bake validated per-frame local meshes for topology changes. A Blender curve/tube is a visualization approximation; do not infer cable force, spring stiffness, or physically determined knee posture from the render. Never stretch a helical spring to a visually convenient length beyond declared bounds, send a tendon through a rigid body, or smooth away a discrete slack-to-taut transition.

Every rigid piece of spring guides, pulleys, clamps, anchors and retainers remains its own transformed physical instance, even when the centerline/coil visual is procedural.

## 7. Exploded-view contract

Exploded geometry is **presentation-only** and must not change CAD pivots, BOM geometry, source mesh files, or kinematic model.

At a selected validated frozen assembly pose t0, assign to each instance/group:

- Sequence/stage and named subassembly.
- Extraction/translation axis in a declared local or world frame, distance, rotation if truly required, and optional staging pause.
- Fastener removal order and plausible service/access path; distinguish a cinematic reveal from a physically achievable disassembly.
- Persistent labels, part number and group color metadata.

For a world translation d_i and a smooth progress s(u)=3u²−2u³, one simple path is

$$
{}^W T_i^{\rm explode}(u)=\operatorname{Trans}(s(u)d_i)\,{}^W T_i(t_0),
\quad 0\le u\le1.
$$

Other paths are allowed when required by geometry. Do not mechanically rotate a bearing or shaft as though its fitting axis differed from the actual assembly. Review collisions along proposed physical extraction routes if calling the sequence an assembly instruction. Highlight removal of torso modules, linkage layers, sliders, servos, spring and cable assemblies, and real hardware; do not omit a structurally important component just for a cleaner shot.

## 8. Timeline generation and rendering

First implement data export and validation; **do not require Blender installation or final video rendering to progress the CAD**.

- Evaluate geometry from the kinematic equations for each output time. Avoid interpolation of independent linked-part transforms that violates closed-loop closure between keyframes.
- Separately perform mechanism/clearance validation at source-required angular increments and critical states under [06](06_verification_and_acceptance.md). Rendering at 60 fps at a high real-cycle frequency can skip tens of input degrees between displayed frames; it is not a substitute for dense mechanics validation.
- Permit time rescaling/slow motion for instructional content, but retain original physical time labels and actual motion-speed assumptions when shown.
- Ensure first/last positions match for a looping spine cycle; enforce quaternion continuity, contact/pose availability, and no absent parts.
- Prefer deterministic Blender Python scene generation (materials, lights, cameras, object hierarchy, markers, joint overlays). Fast previews may use EEVEE; final shots may use Cycles if budget permits.
- Generate frame sequences (PNG/EXR as appropriate), then encode MP4 with a documented tool and settings; keep frames resumable and separate from engineering source files.
- Optional future dynamics video consumes a separately validated MuJoCo trajectory with an explicit state/coordinate mapping; a Blender render never certifies ground reaction forces or dynamic stability.

Illustrative final-video targets, **not current acceptance gates**: exploded 20–30s/30fps; spine 10–15s/60fps; coordinated gait 15–20s/60fps; 1080p first, 4K later if useful.

## 9. Bounded implementation plan and acceptance

Implement the animation handoff in small reversible increments **while the reference-fidelity CAD work continues**:

| Gate | When | PASS evidence |
|---|---|---|
| AX0: Inventory contract | Now/at next safe checkpoint | A read-only audit of canonical App::Links, source parts, group/motion map, stable IDs, part number mapping, units, and statuses. Record missing or ambiguous mappings; no canonical mutation. |
| AX1: Posed-transform prototype | When current CAD pose adapter is usable | Neutral plus two non-neutral, nondegenerate poses exported for every supported rigid instance; frame ordering, rotations, linkage closure and source file SHA verified. All unhandled motion kinds fail closed. |
| AX2: One-part mesh + scene round trip | After AX1 | A distinct source mesh and two physical instances imported into Blender or an equivalent mesh/transform test, confirming local origin, +X/+Y/+Z, 0.001 scale, and no double placement. This is a **minimal smoke**, not a full video. |
| AX3: Full-pose handoff | After mechanical motion gates are adequate | 0..360 spine phase and named leg/wheel demonstration samples exported; regenerated spring/cable geometry is consistent and sign/branch conventions match the native source; no missing/duplicate physical instances. |
| AX4: Video release | Separate later task after CAD candidate readiness | Regenerable Blender scene(s), exploded and coordination videos, source/render metadata and inspected footage. Not required now. |

Suggested test thresholds for AX1–3 (distinct from manufacturing fits and from sampled CAD clearance): numerical transforms finite; rotation orthonormal error and |det R−1| ≤ 1e−8; source-to-imported joint center position discrepancy ≤ 0.02 mm and axis-angle error ≤ 1e−4 rad for an exact numeric round trip; sampled mesh-to-CAD surface error consistent with declared tessellation tolerance (initially choose at most 0.05 mm for small functional parts), measured on representative geometry. If a representation cannot meet a threshold, report the measurement and adjust the representation deliberately; do not silently mark PASS.

Each gate status is NOT_RUN, PASS, FAIL, or BLOCKED with paths, code/config/native hashes, sample count, observed errors, and explicit limits. **These are animation interface gates, not additional proof of manufacturability, dynamics or a new performance benchmark.** A later revision of the CAD invalidates only the exports whose geometry/poses changed; regenerate against the new manifest rather than duplicating old videos.

## 10. Minimal current-agent assignment

While continuing the existing active mechanical/fidelity work, the lead should:

1. Read this document and inspect the latest branch state, active MCP session, saved FreeCAD document and current MotionMap.
2. Preserve all existing geometry, native checkpoint hashes, manufacturing gates and documented source references.
3. Add or adapt a **read-only** animation-inventory and pose-export adapter using the existing r03/r07 APIs, behind an explicit versioned manifest schema. Start with AX0 and AX1; handle unavailable Blender as AX2 BLOCKED, not an excuse to redesign CAD.
4. Test neutral and two non-neutral poses against a disposable or read-only copy. Capture manifest, hash and residual evidence. Do not run a full expensive new clearance campaign solely for animation.
5. Ensure subsequent custom parts and edited r09+ frames preserve stable identities, local coordinate systems, motion descriptors, source/instance separation, anchor metadata, and renderer readiness.
6. Return to the agreed CAD and source-fidelity priorities. Defer polished video rendering and any MuJoCo work until the CAD package is sufficiently mature and separately authorized.

Only the **lead** may operate/write the canonical FreeCAD MCP session. Delegates may implement schema validators, Blender importer or independently review static manifests, with explicit file ownership. Do not let multiple agents modify the live document, shared MotionMap, or canonical parameter sources.

## 11. References and constraints

- [FreeCAD App::Link documentation](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_LinkMake.md) and [relative links](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_LinkMakeRelative.md): source object versus instance placement.
- [FreeCAD STL/OBJ export reference](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Export_to_STL_or_OBJ.md): mesh export, tessellation controls and dimensionless format risks.
- [FreeCAD STEP export](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Part_Export.md): engineering part export, distinct from animation meshes.
- [Blender glTF 2.0](https://docs.blender.org/manual/en/4.5/addons/import_export/scene_gltf2.html) and [Blender Python API](https://docs.blender.org/api/current/): rendering/import APIs; verify installed version before use.

Source-paper locomotion observations are not our robot's measured dynamics. Maintain reference/provenance classification, canonical CAD editability and manufacturing-first priorities throughout.
