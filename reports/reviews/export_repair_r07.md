# r07 spring STEP repair and exporter review

Executed 2026-10-12 in isolated `/snap/bin/freecad.cmd` FreeCAD 27.1.0devR49159, using copies from `cad/flexor_r06_robot.FCStd`. No live-session or canonical-document write was performed. Requested worker routing: Sol/medium; this worker inherited its runtime and did not independently verify model routing.

## Result

A combined native topology normalization and explicit STEP pcurves resolves the strict volume round-trip discrepancy in tested spring definitions. **This is a proposed native repair, not permission to compare a hidden repaired export with the unrepaired native source.** The lead must explicitly integrate normalization into the spring constructor, regenerate/save r07, and run the r07 exporter through the live MCP session. Full r07 export remains NOT_RUN by this worker. All STEP gates remain `volume_relative_error <= 1e-6`, six actual-extremum bounds `<= 1e-5 mm`, valid shape, and exact solid count.

The repaired fore compression native kernel volume changes from 29.89795182629611 to 29.83727746639808 mm³ (0.202938%). This change must remain disclosed; it is not measured wire loss. Supporting helical B-spline poles are exactly unchanged and knots equal; faces remain BSplineSurface + two Toroids. Bidirectional tessellation-vertex samples (502/501 at requested 0.03 mm deflection) give max source→fixed 4.10032e-15 mm and fixed→source 1.61249e-6 mm. This supports a trim/seam normalization inference but is **not a certified global distance bound**. Preserve physical parameters and spring construction; add kernel `fix` to the resulting BRep, rather than reconstructing a different helix or relaxing acceptance.

## Two materially different repair approaches

`attempts.py` records an export representation approach (`write.surfacecurve.mode` 0/1), and a source topology approach (`fix`, sew/re-solidify, conversion to NURBS). For the fore spring:

| Source variant | Mode | Relative round-trip volume error | Relative source volume change |
|---|---:|---:|---:|
| original | 0 | .001913876911 | 0 |
| original | 1 | .002078166135 | 0 |
| fix | 0 | .0001605398893 | .002029381820 |
| fix | 1 | 7.561755185e-12 | .002029381820 |
| sew/re-solidify | 0 | .001913876911 | 0 |
| sew/re-solidify | 1 | .002078166135 | 0 |
| NURBS conversion | 0 | .07596235917 | .00007766166208 |
| NURBS conversion | 1 | .07613019633 | .00007766166208 |

All these attempted roundtrips report valid one-solid shapes, showing validity alone is insufficient. NURBS conversion is rejected. Mode alone and cleanup alone fail; their tested combination succeeds.

## Tested API and integration recipe

Actual installed signatures:

- `Part.setStaticValue(string, string|int|float)`
- `TopoShape.fix(working_precision, minimum_precision, maximum_precision) -> bool`
- `TopoShape.sewShape(tolerance=1e-6) -> None`
- `TopoShape.toNurbs() -> TopoShape`
- `TopoShape.exportStep(filename) -> None`

Lead-owned native spring construction, after existing fuse/removeSplitter and before final validity checks:

```python
if not solid.fix(1e-7, 1e-9, 1e-6):
    raise RuntimeError('Spring BRep topology normalization failed')
```

Export settings tested with both `Part.export` and placement-preserving `Import.export`:

```python
App.ParamGet('User parameter:BaseApp/Preferences/Mod/Part/STEP').SetBool('WriteSurfaceCurveMode', True)
Part.setStaticValue('write.surfacecurve.mode', 1)
```

The isolated placed fore App::Link (`(50,30,20)` translation; 37° rotation about `(1,1,0)`) exported through `Import.export` then `Part.read` yields one valid solid and relative volume error 7.561636116e-12. See `fore_import.py` and `fore_import.json`.

The CLI probes set a preference in their isolated processes and use `os._exit(0)` after flushing diagnostic files to avoid saving a preference configuration or a native document.

## Exporter handoff

`src/export_robot_r07.py` adapts the existing r05 exporter. It:

- exports physical App::Links with `Import.export`, validates independently loaded STEP geometry, and checks a clean disposable document;
- exports every unique used native definition with `Part.export`, requiring strict native-versus-imported volume, bounds and solid count;
- emits PA12-only STL with existing meshing settings; independently reads each STL and checks watertightness, facet count, serialization volume/bounds, while reporting BRep-versus-mesh approximation volume difference separately;
- records SHA-256 files and BOM/mass outputs and writes the success manifest only after every check passes;
- detects sanitized filename collisions, requires explicit pcurves, and does not repair any source shape.

`python -m py_compile src/export_robot_r07.py` passed. Its actual whole-robot runtime and STL checks remain for lead execution; no package success is claimed here.

## Reproducers/evidence

All experiments are under `reports/tmp/export_repair_r07/`: `probe.py` for installed API documentation, `attempts.py`/`attempts.json` for the two approaches, `fore_import.py`/`fore_import.json` for source geometry and placed OCAF export, and `normalize.py`/`normalize.json` for every spring definition. These open r06 read-only and write only diagnostic artifacts. Runtime normalization results are summarized below after completion.

| Native definition | STEP volume relative error | STEP bounds max mm | Native→fix max sample mm | Fix→native max sample mm |
|---|---:|---:|---:|---:|
| LEG_r02_hindR_EXTENSION_WIRE_L25p61137956 | 7.4694311e-09 | 5.9952043e-14 | 7.1365841e-15 | 7.1365841e-15 |
| LEG_r02_hindR_COMPRESSION_WIRE_L29p55480766 | 2.2713806e-12 | 3.3706371e-13 | 7.2768323e-15 | 2.1714593e-06 |
| LEG_r02_hindL_EXTENSION_WIRE_L25p61137956 | 7.4694311e-09 | 5.9952043e-14 | 7.1365841e-15 | 7.1365841e-15 |
| LEG_r02_hindL_COMPRESSION_WIRE_L29p55480766 | 2.2713806e-12 | 3.3706371e-13 | 7.2768323e-15 | 2.1714593e-06 |
| LEG_r02_foreR_EXTENSION_WIRE_L17p5917383 | 8.6476263e-09 | 3.126388e-13 | 3.9738059e-15 | 3.7225598e-15 |
| LEG_r02_foreR_COMPRESSION_WIRE_L24p73863375 | 7.5617552e-12 | 2.3625546e-13 | 5.3731239e-15 | 7.425226e-15 |
| LEG_r02_foreL_EXTENSION_WIRE_L17p5917383 | 8.6476263e-09 | 3.126388e-13 | 3.9738059e-15 | 3.7225598e-15 |
| LEG_r02_foreL_COMPRESSION_WIRE_L24p73863375 | 7.5617552e-12 | 2.3625546e-13 | 5.3731239e-15 | 7.425226e-15 |

All eight source/fixed/imported shapes are valid one-solid BReps. All native→fixed bounding extrema differences are zero. Samples are finite coverage only.

Actual r07 STL-helper runtime probe (`exporter_probe.py`/`.json`): PA12 definition `SPN_r02_L2`, 628 facets, reloaded watertight, serialization relative volume difference 2.090178668e-7, bounds difference 0. Source BRep-to-reloaded-mesh volume difference 1.965345469e-5 is separately reported as tessellation approximation. This confirms the helper executes and distinguishes mesh serialization fidelity from BRep approximation; it does not certify every PA12 STL.
