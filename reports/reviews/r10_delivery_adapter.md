# r10 delivery and manual adapter preparation

Status: PREPARATION ONLY. No PDF was generated and no actual package acceptance or inventory publication was run. No CAD application was opened, mutated, recomputed, saved or exported by this task. Existing helpers and final artifacts were not edited.

Assigned new files: `src/manual_pdf_r10.py`, `src/package_delivery_r10.py`, and this review. The adapters derive from the latest r09 modules and retain their strict final-evidence requirements. The final lead must supply the frozen canonical SHA explicitly to either entry point. The lead supplied current post-bar-repair SHA is `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`; it is context, not a hardcoded substitute for final artifact hashes.

## Current revision contract

- 487 physical App::Links, 107 used source definitions, 95 PartDesign Bodies. Native XML is read without FreeCAD; the one-piece source remains `FRM_LUMBAR_MONOLITHIC_CAGE_r09`, with r10 PartNumber and 52 Pad/Pocket features (40 inherited plus 12 additions).
- Seven changed existing instances and fourteen new central hardware instances; strict identity for the other 466 instances. Exact affected-pair enumeration yields 9996 unique unordered pairs.
- The motion gate requires the frozen r08 full985, coarse105 and cage361 evidence, current strict466 identity, conservative whole-cycle bounds, and all9996 affected pairs at all1346 exact inputs (985 baseline plus361 spine samples).
- Seven motors, six commanded coordinates and four **prescribed** knees; eight springs and two cables regenerated at every AX pose. AX2–4 and Blender stay NOT_RUN. No loaded equilibrium, continuous clearance, physical validation or fabrication release is inferred.

`collect_motion_readonly(partitions)` reproduces the current verifier's collect ledger logic and calls its read-only freeze/bounds/baseline helpers, without calling `collect`, replacing helpers, writing `summary.json`, launching partitions, or importing FreeCAD. It rejects malformed pair masks and additionally rejects negative narrowphase intersection volumes. `validate_inherited_motion` compares the reconstructed result exactly with the persisted summary, checks per-instance source and placed-geometry identity proofs, exact affected pair IDs, native-state guards and all frozen dependencies. Missing reports fail closed; no historical r09 count/default can satisfy this contract.

## Required final evidence and remaining blockers

The final package still requires strict one-to-one STEP reimport and per-source STEP checks, serialized PA12 STL checks, physical BOM/instance and mass reconciliation, engineering screen, neutral/actuator/edit-restore/native-geometry reports, source-build reproduction, current AX payload and source hashes, profile DXF readback, complete native TechDraw exports, source-fidelity and manufacturability reviews, 24 actual native CAD preview frames with matched flex/extend frame markers, both complete PDFs and their visual reviews, and the final independent artifact-hash review. Fabrication release must remain BLOCKED with explicit release blockers.

Native-state evidence now matches the current `r10_native_checks.json` contract: `canonical_reopened_recomputed=true`, `invalid_native_features=[]`, `fully_constrained_sketches=true`, matching canonical SHA, 95 editable Bodies and a complete unique487 valid single-solid physical ledger. Source reproduction remains mandatory; absence of its factory/build evidence cannot be bypassed.

TechDraw counts are calculated from actual sheet/dimension ledgers. The lead reported a provisional CLI stage of67 sheets/311 dimensions, with more diameter callouts being added. Neither tentative count is hardcoded as the final value. Companion templates, SVG/PDF hashes, final drawing-book page count and visual review remain mandatory. Profile coverage retains the r09 exact three flat-metal profiles gate pending the final r10 profile report; an intentionally different selection needs explicit review rather than automatic count relaxation.

The manual gate additionally checks final native-state, strict assembly/per-source STEP geometry, complete source reproduction, canonical image hashes, mass/engineering coherence, changed-pair motion and AX evidence before any PDF or cropped image is written. Manual prose and dedicated profile images cover integral fixed E beam/lugs, separate moving torso clevises and revised plates, four relieved long B-C instances and fourteen central hardware instances. Movie S1 observations versus metric DESIGN_ASSUMPTION are preserved per `docs/21_reference_fidelity_r10.md`; schematic red rods are not physical components.

The current campaign/final deliverables are incomplete. This preparation does not establish actual motion acceptance, current drawing visual acceptance, source reproduction, STEP validation, PDF layout quality or candidate delivery completion. Pre-repair diagnostic outputs remain ineligible as final evidence because every accepted gate binds to the final SHA. The lead must generate and inspect final PDFs before running the delivery validator.

## Entry points after actual evidence exists

Manual: `python src/manual_pdf_r10.py --native-sha256 <final-sha>`.

Read-only package acceptance: `python src/package_delivery_r10.py --native-sha256 <final-sha> --read-only`, or `run(write_inventory=False, expected_native_sha256=<final-sha>)`.

Final inventory publication: same CLI without `--read-only`, or `run(expected_native_sha256=<final-sha>)`. This retains r09's final-mode removal of a stale inventory before validation; read-only mode neither writes nor deletes an inventory. No such final call ran in this task.

## Checks actually performed

- Compiled both new module sources in memory and imported both successfully without FreeCAD. A before/after file-hash scan across the repository found no import file side effects.
- Negative checks: missing final evidence; missing explicit SHA; stale native SHA; invalid native feature states; absent canonical reopen/recompute; invalid partition count; missing, overlapping and out-of-range9996-bit pair masks. Every tested invalid case was rejected.
- A missing-artifact read-only package test used a temporary root and preserved an existing inventory sentinel unchanged. The manual's missing-evidence gate failed before output generation.
- Static saved `Document.xml` inspection confirmed the487 App::Link/95 Body contract and exact9996 affected-pair enumeration; this is schema preparation evidence, not a CAD recompute or geometry acceptance.
- AST inspection confirmed the read-only aggregation contains no report-publish, CAD-open, save or recompute calls.

No tests or final artifacts were added outside the three assigned files; the bounded negative-check harness ran from `/tmp`.
