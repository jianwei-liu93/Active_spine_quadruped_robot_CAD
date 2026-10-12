# r10 changed-pair verification preparation

Owned files: `src/verify_changed_revision_r10.py` and this plan. Initial preparation used pure checks without importing FreeCAD. Subsequently authorized isolated read-only CLI freeze, CAD identity and conservative-bound prepass completed as recorded below. No partition launch, MCP operation, native mutation or save was performed. Frozen r08/r09 verification modules and motion/source helpers were not edited.

## Proof boundary and exact identity migration

The baseline contains486 physical IDs. r10 retires only the prior13 explicit r09 IDs: `LumbarIntegrated_1`, four `FixedLumbarTie` instances and eight exact `FixedTieScrew` instances. The remaining473 IDs persist. Seven may change source geometry: `LumbarIntegrated1`, `Torso_fore`, `Torso_hind`, `Link1_L4_1`, `Link1_L4__1`, `Link2_L4_1`, `Link2_L4__1`. Fourteen new IDs are `CentralE1`/`CentralE2` followed by `_Pin`, `_Bearing0`, `_Bearing1`, `_Washer0`, `_Washer1`, `_Retainer0`, `_Retainer1`. Expected result:487 physical instances,107 used sources, with all used definitions present in the library,466 unchanged r08→r10 instances and21 affected instances.

`prove_identity()` requires this exact migration. Every one of the466 unchanged instances must preserve its neutral LinkPlacement, source name/part number, source-local placement and numerical properties, source-local geometry **and actual placed geometry**. Exact BREP SHA is preferred. A changed serialization requires both directional Boolean differences ≤1e-5 mm³, bbox error ≤1e-5 mm, and the existing strict adaptive per-solid volume comparison ≤1e-6 relative including numerical margin. Missing adaptive support, invalid topology or any mismatch fails closed.

All473 surviving legacy neutral placements must be exact. Their MotionMap descriptors must match the baseline after removing only the13 retired names. Only the10 new moving pin/washer/retainer entries may be added, each following the existing fore/hind `torso_r04_rigid` E output; four new bearings remain grounded. Native mechanism/branch parameters, phase, leg angles and wheel state must match. Assembly/prescribed-motion configuration must match completely except top-level descriptive revision/limits strings and the explicitly added lumbar/central-attachment/plate/bar reconstruction subtrees. Historical r08 numeric configuration is compared. The seven changed sources must retain local frames, prescribed native Body identities/r10 part numbers, and fully constrained profiles.

The final freeze captures canonical native SHA, r08 freeze SHA, r08/r10 config SHAs, exact1346 manifest SHA, source/helper hashes, original baseline evidence hashes and cage-driver SHA. Native files and in-memory physical geometry/placement/pose fingerprints are guarded before and after every CAD function. No source gets a world Shape assignment.

## Exact changed-pair coverage

The pose plan is the unchanged985-state r08 full manifest plus361 integer spine phases with fixed neutral legs/wheel0. Every original sample ID/input hash is preserved. The latter cycle is needed because the985 plan's361 spine states also change legs and wheel. The neutral duplicate is deliberately retained. Total1346 unique IDs; manifest SHA `2676a286a1b5c839f980cd15a6039613c565a50ce115785c4de067711a839385`.

Each pose checks every unordered pair containing at least one affected instance:21×466 unaffected counterparts plus210 affected/affected pairs = **9996 pairs per pose**, or **13,454,616 pair decisions** over the complete plan. The exact sorted pair ledger SHA is `ab96165fa995217e7223b5378f7fde5837938dec407f041b0a47c3259c982e90` for the expected IDs. No unaffected/unaffected all-pairs campaign is duplicated.

Every pose reports its exact input, input SHA and compressed9996-bit decision ledger: whole-cycle Y rejection, pose bbox rejection, or actual Boolean. Categories must be disjoint and exhaustive. Collection independently checks the masks, exact whole-cycle subset, each narrowphase pair index/name, finite intersection volume and raw threshold. Missing, duplicate, mismatched or partial states cannot pass.

## Conservative acceleration

`prepare_whole_cycle_y()` is a read-only descriptor prepass over all1346 inputs. It computes conservative worldY interval unions for each physical member from actual native rigid AABBs under exact placement matrices. Sagittal rigid motion therefore retains a narrow transverse interval without assuming rounded or approximately equal rotations. Transformed-box interval arithmetic expands bounds1e-6 mm; this expands candidate coverage rather than loosening collision acceptance. These unions cover the declared finite inputs, **not continuous motion**.

Dynamic bounds use the unchanged r09 helper's generator-derived containment: actual compression OD4/seat interval; conservative extension helix/hook/torus envelope; per-primitive cable line/full-circle envelopes expanded by actual wire radius0.15. An unsupported/unprovable generator disables whole-cycle exclusion. No approximate dynamic solid enters a Boolean. The interval report includes every input SHA, native/document guards and the exact pair exclusions. Partitions validate that ledger against the freeze/identity/manifest before using it.

At each pose, native solid copies are materialized lazily only when conservative candidate boxes overlap. Actual dynamic source regeneration uses the exact unchanged `leg_motion_r07.regenerate_sources` API and exact request keys. Native rigid validity is checked once per loaded partition; proper rigid transforms preserve its single-solid validity. Generated local sources are validated by the frozen helper. Actual Boolean results are cached only under complete unrounded source/request hashes and exact placement matrices. There is no approximate pose cache or rounded state deduplication.

Collision broadphase uses the existing1e-6 mm bbox overlap threshold. Narrowphase uses actual solids and the unchanged raw common-volume threshold1e-5 mm³; larger volume fails with **no fit/contact exemptions**. Nonfinite/invalid Boolean results fail. Native geometry, helper/config SHA or proof-ledger changes invalidate a partition.

## Lead execution API after canonical freeze

No command should run until the lead supplies the final r10 native SHA. Use fresh isolated FreeCADCmd processes, never the live GUI. The preparation deliberately provides no automatic launch. The safe sequence is:

1. `capture_freeze('/absolute/path/to/cad/flexor_r10_robot.FCStd', '<LEAD_FINAL_SHA256>')`.
2. `prove_identity()`; require `status == 'PASS_IDENTITY_ONLY'`.
3. `prepare_whole_cycle_y()`; require `status == 'PASS_BOUNDS_ONLY'` and1346 completed inputs.
4. `run_partition(i, 24)` for i0..23, with **at most six concurrent CLI processes**.
5. `collect(24)` only after all partitions exit.

For a single explicitly authorized partition, save a temporary runner containing the following and invoke `/snap/bin/freecad.cmd /absolute/path/to/runner.py`:

```python
import os, sys, traceback
sys.path.insert(0, '/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/src')
from verify_changed_revision_r10 import run_partition
try:
    result = run_partition(0, 24)  # change only the explicitly assigned index
    print(result['status'], result['samples_completed'], flush=True)
except Exception:
    traceback.print_exc()
    sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
```

Outputs are revision-isolated under `reports/verification/r10_changed_partitions/`. `capture_freeze`, identity and prepass are explicit separate calls; a partition never recreates or updates a freeze.

Whole finite-sample reuse PASS requires coherent r08 full985, coarse105 and cage361 PASS plus all their unchanged native/document/source guards, strict466-instance identity, and complete coherent1346 changed-pair results. The collector reads every original baseline partition and verifies exact unique coverage, actual per-partition mutation guards and original full input hashes. It never rewrites/recollects baseline evidence. Primary installed MCP graph/S9/AX/neutral checks and supplier/retention/strength/fabrication gates remain separate.

## Checks actually performed during preparation

- Python compilation: passed.
- Pure manifest/identity-set enumeration:487 expected IDs,466 unchanged,21 affected,9996 unique pairs, including210 affected/affected pairs,1346 states: passed.
- Partition unions n1,6,24 retain every sample exactly once: passed.
- Exact mask tests accept complete coverage and reject missing/overlapping/out-of-range bits: passed.
- Synthetic rigid-Y transform bound test: passed without FreeCAD import.
- Read-only baseline gate inspected57 existing r08 evidence files and passed their current985/105/361 records/guards. A synthetic mismatched baseline geometry fingerprint was rejected. This is baseline evidence inspection, not new r10 CAD execution.

## Authorized read-only execution and bounded guard correction

The first sequential CLI run captured the supplied canonical native SHA, then stopped at `FAIL_IDENTITY` before any instance comparison or bounds prepass. Its library-count guard incorrectly required107 total definitions; the native document contains107 **used** source definitions and118 total library definitions. The11 unused historical/cache definitions are legitimate preserved entries. The lead authorized changing only this guard to require107 used sources and inclusion of every used source in the library, while reporting all unused names. No geometry tolerance or other identity criterion changed.

Initial evidence is preserved as `freeze_initial_guard_failure.json`, `identity_initial_guard_failure.json` and `prepare_initial_guard_failure.log`. The corrected verifier was compiled, then freeze was recaptured under its corrected hash against the **same** canonical SHA `b0c43007aac0242b5420084a41c5d350f20dfd56e9893e2244ecb7a53cafbf39`. The isolated sequential driver `reports/tmp/r10_changed_revision/prepare.py` exited0.

Actual corrected results:

- `identity.json`: **PASS_IDENTITY_ONLY**,466 unchanged instances with source and placed geometry checked;487 physical instances,21 affected,107 used sources,118 library definitions,11 explicitly named unused sources. Existing motion/parameters exact; native files and both loaded documents unchanged; zero errors.
- Geometry identity methods: source and placed checks each used464 exact BREP matches and2 strict Boolean/adaptive/bbox comparisons (`HindTendon_L_Cable`, `HindTendon_R_Cable`). All fallback bidirectional differences and bbox errors were0; maximum adaptive relative difference including estimated margin was 2.03755694894e-08, below1e-6.
- `whole_cycle_y.json`: **PASS_BOUNDS_ONLY**, all1346 exact sample IDs/inputs completed, bounds for487 physical instances. Of9996 affected pairs,8521 have conservative disjoint worldY unions across the entire finite ledger, leaving1475 candidate pairs per pose. Document and native unchanged; zero errors.
- Both outputs bind to corrected freeze SHA `b9684a0c8218d40ed0b4c06ab69efaef52fe1d10dc503a8c48650374b56e02b9` and the exact original manifest/pair hashes above.

The11 unused names are: `LEG_r02_JOURNAL_D1p9_L13p75`, `LEG_r02_foreL_COMPRESSION_WIRE_L24p73863375`, `LEG_r02_foreL_EXTENSION_WIRE_L17p5917383`, `LEG_r02_hindR_COMPRESSION_WIRE_L29p55480766`, `LEG_r02_hindR_EXTENSION_WIRE_L25p61137956`, `LEG_r05_ANKLE_SWIVEL_EYE_OD4_ID2p05_T1p2_RADIALp4`, `TENDON_r03_HindTendon_L_CABLE_u001`, `TENDON_r03_HindTendon_R_CABLE_u001`, `TENDON_r03_WHEEL_OD13_4p4772482_1p6145357`, `TENDON_r07_L_CABLE`, `TENDON_r07_R_CABLE`.

All changed-pair collision partitions and collection remain **NOT_RUN**, requiring separate lead authorization. These identity/bounds statuses do not assert changed-pair clearance, continuous clearance or an overall r10 PASS.


## Final repaired-bar native recapture

The lead subsequently repaired the native bar sketch and supplied final SHA `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`. The earlier successful freeze, identity and Y-bounds files were moved intact to `reports/verification/r10_changed_partitions/archive_pre_bar_recompute_repair/`; the earlier CLI log is `reports/tmp/r10_changed_revision/prepare_pre_bar_recompute_repair.log`. They describe the superseded native file. No partitions had run.

Before recapture, the verifier gained a read-only native State guard. On every identity, bounds or partition document open it inspects every PartDesign Body and recursively grouped member (including sketches and unused historical Bodies), rejecting any State containing `Invalid` or `Error` before processing. It does not recompute to mask persisted failures. Pure synthetic tests accepted healthy members and rejected `Invalid`, `Error` and error-detail strings; compilation passed. No other source/helper/schema/native file was edited.

The final sequential isolated CLI exited0:

- Final freeze SHA: `1310c7211f02e06d17773d9223bc8acdcdd7a0e1e738a462d4d009c53ad2db02`.
- Identity: **PASS_IDENTITY_ONLY**, all466 unchanged source/placed geometries;487 physical,21 affected,107 used source definitions,118 total library definitions with the same11 unused names recorded. Source and placed identity each used464 exact BREP matches plus2 strict cable comparisons.
- Native State guard: r08 has95 Bodies/735 Body-and-member objects; r10 has95 Bodies/737 objects. Both report0 Invalid/Error states. The bounds reopen independently passed the same r10 State check.
- Bounds: **PASS_BOUNDS_ONLY**,1346/1346 exact inputs;8521 whole-ledger Y-disjoint pairs and1475 remaining candidates per pose, with the unchanged9996-pair ledger.
- Identity and bounds both report native/document unchanged and zero errors. Final disk SHA was independently rechecked after completion and matched the supplied final SHA.

This final recapture supersedes the earlier successful preparation above. Changed-pair partitions and collection remain **NOT_RUN**, pending explicit lead authorization; no overall r10 collision PASS is asserted.
