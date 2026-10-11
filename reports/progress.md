# Execution ledger

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
