# r09 affected-frame verification reuse plan

Prepared files: `src/verify_frame_revision_r09.py` and this plan. **No verifier CAD execution, freeze capture, partition launch, native save, or installed MCP action has been performed for this task.** Earlier staging construction evidence is separate.

## Strict reuse boundary

The original r08 campaign checks all physical pairs over its exact 985-state full manifest. The r09 assembly removes `LumbarIntegrated_1` and the 12 explicitly named FixedLumbarTie/FixedTieScrew links, changes only the retained `LumbarIntegrated1` source, and therefore has 473 physical instances: one changed frame plus 472 unchanged counterparts. Removing physical members creates no new pair among the remaining 472. Reuse is valid only after identity and frozen-motion input proof; the new frame still needs direct checks against all 472 at every required state.

`prove_identity()` opens the two native documents read-only in an isolated CLI process. It requires the exact 486→473 identity difference and verifies all 472 surviving non-frame IDs, exact neutral LinkPlacement/source placement, source name/part number, source numerical properties, source-local geometry, and actual placed geometry. Exact BREP SHA identity is the preferred fast path. For unstable BREP serialization, *all* fallback checks must pass: both Boolean difference volumes ≤1e-5 mm³; bbox error ≤1e-5 mm; strict adaptive per-solid volume comparison ≤1e-6 relative including the existing numerical margin. It calls the existing `adaptive_volume_r07.validate_solids` unchanged. Missing backend support, invalid topology, tolerance failure or unsupported inputs fails the identity gate.

MotionMap must match exactly after removing only the 13 retired IDs. Native mechanism parameters, phase, leg-angle record and wheel state must match. Prescribed configuration and assembly configuration must match in full except descriptive top-level revision/limits strings and the explicitly new `lumbar_frame_r09` subtree. Historical r08 frame configuration is preserved and compared. Source helper hashes are frozen through the original r08 freeze plus the new module/source and adaptive-volume helper hashes. Native file SHA and in-memory physical source/placement/pose fingerprints are checked before and after.

## Exact coverage

Pure enumeration confirmed the stored full manifest matches current authoritative `verify_motion_package_r08.manifest('full')` under canonical JSON hashing. All original 985 sample IDs, trajectory records and input SHA values are retained verbatim.

The original ledger includes 361 integer spine phases with changing leg angles and wheel position. It does **not** cover a full fixed-leg spine cycle. The affected-frame plan therefore adds 361 phases, θ=0..360° in 1° steps, with all four leg coordinates neutral and wheel=0. IDs are `frame_spine_000` through `frame_spine_360`. The θ=0 neutral duplicate is deliberately retained to avoid rewriting the original ledger. Total: **1346 states**, each with 472 frame/counterpart pair decisions. All states retain their exact numeric input trajectory and SHA. This finite plan is not a continuous-clearance proof.

Pure manifest SHA-256: `2676a286a1b5c839f980cd15a6039613c565a50ce115785c4de067711a839385`.

## Read-only pair checking

`run_partition(i, n)` uses the current `leg_motion_r07.descriptor` API with explicit r09 configuration. Every descriptor must cover the exact 473 IDs and retain a constant grounded frame placement. Only the new frame versus its 472 counterparts is checked; no duplicate all-pairs campaign is performed.

Rigid geometry uses copied actual native shapes under the descriptor placement, preserving the adapter's source/local/world convention. Strictly disjoint actual world AABBs are the only rigid broadphase exclusion. No bbox overlap tolerance hides a positive overlap.

Dynamic springs and cables are regenerated through the **unchanged** `leg_motion_r07.regenerate_sources` with a sparse request map only when conservative generator bounds cannot exclude the frame. Unknown generators or primitive types are not geometrically exempted: they require actual generation and fail closed if unsupported. No approximate solid enters Boolean testing.

- Compression bounds come from the frozen OD4/seat-interval generator and its explicit validation, expanded by its 1e-5 mm bound tolerance.
- Extension bounds analytically contain the OD4 helix, radius0.25 hooks/cylinders with 0.05 mm end extensions, and major1.25/minor0.25 end tori. A conservative radius3.1 mm/end-extension1.6 mm box contains these constituents and the qualified normalization bbox shift. The complete box is transformed through the actual descriptor placement, so lateral/Y exclusion respects the true spring plane.
- Cable line primitives use endpoint AABBs expanded by wire radius0.15 mm. Arc primitives use conservative full-circle bounds from the actual start-to-center radius, likewise expanded0.15 mm, which contain directed and multiturn arcs. Each primitive box is transformed to world coordinates. Potential overlap requires exact regeneration and actual-solid Boolean intersection.

Every narrowphase uses actual valid single solids. Raw common volume >1e-5 mm³ fails without exemptions. Exact repeated frame/pair signatures may reuse their previous actual Boolean volume. Each pose reports all 472 decisions, named rigid/dynamic exclusions, dynamic world boxes and their source basis, exact narrowphase volumes, guide warnings, input trajectory and input hash. Partial partitions never receive whole-r09 PASS.

## Explicit lead execution sequence

After primary integration and a final native freeze, the lead may explicitly run these functions in fresh isolated CLI processes:

1. `capture_freeze(native_path, exact_lead_sha256)` to freeze r09 native/config/helper/manifest inputs while validating the existing r08 freeze.
2. `prove_identity()` to produce `reports/verification/r09_frame_partitions/identity.json`.
3. `run_partition(i, n)` for the chosen bounded partition count, n≤24. It writes only its revision-isolated JSON report; no launch helper or automatic process creation is included.
4. `collect(n)` only after partitions finish and the existing r08 full campaign has its coherent final summary.

Collection grants a finite-sample reuse PASS only if all of the following are true: the r08 full summary is PASS with exactly 985 unique completed states, all original hash-coherence fields and matching frozen native/manifest fingerprints; the strict 472-instance identity proof matches the current freeze; all 1346 affected-frame states complete exactly once with correct per-state input hashes and 472 pair decisions; all partitions agree on hashes, contain no overlap/errors, and preserve native/document fingerprints. An incomplete or failed r08 campaign blocks r09 PASS even if every affected-frame partition passes.

Primary installed MCP neutral, S9/axis and AX checks remain lead-owned separate gates. Supplier dimensions, motor retention, loads, spring equilibrium and fabrication release remain unresolved engineering gates.

## Checks actually performed for this preparation

- `python -m py_compile src/verify_frame_revision_r09.py`: passed.
- Pure enumeration: 985 original +361 fixed-leg =1346 unique IDs; partition unions for n=1,6,24 covered every ID exactly once: passed.
- Confirmed pure enumeration did not import FreeCAD or create freeze/partition reports.
- Inspected frozen source generators, placement adapter, existing strict adaptive-volume verifier, original full manifest and current r08 full summary format. No original verifier/helper/config sources were edited.

Native equivalence, dynamic containment in the loaded assembly, collision outcomes and run-time document immutability are **NOT_RUN for this new verifier** until the lead authorizes execution.

## Authorized execution checkpoint

The lead subsequently authorized execution after primary MCP construction/save. The canonical r09 freeze is SHA-256 `765bb3b9a32365e1c005ff16a246ac284d2e0544d3648d4e4be3f436a58e1b57`. The lead-owned isolated identity runner completed and was adopted without duplicate identity execution or freeze changes.

Strict identity passed for all 472 unchanged instances, with native files and in-memory documents unchanged. Of these, 469 source and placed geometries matched exact BREP hashes. The only fallback instances were HindTendon_L_Cable, HindTendon_R_Cable and Torso_hind. Their source/placed bidirectional Boolean differences were exactly zero; the maximum adaptive comparison including numerical margin was 2.0375568844847514e-8 relative, below the unchanged 1e-6 threshold. Pose, MotionMap, source numerical properties and assembly configuration checks passed.

The affected-frame ledger was launched in 24 isolated CLI partitions with six concurrent processes. This checkpoint does not assert completed collision coverage. Final authority is the coherent partition/collector JSON under `reports/verification/r09_frame_partitions/`. The r08 full campaign must separately reach complete coherent PASS before collection can establish finite-sample reuse PASS.


## Campaign stopped by user steering

The lead relayed new user evidence concerning the central torso transverse support/boss interface and requested an immediate stop. The supplemental r09 launcher and its six isolated FreeCADCmd workers received SIGTERM and exited without forced termination. No frozen input, source module or native model was changed. Completed atomic JSON records were preserved as historical partial evidence; RUNNING partition status is intentionally not converted to PASS. `reports/tmp/r09_frame_revision/stop_record.json` records the exact stopped PIDs and reason. No collection or final r09 campaign claim was made. The strict r09 identity proof remains historical evidence for its frozen revision.
