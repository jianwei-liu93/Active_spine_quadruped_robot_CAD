# OpenRB-150 carrier candidate — r07

**Status:** source candidate successfully generated and checked in an isolated FreeCADCmd process against `cad/checkpoints/r07_frame_clamps.FCStd`. The canonical/live document and checkpoint file were not saved or modified. This remains an engineering adaptation, not a vendor-interface model or fabrication release.

## Interface and layout

The physical board envelope uses the manufacturer-published 25 × 66 mm outline, centered at X=-10 mm and Y=0. It has no invented PCB mounting holes. Board thickness 1.6 mm and bottom Z=39.6 mm are assumptions. The 28 × 70 × 1.2 mm PA12 tray occupies X[-24,4], Y[-35,35], Z[37.2,38.4]. Two long edge supports meet the assumed board underside; removable retainers overlap each board edge by 0.5 mm only where component-free contact is presumed. Four simplified steel retainer screws sit outside the PCB outline.

The PCB is a physical purchased envelope: `PartNumber=OPENRB150_PCB_ENVELOPE_r07`, `MaterialName=electronics`, `Role=PURCHASED`. Its mass remains unknown for the lead's separate load screen. A 5 mm population reservation is a hidden, unlinked nonphysical object in `ReferenceClearances`; it is outside the parts library and assembly links, and excluded from BOM/collision handling. Population height and connector envelopes are unknown. Official dimension evidence and retrieval limitations are recorded in [supplier_completion_r07.md](../sources/supplier_completion_r07.md).

Two 4 mm-wide split-clamp stations at Y=±20 attach to the r07 checkpoint's upper lumbar tie. Rotating source point (local X,Z)=(11.4,28.4) by 30° gives tie axis X=-4.3273104, Z=30.2951215 mm. The PA12 carrier half-collars and steel caps use an assumed 2.5 mm bore around the nominal 2.4 mm tie; the assumed collar outside diameter is 3.6 mm to clear the adjacent motor. Each cap fastens at two registered upper-lug holes, Y offsets ±1.4 mm from its station and Z offset +2.0 mm from the tie axis. The post and offset arm have 1.2 mm minimum web thickness and reach the tray underside, with the arm ending at X=4. Assumed M1.4 bolt envelopes have 1.6 mm clearance bores and 0.9 mm hex sockets. These fits and dimensions remain assumptions pending board measurement, tolerance review, and load design.

## Native validation

[controller_carrier_r07.py](../../src/controller_carrier_r07.py) builds six editable `PartDesign::Body` sources with fully constrained sketches and Pad/Pocket features: tray/supports, steel split-clamp caps, two edge retainers, and two simplified fastener types. It returns fixed-lumbar placement descriptors compatible with the lead-owned fixed-kind mapping.

An isolated FreeCADCmd run opened the checkpoint read-only in a separate process, generated the module, recomputed, checked the physical `App::Link` assembly, then closed without saving. A small headless harness wrapper supplied the identity metadata and links normally styled through `ViewObject`, which is unavailable in FreeCADCmd. Results:

- All six source bodies recomputed as valid single solids; all 19 sketches were fully constrained and no Pad/Pocket feature reported an invalid state.
- The four cap-hole centers registered with the four carrier-lug hole centers at six-decimal-mm precision. All 14 physical links were created, including the PCB envelope. The hidden population reservation was in `ReferenceClearances`, absent from the parts library, and had no `App::Link`.
- Boolean checks found zero positive-volume overlaps above 1e-5 mm³ between physical carrier links and existing checkpoint links, including the PCB envelope. Pairwise checks among new physical links also found zero such overlaps.
- Closest measured gaps included 0.05 mm from the nominal 2.5 mm collar bore to the 2.4 mm tie and 0.18 mm from steel clamp caps to adjacent motor solids. Clamp bolts retained 0.15 mm minimum radial clearance from the tie. These small modeled gaps are assumptions and need tolerance review.

## Remaining limits

- The published 25 × 66 mm board outline does not verify thickness, mounting features, populated height, edge keepouts, connector access, or mass. Validate the PCB envelope against revision-matched vendor data or a measured board.
- The current tie and motor solids are candidate geometry, not verified physical interfaces. The 0.05 mm nominal radial tie clearance and 0.18 mm motor clearance are particularly sensitive to modeling tolerances and print/process variation.
- Clamp strength, screw engagement, retention under vibration, printed PA12 behavior, steel cap details, and harness/service access remain unverified. The isolated check was static; it does not establish pose, load, tolerance-stack, or fabrication suitability.
