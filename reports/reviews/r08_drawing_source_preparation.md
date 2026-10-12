# r08 drawing, profile and image source preparation

Status: SOURCE_PREPARED; LIVE_CAD_AND_PDF_VISUAL_REVIEW_NOT_RUN.

Only the delegated modules below were edited. The worker did not connect to live FreeCAD, change geometry/schema/canonical files, create a companion document, or export CAD/PDF/image artifacts. Read authority: AGENTS.md and docs/08_agent_orchestration.md, with the project specification/reference/development introductions. Source comparison anchors remain Movie S1 51.5 s and 52.7 s; the lead must inspect the resulting real geometry and both views.

## Changes

- `src/drawings_r07.py`: optional `revision='r07'` on `run`, `layout_existing_pages` and `export_existing_pages`; revision-specific object prefixes, templates, directories and manifests. r08 uses `R08Drawing_`, `drawings/r08/templates/A4_r08_editable.svg` and `drawings/r08/drawing_manifest_r08.json`. Native geometry references, non-arbitrary measurements, 1e-6 mm checks, geometry-derived curve extrema and strict failure behavior are retained. Counts derive from the actual selected bodies and dimensions; neither 67 sheets nor 311 dimensions is assumed. Layout replaces a repeated linear dimension lookup with a local dictionary; recomputes needed for native measurements remain intact.
- `src/profiles_r07.py`: optional `revision='r07'` on `run`; r08 output is `exports/profiles/r08/profile_manifest_r08.json`. Exact native-face/DXF/readback checks and source-file hashing remain intact. Names and PartNumbers come from the actual document, so changed lumbar crosswall-cage PNs need no mapping.
- `src/render_robot_r07.py`: `render(doc, root=None, revision='r07')` preserves the existing one-argument call and produces revision-named images. Explicit `bare_lumbar_pos_y_oblique` and `bare_lumbar_neg_y_oblique` captures show both actual lumbar link faces, in addition to the compatibility `bare_lumbar` image. Projected bounding-box fitting adapts to the actual shape. The manifest records included links, normals and image hashes. Source fidelity remains an explicit visual review, not a consequence of camera choice. All object visibility and the original camera are restored even on failure.
- `src/motion_views_r07.py`: optional `revision='r07'`; r08 outputs under `reports/motion/r08`, with revision in the final manifest. Restores all visibility and original camera; excludes nonphysical clearance links from image visibility. Existing finite actual-pose capture and native-file hash checks remain. Invalid noninteger/zero/negative phase increments are rejected before pose mutation.

All revision arguments accept only `r` followed by digits, preventing accidental path traversal. The expected assembly identity (486 links / 95 bodies / 105 unique PNs) belongs to the lead's actual r08 verification and is not fabricated by these modules. Likewise, native sketch constraint status must be checked in the real companion; drawing code does not modify source sketches.

## Lead execution contract

Execute through the lead-owned FreeCAD GUI/MCP session after r08 source integration and verification. Modules must be reloaded if previously imported. Use the actual r08 document, not the r07 companion.

```python
from pathlib import Path
import importlib
import drawings_r07, profiles_r07, render_robot_r07, motion_views_r07
for module in (drawings_r07, profiles_r07, render_robot_r07, motion_views_r07):
    importlib.reload(module)
root = Path('/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD')

# On the verified r08 robot (without saving UI changes):
render_robot_r07.render(doc, root, revision='r08')
profiles_r07.run(doc, root, revision='r08')
motion_views_r07.render(doc, root, step_deg=15, revision='r08')

# On the lead's separate r08 drawing companion copied from the verified robot:
drawings_r07.run(drawing_doc, root, export=False, strict=True, revision='r08')
# export=False still applies layout; the GUI run can persist its view providers.
# Probe representative pages, including both changed lumbar sources and carrier:
drawings_r07.layout_existing_pages(drawing_doc, root, sheets=[1], revision='r08')
drawings_r07.export_existing_pages(drawing_doc, root, sheets=[1], revision='r08')
# Inspect probe PDFs, then finish all pages:
drawings_r07.layout_existing_pages(drawing_doc, root, revision='r08')
drawings_r07.export_existing_pages(drawing_doc, root, revision='r08')
# Lead saves only the companion as cad/flexor_r08_drawings.FCStd,
# reopens/recomputes it, and verifies native references and constrained sources.
```

For a completed full GUI run, `drawings_r07.run(drawing_doc, root, export=True, strict=True, revision='r08')` combines construction, layout and export. Sheet 1 is only a generic probe; locate the changed lumbar/carrier sheet numbers from the newly generated manifest rather than assuming their indices. Do not reuse r07 sheet counts, dimensions or rendered exports as r08 acceptance evidence. Render and visually inspect actual final PDFs before marking visual review complete.

## Checks actually performed

`python -m py_compile` passed for all four modules. A Python smoke check imported the modules without CAD execution, confirmed all six public revision arguments default to r07, checked r08 prefix extraction, and generated/checked a revision-specific editable template in a temporary directory. No runtime CAD/profile/drawing/capture gate is claimed by these source checks.
