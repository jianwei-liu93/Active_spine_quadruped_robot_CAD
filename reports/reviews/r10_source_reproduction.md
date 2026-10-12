# Supplemental r10 fresh source reproduction

Status: PASS for the bounded supplemental isolated CLI rebuild and strict placed-solid comparison. This evidence supplements the installed FreeCAD MCP, which remains the primary CAD/source-build authority. It is not a package, fabrication-release, collision-campaign or physical-performance acceptance.

## Actual execution

The unconditional driver at `reports/tmp/r10_source_reproduction/driver.py` ran through `/snap/bin/freecad.cmd` with `QT_QPA_PLATFORM=offscreen`, using `build_robot_r10.build(save=False, doc_name='FlexorR10SupplementalSourceRebuild')`. No canonical document save or live MCP operation was performed. The fresh document was fully touched and recomputed, with all sketches fully constrained, before source reproduction. The existing `verify_reproduction_r07.run(..., revision='r10', expected_instances=487)` regenerated actual neutral spring lengths and performed the strict adaptive 487-solid comparison against the opened canonical r10 document. No epsilon or comparison tolerance was relaxed.

Canonical SHA before and after: `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`.

Actual report: `reports/verification/r10_source_reproduction.json`. Driver SHA: `b0b43682182a194e33ca9a40985f7ce6e0edac0e60dabb1a653bd35162a64602`. Full successful run elapsed 511.256 seconds; initial fresh constructor and full recompute reached its state guard after 347.693 seconds. The reproduction helper's comparison stage including spring refresh took 107.017 seconds.

## Actual result

- All 487 physical instance IDs and part numbers matched the canonical candidate; all 487 one-to-one adaptive comparison rows passed.
- 95 source PartDesign Bodies; native-state guards covered 737 Body/member objects with zero Invalid/Error states in the fresh constructor, final rebuilt document, canonical read-only inspection and reopened checkpoint.
- Maximum per-solid relative volume error: `7.274839786281319e-10`.
- Maximum estimated margin upper relative difference: `3.299617672609171e-7`, below the unchanged `1e-6` strict limit.
- Maximum absolute bounding-box error: `1.2789769243681803e-13 mm`, below the unchanged `1e-5 mm` strict limit.

Only after source comparison and final rebuilt native-state validity passed, the driver saved `cad/checkpoints/r10_source_rebuild.FCStd` (7,389,883 bytes), SHA `c632d6076ac8d0918efbbedc4b46a3e58319924f88566898ac1305bbe9d95be6`. The checkpoint was then reopened, all objects touched and recomputed, and its native-state guard passed with 487 valid single-solid physical instances. The checkpoint is supplemental and does not replace `cad/flexor_r10_robot.FCStd`.

## Headless adaptation and diagnostic history

The first attempt failed on the inherited `refine_flexor.apply` GUI material override because headless `ViewObject` is None. Its actual traceback and log are retained at `reports/tmp/r10_source_reproduction/attempt1_failure.json` and `attempt1.log`; canonical SHA stayed unchanged.

The successful driver preserves every `cad_common.metadata` identity field and every `cad_common.instance` link/placement operation, omitting GUI-only color styling. It also asserts an exact match to the single `refine_flexor.py` material-styling line and guards that line in process when `ViewObject` is None. This is an in-memory GUI compatibility guard, not an edit to the source file or geometry constructor. The original `refine_flexor.py` SHA is recorded in the actual report. Other ViewObject styling already catches unavailable GUI state in existing source.

Inherited WireJoiner warnings appeared during source construction. They were not dismissed as acceptance evidence: the fresh full recompute, all-sketch constraint check, full native-state guards and strict 487-solid comparison subsequently passed. The final result describes exact finite native geometry reproduction; it does not claim byte equality, strength, manufacturability, motion clearance or fabrication readiness.

Changed artifacts are confined to the assigned driver/diagnostics/log directory, supplemental checkpoint, actual source reproduction JSON and this review. No frozen helper, source builder, shared schema or canonical file was edited.
