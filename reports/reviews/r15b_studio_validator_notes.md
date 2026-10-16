# r15b studio serialized-scene validator preparation

Scope: source-only adaptation of the accepted r14 Movie S2 validator. The lead owns CAD export, source-library construction, presentation construction, rendering, and fresh-process execution. This preparation does not establish a Blender runtime PASS.

## Changed file

`animation/blender/verify_coordination_s2_r15b.py` targets the r15b scene, source manifest, presentation manifest, report, body root, floor marker, and `build_coordination_r15b.py` helper dependency hash. The existing r14 validator is unchanged.

All 65 existing `check(...)` calls are retained verbatim apart from the revision substitution. Coverage remains 455 physical instances and 108 source identities; strict source-local rigid vertex/topology sharing; 10 procedural instances and all 3,000 stored procedural states; 108 output-frame transform readbacks spanning 100 distinct source samples; evaluated procedural geometry on those frames; all 1,500 root transforms, floor clearances, procedural evaluation times, and declared camera framing inventories. Existing numerical tolerances and camera safe rectangle remain unchanged.

Additional gates require exactly 98 shared rigid source meshes, the full source timeline count matching its manifest `sample_count` (1,201 samples in the native export), with its first 300 samples selected as the studio cycle, full 1920 x 1080 output at 100% scale, and a standalone background invocation opening the saved `.blend` before this script. The report's `reopened_in_fresh_process` field now reflects those invocation checks rather than a constant. Use:

```text
blender -b <saved r15b studio scene.blend> --python animation/blender/verify_coordination_s2_r15b.py
```

The saved-scene check requires `--python` to name this validator directly. Running its contents with `exec` inside an existing Blender session intentionally fails that gate.

Each of the four legs additionally checks thigh, shank, and foot rotation relative to its own moving fore/hind torso, over all 100 distinct stride-three samples. Every segment must exceed a one-degree excursion from the first sample. The report records the measured excursion for each of the 12 segments. This bounded non-rigidity check prevents root bobbing or spine motion alone from satisfying the articulation claim; it makes no loaded-gait or dynamics claim.

## Checks actually performed

- Python syntax compilation: PASS.
- AST comparison of all original `check(...)` calls after revision substitution: PASS; no original gate was removed or changed.
- Static calculation on the accepted r14 source timeline using the same torso-relative orientation metric: all four thighs and feet reach approximately 67.072382 degrees from the first sample; all four shanks reach approximately 47.561817 degrees. This confirms that the added one-degree threshold is compatible with the accepted motion prescription. The lead is regenerating the r15b motion and all geometry assets through a fresh native CAD export; the r14 calculation is not an r15b export or saved-scene result.

## Execution status

Blender/FreeCAD runtime execution, generated r15b source assets, saved-scene readback, render inspection, and final acceptance: NOT_RUN by this worker. The lead must execute the validator in a fresh Blender process after saving the completed scene. The runtime report is written to `reports/animation/spine_leg_coordination_s2_r15b_readback.json` and exits nonzero on any failed mechanical, presentation, or framing gate.

## Timeline gate correction

The first lead-run saved-scene check exposed an incorrect added assumption that the complete production timeline had only 300 samples. The native export correctly contains 1,201 samples (four cycles plus endpoint), while the studio uses its first 300-sample cycle. The validator now counts all source rows against the manifest `sample_count` and retains only the first 300 for the unchanged transform and procedural checks. The failed report is preserved by the lead; rerun acceptance remains a lead-owned runtime step. Python syntax compilation and retention of all 65 original gates were rechecked after this correction.
