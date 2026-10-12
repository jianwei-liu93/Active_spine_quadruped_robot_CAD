# r07 motion verification — superseded / incomplete

**Full result: SUPERSEDED / INCOMPLETE; no full PASS.** Lead/user steering stopped the current run because new51.5/52.7s source frames establish an orthogonal channel/cradle center frame. The r07coplanar center frame requiresr08 correction. Frozenr07 remains a checkpoint.

Qualified coarse: **PASS105/105**. Full partial: **477/985 published poses, all477 PASS, 0 failed records**. All24neutral baselines passed zero overlap. Remaining poses are **NOT_RUN**. This is finite evidence for the frozenr07 geometry and does not qualifyr08. Native SHA256`cea39190bd1265a7a9be2eddcd061a4abc85e19076e15e1514aa318cdffbb227`.

All coarse/full records, manifests, logs, launchers, exact termination PIDs and scoped partial summary are preserved in `reports/diagnostics/r07_before_channel_cradle/`. No model save or shared-source edit occurred during termination.

---

Historical verification details follow; earlier RUNNING statements are superseded by the stopped status above.

# r07 actual native motion package verification

This is a read-only verification task. Only `src/verify_motion_package_r07.py`, this review and isolated runtime reports/wrappers are owned here. No live FreeCAD MCP, canonical model/schema edits, GUI or native saves are used. Command processes open `cad/flexor_r07_robot.FCStd` and inspect copied native shapes through `leg_motion_r07`.

## Exact coverage

- Coarse screen:105 states, six command-process partitions. Individual leg excursions±10° at5° steps, wheel at5° steps, coordinated/asymmetric paths (wheel increments22.5° in this coarse screen), combined spine/gait every15°. **Screening only.**
- Full requested finite coverage:985 states, six partitions:260 neutral/individual-coordinate/wheel states;364 coordinated/asymmetric states;361 combined full spine/gait states. All adjacent coordinates within each declared trajectory change by≤1° (floating residual4e-14°).
- The combined trajectory spans spine0..360° at1°, qh=neutral+5°sin(theta), qk=neutral+5°sin(theta+offset), offset0 fore/π hind, wheel=45°+45°sin(theta). Maximum wheel change is below0.786° per sample. Both endpoints are retained.
- Existing `sample_states(1,10)` coordinated paths advance the wheel4.5° per pose. Those paths are subdivided with2/9° leg increments, preserving the prescribed path and keeping wheel increments1°. This is why full coverage exceeds the earlier344-state list.

Every fixture records its inputs, deterministic ID and input hash. Full positive-terminal pure descriptors validate against `assembly_r07.json` before runtime. A full Cartesian product of all robot coordinates and continuous-time swept clearance are not claimed.

## Verification gates

Each partition requires486 native App::Link instances, valid single-solid source copies, a zero-overlap neutral baseline and zero raw intersection volume above1e-5mm³ at every checked pose. There are no fit/contact overlap exemptions. Only exact unchanged world-source/placement/bounds pairs reuse checks. Every error, collision and uncompleted sample is retained; a partial partition cannot pass.

Selected finite minimum distances are measured for lumbar/torso frames against actual B cross-shafts, controller carrier/board and cables, plus controller against B shafts/cables. AABB distance lower bounds prune only poses which cannot improve an already observed minimum. These are sampled distances for named pairs, not global minimum-clearance certificates; deliberate contacts outside this selected set are not described as minimum moving clearances.

Evidence contains native file SHA256, source BRep/placement/MotionMap geometry SHA256, parameter SHA256, dependency hashes, exact expected/completed records and before/after immutability checks. Drawing-only changes may alter the native file hash; any final reassociation must compare the exact geometry fingerprint and retain the original execution hash.

## Current gate status

- Pure configuration/985-state fixture validation: **PASS**.
- Initial coarse native screen: **FAIL**, preserved as `failed_v1_coarse_*.json`; all six processes finished. Corrected-native rerun is RUNNING in12 partitions.
- Full native motion verification: **RUNNING**,24 partitions after corrected coarse PASS.
- Continuous clearance, loaded passive equilibrium, manufacturer interfaces and fabrication release: **NOT_RUN / NOT_CERTIFIED**.

Reports: `reports/verification/r07_motion_partitions/`; logs/wrappers: `reports/tmp/motion_package_r07/`. Final statuses and concrete findings will be appended when runtime results are available.

## Initial coarse evidence (preserved)

The initial six partitions completed 93/105 records before per-partition failure stops. Every neutral all-pair baseline passed with zero overlap; native file and geometry fingerprints remained unchanged. One partition passed all 18 assigned poses; four stopped on actual C1/frame material intersection and one stopped on a compression source OCC exception. Missing poses remain unverified. The exact native execution SHA256 is `862955f0052becb1642b2ef9f0f7dc906b396dd516826580b0705d57cdfc3625`; geometry SHA256 is `f35aefb3251da1027cbf299a4b1193d29fb8f64cf02ce2d26669fce627a70ba6`. These identify the failed version, prior to the lead's new travel relief save.

The worst screened C1 collision occurred at spine60°: 5.5800492518mm³ against each lumbar frame. The all-25-phase diagnostic union in world coordinates is X[-22.204507859,-20.453403559], Z[7.802677034,10.459335769], Y[-28.4,-25.4] right and [25.4,28.4] left. In the unrotated case profile the overlap union is X[-14,-13.142012803], Y[17.092659140,20.160304412]. At worst phase, CaseWindowBase contributes2.9760262676mm³ and CaseEdgeCollar2.6040229842mm³. The new rectangular perimeter and edge collar cause this collision; existing guide shelves do not. Diagnostic records are `c1_frame_diagnostic.json`.

At combined285°, the fore compression spring has installed length17.043604814814746mm. In `_spring_source`, seam23° fusion returns three solids and `removeSplitter()` raises `OCCError('Bnd_Box is void')`. Isolated identical-geometry seam11° succeeds with one valid solid, volume29.757850792567808mm³. This is source construction, not intersection testing or distance computation. Full traceback and seam tests are retained under `reports/tmp/motion_package_r07/285_diagnostic.log` and `spring_285_seams.log`. A per-seam OCC exception must move to the next candidate; the failed candidate must never be accepted. No verifier gate has been weakened.

Initial coarse wall times were478–695seconds per partition, with six simultaneous command processes. A corrected coarse run is expected to take12–15minutes and full985-state coverage roughly90–120minutes; these are estimates, not deadlines. Full native verification remains **NOT_RUN** until corrected coarse success and lead confirmation.

## Corrected run

The lead saved the full-stack C1/C2 travel relief native model with SHA256`8d0d363add856115761ac767c5b3948d62360c36a5b4d80d76a8de87b9162ca5`. This run uses12 isolated coarse partitions, followed automatically by24 full partitions only after complete coarse PASS. Hardware reports32 logical CPUs and71GB available memory. Coverage and every Boolean/valid-solid gate are unchanged; partition count only distributes identical fixtures.

The implemented source fix now catches a failed OCC operation inside each approved seam retry. Every compression candidate also satisfies analytic constituent volume bounds: helix volume=πr_wire²√[(2πR·12)²+(L−0.5)²], closed end torus volume=2π²Rr_wire² each. The complete union contains the helix and cannot exceed the sum of helix plus two tori; the existing recorded0.3% neutral kernel integration budget covers numerical volume integration. Optimal bounds must agree with X/Y±2mm and Z[0,L] within1e-5mm. Exact285° length and five reference lengths all pass (`spring_source_fix_check.json`). This rejects the demonstrated truncated valid-solid seam result. No source geometry or gate was weakened.

## Qualified spring run (current)

The earlier source retry runs are historical diagnostics; they do not qualify the final source. They are preserved under `reports/diagnostics/r07_pre_qualified_springs_motion/`. The lead integrated the escalated `compression_spring_r07.py` source and exact-length immutable BRep cache, after1001/1001 requested installed lengths passed validity, complete envelope, constituent volume and sampled wire-interior containment checks. See `reports/reviews/spring_kernel_escalation_r07.md`. The motion verifier dependency ledger now includes that generator and neutral normalization source.

Current pinned native SHA256: `cea39190bd1265a7a9be2eddcd061a4abc85e19076e15e1514aa318cdffbb227`. Twelve coarse workers are running; the existing workflow (`qualified_workflow.log`) will collect105 states and launch24 full workers over985 states only on complete PASS. No duplicate workflow has been launched. Final native and source geometry hashes, exact completed coverage, baseline outcome and sampled selected distances will be recorded below when available.

## Qualified coarse result

**PASS105/105** exact coarse records;12/12 partitions PASS, zero missing or duplicate sample IDs, zero baseline overlaps and zero failed records. Every partition reports document geometry and native file unchanged. Native/config/geometry/manifest hashes agree across all12 workers. Both earlier source failures (combined30°/150° and285°) pass actual native shape regeneration and intersection checks. Full985-state verification has automatically launched in24 isolated workers.

Coarse geometry SHA256: `f4ce79ce06ec3accc8b3b84b5ec20615d3430ff7331884b0c63215f6fe46e075`.

Coarse configuration SHA256: `6537f008ea524bfa006ab3fe56e146a33e65d58f91881e4dee0e82a4eb8df82e`.

Coarse manifest SHA256: `3944c27aba68495e0b9be7000d259ce103f5f638b25b38efc3d448bfea68a429`.

Coarse worker elapsed range: 341.3–509.0seconds. These results screen the specified poses; the full one-degree coverage is still pending.
