# Execution ledger

## User pause at verified r10 CAD checkpoint — 2026-10-13

The user deferred drawings and other deliverables and requested commit/push of all changes. The active export batch finished safely; FreeCAD is healthy with the r10 robot active and all existing documents retained. No canonical geometry changed during pause preparation. Native SHA is `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`.

All 24 r10 changed-pair partitions pass for 1,346 states, with 317,087 actual OCC checks, 308,495 exact cached checks and zero recorded intersection volume; continuous clearance, minimum separation and loaded equilibrium are not established. Native/source/export and AX0/AX1 evidence is saved. The 77-sheet/321-dimension editable drawing companion is saved and reopened; final exports cover sheets 1–11 and 68, with final visual review NOT_RUN. Remaining drawings, manual, package acceptance and Blender work are deferred. Physical-interface/process/load blockers and fabrication release BLOCKED are unchanged. Resume from `reports/checkpoints/r10_paused_2026-10-13.json`; earlier ledger entries are historical snapshots.

## r08 corrected cage and accepted export checkpoint — 2026-10-12

The installed-MCP r08 assembly integrates broad windowed transverse crosswalls and solid upper sagittal horn cheeks, correcting the face ownership visible in Movie S1 at 51.5–52.7 s. The two half-cages, seam, carrier clearance pockets and controller screw margins are explicit engineering adaptations. Source-fidelity review records no additional required morphology correction in the inspected views. The corrected native/source checkpoint was committed and pushed as `8dcc006`.

Actual r08 checks now pass: 486 physical links, 95 editable bodies, fully constrained sketches, neutral raw intersections, S9 topology and axes, distinct same-direction fore/hind layouts, and two XL330-M077-T plus five XC330-M181-T motor envelopes. Clean source rebuild passes strict per-solid comparison for all 486 placed solids; edit/restore and saved-native reopen/recompute pass. The completed 105-state coarse and 361-phase cage screens are PASS. The existing 985-state detailed motion campaign is still running; its incomplete records are not accepted as a full PASS.

Final r08 exports pass strict per-solid STEP readback and print-mesh validity. Three applicable analytic profile DXFs pass exact readback. Actual CAD cycle captures and a GIF are saved separately from mechanical clearance evidence. Native drawing staging passes reopen checks with 67 sheets and 312 dimensions; GUI exports and visual review remain pending. The final manual and complete-package independent review remain pending. Supplier interfaces, physical strength, cable/spring characterization and fabrication release remain unresolved.

User commit `8103449` is already HEAD and agrees with the fetched branch. Its AX0/AX1 constraints are being integrated through a read-only adapter; no canonical geometry or frozen mechanical dependency changed for animation convenience. AX2–AX4 remain future work.

2026-10-11 | r01 | A0/G0 | PASS | verification/environment.json, views/mcp_sanity.png | no connection blocker | committed/pushed 85c8a96
2026-10-11 | r01 | A1 numerical spine | PASS (bounded) | verification/spine_cycle.json,csv | paper phase/visual branch unresolved | full native physical review
2026-10-11 | r01 | A2 native spine | initial CAD built | ../cad/checkpoints/spine_r01.FCStd | review identified crank bore/support/coupling defects | repair before legs
2026-10-11 | r01 | workflow | user directed docs/08 orchestration only; superpowers discontinued | decisions.md | none | continue authorized work

## Source-fidelity recovery, 2026-10-11

Exploratory r01 whole-robot checkpoint is preserved before correction. It is not an accepted reconstruction or manufacturing release: 258 raw neutral overlaps remain, and the source review identifies wrong guide heights/output branches and unsupported gear/chassis packaging. `codex_current_cad_reference.png` depicts the earlier spine-only intermediate; the actual later exploratory whole robot has 476 physical instances and 67 editable bodies. Neither state passes reference fidelity. See `reports/source_review/spine_reconciliation.md`. Original paper/video references were subsequently located outside this repository; previous missing-reference assumptions must not be reused.


### Corrected spine checkpoint

r02 native spine generated through installed MCP at `cad/flexor_r02_spine.FCStd`. Source-audit geometry replaces gears/platform with direct-crank packaging, upper/lower captured slots, short output connectors and compact native frames. 721-sample closure/Jacobian run passes; separate 1441-sample seed scan keeps source-side D branches. Native placement residual 7.94e-15mm, 25 used native body definitions, fully constrained sketches, 77.40×83.20×58.83mm spine-only envelope. Raw neutral diagnostic improved from54 overlaps to0 after physical frame/stack corrections. These metrics are spine-only, not a whole-robot source envelope comparison.

Independent review `reports/reviews/spine_r02_review.md` gives conditional body-development GO after axial capture repair and output-attachment reservations. It identified insufficient pin engagement and missing horn/crank coupling. Positive capture detail is being corrected; full1° copied-native-shape sweep is running and has not yet passed. No body gate or fabrication release is claimed. Manufacturer follow-up still cannot establish critical output-center/mount/horn dimensions.

### Runtime recovery

FreeCAD stopped making progress while the GUI journal-groove recompute and detached-shape Boolean sweep ran concurrently. Sweep progress remained121/361 and process threads waited on futexes. This suggests a kernel/thread interaction; root cause is unproven. Preserve saved native as `cad/checkpoints/reference_spine_pre_retention_r02.FCStd`, restart the application, and serialize heavy OCCT checks with document edits. The partial sweep is NOT a completed PASS. Unsaved retention edits are reproducible from `src/retain_flexor.py`.

### Slider plate morphology recovery

Inspected user close-ups, Fig1A/S9 and MovieS2; independent source review confirms C1/A2 and C2/A1 tall fixed journal/slot plates. Corrected the native integrated frame profiles, extended A journal/bearing/spacer stacks, added grooved C shafts and broad moving capture washers. Native:190 instances,27 editable bodies, all valid single solids and fully constrained sketches. Neutral raw overlap check:0 intersections at1e-5mm³ threshold. Actual A-axis error3.55e-15mm; neutral roller/liner gap0.10mm, washer/frame gap0.20mm; sampled track end reserve1.043mm. Fresh source rebuild matches instance volumes/bounds within7.11e-15; native thickness edit/restore and save/reopen pass. STEP round-trip retains190 solids with2.24e-14 relative volume error. Full361pose sweep is running in an isolated FreeCADCmd process; no completed motion PASS yet. Independent review resolves morphology, while liner retention, supplier fits, horn coupling and full robot integration remain open.

Completed isolated full-cycle spine sweep: PASS,361 poses at1° spacing,76,378 narrowphase checks,zero raw overlaps at1e-5mm³ volume threshold,no contact exceptions. Runtime700.89s. Static/static and same-joint point/point pairs were checked in neutral because their relative geometry is invariant. See `verification/r02_spine_sweep.json`. This is finite sampled collision evidence; continuous bounds, global minimum positive clearance, fits, liner retention and whole-robot acceptance remain unresolved. GUI remained healthy throughout. Copper liner identity corrected from brass to paper-reported copper; no solid or placement changed. CAD checkpoint/source/export recovery was pushed as7463d07 before this final evidence commit.


### r03 torso/leg checkpoint — 2026-10-12

Native r03 integrates the source S9 spine graph, monolithic E/D torso carriers, distinct fore/hind leg modules, directly keyed proximal drive, closed return rails, actual hooked extension coils and guided compression coils. Latest user steering supersedes the earlier opposing-leg interpretation: both chains now share forward/down thigh/toe and rearward/down shank directions. Native build was executed through installed FreeCAD MCP; the isolated verification process reopens/recomputes the saved file. See `cad/flexor_r03_robot.FCStd`, `reports/views/r03_robot_side.png`, `parameters/assembly_r03.json`, `src/build_robot_r03.py` and `src/robot_pose_r03.py`.

33 pure tests pass, including explicit same-direction assertions. Native S9 graph/axis audit passes (maximum axis error1.42e−14mm); physical torso cages replace redundant L6 instances. Neutral native intersection evidence is revision-specific in `verification/r03_robot_neutral.json`. Full whole-robot cycle evidence is not yet complete. This is an intermediate six-motor checkpoint; source wheel/cable mathematics and component source exist, while seventh-motor integration, physical guide mounts, cable terminations, controller/wiring and final export/drawing gates remain outstanding. Supplier interface and physical load validation remain separate unresolved requirements.

Corrected same-direction native checkpoint: neutral PASS,439 instances/63 editable bodies, all sketches fully constrained,960 narrowphase tests and zero raw overlaps at1e−5mm³. Current selected display-pose envelope154.24×112.80×94.12mm and nominal/volume-estimated incomplete mass195.31g. These differ from the paper reference and exclude pending knee motor/cables/controller/wiring. A coarse15° spine-cycle check is running; no completed whole-robot motion PASS is claimed.

### r04 Movie S1 frame and motor distinction — 2026-10-12

Rebuilt the fixed lumbar cradle with broad horizontal shelves, A/C journal bosses, six full transverse stepped shafts and native recessed capture caps, informed by Movie S1 51–80s. Preserved S9 topology; no added planar linkage edges. The hind case/cage datum moved 6mm rearward relative to the unchanged H axis to clear the frame/rocker over the cycle. This datum remains an engineering assumption, not a recovered motor output dimension. Native checkpoint:431 valid single-solid instances,67 editable bodies. Post-correction coarse whole-robot spine sweep PASS:25 poses at15° intervals,9,170 narrowphase checks,zero raw overlaps at1e−5mm³,holding leg angles fixed. See verification/r04_frame_spine_sweep.json. Finite samples do not establish continuous clearance or independent leg-motion acceptance.

Actual manufacturer PartNumber identity now distinguishes XL330-M077-T spine and XC330-M181-T legs. Canonical checkpoint contains2XL+4XC; actuator audit deliberately FAILS the complete2XL+5XC requirement. FifthXC/wheel/tendon/keyed coupling exists separately in cad/modules/hind_tendon_r04.FCStd:24 valid single-solid instances,8 editable bodies,neutral raw overlaps0. Physical guide supports, motor cage and distal termination remain pending. 34 pure tests pass. Earlier failing sweep is preserved under reports/diagnostics; accepted r03 and r02 native files remain intact.

### r05 seven-motor integration — 2026-10-12

Native r05 installs the shared hind-knee XC330-M181-T, two-groove winding wheel, fixed guide journals/supports, continuous routed cables, removable knee-case rear lock and extended ankle journals with swivel eyes/spacers. Actual motor inventory PASS:2XL330-M077-T+5XC330-M181-T. Neutral actual-native PASS:464 valid single-solid instances,80 editable body definitions,fully constrained sketches,zero raw overlaps at1e-5mm3. Independent native leg-axis audit315checks PASS. Completed coarse spine sweep25poses/15degree spacing PASS,zero raw intersections,825.02s,holding hind/wheel states fixed. Native pose API refuses stale hind-leg/wheel changes until cable regeneration.

Fresh current-source rebuild matches all464 instance inventories/bounds. One torso volume integration difference3.87e-6mm3 (9.35e-10 relative) is localized; both directional Boolean set differences are empty. Earlier cached-module diagnostic is retained. 42puretests PASS. Actual installed nominal/volume estimate253.02g; purchasedmotorportion151g; selectedposeenvelope163.54x117.60x94.12mm. These exclude uninstalled controller/wiring and do not reproduce source dimensions/mass.

STEP validation FAIL remains explicit: fullassembly relativevolume discrepancy1.25e-6 against1e-6 gate; spring supporting surfaces/trim topology are under bounded review. No accepted final export package is claimed. User latest Movie S1 steering prioritizes rounded lumbar cradle and transverse slotted output/torso plates; existing largeE-D-Htriangular carriers remain source-morphology approximations. Stopped partial one-degree sweep workers; no361posewhole-robotPASS. r06 frame revision has started and will require new checks; r05 results are historical only. Manufacturer output/mount geometry, cable securing, fits, controller and finaldrawings remain open.

### r06 Movie S1 attachment correction — 2026-10-12

Installed-MCP native integration replaces the lumbar rectangular lower annulus/full middle rail with rounded lower opening/local shelves, and both long triangular E-D-H carriers with transverse slotted moving plates and short E/D ears. Distinct vertical fore/horizontal hind mounts retain H/motor/leg datums; hind-knee cage/guide supports are regenerated on the new frame. All profile dimensions and generic mounting slots remain reconstruction assumptions. Source stills52/60/76s and hashes are retained under references/visual/movie_s1.

Actual saved-native checks PASS:464 valid single-solid instances,80 editable bodies,all sketches fully constrained,neutral1129 narrowphase checks/zero raw overlaps; S9 no missing/extra edges and maxaxiserror8.56e-14mm;315 leg-axis checks;2XL+5XCinventory;fresh source rebuild all464match;native thickness edit/restore. Coarse15°cycle PASS25poses/no raw overlaps with fixed saved leg/wheel states. Three read-only partitions aggregate only after shared native/motion SHA and inventory checks.43puretests pass. Revision notes:docs/13_candidate_frames_r06.md. Final STEP/drawings, supplier mounts/output interfaces, cable securing and controller/harness remain open.

The first combined live integration segfaulted before saving r06; saved/pushedr05 remained intact. Restarted installed FreeCAD, dismissed recovery dialog and reopened savedr05; isolated lumbar/torso/tendon stages and body-first name-based cleanup succeeded. Rootcause unproven. Canonicalr06 and three staged checkpoints are preserved. Earlier failedSTEP and interruptedr05full-degree progress are moved to diagnostics and must not be mistaken for accepted results.


### r09 recoverable checkpoint and r10 source correction — 2026-10-12

Saved/reopened installed-MCP r09: 473 physical instances, 104 source definitions, 92 editable Bodies, 295 constrained sketches; single 40-feature lumbar Body. Native geometry/S9/2XL+5XC/leg-axis checks pass. AX0/AX1 actual neutral+two nonneutral read-only manifests PASS; source-to-world maximum point error 9.775e-14mm. Native SHA765bb3b9a32365e1c005ff16a246ac284d2e0544d3648d4e4be3f436a58e1b57. Evidence: reports/verification/r09_*, reports/animation/ax01_r09.json and animation/motion/ax01_r09.json. No meshes/Blender videos produced.

r08 historical full motion: 985/985 records and 361 fixed-leg spine states PASS. r09 unchanged-instance identity proof472 PASS; r09 affected-frame campaign stopped deliberately after169/1346 partial records as user requests further geometry correction. Partial records are not full clearance acceptance.

Source S1 requested51–79s frames extracted with decoded PTS/provenance. Independent review confirms r09 missing Y-spanning open-box E crossmembers/central lugs and corresponding moving torso connection. r10 adds these at existing E1/E2 pitch axes; front/hind plate and spine-bar profile refinements are also authorized. Exact dimensions/fits remain assumptions. r09 drawings/manual/package validator are preparation, not final delivery approval. Next: stage and integrate r10, verify changed interfaces and refresh revision-bound deliverables.


## 2026-10-12 — r10 corrected attachment/profile checkpoint

Installed MCP integration saved and reopened `cad/flexor_r10_robot.FCStd`, SHA `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`: 487 physical instances, 107 used source definitions, 95 editable Bodies. The one-piece frame gains open transverse beams and central E lugs; distinct moving torso clevises remain on the existing E axes. Front/rear mounting plates and four long B–C bars receive source-supported opening profiles with explicit metric assumptions. Fourteen separate central hardware instances retain stable IDs and torso/fixed ownership.

The drawing build exposed a stale cached long-bar Pocket: its planar Boolean sketch contained internal seams. The lead replaced it with an explicit four-line/four-arc boundary plus two original bores; actual recompute/save/reopen reports zero invalid native features and source volume 199.60229607815495 mm³. Pre-repair native/results are preserved as diagnostics and excluded from acceptance. Refreshed native/S9/actuator/315-leg-axis and AX0/AX1 checks pass against the corrected SHA; three poses cover all 487 instances with source-to-world reprojection error below 1e-12 mm. Actual reference images show bare frame, both plates, long bar, complete robot and two non-neutral central-attachment poses.

Strict identity for 466 unchanged r08 instances and conservative bounds across 1346 states pass. The affected 21-instance/9996-pair campaign is running; no overall motion PASS is claimed. Supplemental source rebuild and drawing interface work are ongoing; final STEP/STL/DXF, drawing book, manual and candidate reviews remain pending. No Blender videos, AX2–4, loaded-motion prediction or fabrication release.
