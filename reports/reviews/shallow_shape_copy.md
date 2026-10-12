# Shallow shape-copy diagnostic

**Result: geometrically equivalent in the bounded test, with negligible performance benefit.** `shape.copy(False)` worked in the installed FreeCAD and preserved the originals during placement-only use. Median time to copy and pose all 431 links improved by approximately **1.85%**, from 0.32369 s to 0.31769 s, with overlapping run ranges. This cannot explain or materially resolve a many-minute full-robot sweep. No sweep code was changed and no further optimization search was pursued.

Requested inherited routing: Sol/high; actual routing is not observable. Work was confined to this report and ignored `reports/tmp` runner/evidence. No MCP, canonical edit, document recompute/save or full sweep was performed.

## Installed API and usage boundary

Actual `Part.Shape.copy.__doc__`, obtained inside the isolated installed FreeCAD process:

```text
copy(copyGeom: bool=True, copyMesh: bool=False, *, noElementMap: bool=False) -> TopoShape
copy(op: str, hasher: StringHasher, copyGeom: bool=True, copyMesh: bool=False, /) -> TopoShape
```

The installed documentation explicitly states that `copyGeom=False` copies topological objects while sharing geometry and triangulation with the original. Thus the positional `False` means the requested geometry-sharing mode; default `copy()` uses `copyGeom=True`.

This result supports using it for independently changing **Placement only** on temporary copies. It does not authorize editing shared curves, surfaces, mesh/triangulation or tolerances. Never replace a placed world shape's Placement directly by a source-local target: retain the existing `target * initial.inverse() * original.Placement` transform. If the installed API rejects the shallow signature, retain ordinary `copy()`; no fallback or integration was added to shared source in this task. The separate `noElementMap` option was not benchmarked.

## Native snapshot and method

- Saved file: `cad/flexor_r04_robot.FCStd`, 5,088,462 bytes; SHA256 `078474c027b64579968bddd01343761fa43beeaa1cec0295123887b4f49b7f3f`.
- Runtime: FreeCAD 27.1.0 dev, Git revision 49159 / `e5fabddebb0dc54ecf324cedddd26e053e2a8488`.
- Isolated command: `env QT_QPA_PLATFORM=offscreen /snap/bin/freecad.cmd reports/tmp/shallow_shape_copy_benchmark.py`.
- Detailed evidence: `reports/tmp/shallow_shape_copy_benchmark.json`.

The unconditional runner opened the saved document read-only, read every App::Link's actual world Shape and initial LinkPlacement, and called existing `robot_pose_r03.placements(doc, pi/2)`. It built both default and shallow copies, applied only the same 90° placement delta, and compared bounds, volumes, validity and solid counts. Three timing rounds alternated mode order. Qualification/geometry validation and Boolean timings were separate from the timed copy-and-place path. The runner closed without recomputing or saving.

| Mode | Median copying all 431 links | Median placement assignment | Median combined | Combined range |
|---|---:|---:|---:|---:|
| Default `copy()` | 0.32188 s | 0.00182 s | 0.32369 s | 0.32110–0.33203 s |
| `copy(False)` | 0.31600 s | 0.00169 s | 0.31769 s | 0.31741–0.32434 s |

These are a few wall-clock measurements in one process, not controlled statistical performance results. The median saving is about 0.006 s per whole-robot pose, or approximately 2.17 s over 361 poses if the same difference persisted. No full-sweep speedup is claimed.

## Geometry and original-state checks

All 431 default and shallow 90° copies were valid with exactly one solid. Maximum difference between the modes was **0 mm in every bound** and **0 mm³ in volume**. After copied placements and sample Booleans, both original shape-Placement and document LinkPlacement matrices were unchanged; original bounds and volumes were unchanged; all originals remained valid single solids.

| 90° sample pair | Default common mm³ | Shallow common mm³ | Difference |
|---|---:|---:|---:|
| LumbarIntegrated1 / Torso_hind | 0 | 0 | 0 |
| LumbarIntegrated1 / hind_ProximalMotor_1 | 0 | 0 | 0 |
| SyncB1 / SpineMotor1 | 0 | 0 | 0 |

The first two are historically colliding pair classes; they are clear at 90° in this newer snapshot after the hind case/cage shift. This does not establish clearance at other phases or for other pairs. All three tested Boolean results were zero, so this particular comparison does not supply a positive-volume intersection example.

**Recommendation:** retain the current copy path unless the lead prefers the explicitly geometry-sharing temporary-copy contract. Either choice is supported for these read-only rigid placements, but shallow copying is not a useful primary performance fix here. Keep subsequent geometry/source mutations separate from shared shallow copies and retain default-copy fallback on unsupported versions.
