# Assembly and calibration PDF - r07 review

**Status update — 2026-10-12:** The existing PDF and its visual review describe an earlier r07 snapshot and are stale for package delivery. The 985-state native motion run was stopped before completion after review found the reproduced S1 window and sagittal horn/opening cheek coplanar in r07, where the source requires a corner relationship. The r07 candidate is superseded pending geometry correction. Its recorded final assembly STEP export/round-trip attempt failed, and the 67-sheet drawing PDF export/review is incomplete. Do not present the current PDF as a complete candidate package; regenerate and re-review only against the corrected frozen candidate and successful current manifests.

**Result:** regenerated the ten-page A4 review manual at `docs/flexor_r07_assembly_calibration.pdf` from the current assembly/calibration record, primary-MCP engineering-screen JSON, BOM and saved FreeCAD view captures. The PDF is explicitly watermarked as a review candidate, preserves the no-hardware-operation hold, and distinguishes the scoped frame-pair sample from full whole-robot motion qualification.

## Contents and traceability

- Architecture/source-fidelity overview with four cropped actual FreeCAD captures; these are CAD views, not photographs of a physical build.
- Nine-step assembly order, nominal interface stackups, proposed seven-motor ID map representing six commanded coordinates, and torque-off record-only calibration checklist.
- Known mass, center of mass, full point-mass inertia tensors, separate controller/harness sensitivity mass, alpha 1/3/6 demand table, assumptions, and explicit missing allowables. Numeric mass/CoM/inertia/load values are read directly from `reports/verification/r07_engineering_screen.json`; point-mass inertia still omits each solid's own centroidal inertia.
- Supplier interface limitations, source evidence references, verification boundary, and open fabrication blockers.
- Appendix generated directly from `bom/bom_r07.csv`: all 105 exact part numbers with aggregate quantities, totaling 486 instances.

## Validation and visual review

- Generator: `python3 src/manual_pdf_r07.py`; the script reads the BOM, r07 mass/envelope report and engineering-screen JSON and writes the PDF and image crops under `reports/views/manual_r07/`.
- `pdfinfo`: 10 pages, A4 portrait, 604,833 bytes.
- `pdftotext` verification: all 105 BOM PNs present, quantities match the CSV, and the refreshed mass/CoM and scoped-clearance status are present.
- Rendered all ten pages at 100 dpi using system Poppler to `reports/views/manual_r07/page-01.png` through `page-10.png`; the contact sheet is `reports/views/manual_r07/contact_sheet.png`.
- Inspected the contact sheet and full-size pages 6-7, including the refreshed mass/inertia/load tables and verification boundary. Headers, page numbers, visual captions, release blockers and BOM appendix are legible; no clipping or overlap observed. The BOM appendix spans pages 8-10 with repeated column headings.
- The bundled Poppler binary could not run on this host because it requires GLIBC 2.38; system `/usr/bin/pdfinfo`, `/usr/bin/pdftoppm` and `/usr/bin/pdftotext` ran successfully.

PDF SHA-256: `2539e5abd795930b64a0d08db5830582902b92a5e4b0d21a29724b4fa10be129`.

## Remaining limits

The document summarizes the existing candidate and its assumptions; it does not close the listed motor/horn, OpenRB population, fits, spring/cable, allowable, whole-robot collision/access, loaded-equilibrium, drawing/export or fabrication-release gaps. A primary-MCP check sampled the C1/C2 moving frame pair against two frame pieces at 361 states and reported PASS at a 0.35 mm minimum gap. Full whole-robot motion remains unqualified and no whole-assembly G3 pass is claimed. The available 472-link frame/clamp report remains identified as a partial integration, not validation of the current 486-link assembly.
