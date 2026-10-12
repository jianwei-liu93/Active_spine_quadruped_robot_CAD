# r09 isolated native drawing companion

Status: SUPPLEMENTAL_NATIVE_CONSTRUCTION_REOPEN_VERIFIED; GUI_STYLES_EXPORTS_VISUAL_REVIEW_NOT_RUN.

Prepared `cad/staging/r09_drawings_prepared.FCStd` from frozen source staging `cad/staging/r09_monolithic_prepared.FCStd`, SHA-256 **`167c24f07ea0ecca2d393649fc94f20dd29e5033042a225cfdd9cc6134510102`**. Source staging hash is unchanged. Final canonical robot hash is **NOT_SUPPLIED**, pending lead r09 integration. No live MCP, canonical write, frozen module edit or geometry repair occurred.

Actual results: **64 native sheets / 296 native dimensions / zero dimension errors**. After save/reopen/recompute, maximum native dimension error is **2.4436858581111665e-07 mm**, below unchanged 1e-6 mm tolerance. All 296 dimensions retain their original native references and reject arbitrary overrides. Counts derive from actual r09 source geometry, rather than prior r08 totals.

The companion retains **92 PartDesign bodies / 473 physical App::Links / 295 fully constrained sketches**, with unchanged MotionMap/input phase. Its one lumbar physical instance is `LumbarIntegrated1`, linked to `FRM_LUMBAR_MONOLITHIC_CAGE_r09`, with **40 native PartDesign features / one valid solid**. Monolithic cage drawing sheet: **3**.

Identity, topology, shape validity and solid-count checks match before/after construction and after reopen. Construction maximum bbox/placement/raw-volume deltas: **0 mm / 0 / 0 mm³**. Reopen maximum bbox and placement deltas: **0 mm / 0**. Maximum raw reopen volume drift: **3.5527136788005009e-15 mm³**, relative **4.1224509315327469e-16**, limited to floating-point cable integration. Numerical no-change checks used 1e-9 mm bbox, 1e-12 placement-matrix entries and 1e-12 raw relative volume, tighter than existing reproduction limits. No adaptive-volume or manufacturing-accuracy claim is made by these drawing checks. Full before/construction/reopen snapshots, serialization differences, raw metric deltas and native dimension/reference records remain in `drawings/r09/native_staging_verification.json`.

Staging SHA-256: **`36536b3431129edf4a834b1eb5fdca6c27ba98f0b17a2da8b72acd7805ae5669`**. All GUI styles, PDF/SVG exports and visual review remain **NOT_RUN**. `export=False` applies the existing native-coordinate layout orchestration without GUI view providers. Native dimension PASS is supplemental evidence, not final package, visual or fabrication acceptance. Fits and manufacturing release remain provisional.

The CLI completed construction, save/reopen and all verification before a report-generation error accessed a closed object's Name. That reporting error was corrected using the complete persisted verification records and stored cage identity; no CAD rerun or native change was needed. The original exception/recovery is retained in the verification JSON. The optional runner now uses the stable stored identity.

Lead completion: open `/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/cad/staging/r09_drawings_prepared.FCStd` after r09 canonical integration, confirm canonical geometry matches the stated source staging, and call:

```python
import importlib, drawings_r07
importlib.reload(drawings_r07)
ROOT = '/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD'
drawings_r07.layout_existing_pages(doc, ROOT, revision='r09')
drawings_r07.export_existing_pages(doc, ROOT, sheets=[3], revision='r09')
# Render/inspect cage probe, then export and review the complete set:
drawings_r07.export_existing_pages(doc, ROOT, revision='r09')
```

Save the final companion separately after primary GUI/provider/reference verification and final PDF review. No GUI layout/export/visual PASS is claimed here; final canonical identity still needs lead evidence.
