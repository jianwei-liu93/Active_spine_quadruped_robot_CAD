# 10 — Reference morphology audit and recovery

## Evidence and preserved state

Audit date: 2026-10-11. Recovery branch: `fix/flexor-reference-fidelity`. Commit `6820c2d` preserves the exploratory whole robot, generation sources, native checkpoints, inventory and raw interference evidence. `cad/checkpoints/superseded_exploratory_robot_r01.FCStd` is recoverable; it is not an accepted source reconstruction. The supplied `codex_current_cad_reference.png` depicts the earlier spine-only intermediate. The live later whole robot contains 476 instances / 67 native bodies, so the absent legs in the supplied screenshot were incomplete at that time, whereas the spine/chassis discrepancies are architectural.

Source locations are outside this repository: original main/supplement PDFs and Movie S2 in `/home/jianwei/freeCAD_projects/active_spine_robot_paper`; the six user-supplied evidence images in `/home/jianwei/freeCAD_projects/flexor_visual_reference_pack/references/visual`. All six images and the pack README were inspected. Source drawings, equations and reported dimensions govern topology; perspective video frames govern visible arrangement, not precision dimensions. See `reports/source_review/spine_reconciliation.md` for diagram picks and uncertainties.

## Audit before correction

| Reference feature | Exploratory r01 state | Classification | Evidence and action |
|---|---|---|---|
| Two serially coupled crank-rocker/slider/output loops | Correct closure graph and solver | MATCHED | Fig 2A, S9; preserve exact intersections, residuals and continuation checks |
| Common cyclic phase, two redundant motors | Common phase implemented via invented external gear train | INCORRECT | Fig 2A/Movie S2 10.5s; retain phase relation, replace gears with two direct horn cranks |
| A1/A2 offsets and L1–L4 reported lengths | Numeric values retained; source previously marked absent | MATCHED | Supplement equations/table; update evidence attribution after inspecting original PDFs |
| Upper C1 and lower C2 horizontal guides | Both placed at z=0; physical rails also detached from solver heights | INCORRECT | S9, Movie S2 10.5s; parameterize ±h and physically align slots/rollers |
| Short C–D connectors / upright E–D output rockers | Assumed 25/18mm output links, opposite branch | INCORRECT | S9A/B; replace assumed dimensions with explicit bounded visual estimates and correct branch |
| Slim white crossed links with windows | Rectangular thick blue/gray bars | INCOMPLETE | Movie S2; retain graph, replace section geometry with native rounded/windowed profiles |
| Compact open dark spine frame | Broad floor, tall walls, outboard rails | INCORRECT | Fig1A/MovieS2; replace with motor cradle, backbone and integrated slot bosses |
| Compact fore/hind torso motor frames | Wide 102mm cross decks and tall output plates | INCORRECT | S17/S19/S20; replace after corrected-spine review, keep pivot/output attachment logic |
| Large upper central controller block | Unverified board envelope on four tall posts | INCORRECT | Not supported by inspected source arrangement; remove from corrected spine, packaging unresolved |
| Three segments and hind parallelogram | Present in later whole robot | MATCHED | Fig2B/S17; retain FK/coupling math; repair geometry and spring attachments |
| Separate fore/hind leg morphology | Near-identical rectangular module shapes | INCORRECT | S17 and MovieS2 16.5/26.5s; distinct proportions/features required |
| Extension and compression springs | Separate unilateral models, arbitrary physical anchors | INCORRECT | Fig2B/S17; preserve constitutive functions, relocate compression element across shank and extension lever near proximal joint |
| Common bilateral knee winding wheel | Seventh motor and two tendons exist; wheel axis/route provisional | INCORRECT | S19/MovieS2 16.5s; correct rear packaging and both physical routes |
| Curved distal feet | Rectangular TPU contact blocks | INCORRECT | Fig1A/S17/MovieS2; replace with curved native distal profiles |
| Supplier output datum, horn spline, mount pattern | Envelopes only | UNVERIFIED | Manufacturer tables verify case size/mass only; critical interface drawings remain required |
| Manufacturing release / motion clearance | 258 raw neutral overlaps; no full swept clearance | UNVERIFIED | Saved diagnostic; release stays blocked until replacement geometry checked |

## Why the divergence occurred

Missing dimensions were synthesized without first locating the original PDFs/videos outside `references/`. The long output links, zero guide height, opposite output branch, gear reduction and platform chassis were engineering inventions that accumulated around a mathematically closing mechanism. Closure alone did not establish source fidelity. Adding legs did not repair these architectural choices. Color and detailing are secondary to the physical topology, output branch and actuator arrangement.

## Recovery controls

1. Preserve r01 native/source evidence in Git and checkpoint files.
2. Keep the intersection solver and independently derived Jacobian. Introduce a separate r02 parameter file; do not relabel estimated dimensions as published values.
3. Correct spine first: direct horns, ±h guides, short output links, native windowed rods, compact open frame and real axial stacks.
4. Check full-cycle closure, branch continuity, actual native placements and sampled interference. Obtain a bounded independent mechanism review before dependent whole-body reconstruction.
5. Rebuild torso/legs from S17–S20 and movie details; maintain seven motors/six commands and explicit passive elastic states.
6. Compare side/front/top/isometric views and extreme spine poses. Classify each departure as SOURCE_MATCH, ENGINEERING_ADAPTATION or UNRESOLVED.
7. Complete native/STEP/drawing/BOM package and reopen checks. Unresolved supplier interfaces preclude fabrication release even if source fidelity improves.

## r02 provisional synthesis

Starting values h=8.66, HE=33, L5=6, L6=11mm are DESIGN_ASSUMPTION values informed by S9 scale-consistent estimates (h≈8–9, HE≈32–34, L5≈5–7, L6≈9–11mm). Selecting L6 near 11mm also gives approximately 60° output excursions without imposing exact symmetry. These are neither recovered precision dimensions nor a claim of an exact paper replica. B uses the positive oriented circle intersection; D uses the negative intersection, yielding D1 above E1 and D2 below E2. Both branches must remain continuous over 2π.
