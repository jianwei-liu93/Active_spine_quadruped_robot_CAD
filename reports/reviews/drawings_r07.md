# r07 native drawing module handoff

Owned changes: `src/drawings_r07.py` and this review. Isolated CLI probe sources/results are under `reports/tmp/drawings_r07/`; scratch generated drawings/templates/manifests went under `/tmp/drawing_module_r07/`. No live MCP access, canonical save, source geometry edits, or PDF creation occurred in this worker task. The lead owns PDF operation marking and final export/visual review.

## Lead invocation

```python
import sys, importlib
sys.path.insert(0, '/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/src')
import drawings_r07
importlib.reload(drawings_r07)
manifest = drawings_r07.run(App.ActiveDocument,
    '/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD')
```

Requires the already-open, final lead-owned r07 FreeCAD document and GUI for `TechDrawGui` SVG/PDF export. Dynamically enumerates unique App::Link-used native PartDesign::Body definitions; excludes explicit PURCHASED/ENVELOPE/SPRING/CABLE roles and `purchased` process descriptions. Includes custom/HARDWARE shafts, caps, plates, clamps and carriers. `only=[source.Name]`, `export=False`, and `strict=False` support bounded diagnostics. Each run replaces this module's prefixed drawings only; it never saves the canonical file.

Output: editable TechDraw pages, a module-generated modern-namespace editable A4 SVG template, one numbered SVG and PDF per page under `drawings/r07/`, and `drawing_manifest_r07.json`. The existing candidate template is read without modification. Template fields include part identity, sheet count, material/role, process/provisional notes, units/scale, critical fits UNKNOWN and native feature depth/length notes. Full native Pad/Pocket/sketch dimensional-constraint parameter records are in JSON.

## Actual checks

- Python compilation passed.
- Installed isolated FreeCAD 27.1.0 CLI synthetic fixture: 3 sheets / 12 native dimensions, no errors. Includes a bored plate, round shaft and arbitrary XYZ placement/rotation. Plate diameter 4 mm and true pivot/feature center pitch 20 mm verified. All raw values agree with geometry within 1e-6 mm.
- Separate read-only opening of saved r06 native document: 55 selected sheets / 260 native dimensions, `PASS_NATIVE_DIMENSIONS`, zero errors. Includes 165 overall XYZ extent dimensions; 37 require real curved-edge extrema represented by native cosmetic reference vertices.
- Proven modern SVG namespace is `https://www.freecad.org/wiki/index.php?title=Svg_Namespace`. Nested `<tspan>` text plus this namespace returns all editable fields; original historical namespace returned `{}`.
- Native `getVertexByIndex` is zero-based and its order differs from `getVisibleVertexes` list order. Module scans actual indexed vertices; never zips these lists.
- Native full-circle Diameter works. Native edge-to-edge Distance measures a gap, not center pitch; module locates real projected center vertex indices for actual pitch measurements.

## Authorized curved-outline reference extents

The lead explicitly authorized native cosmetic reference extrema derived from actual curves, with raw dimensions verified and regeneration notes. Native FreeCAD `TechDraw.makeDistanceDim` creates the dimension and cosmetic vertices. We calculate actual edge extrema using analytic circular parameters or native edge-parameter numerical refinement, require agreement with `optimalBoundingBox(False, False)` within 1e-6 mm, then project the exact real source points using the actual view scale. No arbitrary Override value is present.

Every such dimension has `Caption = REF overall extent`, an explicit `ReferenceNote = REF overall extent; regenerate drawing after model edits`, and JSON source name, 1-based source edge index, native curve parameter and world point for both extrema. These are DERIVED from the DESIGN_ASSUMPTION source geometry. They do **not** claim automatic propagation after source geometry edits; rerun the module after edits. Regular dimensions reference native projected or 3D geometry. All nominal design dimensions remain DESIGN_ASSUMPTION and all critical fits UNKNOWN.

## Lead acceptance still required

1. Execute on final r07 with real GUI exports enabled; confirm selected sheet count equals all used manufactured native definitions, including newly integrated r07 parts.
2. Confirm manifest status, dimension counts, all XYZ extents and native raw-value errors; source fixture is not final r07 evidence.
3. Render and inspect final PDFs, specifically longest part numbers/process notes, crowded circular feature dimensions, REF extent captions, and arbitrary orientation parts. This worker did not render or approve final visual layout. Three orthographic views and one isometric view have explicit fixed directions and standard scales fitted to all view cells.
4. Combine per-page PDFs into the final drawing book using the lead's marked PDF operation; inspect final page count, numbering and readability. Save/reopen the final FCStd through the lead's canonical workflow and verify editable template fields and dimensions persist.

No DXF/profile export is implemented here; the scope is editable drawing pages and per-page SVG/PDF. The manifest/parameter records support review, not fabrication release, load validation or supplier interface certification.

## Actual final r07 isolated companion execution

After an unexplained live GUI interruption, the lead authorized an isolated native companion drawing artifact. Cause of the GUI interruption is **not established**; the same bounded source/body construction passed in isolated CLI.

- Actual saved r07 minimal body `FRM_LUMBAR_ROUNDED_CRADLE_L_r07_final`: PASS, 1 sheet / 7 verified dimensions, no process crash (`reports/tmp/drawings_r07/r07_minimal_result.json`).
- Actual saved final r07 full dynamic build with exports disabled: PASS, 67 sheets / 311 native dimensions. Saved **only** `cad/flexor_r07_drawings.FCStd`, then closed/reopened/recomputed the companion in the isolated CLI process. All editable template fields persisted and all 311 native dimension raw values passed after reopen; maximum absolute error 2.4436858581111665e-07 mm.
- Canonical robot SHA256 before and after is identical: `862955f0052becb1642b2ef9f0f7dc906b396dd516826580b0705d57cdfc3625`. The canonical robot was not saved or replaced.
- Detailed source/sheet/dimension records and canonical/companion file hashes: `drawings/r07/drawing_manifest_r07.json`, status `PASS_NATIVE_SAVED_REOPENED`. Native runtime check results: `reports/tmp/drawings_r07/r07_companion_result.json`. Reproducible isolated driver: `reports/tmp/drawings_r07/build_r07_companion.py` (unconditional execution and explicit process exit).

The companion is a complete editable copy of the robot plus native TechDraw pages and source feature histories. The lead should open the companion rather than construct pages again in the live canonical robot. No PDF was authored in this worker run.

Lead GUI export without constructing or recomputing pages:

```python
import drawings_r07
# First bound the export to one existing sheet, inspect it, then export all.
result = drawings_r07.export_existing_pages(App.ActiveDocument, ROOT, sheets=[1])
result = drawings_r07.export_existing_pages(App.ActiveDocument, ROOT)
```

This helper reads the verified manifest, exports only existing named pages, and updates export paths in the same manifest. It does not save or recompute the CAD document. Final GUI/PDF rendering and visual review remain NOT_RUN until performed by the lead.

## Corrected-frame companion rebuild

The lead subsequently corrected the two lumbar rectangular frames with native C1/C2 travel-relief pockets. This worker rebuilt the entire drawing companion from corrected canonical SHA256 `8d0d363add856115761ac767c5b3948d62360c36a5b4d80d76a8de87b9162ca5`, using the existing isolated driver with exports disabled.

Save/reopen/recompute verification again passed: **67 sheets / 311 native dimensions**, maximum absolute raw-value error **2.4436858581111665e-07 mm**. Canonical SHA256 before/after remained the exact corrected hash above. The regenerated manifest and companion replace the earlier pre-relief drawing evidence; the previous pre-relief geometry hash in historical sections is superseded for final-package use.

The companion preserves every corrected canonical object name/type, 486 physical App::Links and 95 native PartDesign bodies. No profile module change, canonical save, GUI/MCP operation or PDF/SVG export occurred in this rebuild. The lead should now export existing companion pages and perform visual review.

## Visual QA failure and view-relative layout correction

The first lead-exported PDF rendered to `/tmp/r07_drawing_first.png` failed visual review: extent lines left the page and diameter leaders crowded the upper area. Numeric/reference checks alone had not established usable drawing layout. This is corrected in the module source with `layout_existing_pages`; no companion save or bulk PDF export has occurred in this worker correction.

Cause established from official FreeCAD source: dimension X/Y position the text in **scaled drawing millimetres relative to the parent view**, with +Y up. The creation code had supplied absolute page coordinates. With XY at (76,127), the old dimension position (76,95) put its label near page (152,222), outside A4. Free annotations use absolute page coordinates. Separately, CLI has no view providers, so native GUI font/arrow/line defaults persisted; the native arrow property is `Arrowsize`, not `ArrowSize`.

Primary sources:

- [Official QGIViewDimension updateView: local X/-Y label placement and native Fontsize use](https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/TechDraw/Gui/QGIViewDimension.cpp)
- [Official AppTechDrawPy: page text location adds parent view X/Y](https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/TechDraw/App/AppTechDrawPy.cpp)
- [Official ViewProviderDimension: Fontsize, Arrowsize and LineWidth properties](https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/TechDraw/Gui/ViewProviderDimension.cpp)
- Installed official `TechDrawTools/CommandAxoLengthDimension.py` lines 135-140 also assign a scaled local linear-point midpoint directly to dimension X/Y.

Lead bounded GUI probe:

```python
import importlib, drawings_r07
importlib.reload(drawings_r07)
result = drawings_r07.layout_existing_pages(App.ActiveDocument, ROOT, sheets=[1])
result = drawings_r07.export_existing_pages(App.ActiveDocument, ROOT, sheets=[1])
```

The helper preserves all native reference tuples, verifies raw values before/after within 1e-6 mm, rejects arbitrary overrides, applies GUI Font=DejaVu Sans / Fontsize=3 mm / Arrowsize=1.6 mm / dimension LineWidth=0.18 mm / view LineWidth=0.25 mm, and places extent lines near actual scaled bounding extents. Units remain mm in the global note; individual labels suppress redundant suffixes. Diameter labels retain native `Ø` formatting and split into ordered nearby slots around their actual view. Very short thickness dimensions put their text above the short line with flipped arrowheads. View labels move to cell corners, and feature parameters wrap at words rather than splitting a decimal value.

Isolated first-page math/reference probe (no GUI/style validation, no save/export) passed, all 7 references/raw values unchanged. Expected first-page positions:

| Dimension | Local X,Y relative to parent view mm | Absolute label center X,Y mm |
|---|---|---|
| X extent 12 | (0, -18) | (76,109) |
| Y extent 9 | (-21,0) | (55,127) |
| Z thickness 1.2, YZ parent | (-18,7.2) | (194,134.2) |
| Diameter 2.2 | (27,-8) | (103,119) |
| Diameter 2.05 | (27,8) | (103,135) |
| Diameter 1.9 | (27,0) | (103,127) |
| Pitch 5 | (-32,0) | (44,127) |

Evidence: `reports/tmp/drawings_r07/layout_first_probe.json`. The corrected manifest records local/page positions, applied GUI style properties and raw value errors. Layout changes mark PDF exports stale until the native pages are freshly exported. The exporter now preflights selected sheets for GUI-applied layout; `run()` also defers exports until layout is applied, avoiding the original layout regression on a future rebuild.

Acceptance remains **visual NOT_RUN** for the correction until the lead exports/renders sheet 1. Inspect that first PDF for all labels inside the border, no crossing diameter leaders, legible 3 mm text, short Z dimension arrowheads, and no decimal split in notes. Then probe representative large/round/crowded parts (for example sheets 8/10 washers, 34 ankle clamp, 52 capture collar, and the longest frame) before applying the accepted helper to all 67 sheets. Preserve the native raw/reference gate and perform final PDF review after saving the companion in the GUI. No bulk PDF export should proceed from the prior failed layout.

## Accepted first-page layout and final neutral-wire companion

The lead exported/rendered the corrected first sheet and marked visual PASS at `/tmp/r07_drawing_fixed.png`; this worker also inspected that PNG. All extent labels/extension lines are inside the page, 3 mm dimension text is readable, diameter leaders are separated, the short 1.2 mm thickness is readable, and feature notes retain whole decimal values. This is a one-sheet visual result, not all-page acceptance.

After the lead regenerated the eight neutral wire sources, this worker rebuilt only the companion from final canonical SHA256 **`cea39190bd1265a7a9be2eddcd061a4abc85e19076e15e1514aa318cdffbb227`**. The canonical hash before/after is identical. Final isolated companion SHA256 before lead GUI styling is **`ed02a4b14e8d9b6f529876ad1f45af891842af429bde25d7973dcade3fd651da`**. GUI styling/save will change the companion hash; update final-package hash evidence after that save.

Saved/reopened/recomputed verification passes **67 native pages / 311 native dimensions**, maximum absolute raw-value error **2.4436858581111665e-07 mm**. All **2,004** canonical object names/types remain present, including **486** physical App::Links and **95** native PartDesign bodies. The corrected view-relative coordinates and note wrapping are already persisted; the lead must still apply `layout_existing_pages` in the GUI to set font/arrow/line view-provider properties before exporting.

All 311 computed label centers lie inside x=8..289 mm and y=36..167 mm, avoiding the border, footer and top-note region. This center-only screen does not prove text-box clearance or leader separation. Evidence: `reports/tmp/drawings_r07/final_layout_screen.json`.

Proposed stress visual QA sheets, before broad acceptance:

| Sheet | Part | Scale | What to inspect |
|---|---|---:|---|
| 5 | FRM_LUMBAR_ROUNDED_CRADLE_L_r07_final | 0.5 | Large rounded outline, curved-extrema REF dimensions and new native C1/C2 reliefs |
| 8 | HORN_GAP_WASHER_OD8_T0p3 | 2 | Short 0.3 mm thickness with outward arrowheads; two envelope diameter REF labels and concentric/native hole labels |
| 34 | LEG_r07_ANKLE_CLAMP_R_OD6_ID2p05_T2p4 | 2 | Circular features in multiple orthographic views; small radial/axial interface geometry |
| 52 | SPINE_r04_CAPTURE_CAP_NEG | 2 | Highest total diameter-dimension count; fan-out of concentric feature leaders and left-hand REF labels |
| 54 | SPN_r02_L2 | 2 | Largest scaled overall span (72 mm on paper), near-cell margins and pivot pitch |
| 66 | TORSO_HIND_TRANSVERSE_FRAME_r06 | 0.25 | Arbitrary XYZ source orientation, long 114.26 mm projected height, small bore visibility and all orthographic/iso cells |

These six complement the accepted first crank sheet. The source algorithm places ordinary diameter labels beside their own view and orders them by real feature-center height; extent lines sit 9 mm from the scaled shape; pitch dimensions get a separate outer level; duplicate circular X/Y envelopes fan to opposite left quadrants. The geometric margins are adequate for the current native extents, but concentric leaders and the thinnest washer still require the proposed rendered checks. No PDF/SVG export or live MCP operation occurred in the final rebuild.
