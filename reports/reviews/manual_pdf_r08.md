# r08 assembly/calibration PDF preparation

**Status: generator prepared; final PDF intentionally not generated.** The r08 candidate is still moving through final native, export, motion and drawing checks. The current neutral report is `PASS` for the prescribed pose, but the complete final manifest set is not present yet. Do not reuse `docs/flexor_r07_assembly_calibration.pdf` for r08.

## Owned changes

- `docs/17_assembly_calibration_r08.md` records the two half-cage center frame, source evidence, assembly order, motor map, torque-off calibration checklist, nominal interfaces and release boundary. It documents the 0.2 mm nonstructural seam held by the four existing ties, the orthogonal windowed crosswalls, solid upper horn cheeks, open top, Ø2.6 mm tie passages, carrier access pockets and 0.8 mm retainer wall.
- `docs/18_engineering_screen_r08.md` replaces r07 mass and screening figures with the current r08 report values, labels those values provisional pending the final SHA freeze, and distinguishes the current neutral PASS from pending full-motion/export/drawing gates.
- `src/manual_pdf_r08.py` is an r08-specific generator. It reads counts and exact part quantities from the r08 BOM/mass outputs, mass and demand values from `r08_engineering_screen.json`, the native SHA from the package manifest, r08 views and revision-specific verification manifests. It requires a matching package SHA, neutral PASS, full-motion PASS, drawing export and visual-review completion, profile PASS, source-fidelity capture PASS, and matching r08 BOM/counts before writing a PDF. It writes only `docs/flexor_r08_assembly_calibration.pdf` and presentation crops under `reports/views/manual_r08/`.

## Current evidence and regeneration gate

At handoff, `r08_neutral.json` reports PASS for 486 instances, 95 editable bodies, fully constrained sketches and 1,207 narrowphase checks. Current r08 mass reports 273.0556 g known mass, one unknown-mass instance, 105 unique part numbers, and a 164.3376 × 119.6000 × 104.0254 mm envelope. The engineering calculation reports a separate 291.0556 g sensitivity case using the explicit 10 g controller and 8 g harness assumptions. These are provisional file values; the final native freeze and package manifest must agree before publication.

The final package manifest, full motion summary, drawing manifest and r08 profile manifest are not yet available. The pose manifest files with 105 coarse and 985 full states are only input coverage definitions; they are not motion-check results. The capture manifest has not completed its visual source review. Therefore the manual generator's publication gate is not satisfied and the PDF remains ungenerated.

After the lead freezes and verifies the final r08 native file, finish the r08 native/export/full-motion/drawing/profile/capture checks and make sure all manifests identify the same native SHA. Then run from the repository root:

```bash
python3 src/manual_pdf_r08.py
```

The generator checks revision identity, source hashes, BOM/mass counts, and declared statuses before producing the PDF. Review the generated PDF pages and BOM totals, then update this record with the final page count, checks, visual-review result and PDF SHA256. Do not mark this preparation note as final delivery before that review.
