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
