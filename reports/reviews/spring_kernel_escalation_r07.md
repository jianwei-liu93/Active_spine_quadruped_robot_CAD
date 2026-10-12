# r07 compression-spring kernel escalation

Scope: bounded escalation of two unresolved OCC union failures, at installed lengths **17.043604814814746 mm** and **17.791246138622558 mm**. The lead owns the live MCP session and canonical model. This work uses isolated `/snap/bin/freecad.cmd` processes and writes no native assembly.

## Result and implementation

**PASS: all 997 exact compression-length requests from the 985-pose full manifest, plus four explicit regressions (1,001 executions; 999 unique qualified lengths).** No candidate sequence exhausted. The four-partition final run took 440.65 seconds, with median per-test time 1.665 seconds and maximum 9.350 seconds under concurrent load. 176 executions reused and revalidated already-generated SHA-matched native BReps. Maximum rejected candidates before success was 11 (length 21.796615348461053 mm, accepted seam 131°).

Generator/normalizer source fingerprint: `6dea8f4374c2ed5e6f7e726a0f9630fbd7b3d036b002788db237f24b2b9be7d6`. The final cache manifest indexes all 999 required unique native BReps; their source and BRep hashes were checked after all partitions finished.

`src/compression_spring_r07.py` implements a bounded sequence of full-torus seam rotations: 43°, 11°, 23°, 37°, 61°, 17°, 29°, 53°, 71°, 89°, 101°, 131°, 0°. A seam rotation changes the parameterization of a full torus, not its occupied geometry. Every candidate contains the original swept helix and the same two end tori; there is no cylinder proxy, scale change, seat displacement, omitted wire, or end-shape redesign.

Frozen geometry is OD 4 mm, circular wire diameter 0.5 mm, helix center radius 1.75 mm, 12 active helical turns, pitch `(installed_length - 0.5) / 12`, and full closed end rings centered at z = 0.25 mm and z = installed_length − 0.25 mm. The existing assumed end-ring/helix overlap geometry is retained; this is not a new spring manufacturing definition or strength claim.

The existing **qualified-neutral-only** `spring_normalization_r07.normalize` is applied to every candidate before acceptance. It is not applied at nonneutral lengths. Generic `Shape.fix` across motion poses is rejected: it demonstrably removes end material or creates invalid solids on the original failing lengths. No STEP-based normalization is used by the final generator.

Every returned result must be non-null, valid, and exactly one solid; must satisfy the existing complete-wire constituent-volume interval (helix lower bound and helix + two tori upper bound, with the unchanged 0.3% integration budget); and must span [−2, 2] × [−2, 2] × [0, installed length] within 1e−5 mm. This broad volume gate detects catastrophic wire loss; it is not substituted for the strict 1e−6 native/STEP volume gate.

The public `validate(shape, length, containment=False)` executes these mandatory gates. Its optional dense 1,732-point interior test is expensive. Additional finite exact-OCCT containment was performed separately at 25 representative lengths using 160 centerline points each: eight per active turn and 32 per closed end ring. Finite samples support only sampled coverage.

## Evidence

All raw scripts, outputs and exploratory BReps are under ignored `reports/tmp/spring_kernel_escalation/`.

- `module_test.json`: both original failing lengths pass at seam 43°. Neutral length 17.53863375 mm passes at seam 37° after three rejected candidates; neutral length 22.35480766 mm passes at seam 43°.
- `containment_test.json`: **25/25 pass**, including both failures, both neutral lengths, and 21 evenly distributed selections over 16.506314028796716–23.394117081556708 mm. Every point is classified IN or ON by `BRepClass3d_SolidClassifier`, with 1e−6 mm classifier tolerance. Total generation/classification time 177.71 seconds; mean 160-point classification time 5.14 seconds under concurrent verification load.
- `input_provenance.json`: 985-pose full-manifest/configuration hashes and the read native-file SHA-256 (`8d0d363add856115761ac767c5b3948d62360c36a5b4d80d76a8de87b9162ca5`).
- `descriptor_lengths_exact.json`: actual requests from all full-manifest poses, read from the canonical model in an isolated process without saving or mutating it. There are **997 exact float lengths**; extraction took 19.80 seconds. Values are not rounded. Pure local-geometry lengths differ from world-transformed distances by floating-point roundoff and are not used as the final qualification target.
- `range_0.json` … `range_3.json`: final full-request qualification, plus four explicit regressions. Final aggregate is `qualification_summary.json`; cache index is `qualified_shapes/manifest.json`. All 1,001 execution records pass, including the exact requested floating-point inputs.
- `neutral_step_test.json`: **4/4 pass** (two neutral definitions and both original failures). Maximum relative volume difference is 4.37e−9; maximum numerical-margin upper difference is 4.04e−7; maximum bounding-extrema difference is 4.41e−13 mm. Total runtime 20.18 seconds. Strict native/STEP comparisons use `adaptive_volume_r07` with the same 1e−6 relative-volume and 1e−5 mm bounds tolerances. Gauss–Kronrod, precision convergence, and paired Gauss/GK disagreement contribute the numerical margin; default `TopoShape.Volume` is not treated as an accurate strict volume measurement.

Exploratory probes also tested split circular profiles, one-turn helix subdivisions and a 1e−5 mm fuzzy Boolean tolerance. These were not selected: some outputs had lost wire or incomplete end geometry, or offered no demonstrated benefit over unchanged-geometry seam retries. Default-volume disagreement alone is not evidence of physical geometry loss; it was separated from actual validity/bounds failures once the adaptive-integration investigation identified that measurement limitation.

## Integration recipe

1. Keep extension-spring generation unchanged. For compression, call `compression_spring_r07.shape(length, free_length)` from the lead-owned `_spring_source`. It either returns a gated native BRep or raises after all 13 candidates fail.
2. Keep the existing outer motion/STEP acceptance gates. Do not call a second generic `Shape.fix` on nonneutral output.
3. Optional immutable source cache: files live in ignored `reports/tmp/spring_kernel_escalation/qualified_shapes`. Key is `float(length).hex() + '_' + source_hash()`. The hash covers both the generator and neutral-normalizer source bytes. Each BRep has a JSON sidecar with exact length, accepted seam, validity, solid count, bounds, source hash and BRep SHA-256. Verify both hashes before reuse, read the LOCAL BRep, and rerun `validate(shape, length, False)` before placement. If a key is missing, generate exactly that requested float rather than rounding to a nearby key.
4. `shape(..., evidence=dict, cache_dir=path)` optionally records generation evidence and retains the native BRep. No document or object is created or modified.
5. Add this module and `spring_normalization_r07.py` to the lead-owned verification dependency fingerprint. A generator edit invalidates cached keys; no stale-cache acceptance is permitted.

This is finite CAD-kernel qualification of the prescribed samples, not continuous motion, loaded equilibrium, spring rate/fatigue validation, fabrication release, or a guarantee that every arbitrary floating-point length can be built.
