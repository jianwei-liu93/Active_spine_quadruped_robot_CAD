# r10 center-pin sampled assembly-access audit

**Result: PASS_SAMPLED_PIN_SEQUENCE_ONLY.** Both E1 and E2 center pins have a nominal axial insertion sequence from either world-Y side at the sampled stations, provided the entry-side outer journal and its two retainers are deferred, along with both center retainers. This resolves the pin-path portion of R10-IR-02 for that declared initial assembly order. Elastic clip installation, tool/service access, fits, thrust retention, alignment and strength remain unresolved.

## Actual execution and artifact binding

One isolated installed `/snap/bin/freecad.cmd` process read the frozen native file. It copied actual `App::Link.Shape` world solids and translated only copies of the two actual grooved center pins. No second link transform, document placement assignment, recompute, source change, native save or export occurred. The audit used all 487 physical instances and retained structural bodies, cables, bearings and spacers in the minimum-exclusion scenario.

Native SHA-256 before/after and independent postprocess check: `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`.

Audit JSON SHA-256: `5a23d7fc1a4aa1bc22858fb08344b04af3a24a028c2112557db7830a4e74c56a`.

Driver SHA-256: `4836377283d3cd32959566e844bd588b8e63e89041e84d858d108d1f1074ee5e`. Log SHA-256: `8c344b1a11bc026374d485f0f2daae855d32142650ddf5b5b0672bc50a346fc9`.

Runtime: 51.254 s; actual OCC common operations: 340. Each of four paths used 24 stations, 96 total, from outside the entire assembly to the saved seated position. AABB overlap with 1e−7 mm threshold selected actual OCC common checks; positive intersections above 1e−5 mm³ were reported. Every raw hit, station coordinate, volume and stage exclusion is retained in the JSON.

## Exact minimum tested exclusion lists

The target center pin is omitted from the obstacle set because its copy is the moving test solid. Its two center retainers are deferred until after insertion. Only the entry-side outer pin and its two retainers are additionally deferred; the opposite outer E hardware remains included. All four minimum-exclusion paths have zero above-threshold hits at the declared stations.

| Joint / entry side | Exact obstacle exclusions | Saved-stage blocking instances |
|---|---|---|
| E1 / −Y | `CentralE1_Pin`, `CentralE1_Retainer0`, `CentralE1_Retainer1`, `E1__1_Pin`, `E1__1_Retainer0`, `E1__1_Retainer1` | `CentralE1_Retainer0`, `E1__1_Pin`, `E1__1_Retainer0`, `E1__1_Retainer1` |
| E1 / +Y | `CentralE1_Pin`, `CentralE1_Retainer0`, `CentralE1_Retainer1`, `E1_1_Pin`, `E1_1_Retainer0`, `E1_1_Retainer1` | `CentralE1_Retainer1`, `E1_1_Pin`, `E1_1_Retainer0`, `E1_1_Retainer1` |
| E2 / −Y | `CentralE2_Pin`, `CentralE2_Retainer0`, `CentralE2_Retainer1`, `E2__1_Pin`, `E2__1_Retainer0`, `E2__1_Retainer1` | `CentralE2_Retainer0`, `E2__1_Pin`, `E2__1_Retainer0`, `E2__1_Retainer1` |
| E2 / +Y | `CentralE2_Pin`, `CentralE2_Retainer0`, `CentralE2_Retainer1`, `E2_1_Pin`, `E2_1_Retainer0`, `E2_1_Retainer1` | `CentralE2_Retainer1`, `E2_1_Pin`, `E2_1_Retainer0`, `E2_1_Retainer1` |

The JSON also contains each entry-side eight-instance outer capture inventory with actual source identities and world bounds: journal, two outer bearings, two retainers, spacer, torso bearing and torso spacer. Removing that entire stack was evaluated as an additional scenario but is unnecessary for the demonstrated minimum-exclusion pin path. This audit does not prove removal of a press-fitted bearing or qualify maintenance disassembly.

## Explicit initial assembly order

1. At the saved neutral pose, support/align the torso and center lug with the center bearings and washers in their modeled locations; no fixture or hand/tool access qualification is claimed.
2. Defer both center retainers. On the chosen entry side, leave the existing outer E journal and its two retaining clips uninstalled; the opposite outer E stack may remain installed. Bearings and spacers need not be removed in the tested minimum-exclusion stage.
3. Translate the actual center pin along world Y from outside the whole assembly to its saved seated position. Each joint was tested from both sides at 24 travel stations.
4. Install the center retainers using a separately resolved elastic installation method; this operation and tool/service access are not established by the pin-path audit.
5. Install/retain the deferred entry-side outer E journal and its capture clips using the existing assembly procedure; their installation path and elastic clip behavior were not audited here.

## Remaining limitations

With outer journals already installed, both insertion directions fail at sampled stations. The center retainer on the entry side also obstructs passage if left installed; the seated pin clears its ring only after its groove reaches the intended axial location. These are measured solid intersections, not a visual inference.

The audit samples 24 positions per path. It does not certify a continuous swept path, a minimum clearance, access at other spine poses, fingers/fixtures/tools, or in-place maintenance. It does not model elastic opening of any split clip, installed clip strain or retention capacity. Nominal bearing/spacer bore clearance does not select real supplier fits or establish race-specific axial restraint. No full robot motion, candidate package or fabrication-release PASS is claimed.
