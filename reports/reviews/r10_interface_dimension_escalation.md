# r10 critical-interface native dimension escalation

Bounded isolated CLI work; no live MCP, canonical assembly, source geometry or schema writes.

The earlier true-3D Diameter attempt returned 0.0 mm. The second projected-view attempt stopped at an unnecessarily restrictive full-circle guard. Both original logs remain under reports/tmp/r10_drawings.

The escalation tested the actual projected circular arc at API Edge13, corresponding to the fore clevis source Edge129. Native Diameter measured exactly 2.0 mm with Arbitrary=False. Diameter accepts a circular arc; a full-circle guard is not applicable here. The probe evidence is interface_arc_probe.json.

The implementation resolves source circles by actual radius, center and axis, then matches the native projected circle using getEdgeByIndex. It never relies on visible-list ordering or nominal dimension text. Every native value is required to agree within 1e-6 mm.

Ten auxiliary interface sheets each contain one source-associated view and one diameter dimension: fore/hind clevis 2.0; lumbar E1/E2 bores 2.2 and seats 4.05; central pin OD 1.9 and groove root 1.6; split retainer OD 3.6 and ID 1.6 mm. Their view footprint is bounded to 140 × 70 mm with the dimension label outside it. Final GUI typography, rendered overlap inspection and PDF/SVG export remain lead-owned and NOT_RUN.

Run result: PASS. Saved and reopened all 77 sheets / 321 native dimensions, including ten added interface diameters. All retained native values matched within 1e-6 mm and Arbitrary=False. Native Body volume, area and edge counts remained equal before construction and after reopening. See reports/tmp/r10_drawings/interface_expand.json.
