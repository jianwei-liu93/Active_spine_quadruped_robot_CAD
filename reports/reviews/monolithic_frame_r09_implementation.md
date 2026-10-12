# Monolithic center frame r09 implementation handoff

Worker scope: `src/spine_frame_r09.py` and this report only. Initial implementation used no CAD execution. The lead subsequently authorized supplemental isolated FreeCADCmd execution; the results are recorded below. No installed MCP/live GUI, canonical native-file, shared-parameter, frozen-module, or export writes were performed.

## Implementation

`build(doc, p)` constructs `FRM_LUMBAR_MONOLITHIC_CAGE_r09` as one `PartDesign::Body`, returning `(body, diagnostics)` without creating a physical AppLink. `apply(b, remove_old=True)` calls that build, adds its source to PartsLibrary, preserves the existing `LumbarIntegrated1` LinkPlacement, and returns an explicit identity merge `{LumbarIntegrated_1: LumbarIntegrated1}`. Build and integration do not autosave.

The native construction order is near sagittal cheek at localZ 0..1.6, two continuous full-span orthogonal walls at localZ 0..56.8, then the far cheek at 55.2..56.8. Each wall has one aperture at localZ 10.4..46.4 (worldY ±18), caseZ 10.5..27.5. Wall caseX bands remain −14..−12.4 and 12.4..14, with caseZ 0..33. There is no roof and no midplane seam. The solid upper sagittal cheeks and R9 lower horn opening retain the r08 contour.

The existing right interface features are translated +55.2 along source-local Z. All r08 A/E/O joint, ear, guide-slot, shelf, collar and motor-face-band datums remain unchanged. Positive case-X carrier access pockets retain worldY ±[17.75,22.25], caseZ [26.65,31.15]. Final journal and C-travel pockets span the complete outer stack −12.6..69.4, using 82 mm depth. C relief geometry retains the actual solver-derived center range with 0.01 mm endpoint allowance and the r09 configured radius.

The intended feature tree contains 34 native Pads and 6 native Pockets, each with a distinct constrained sketch (40 profiles). The inherited `sketch_face` helper fixes contour primitives with Block constraints; circle pockets use dimensional center/radius constraints. Native Pad/Pocket profiles remain exposed in the tree, with no opaque Part::Feature/PartDesign::Feature fused result. The `section` helper uses temporary shapes only to obtain a complete sketch contour with all wires. Each feature recompute checks a fully constrained profile and one valid connected solid, and raises on failure.

## Obsolete separation hardware

Following the lead's source-review decision, no BraceBoss, TieClearances, TieCollarRecesses, or WholeCrosswallTiePassages features are generated. No integral replacement rods are added. `apply` retires exactly these 12 AppLinks:

- FixedLumbarTie0, FixedLumbarTie1, FixedLumbarTie2, FixedLumbarTie3
- FixedTieScrew0__1, FixedTieScrew0_1
- FixedTieScrew1__1, FixedTieScrew1_1
- FixedTieScrew2__1, FixedTieScrew2_1
- FixedTieScrew3__1, FixedTieScrew3_1

Both frame links and all 12 obsolete links must exist before build/integration. The resulting physical link delta is −13 (486→473 for the stated baseline). Actual before/after counts and all retired names are returned. Retired names are removed from both `b.motion` and the existing native MotionMap; missing fixed-frame map entries are not invented. Source cleanup considers only sources previously used by these exact retired/replaced links, checks external references and surviving AppLinks, and preserves shared screw definitions. `remove_old=False` retains unused source definitions but still performs the requested physical merge/hardware retirement.

Motor center shims, motor collars/bands, moving synchronization shafts and all other existing hardware remain unchanged. Native motor retention, supplier fits, structural adequacy and fabrication release remain provisional.

## Checks actually performed

- `python -m py_compile src/spine_frame_r09.py`: passed.
- Static AST/import checks: one PartDesign::Body factory, no opaque feature factory, no save/export/application launch, no `assembly_r08.json` reads: passed.
- Twelve unique explicit obsolete tie IDs and full-span/stack arithmetic (within floating-point tolerance): passed.
- Reviewed against `spine_frame_r08.py`, `refine_flexor.py` sketch helpers, `spine_attachments_r02.py` actual tie name generation, AGENTS.md, and docs 02/08.

All newly read frame configuration comes from `parameters/assembly_r09.json` / `lumbar_frame_r09`, owned by the lead. Native topology, sketch solve, neutral collision, motion clearance and STEP validation require lead execution. The `execution_native_validity` result is produced only after the native build checks execute successfully; this report does not assert that they have executed.

## Authorized supplemental CLI exercise

The lead authorized an isolated FreeCADCmd run after the source handoff. The runner is `reports/tmp/monolithic_frame_r09/prepare.py`, with stdout/stderr in `prepare.log`. Snap required normal sandbox escalation, which was accepted. The only headless adjustment was a harness-local `cad_common.metadata` replacement preserving every identity property while skipping GUI-only color styling.

Construction and staging save/reopen/recompute passed on the first CAD attempt. Actual results: one retained frame AppLink, one valid native solid, 34 Pads, 6 Pockets, 40 fully constrained frame sketches, all assembly sketches fully constrained, no opaque frame features, and 473 physical links. Frame volume before save was 14472.419033190285 mm³ (reopened 14472.419033190281 mm³). Source-local bounds were X ±38.30736611867309, Y [−15.977241335952169, 35.57883832488649], Z [−12.6, 69.4] mm.

The staged native model is `cad/staging/r09_monolithic_prepared.FCStd`. The machine-readable record is `reports/verification/r09_frame_staging.json`. The frozen canonical r08 native model SHA-256 remained `3832778436b75539d0ecf0e95df935099005331157c1328c2f77389985a817c8` before and after construction/readback. Four unused source definitions were removed from the staging document: the two r08 frame bodies, the old tie tube source and the old tie screw source. The screw source had no remaining AppLink references; other screw sources were preserved.

The supplemental neutral raw intersection check passed: 473 actual physical links, 1165 narrowphase tests, zero raw intersections above 1e-5 mm³, elapsed 213.06347846984863 seconds. It ran only after construction/readback passed; the separate detailed result is `reports/tmp/monolithic_frame_r09/neutral_raw.json`. The canonical r08 SHA-256 also remained unchanged after this check. This supplemental exercise does not replace installed MCP validation, motion coverage, supplier interfaces, structural validation or fabrication release.
