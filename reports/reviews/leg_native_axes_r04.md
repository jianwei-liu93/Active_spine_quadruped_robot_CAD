# r04 actual-native leg axes and orientation

**PASS for the bounded neutral geometry audit.** Actual cylindrical shaft surfaces confirm that both fore and hind legs have H→K forward/down, K→A rearward/down, and A→F forward/down. Left/right copies have identical sagittal H/K/A/F coordinates. The measured shaft axes coincide with the inspected native bores, bearing inner axes and torso H support axes. This is actual saved BRep evidence, not a conclusion drawn solely from MotionMap or source placement formulas.

Evidence: `reports/verification/r04_leg_native_axes.json`. Reproducible read-only implementation: `src/audit_leg_axes_r04.py`, API `audit(doc, output=None)`; `main()` opens/closes the saved r04 file without recomputing, changing or saving it. Requested inherited routing: Sol/high; actual model routing is not observable. No live MCP or canonical changes were made.

## Native snapshot and measurements

- Saved `cad/flexor_r04_robot.FCStd`: 5,088,359 bytes, SHA256 `29183261bb91720b5b6a82e6ff0646ebc38f233481f632860644da2028659d9d`.
- Isolated installed FreeCADCmd: FreeCAD 27.1.0 dev, Git revision 49159 / `e5fabddebb0dc54ecf324cedddd26e053e2a8488`.
- Assembly: 431 App::Link instances. Audit inspected actual geometry of 62 relevant instances and completed **315 checks**, with no failed check or error.
- Position/coaxial tolerance: 1e-6 mm. Maximum measured coordinate/coaxial error: **2.01e-14 mm**.
- Axis direction tolerance: transverse unit component ≤1e-9 relative to Y. Maximum measured component: **4.58e-16**.

The audit finds actual `Part.Cylinder` faces on world `o.Shape`. Main journal surfaces have radius 0.95 mm; their axis centers/axis directions identify H, K and A. Split cylindrical faces after grooves must lie on the same Y axis. Surface-center Y is an arbitrary coordinate along that axis, not a joint's axial stack datum. For example, native hindL H has cylinder axis point `(-60, 52.85, 0)` and hindL K `(-37.78471115, 47.65, -18.64084068)`.

Expected neutral coordinates come from `leg_geometry(kind)` plus independently checked native E-family ground axes, hind E=(-33,0) and fore E=(33,0). Saved spine phase is zero, and recorded leg angles match the current candidate seeds: hind (-40°,-100°), fore (-50°,-90°). These seeds, hip offsets and detailed dimensions remain candidate reconstruction assumptions.

| Leg family; both Y copies | Native H (X,Z) mm | Native K (X,Z) mm | Native A (X,Z) mm | Native F (X,Z) mm |
|---|---|---|---|---|
| Hind | (-60.000000, 0) | (-37.784711, -18.640841) | (-60.766044, -37.924469) | (-37.018667, -57.850885) |
| Fore | (57.000000, 0) | (71.141327, -16.852978) | (52.756261, -32.279880) | (74.611040, -58.325391) |

| Leg family | Native H→K (ΔX,ΔZ) mm | Native K→A (ΔX,ΔZ) mm | Native A→F (ΔX,ΔZ) mm | Native lengths H–K / K–A / A–F |
|---|---|---|---|---|
| Hind | (+22.215289, -18.640841) | (-22.981333, -19.283628) | (+23.747378, -19.926416) | 29 / 30 / 31 mm |
| Fore | (+14.141327, -16.852978) | (-18.385067, -15.426903) | (+21.854779, -26.045511) | 22 / 24 / 34 mm |

F uses the actual `hindR_FootPad`, `hindL_FootPad`, `foreR_FootPad` and `foreL_FootPad` LinkPlacement origins. Each is independently corroborated by its native radius-3 cylindrical contact-cup surface axis. This establishes the intended foot reference/contact-cup center, rather than a loaded ground-contact point on the rubber surface.

## Coaxial geometry checked

For every leg, native cylindrical surfaces were extracted from:

- H/K/A journals, all radius 0.95 mm, without assuming a `SourceName` property exists.
- H keyed curved bores on thigh and input horn, radius 1.025 mm. The D-profile's curved portion supplies its center axis; the flat's angular engagement is outside this audit.
- K bearing seats on thigh and shank, and A bearing seats on shank and curved Foot, radius 2.025 mm.
- The torso cage's H support bores, radius 2.025 mm, including its axially separated supporting faces.
- Every instantiated H/K/A bearing's radius-1 inner cylindrical surface.

Matching uses actual radius and nearest native cylinder axis to the measured shaft, with the resulting offset checked against tolerance. The JSON retains instance names, linked source names, cylinder face indices, centers, directions and errors. Source names are provenance only; the actual measurement comes from world surfaces. E-family native output journals were also measured against the ±33 mm neutral ground contract.

Source compilation and isolated native execution passed. A first run completed 313 checks; the final run added explicit left/right sagittal equality checks and summary metrics, producing the saved 315-check report. The transient runner is `reports/tmp/run_leg_native_axes_r04.py` and calls `main()` unconditionally for FreeCADCmd's execution context.

## Limits

This settles neutral native axis positions and the corrected common sagittal orientation. It does not verify running fits, bearing-race clamp paths, pin retention, key-flat angle/contact, source supplier splines, spring/cable behavior, strength or loaded equilibrium. No gait sweep, collision sweep or final assembly/fabrication approval was performed here. The lead's separately reported 25-pose spine collision result is not rerun or promoted by this audit. Prior opposing fore/hind orientation recommendations remain superseded.
