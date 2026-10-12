# r09 delivery validator preparation

Prepared `src/package_delivery_r09.py` as a fail-closed static candidate-package validator. **No final delivery acceptance or inventory was written.** The lead reports a further source-fidelity geometry correction pending (likely r10); this r09 preparation must not be represented as final approval of that future geometry. Only the two assigned files were edited; no MCP, CAD saves, canonical changes or delegation occurred.

## Current actual configuration

The saved native file was inspected as a ZIP/XML artifact, without opening FreeCAD. At this snapshot its SHA-256 is `765bb3b9a32365e1c005ff16a246ac284d2e0544d3648d4e4be3f436a58e1b57`; it contains473 physical App::Links,92 PartDesign bodies and the one retained `LumbarIntegrated1` source `FRM_LUMBAR_MONOLITHIC_CAGE_r09` with40 native features (34 Pads/6 Pockets). AX0/AX1's actual inventory supplies104 used source definitions. The prepared drawing manifest has64 sheets/296 dimensions, with final GUI export/visual review still pending at the earlier staging snapshot. These are observed values, not invented completed package counts.

`run()` computes the canonical SHA afresh from `cad/flexor_r09_robot.FCStd`; it does not hardcode this snapshot SHA. It checks report hashes against that current file and verifies the file remains unchanged at completion. Body counts derive from native XML; used definitions/PNs/quantities derive from actual native source mappings, export records and BOM CSV rows and must reconcile. Expected473 physical instances, the one-piece40-feature frame and explicitly retired hardware are revision-specific design gates. A future revision must adapt those gates and its conditional-proof contract explicitly; this module does not extrapolate r09 evidence to changed geometry.

## Conditional motion acceptance

The validator implements the actual contract in `src/verify_frame_revision_r09.py`. It does **not** require a fresh r09 full985 all-pair rerun. It requires all three independent conditions:

1. Inherited r08 full985 campaign PASS, complete unique sample IDs, actual accepted partition records, stored authoritative manifest, unchanged native/document fingerprints, and exact native/config/source/freeze hashes.
2. Current r09 strict472-instance non-frame identity proof, exact retirement/merge mapping, unchanged placements and numerical pose/configuration, native/source identity, and exact BRep or strict bidirectional Boolean/adaptive-volume/bounds proof for both source and placed geometry.
3. All1346 affected-frame poses (original985 plus361 fixed-leg integer spine phases), exact source/input/freeze/identity hashes, one frame-to-each-of472 pair ledger per pose, no missing/duplicate/failing records, actual-solid intersection gates, complete summary/partition union, unchanged canonical and in-memory geometry.

The old native, r08 freeze, manifest, summary and accepted partitions are explicitly inventoried as **inherited dependencies**, with their own old SHA. They are never labelled current r09 geometry. Current frame summary/proof bindings must pin those exact inherited files. At the initial inspection r08 summary was INCOMPLETE,912/985; the validator correctly rejects such evidence. Finite sampling never becomes continuous-clearance, loaded-equilibrium or fabrication acceptance.

## Remaining package gates

Missing or stale evidence fails closed: native reopen/recompute; all473 source-reproduced placed solids; assembly and unique STEP/PA12 STL exports and strict local geometry ledgers; final native drawing companion, every SVG/PDF output and portable editable templates;3 exact profiles; reconciled BOM/mass and engineering data; current source-fidelity views/review; native motion preview; AX0/AX1; final manual/drawing-book PDFs; manufacturability candidate review; and final independent package review. Each artifact's hash is checked against its producer/review record and pinned for the duration of validation. No aggregate volume cancellation can authorize a failed individual solid. Current source/PN mappings must agree with native XML and BOM.

Drawing counts derive from real sheet/dimension records and must agree with the manifest; no historical counts are silently reused. PDF readers independently check actual final page counts, and drawing-book pages must equal actual sheets. Both final PDFs require visual review evidence with exact hashes. Final independent review requires `PASS_CANDIDATE_WITH_RELEASE_BLOCKERS`, `independent_review:true`, current native SHA and reviewed hashes covering every critical final artifact, current build/frame source/parameter/macro, animation schema/adapter/validator/grounding/payload/report, current frame proof/summary and the inherited r08 baseline summary. Fabrication remains BLOCKED; physical validation and continuous clearance remain NOT_RUN.

## Native preview and AX0/AX1 are separate

`reports/motion/r09/capture_manifest.json` requires24 actual hashed PNG frames at phases0,15,…345°, current native SHA, `PASS_CAPTURED_RESTORED`, `native_file_unchanged:true`, `pose_restored:true`, `visibility_restored:true`, and `pose_provenance:"PRESCRIBED_KINEMATIC"`. A complete frame sequence suffices; a GIF is optional, but if listed it must decode as24 real CAD-capture frames. The explicit matched-view record is:

```json
{"matched_flex_extend":{"flex_frame":0,"extend_frame":12,"same_camera":true,"fixed_leg_wheel_state":true}}
```

Indices above are schema examples; the lead selects actual inspected flexion/extension frames. The existing preview producer restores pose/visibility in its finally block but does not emit the new explicit restoration/matched-view fields; lead must record actual checks rather than insert unverified flags. Native preview is visual evidence only and never motion/clearance proof.

`reports/animation/ax01_r09.json` and `animation/motion/ax01_r09.json` must bind the current source SHA and actual473-instance inventory. The versioned schema and standard-library semantic validator run on the payload; the grounding supplement, original native MotionMap, every source/PN mapping, component metadata, complete source hashes and three actual pose residual ledgers are checked. The delivery metadata records SHA-256 of the schema, adapter-produced report/payload, grounding supplement and canonicalized component metadata. The actual r09 ground file uses `cad_revision:r09` plus explicit lead-audit `provenance`; the prior `REVIEWED_EXPLICIT_GROUND` form is also accepted when hash/current-native/ground coverage checks pass. AX2–AX4 and Blender stay NOT_RUN. No meshes or video claims are inferred from AX0/AX1.

## Review evidence contracts

`reports/reviews/r09_pdf_visual_review.json`: status PASS, current native SHA, and `documents` entries for `docs/flexor_r09_assembly_calibration.pdf` and `drawings/flexor_r09_drawing_book.pdf`, each with actual path/SHA/page_count/visual_review PASS. All pages must have been visually inspected before the lead records acceptance.

`reports/reviews/r09_manufacturability.json`: revision r09, status `PASS_CANDIDATE_WITH_RELEASE_BLOCKERS`, current native SHA, `fabrication_release:"BLOCKED"`, nonempty `release_blockers`, and `reviewed_files:[{path,sha256}]` covering at least native, package export manifest, drawing manifest and exact-profile manifest. This is a bounded candidate/manufacturing-risk review, not fabrication release.

`reports/reviews/r09_final_review.json`: current native SHA, status `PASS_CANDIDATE_WITH_RELEASE_BLOCKERS`, `independent_review:true`, and exact reviewed hashes for the module's explicit complete critical package list. It must follow actual artifact creation; no placeholder review passes.

## Executed static checks

- Python compilation with `compile(...)`: PASS; no pycache/output artifact written.
- Read-only `run(write_inventory=False)`: correctly rejects missing `reports/verification/r09_native_checks.json`; no inventory created or deleted.
- Five targeted negative checks: outside-project path, stale current native SHA, missing one-to-one ledger, local volume above1e-6 and incomplete inherited912/985 baseline all rejected.
- Actual current AX0/AX1 static gate: PASS on473 instances/104 source definitions/3 poses. Payload hash `0b952834913ce4dbfc152ba1409dd37e783f8dcc4975c8e9f831f2e2ddcc2d64`; report hash `f09a1537f142d885990a3dfa833abdb4330322e8d210f22fc646c5896985b367`. Schema/grounding/metadata hashes were independently calculated by the gate. This is JSON/native-XML validation of existing evidence, not new CAD execution.

The default `run()` is reserved for the lead after all final artifacts/reviews exist; it removes a stale success inventory before checks and writes `reports/delivery_manifest_r09.json` only after every gate passes. `run(write_inventory=False)` performs identical validation but writes/deletes nothing. A future changed canonical SHA automatically invalidates stale r09 evidence. Final validator/package execution remains NOT_RUN.
