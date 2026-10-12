# r10 native drawing companion preparation

Status: **PASS_SUPPLEMENTAL_NATIVE_CONSTRUCTION_REOPEN**. GUI styles, PDF/SVG exports and final visual QA remain **NOT_RUN**.

Prepared only `cad/staging/r10_drawings_prepared.FCStd` from frozen canonical `cad/flexor_r10_robot.FCStd`, SHA-256 `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`. The canonical hash remains unchanged. Stage SHA-256: `09d79b4128e68de951ab0f704f072c1702c022553bd60149704ef7df8676bfb6`. No live MCP, canonical save, shared helper/schema edit or historical drawing change occurred.

Actual results: **67 native sheets / 311 native dimensions / 0 dimension errors**. After staged save/reopen/recompute, maximum native dimension error is **2.4436858581111665e-07 mm**, below the unchanged 1e-6 mm tolerance. Every dimension retains its original native references and rejects arbitrary overrides. Native curve-extrema REF dimensions retain regeneration associations; they must be regenerated after model edits.

The companion preserves **487 physical App::Links / 107 used source definitions / 95 PartDesign bodies / 321 fully constrained sketches**, unchanged MotionMap and 0 rad input phase. Initial native Invalid-feature guard passed. A separate read-only staged reopen/recompute found **zero Invalid native features** and verified **all 67 editable Title fields against actual source PartNumbers**. Candidate notes explicitly preserve DESIGN_ASSUMPTION dimensions, UNKNOWN fits and validation of bores, threads and loads. See `reports/tmp/r10_drawings/stage_feature_states.json`.

Relevant changed/additional source sheets:

| Sheet | Actual source PartNumber | Native dimensions |
|---|---|---:|
| 1 | `CENTRAL_E_GROOVED_PIN_r10` | 4 |
| 2 | `CENTRAL_E_SPLIT_RETAINER_r10` | 3 |
| 3 | `CENTRAL_E_THRUST_WASHER_r10` | 5 |
| 6 | `FRM_LUMBAR_MONOLITHIC_CAGE_r10` | 6 |
| 54 | `SPN_LONG_BC_RELIEVED_r10` | 5 |
| 65 | `TORSO_FORE_TRANSVERSE_FRAME_r06_r10` | 6 |
| 66 | `TORSO_HIND_TRANSVERSE_FRAME_r06_r10` | 8 |

All original body/link Names, types, PartNumbers, face/edge/vertex/solid counts and validity agree before construction, after construction and after reopen. Construction bbox/placement/raw-volume deltas were exactly zero. Reopen maximum bbox/placement deltas were **0.0 mm / 0.0**; raw volume drift was **7.1054273576010019e-15 mm³** (relative **8.2546501578674783e-16**), limited to floating-point integration. No geometric tolerance was relaxed. Full source/construction/reopen snapshots, exact differences and native reference checks are in `reports/tmp/r10_drawings/native_staging_verification.json`; manifest is `drawings/r10/drawing_manifest_r10.json`. BREP byte differences are diagnostic rather than geometry acceptance.

The generic package includes editable native orthographic/isometric views, native envelope/circular/pitch dimensions and complete native source-feature parameter records. It is a provisional source drawing package, not complete fabrication dimensioning. Hidden Ø2.0 central-clevis bores and open retainer ID do not receive direct diameter labels from the generic projection pass; add source-associated critical interface callouts/sections during lead GUI review as needed. Pin groove, retainer installation, supplier bearing fits, print bore allowances, loads and manufacturing release remain unresolved. No source geometry was substituted or omitted to make a drawing pass.

Earlier attempt and resolved source defect: the prior frozen source `b0c43007aac0242b5420084a41c5d350f20dfd56e9893e2244ecb7a53cafbf39` initially exposed valid cached Body shapes but emitted `SPN_r02_L4_Pocket: Wire is not closed` during native drawing recomputes. TechDraw then SIGSEGVed at long-bar X extent 51.7876 mm in `addCosmeticVertex`. The lead repaired the bar profile via MCP to an explicit closed boundary and supplied the current frozen source. That repaired source completes construction and staged reopen. Original crash logs remain `prepare.log` and `prepare_instrumented.log`; successful run is `prepare_repaired.log`. The precondition Invalid-feature guard was added to the isolated runner, not the shared helper. The stale cached-shape finding was material and has not been represented as an initial full native-feature pass.

Lead completion: open the staged companion in the live GUI; call `drawings_r07.layout_existing_pages(doc, ROOT, revision='r10')`; inspect source-associated critical interface coverage and candidate notes; export representative changed sheets 1/2/3/6/54/65/66, render and inspect; then export/review all 67 sheets and save the final companion separately. No GUI layout/style, export, visual, fit, clearance or fabrication PASS is claimed here.

## Bounded critical-interface diameter follow-up

Status: **UNSUPPORTED_NATIVE_3D_DIAMETER — stopped at first unsupported native measurement**. Existing saved companion and manifest remain unchanged at **67 sheets / 311 native dimensions**.

New source: `src/drawing_interfaces_r10.py`. It resolves actual 1-based source-Body circular edges by diameter, center in the preserved source-local frame and transverse/source-Z axis. Its specification inventory covers both torso clevis bores, both central fixed-lug bores/seats, pin OD/groove root and split-retainer ID/OD. The first standalone probe used `drawings_r07._dimension(..., refs3d=True)` without nominal overrides and stopped at the unsupported result. No remaining dimensions were attempted after the small probe failed. The current module implements only the second bounded auxiliary-projection gate described below; the failed true3D approach is retained as evidence, not retried.

Actual first small-source test: fore torso `Edge129`, actual radius1.0 mm, center approximately `(0, 0, 19.6)` in source coordinates, axis approximately `(0, 0, 1)`. This is a split circular bore arc, rather than a projected visible-circle surrogate. The installed native true3D `Diameter` returned **0.0 mm** for the actual Ø2.0 source edge. The unchanged helper rejected it with `ValueError: INTERFACE_PROBE_Clevis: native 0.0 != geometry 2.0`, and removed the rejected dimension. Probe runtime was **27.6589 seconds**, including staged open/recompute and actual-edge inventory. There was no segmentation fault and no stage/manifest save. This result establishes unsupported behavior for this actual source arc/reference configuration; it does not prove all native 3D diameter configurations fail.

Actual edge inventory is in `reports/tmp/r10_drawings/interface_probe.json`; it verifies central-lug centers at source X=±33, Y=0, local Z=26.8/28.0/28.8/30.0, Ø2.2 through-web circles and Ø4.05 bearing-seat circles. The pin has actual Ø1.9 and groove-root Ø1.6 circles. The split retainer has actual partial circular arcs for Ø1.6 ID and Ø3.6 OD. Those later dimension types were not trialed after the first unsupported measurement, per the bounded task instruction.

A source-associated alternative for the clevis split-circle diameter requires lead authorization/implementation before replacing the missing interface callouts. No arbitrary or cosmetic values have been substituted. Fits, print allowances, pin groove axial fit, retainer temper/retention and fabrication qualification remain UNVERIFIED.

A second, materially different approach was explicitly authorized: one dedicated auxiliary `TechDraw::DrawViewPart` normal to the actual source-circle axis, then native projected `Diameter` only if a real full projected circle could be reliably identified. The in-memory probe completed safely in **24.4549 seconds**. Its actual source-associated Ø2 bore projected as six split arcs at verified view-local center **(−16.25, −6.5, 0)**: API indices **13/14/15** and **95/96/97**, each triplet with lengths approximately **π/2, π, π/2 mm**. The source projected center minus the source bounding-box projected center matches that actual arc center. No complete projected Ø2 circle was present. The probe therefore stopped **before** attempting a projected diameter or expanding to other sources, as instructed. No arbitrary/caption dimensions or joined surrogate circles were introduced.

Evidence: `reports/tmp/r10_drawings/interface_projected_probe.json` and `.log`. `src/drawing_interfaces_r10.py` now exposes the bounded auxiliary-projection gate and always rolls back its probe objects. It does not retry true3D Diameter. No stage/manifest changes were saved; the prior **67-sheet / 311-dimension** companion is preserved. Full native central interface callouts remain BLOCKED under these two tested methods. The module compiles; its API refactor after the standalone probe was not rerun as a third CAD attempt.
