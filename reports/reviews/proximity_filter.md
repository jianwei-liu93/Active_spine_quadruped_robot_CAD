# Proximity prefilter — correctness and bounded native benchmark

**Disposition: implemented conservatively, but do not enable it globally as a speed optimization.** The tested distance/containment filter produced no false-zero result, including contained solids, a through-bore and sealed cavities. On the six representative robot pair/pose checks it would take approximately **4.13×** the Boolean-only time. The distance operation itself is more expensive than `common` for these parts.

New source: `src/proximity_filter.py`. No sweep integration, MCP operation, canonical native edit, document save or full-cycle run was performed. Requested inherited role: Sol/high; actual model routing is not observable.

## API and safe topology boundary

```python
from proximity_filter import prepare, separation

# Once per original world shape; retain only while its topology is unchanged.
qualified = {name: prepare(shape) for name, shape in original_shapes.items()}

# After the caller rigidly places copies of those same shapes:
evidence = separation(posed[a], posed[b],
                      a_check=qualified[a], b_check=qualified[b],
                      tolerance=1e-6)
if evidence['skip_boolean']:
    volume = 0.0
else:
    volume = posed[a].common(posed[b]).Volume
```

Only `decision == 'ZERO_INTERSECTION'` / `skip_boolean == True` authorizes discarding the pair. All other decisions require the original Boolean check. Qualification and kernel failures return `BOOLEAN_REQUIRED` with a reason/evidence rather than raising per pair. This does not convert a Boolean failure into a pass: the caller still handles a subsequent failed Boolean as incomplete/error evidence.

The accepted topology is one valid, closed, positive-volume Solid with **exactly one valid closed boundary Shell** and at least one boundary vertex. A single-child Compound wrapper may be unwrapped recursively, retaining cumulative world placement. Multi-child compounds—including one Solid plus an extra edge—are rejected; no loose geometry is discarded. This matters because 126 of the 431 native links expose their one Solid through a Compound wrapper. All 431 links qualify after this guarded unwrapping.

The proposed “one connected solid” prerequisite alone is insufficient for the first-vertex argument: one connected volume can have disconnected inner cavity shells. For example, solid A can occupy the region between nested outer/inner boundaries while B occupies another overlapping nested region; arbitrary first vertices can lie on unrepresentative shell components. The helper deliberately falls back for any multi-shell solid, rather than trying to prove whole-solid containment from one vertex.

For eligible connected boundaries, a kernel distance greater than the positive tolerance establishes boundary separation. Strict `isInside(vertex, tolerance, False)` tests on each **current world** boundary vertex then reject containment. Only separation plus both outside classifications permits zero intersection. Distance ≤ tolerance retains Boolean checking for contact, intersection, containment or uncertainty. FreeCAD's solid distance returned zero for the tested fully contained box, so that case already took the conservative path before the point tests. A cylinder in an open through-bore had positive distance and both vertices outside, correctly permitting zero intersection.

Frozen `Qualification` objects certify topology only. They must belong to the same original topology as each rigidly posed copy. Reusing one after cutting, fusing, source replacement, spring regeneration or another topology change violates the API contract and requires requalification. Shape contents and placements are never changed by this module. It imports neither FreeCAD nor FreeCADGui.

## Native execution and provenance

Two bounded benchmark runs were made: the first exposed the single-child Compound representation and conservatively rejected those shapes; the second qualified those wrappers without discarding children and exercised the actual filter. A subsequent guard-only run checked cumulative placements and error fallbacks, without repeating the six native Boolean pair checks.

Invocation used the authorized isolated process:

```text
env QT_QPA_PLATFORM=offscreen /snap/bin/freecad.cmd reports/tmp/proximity_filter_benchmark.py
```

The runner imports and calls unconditionally, rather than relying on a `__main__` guard in FreeCADCmd's execution context. It opens the saved native file, obtains copied world shapes and `robot_pose_r03.placements` at 0°/90°, and closes without recomputing, applying placements to document objects or saving.

- Native snapshot: `cad/flexor_r04_robot.FCStd`, 5,052,081 bytes.
- SHA256: `f0c8482005b651e1af6694ccd79e6d878db5edb632655c154b1f9d703f113b5a`.
- Runtime: FreeCAD 27.1.0 dev, Git revision 49159, `e5fabddebb0dc54ecf324cedddd26e053e2a8488`.
- Detailed transient evidence: `reports/tmp/proximity_filter_benchmark.json`; guard evidence: `reports/tmp/proximity_filter_guards.json`. Initial conservative run retained separately as `proximity_filter_benchmark_strict_initial.json`.

## Representative robot pairs

Times below are single measurements in seconds, with qualification excluded so they reflect the intended once-qualified use. They are bounded observations, not a controlled performance distribution. `common` ran independently on every listed pair to test the decision.

| Phase | Native pair | Distance mm | Filter decision | Actual common mm³ | Filter s | Common s |
|---|---|---:|---|---:|---:|---:|
| 0° | LumbarIntegrated1 / Torso_hind | 0.498227 | ZERO_INTERSECTION | 0 | 0.66377 | 0.11223 |
| 0° | ThroughC1 / Torso_hind | 0.700000 | ZERO_INTERSECTION | 0 | 0.14743 | 0.06658 |
| 0° | SyncB1 / SpineMotor1 | 15.774615 | ZERO_INTERSECTION | 0 | 0.00476 | 0.00135 |
| 90° | LumbarIntegrated1 / Torso_hind | 0 | BOOLEAN_REQUIRED | **1.08933757** | 0.66319 | 0.20109 |
| 90° | ThroughC1 / Torso_hind | 0.700000 | ZERO_INTERSECTION | 0 | 0.14669 | 0.06143 |
| 90° | SyncB1 / SpineMotor1 | 18.068363 | ZERO_INTERSECTION | 0 | 0.00546 | 0.00136 |

Boolean-only total: 0.44403 s. Filter total plus the Boolean it retains: 1.83240 s. Therefore this helper is **not an effective general prefilter for these native parts**. The frame/torso 90° result is a real sampled intersection in this snapshot, not a cache exception; the lead was notified. Its scope is this copied pose and exact saved native revision.

## Synthetic and fallback checks

| Case | Result | Independent Boolean evidence |
|---|---|---|
| External disjoint boxes | ZERO_INTERSECTION, distance 2 mm | 0 mm³ |
| Fully contained 2 mm box | BOOLEAN_REQUIRED, distance 0 | 8 mm³ |
| Cylinder inside through-bore | ZERO_INTERSECTION, distance 2 mm | 0 mm³ |
| Intersecting boxes | BOOLEAN_REQUIRED, distance 0 | 4 mm³ |
| Face-touching boxes | BOOLEAN_REQUIRED, distance 0 | 0 mm³ |
| Interleaving sealed-cavity solids | BOOLEAN_REQUIRED, two-shell guard | 488 mm³ |
| Edge rather than solid | BOOLEAN_REQUIRED, topology guard | No Boolean needed for guard check |

All six synthetic volume comparisons and all six robot comparisons had zero false-zero decisions at the caller's 1e-5 mm³ overlap threshold.

Eleven additional guard checks passed: a translated/rotated nested wrapper retains bounds; a contained box in that posed wrapper remains Boolean-required; a one-solid-plus-stray-edge compound is rejected; null/invalid geometry is rejected; a true two-shell Solid is rejected; deliberate distance exception, NaN distance, missing current vertices, point-classifier exception and positive-distance classified containment all fall back; cumulative unwrapping preserves world bounds for every one of the 431 native links. Maximum world-bound difference for all native wrappers was zero. The deliberate error cases used thin test proxies; the geometric cases used actual FreeCAD/Part BReps.

Syntax compilation also passed. No full sampled sweep, native feature mutation or fabrication claim is part of this review. Keep the existing bbox-plus-Boolean path as the default; use this module only for a separately justified diagnostic or a narrowly profiled pair class where measured cost is favorable.
