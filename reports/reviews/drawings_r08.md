# r08 staging native drawings

Status: NATIVE_DIMENSIONS_AND_CONSTRAINTS_VERIFIED_AFTER_REOPEN; GUI_STYLES_EXPORTS_VISUAL_REVIEW_NOT_RUN.

An isolated installed FreeCADCmd process constructed native pages from frozen `cad/flexor_r08_robot.FCStd`, using `drawings_r07.run(doc, ROOT, export=False, strict=True, revision='r08')`. It saved only **`cad/staging/r08_drawings_prepared.FCStd`**. A subsequent separate read-only process opened/recomputed the frozen source and staging companion and checked the actual native dimensions, sketch constraints and source geometry snapshots. No live MCP operations, canonical save, source repair, module edits, PDF/SVG export or visual acceptance occurred in this task.

## Actual results

- **67 sheets / 312 native dimensions / zero dimension errors.** Counts derive from actual r08 source selection. After staging reopen/recompute, maximum raw dimension error is **2.4436858581111665e-07 mm**, below the unchanged 1e-6 mm dimension tolerance. All 312 dimensions reject arbitrary overrides.
- **95 PartDesign bodies / 486 App::Links / 320 fully constrained sketches** retained. Every body/link remains a valid single solid. Names/types and face/edge/vertex/solid counts match the frozen source.
- **Placement matrix and optimal bounding-box deltas are exactly zero** after reopen. The maximum volume delta is **5.329070518200751e-15 mm³**, limited to `HindTendon_R_Cable` (8.607787394634585 to 8.60778739463458 mm³) and `HindTendon_L_Cable` (8.61796474428766 to 8.617964744287654 mm³). Exact equality was therefore not claimed. Raw source/staging snapshots and all exact deltas are preserved under `staging_reopen_diagnostic` in the manifest for audit. The lead accepted the 5.329070518200751e-15 mm³ cable integration drift under the original strict metric tolerance; no metric tolerance was relaxed.
- During construction, 10 BREP serialization hashes changed with exactly zero missing/excess Boolean volumes and zero bbox deltas. After save/reopen, 14 BREP hashes differ from the source. BREP byte identity is recorded diagnostically, not used as geometric acceptance. No shape repair was applied.
- Frozen original SHA-256 remains **`3832778436b75539d0ecf0e95df935099005331157c1328c2f77389985a817c8`**. Staging SHA-256: **`9ff7496569d84c0fa69128565ea95a0c43203bed677e088e5281b071bf5ddee6`**.

Strict native construction status is `PASS_NATIVE_DIMENSIONS`; this is not final package acceptance. CLI has no GUI providers. GUI styling, all exports and PDF visual review remain NOT_RUN. OCC FaceFinder emitted generic warning text during projection but no native-dimension gate errors.

## Lead GUI completion

Open `/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/cad/staging/r08_drawings_prepared.FCStd` in the lead-owned GUI/MCP. Use:

```python
import importlib, drawings_r07
importlib.reload(drawings_r07)
ROOT = '/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD'
# Lumbar cages: sheets 5/6. Changed controller tray: sheet 44;
# controller edge retainers: sheets 39/40.
drawings_r07.layout_existing_pages(doc, ROOT, revision='r08')
drawings_r07.export_existing_pages(doc, ROOT, sheets=[5, 6, 39, 40, 44], revision='r08')
# Inspect representative PDFs, then export all pages:
drawings_r07.export_existing_pages(doc, ROOT, revision='r08')
```

The lead should render/inspect the actual final PDFs, confirm GUI styles and native values, and save the completed companion as `cad/flexor_r08_drawings.FCStd`. Preserve the canonical robot. Curved REF extents retain regeneration associations; critical fits/fabrication readiness remain unresolved.
