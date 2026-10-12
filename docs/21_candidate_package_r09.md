# r09 one-piece lumbar candidate package checkpoint

**Status: PREPARED / primary canonical acceptance NOT_RUN at this checkpoint. Not a fabrication release.** This record supersedes the two-half lumbar adaptation in r08 and its checkpoint in document 19. It records supplemental staged evidence separately from final canonical acceptance. The final native SHA has not been supplied to this manual preparation task; no r09 manual PDF has been generated.

## Candidate identity

The intended canonical document is `cad/flexor_r09_robot.FCStd`, built through `src/build_robot_r09.py`, `src/spine_frame_r09.py` and `parameters/assembly_r09.json`. The center frame is **one physical monolithic cage**, part number `FRM_LUMBAR_MONOLITHIC_CAGE_r09`, retained physical identity `LumbarIntegrated1`. There is no center assembly seam and no second half to install. Native geometric continuity does not establish strength, fatigue life, print quality or a validated load path.

The retired physical instances are `LumbarIntegrated_1`, `FixedLumbarTie0` through `FixedLumbarTie3`, and the eight `FixedTieScrew{0..3}__1` / `FixedTieScrew{0..3}_1` instances. The expected physical inventory changes from 486 to 473 AppLinks. Motor center shims, collars/bands, moving synchronization shafts and other retained hardware remain part of the actual instance inventory. Do not install the retired lumbar ties or their screws, and do not confuse them with retained carrier clamps or other torso ties.

The staged cage contains 34 native Pads, 6 native Pockets and 40 fully constrained profile sketches in one valid single-solid PartDesign Body. Solid sagittal horn cheeks meet two continuous orthogonal windowed crosswalls, with an open top and native carrier/travel reliefs. Movie S1 at 51.5 and 52.7 seconds supports the visible arrangement; metric contours, windows, walls and reliefs remain reconstruction or engineering assumptions. Final source-definition, body, BOM part-number, sheet and dimension counts must come from the canonical package manifests; none is inferred from an earlier revision.

Mechanical invariants remain seven physical motors, six commanded coordinates, two redundant spine motors sharing one phase, four prescribed knee coordinates, distinct fore/hind leg geometry with the same modeled sagittal direction, physical extension/compression springs, and the bilateral hind cable route. The prescribed knee values do not solve loaded passive equilibrium. The motor inventory is two XL330-M077-T plus five XC330-M181-T. Both case envelopes use 20 × 26 × 34 mm in native XYZ, corresponding to catalog W/H/D 20 × 34 × 26 mm. Critical output, mount, horn, fastener and connector interfaces remain provisional.

## Evidence boundary at preparation

The supplemental isolated construction/readback record is `reports/verification/r09_frame_staging.json`. It reports one valid frame solid, 473 physical links, fully constrained sketches, frame volume 14472.419033190285 mm³ before save and 14472.419033190281 mm³ after reopening. Its staged neutral check reports PASS for 473 instances, 1,165 narrowphase checks and zero raw overlaps above 1e-5 mm³. These results concern `cad/staging/r09_monolithic_prepared.FCStd`; they do not establish installed MCP acceptance or final canonical identity.

| Required final gate | Checkpoint status / required evidence |
|---|---|
| Primary canonical integration, native recompute/readback, S9 and leg-axis checks | NOT_RUN for this preparation task; lead must execute through installed MCP and bind actual results to the final native SHA |
| Final neutral raw intersections | NOT_RUN for canonical r09; staged neutral PASS remains supplemental only |
| Composite finite-sample motion | NOT_RUN; require `reports/verification/r09_frame_partitions/summary.json` and its freeze, identity and complete partition records |
| AX0 inventory and AX1 posed-transform contract | NOT_RUN; require both `reports/animation/ax01_r09.json` and `animation/motion/ax01_r09.json`, with matching canonical SHA and payload hash |
| STEP/export round trips, final BOM, mass and demand calculations | NOT_RUN for final canonical r09; require revision-matched package, mass and engineering reports |
| Source-fidelity captures | NOT_RUN for final canonical r09; require SHA-matched actual captures and visual PASS |
| Drawing book and applicable flat-stock profiles | NOT_RUN for final canonical r09; staging dimensions do not replace canonical regeneration, GUI export/render/visual review and profile readback |
| Manual and combined drawing book PDF delivery | NOT_RUN; generate only after all required gates; visually inspect both final PDFs |

The motion acceptance is a composite proof with three mandatory legs: the actual full r08 campaign PASS for 985 states; strict geometric, placement, configuration and motion-map identity for all 472 retained nonframe instances; and independent new-frame checks against those 472 counterparts for **all 1,346 r09 states**. The affected-frame inputs comprise the original 985 states plus 361 integer spine phases with neutral legs and zero wheel command. The new frame never inherits r08 clearance merely because other parts are unchanged. Partial partitions, input manifests, or a historical r08 PASS cannot establish whole-r09 acceptance. Finite sampling does not prove continuous clearance, loaded equilibrium or dynamics.

AX0/AX1 are animation interface checks, not a new collision or performance campaign. Require complete stable physical identities, source-local frames, reviewed grounding/MotionMap coverage, neutral plus two nonneutral prescribed poses, consistent transforms and separately regenerated deforming states. AX2–AX4 meshes, scenes and videos remain NOT_RUN and are outside this package task.

## Manual generator and finalization contract

`src/manual_pdf_r09.py` is prepared without authoring a PDF. Importing it performs no CAD operation or output write. The lead must explicitly invoke `build(expected_native_sha256)` or pass `--native-sha256` with the final frozen canonical SHA. Its guards require final revision-matched package, mass, engineering, neutral, drawing, profile, capture, composite motion and AX0/AX1 records. Staging-only drawing hashes and missing evidence fail closed. It rechecks the current frame proof, freeze/dependencies, historical baseline, partition union and state input hashes without executing CAD partitions or writing verification reports.

The generator reads actual physical/BOM quantities, known and unknown mass, center of mass, point-mass inertia, load-demand values, source counts and drawing sheet/dimension counts from the final evidence. It checks the single cage and two-XL/five-XC motor quantities against the final BOM. It preserves unknown controller mass, distinguishes the separately assumed controller/harness sensitivity case, and states that point-mass inertia omits solid centroidal inertia. No r08 mass or inventory values are reused as r09 values.

The final PDF deliverables are exactly the assembly/calibration manual, `docs/flexor_r09_assembly_calibration.pdf`, and one combined dimensioned drawing book at the lead's final package path. Individual drawing exports are working inputs to the combined book. Lead generation must follow the PDF skill's authoring marker and render/review requirements, with page overflow, typography, images, tables, dimensions and provenance checked on the actual final PDFs. This preparation task does not run the authoring marker or produce either PDF.

## Fabrication and hardware boundary

The one-piece geometry does not close supplier, structural or physical assembly questions. Exact motor case mounts, output centers, pilots/splines, horn patterns, motor retention and fastening, screw thread/engagement, bearing/shaft/clip identity and fits, OpenRB footprint/population/mounting and electrical routing remain unresolved. Confirm real connectors, solder joints, bend space, strain relief, power/TTL wiring, polarity and service access.

Spring identity, free length, rate, end forms and preload; cable bend radius, terminals, clamp pressure, holding force, slip and fatigue; material/process allowables, printed wall quality, creep, contact stresses, load distribution, fastener capacity and assembly/tool access remain fabrication blockers. Quasi-static pin/seat/shaft and hip-moment demand estimates are not strength or safety-factor passes. Motor stall torque is not a continuous-duty or thermal rating. Physical fitting, torque-off inspection, weighing, load and endurance tests remain separate work.

No powered hardware, IDs, encoder offsets or calibration motions have been commissioned by this CAD record. Keep offsets unset and torque disabled until actual interfaces, safe restraints and separately authorized commissioning are established. This candidate does not authorize fabrication, purchasing, energizing, gait operation, load testing or hardware release.

## Preparation checks performed

The r09 generator passed Python compilation and a read-only import. Guard probes rejected an invalid lead SHA and the currently missing final r09 package manifest before any output creation. Temporary synthetic fixtures exercised acceptance of a complete composite ledger and rejection of incomplete affected-frame pair coverage and a failed historical baseline. These are source guard checks, not execution or acceptance of the actual r09 collision campaign. No CAD operation, PDF authoring marker, PDF generation or canonical/native save occurred in this preparation task.
