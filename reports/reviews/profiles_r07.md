# r07 exact metal-profile exporter handoff

Owned source: `src/profiles_r07.py`. This task inspected the saved robot in isolated FreeCAD CLI, wrote only disposable probe outputs under `reports/tmp/profiles_r07/`, and performed no live MCP operation or native save. Final DXFs have not been exported; the lead must execute after the geometry correction.

## Lead invocation

```python
import sys, importlib
sys.path.insert(0, '/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/src')
import profiles_r07
importlib.reload(profiles_r07)
manifest = profiles_r07.run(App.ActiveDocument,
    '/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD')
```

The module creates exact per-manufacturing-part-ID DXFs and `profile_manifest_r07.json` under `exports/profiles/r07/`. `only=[source.Name]` and `output_dir=...` permit bounded disposable probes. It does not alter source geometry, recompute/save the source document, or alter source metadata. Each independent DXF readback uses a temporary document closed in `finally`; the prior active document is restored. Canonical source file SHA256 is checked unchanged.

Selection is dynamic over actual App::Link-used PartDesign::Body definitions with steel/aluminium material metadata. Purchased envelopes, actual SPRING/CABLE roles, collars/shafts/journals/spacers/clamps/fasteners and complex PA12 parts are excluded. A spring-steel split retaining clip can qualify as actual thin flat stock; it is not classified as an axial/helical spring.

A candidate must have a real planar closed cap face, thickness at most 0.35 of its smallest in-plane span, and an extrusion of that exact face matching the entire source solid. Both missing and excess volumes must be <= max(1e-9 mm3, source volume * 1e-8). This rejects blind bores, counterbores, shoulders and nonuniform thickness. The 0.35 ratio is an explicit conservative classification rule, not a material/manufacturing specification; changing it never changes the source geometry.

Actual native cap wires transform into their own orthonormal local plane; world plane origin/axes, cap face index and exact thickness are recorded. Separate outer/inner DXF layers preserve their topology. Only native analytic LINE/ARC/CIRCLE entities are supported. Unsupported splines/ellipses are excluded, with a reason; no polygon approximation or invented holes are written. DXF header declares INSUNITS=4 (millimetres), metric measurement and decimal display.

## Actual saved-r07 sample evidence

Isolated installed FreeCAD 27.1.0 CLI passed Python compilation and the actual saved-r07 sample. The independent compiled `Import.readDXF` reader verified exported entity/edge counts, closed wires/hole counts, all 6 geometric bound coordinates <=1e-6 mm, total contour length <=1e-6 mm, profile area, and zero missing/excess planar profile area after reconstructing imported wires with native FaceMakerBullseye. The symmetric-difference check also verifies hole positions and contour geometry.

| Actual definition | Thickness mm | Entities | Inner holes | Result |
|---|---:|---:|---:|---|
| HORN_GAP_WASHER_OD8_T0p3 | 0.3 | 4 circles | 3 | PASS |
| HORN_PATTERN_ASSUMED_OD8_T1p2 | 1.2 | 4 circles | 3 | PASS |
| RETAINING_CLIP_1p7x3p6_T0p6_PROVISIONAL | 0.6 | 2 lines + 2 arcs | 0 | PASS |
| DIRECT_CRANK_FLUSH_M2_L | nonuniform | not exported | not inferred | Correctly excluded: counterbores/steps prevent whole-solid constant-thickness extrusion |

All sample bound errors and contour length errors are exactly zero at reported precision. Maximum profile area difference is 2.842170943040401e-14 mm2. Missing/excess solid volumes and imported planar symmetric-difference areas are zero. No curved approximation occurred.

Probe source and detailed evidence:

- `reports/tmp/profiles_r07/profile_sample_probe.py`
- `reports/tmp/profiles_r07/sample_result.json`
- `reports/tmp/profiles_r07/sample/profile_manifest_r07.json`
- The three per-ID sample `.dxf` files in that same disposable sample directory.
- Read-only used-body metadata inventory: `reports/tmp/profiles_r07/definitions.json`.

The source canonical SHA256 for this evidence was unchanged: `862955f0052becb1642b2ef9f0f7dc906b396dd516826580b0705d57cdfc3625`. These checks precede the pending frame correction and are not a final-package pass.

## Lead acceptance after correction

Run against the corrected final robot, omit `only`, and verify all eligible definitions appear in the final manifest while nonuniform or excluded definitions retain explicit exclusion reasons. Keep part numbers separate even when geometrically similar. The module includes native process/material notes and DESIGN_ASSUMPTION/DERIVED provenance but does not choose kerf, heat treatment, stock grade, hole fits or tolerances. The retaining clip is an unverified candidate, and horn interfaces remain unverified. Outputs remain PROVISIONAL and are not fabrication release.
