# r10 auxiliary TechDraw layout adapter

Status: PREPARATION ONLY. `src/drawing_layout_r10.py` is ready for the lead to execute in the GUI on the frozen staged companion. No actual drawing layout, CAD save, artifact export, geometry operation or MCP action was performed by this task. Only the adapter and this review were added.

The inspected current manifest has 77 sheets and 321 native dimensions. Sheets 1–67 retain the established four-view drawing layout. Sheets 68–77 each contain one actual native projected circular-arc Diameter and lack the XY/XZ/YZ/ISO label convention required by the generic helper.

The wrapper preflights all selected objects before presentation changes, delegates sheets 1–67 to `drawings_r07.layout_existing_pages(..., require_gui=True, revision='r10')`, and lays out sheets 68–77 using `drawings_r07._apply_gui_style` for their native view and dimension. No new dimension, cosmetic point, source geometry or override is constructed. Auxiliary dimension labels move to relative drawing coordinates `X=hx+15`, `Y=hy+8` (scaled millimetres relative to the parent view, +Y up), rather than the initial off-page relative 240/155 positions. Source-Z-normal direction, source-X-right convention, scale and actual source/projected arc diameter and center are checked before using the staged projected extents. All ten planned label centers fall within the usable landscape A4 page bounds.

The ten preserved interfaces are: fore/hind clevis bores; E1/E2 lug through-bores and bearing seats; pin OD and groove root; retainer ID and OD. The adapter checks each original 1-based source arc and projected native edge index, References2D, References3D, actual getRawValue and Arbitrary=false. After recompute it rechecks all selected native reference lists and raw values to the unchanged strict 1e-6 mm tolerance. It fails on missing GUI providers, stale source/stage hashes, missing or wrong native objects, duplicate dimension identity, unexpected interface order, source/projected arc mismatch or an off-page planned label.

Accepted manifest layout records use the existing exporter contract exactly: `layout.status=PASS_NATIVE_REFS_VALUES_UNCHANGED`, nonempty `placements`, and `placements[].style.gui_provider=true`. They also record actual local/page coordinates and native values. Updated sheets mark exports stale. Visual review remains NOT_RUN and the adapter neither saves the document nor exports PDFs/SVGs.

## Lead entry point

With the staged companion open in the installed FreeCAD GUI:

```python
import drawing_layout_r10
result = drawing_layout_r10.run(doc, root)
```

A bounded probe can use `sheets=[68]`; the default selects all 77. The default frozen native SHA is `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`, and staged SHA is `26fb62d0727f73fccb6e814e50f32dd1f4a3669e2958bb8c54c9f137d9c93164`. Static file hashing confirmed both exact bytes during preparation. The open document must identify `cad/staging/r10_drawings_prepared.FCStd`; the wrapper does not silently operate on another document. Explicit expected-SHA arguments allow a separately reviewed future freeze, but the current 77-sheet/ten-interface contract remains strict.

The lead must inspect the result, save a final companion separately, export through the established GUI exporter, and render/review all final PDFs. Code readiness and mock coordinate plans do not establish readable leaders, absence of PDF overlap, or final native drawing acceptance.

## Checks performed

- In-memory compile and import passed without FreeCAD imports or changes to the actual manifest, canonical native or staged companion.
- Static manifest/interface/hashes inspection passed for the current 77 sheets and ten auxiliary keys.
- Mocked native objects using each actual staged interface record produced ten on-page relative-coordinate plans.
- Negative mock guards rejected Arbitrary overrides, wrong raw diameter, altered reference, wrong source radius, changed projection or scale, and post-layout native reference mutation.
- A mocked one-sheet GUI run in a temporary directory produced the exact exporter gate schema, retained native references/Arbitrary, marked exports stale, and left both fixture native files unchanged. This was a code test, not actual FreeCAD layout or visual validation.

No frozen campaign dependency, shared drawing helper, interface constructor, geometry source, schema or existing artifact was edited.
