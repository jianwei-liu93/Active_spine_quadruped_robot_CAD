# r08 delivery validator preparation

Prepared `src/package_delivery_r08.py` without executing `run()`. The lead must authorize final validation after all final manifests, PDFs and reviews exist. This worker did not modify CAD, MCP state, parameters, or other source modules during this bounded follow-up.

`run()` returns the absolute delivery manifest `Path`. It fails closed and removes a prior delivery success manifest before checking inputs. It writes `reports/delivery_manifest_r08.json` only after every gate passes. The frozen native SHA is `3832778436b75539d0ecf0e95df935099005331157c1328c2f77389985a817c8`. Expected final counts are 486 physical instances, 95 editable custom bodies and 105 BOM part numbers. Drawing sheet/dimension counts derive from actual sheet records and must agree with the drawing manifest; no historical 67/311 constants are used.

The gates require native reopen/recompute acceptance; all 985 full-motion and 361 cage-motion samples; frozen native/config/dependency coherence; accepted assembly and unique-part STEP/STL export records; exact profiles; source reproduction; source-fidelity image capture visual acceptance; native drawing companion hash; all individual SVG/PDF sheet outputs; complete manual and drawing book; and final independent review. Motion partitions must be PASS with actual PASS sample records and unchanged document/native flags. Cage summaries that do not repeat a top-level native SHA are bound to the same SHA through every coherent accepted partition. Full plan must equal the summary's plan. The exporter manifest binds every listed assembly, STEP, STL and BOM/mass artifact to its actual bytes.

Mass output is copied from final BOM/mass and engineering JSON, preserving known purchased mass, geometry estimates, unknown-mass records, actual/reference envelope and differences, and separate controller/harness sensitivity assumptions. Known mass totals must agree across reports. No mass target or nominal reference envelope substitutes for actual results.

## Review JSON contracts

`reports/reviews/r08_pdf_visual_review.json` requires:

```json
{
  "status": "PASS",
  "native_sha256": "3832778436b75539d0ecf0e95df935099005331157c1328c2f77389985a817c8",
  "documents": [
    {"path": "docs/flexor_r08_assembly_calibration.pdf", "sha256": "ACTUAL_PDF_SHA", "page_count": 1, "visual_review": "PASS"},
    {"path": "drawings/flexor_r08_drawing_book.pdf", "sha256": "ACTUAL_PDF_SHA", "page_count": 1, "visual_review": "PASS"}
  ]
}
```

The displayed counts are schema examples, not acceptance claims. Each count must match the actual final PDF. Drawing-book pages must equal the actual sheet count. PDF page inspection uses `pypdf`, falling back to installed `pdfinfo`; unavailable readers fail. The lead creates this evidence only after rendering and visually accepting every final page.

`reports/reviews/r08_final_review.json` requires status `PASS_CANDIDATE_WITH_RELEASE_BLOCKERS`, `independent_review: true`, the frozen `native_sha256`, and `reviewed_files: [{"path": "…", "sha256": "…"}]` covering each of:

- Final robot and drawing-companion FCStd files.
- Final manual and drawing-book PDFs.
- Export package manifest and drawing manifest.
- Full motion summary and 361 cage summary.
- Profile manifest and source reproduction report.
- Native checks, both BOM CSV files, mass JSON and engineering JSON.
- Source-fidelity image capture manifest and final PDF visual-review JSON.

The reviewer must review the complete existing critical package and record its actual hashes. The validator checks those hashes, not filesystem timestamps. Strict export manifest/readback checks cover individual part exports; independent review is not required to manually inspect every part file. Additional review fields are allowed.

The source-fidelity manifest must carry the frozen `native_sha256` alongside its final `visual_review: PASS`; its capture image hashes must match. Existing image manifests without a native SHA will fail closed until the lead completes that evidence.

## Inventory boundary and checks

The inventory includes only named accepted r08 generated deliverables, manifest-referenced part/profile/drawing/image outputs, accepted verification partitions, two named r08 preparation/repair reviews, and reproducible `src`, tests, macros, Markdown docs, parameters and project instructions. Historical dependency source module names remain valid reproducible inputs. It excludes generated r07 assets, partial capture progress, failed/partial diagnostics, checkpoints, temporary files, arbitrary directory leftovers and its own manifest hash. Fabrication release remains `BLOCKED`; physical validation and continuous clearance remain `NOT_RUN`.

Executed: Python compilation and `git diff --check` for the new module. Not executed: final validator, PDF readers, package inventory, final gate acceptance. No final package success is claimed by this preparation report.

## Completion of source-fidelity and animation inventory

The validator also requires `reports/reviews/r08_source_fidelity.json`, with revision r08, disposition beginning `PRINCIPAL_R07_FACE_OWNERSHIP_ERROR_CORRECTED;`, no remaining required morphology corrections, and matching `artifacts_sha256` entries for the frozen native, `src/spine_frame_r08.py`, `parameters/assembly_r08.json` and reviewed r08 images. Every listed artifact hash is checked. Existing within-repository source-evidence images are inventoried even when their folder names include r07, because they are reviewed source evidence rather than historical generated CAD assets. External clipboard/temp paths remain recorded provenance in the review JSON but are excluded from inventory. The source-fidelity JSON is a required final critical reviewed artifact.

The accepted motion capture manifest must identify exactly 24 frames numbered 0…23 at phases 0,15,…345 degrees, with matching individual hashes. Its `animation` entry must declare an actual CAD GIF capture with 24 frames and an actual matching file hash. Pillow independently checks the GIF format/frame count; the accepted `contact_sheet.png` must exist and decode as PNG. The manifest, GIF and contact sheet are inventoried; the motion capture manifest is also required in final critical review hashes. Missing Pillow fails closed. `macros/Rebuild_r08.FCMacro` is now explicitly required, so an empty macro glob cannot hide its absence.

Re-executed only Python compilation and whitespace checks after these additions. The final validator remains NOT_RUN.

## Drawing compatibility audit completion

The lead completes drawing provenance after final GUI companion save/reopen: `canonical_robot_sha256`, `native_companion_sha256`, and each sheet's `export_sha256: {"svg": "ACTUAL_SHA", "pdf": "ACTUAL_SHA"}`. The validator now requires those exact individual export hashes as well as the accepted book/companion/manifest review. A changed individual SVG/PDF cannot be silently accepted into a new inventory. The original `drawings/templates/A4_candidate.svg` and generated `drawings/r08/templates/A4_r08_editable.svg` are explicitly inventoried as necessary portable drawing/reproduction inputs.

Re-executed Python compilation and whitespace checks only. No final gate or manual generation was executed during the static audit.

The validator statically inspects `Document.xml` inside the final drawing FCStd archive. Each sheet's `Template` file property must resolve to the existing repository r08 editable template; the number of file properties must match the actual sheet count. External or obsolete template paths therefore fail closed. The final companion did not yet exist at the audit snapshot, so its actual referenced paths remain NOT_RUN until the lead saves it and performs the planned GUI reopen check.
