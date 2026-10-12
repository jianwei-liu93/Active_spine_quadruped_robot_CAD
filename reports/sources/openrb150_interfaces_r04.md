# ROBOTIS OpenRB-150 interface evidence

**Status: PARTIAL / CAD interface unresolved.** This report records evidence for the OpenRB-150 controller candidate cited by [01_reference_evidence.md](../../docs/01_reference_evidence.md) and the controller row in [04_components_and_manufacturing.md](../../docs/04_components_and_manufacturing.md). No CAD, FreeCAD document, purchase, or hardware inspection was performed.

## Verified facts

| Interface item | Verified information | Evidence / limit |
|---|---|---|
| Product identity | ROBOTIS OpenRB-150 embedded controller. | [R1] official e-Manual. Product name only; no hardware revision identifier is stated in the consulted material. |
| Nominal board envelope | 25 × 66 mm (width × length as presented by the manual). | [R1], Specifications > Board Dimensions. Board thickness and whether this is bare PCB edge or full protruding assembly are not defined in the text. Treat this only as the published board dimension, not an enclosure/keepout envelope. |
| Main host connector | USB Type-C receptacle is documented for connecting to the PC/power. | [R1], Connecting Power > USB C. Connector body, shell protrusion, insertion direction, plug envelope, and position on board are not dimensioned in accessible text. |
| DYNAMIXEL interfaces | Four dedicated TTL DYNAMIXEL ports; manual links the TTL connector type pinout/include. | [R1], Overview, Specifications, and DYNAMIXEL Ports. Connector body/plug dimensions, exact centers and cable exit directions are unknown. Do not confuse communication compatibility with the physical connector envelope. |
| Other power interfaces | Included terminal block for VIN; optional right-angle XT60 can be assembled on the rear after removing the terminal block; VIN/USB source jumper is present. | [R1], Terminal VIN, XT60 Connector, and Power Source Jumper. The manual gives no measured locations/heights or XT60 variant drawing for this board. The terminal-block and XT60 arrangements are alternatives, not simultaneous installed hardware. |
| Mounting form-factor statement | Manual says the controller has the same pinout and form factor as Arduino MKR for accessory compatibility. | [R1], Overview. This is not sufficient evidence for OpenRB hole centers, hole diameters, copper keepouts, PCB thickness, or populated-part clearance. Do not derive hole coordinates from a photograph or generic MKR data. |
| Official drawings/models offered | e-Manual download section lists OpenRB-150 2D Drawing (PDF, DWG) and 3D Modeling (STL, STEP). Official download links resolve to ROBOTIS `download.php?no=2120` (PDF drawing) and `download.php?no=2121` (STEP model) in this access session. | [R1] download list; [R2] and [R3] official download splash pages. The linked files themselves were not obtained or inspected, so no dimensions are extracted from them here. |
| Revision/source date | The e-Manual notes the 5 V regulator was updated as of 2024 and supplies changed from 300 mA to 150 mA. The accessible manual and download page do not identify which PCB revision the linked model/drawing depicts or provide a drawing revision/date. | [R1]. This regulator note is not proof of a mechanical change or drawing revision. Freeze exact hardware revision against the physical purchase/marking before release. |
| Paper evidence | FLEXOR supplementary Table S1 reports OpenRB-150 and 5 V. | [P]/[S] registry in `docs/01_reference_evidence.md`. This is the paper's controller/voltage statement; it provides no mounting, connector, wiring, or battery interface geometry. |

## Unresolved geometry

| Required datum | Status | Reason |
|---|---|---|
| Mounting-hole count, centers, pitch, diameter, slot shape, edge offsets, and permitted fastener/head geometry | `UNKNOWN` | The official 2D PDF/DWG links were exposed but inaccessible as files in this run. The prose manual does not dimension these features. |
| PCB thickness, board-edge profile/corner radii, underside components and keepouts | `UNKNOWN` | Not dimensioned in accessible source text. |
| USB receptacle exact location, body/plug envelope, mating approach and cable bend keepout | `UNKNOWN` | Connector type is documented; location and dimensions require the actual drawing/model. |
| Four TTL port locations, physical connector variant/body size, mating plug envelope, cable exit and bend keepouts | `UNKNOWN` | Port count/type documentation does not establish mechanical geometry. |
| Terminal block installed envelope and wiring insertion/access; XT60 variant, position and cable keepout | `UNKNOWN` | Optional interfaces are documented but no dimensional model/drawing was retrieved. |
| Reset switch/button, DYNAMIXEL power switch, jumper, LEDs, and component access volumes | `UNKNOWN` | Controls/status indicators are identified by the manual but not mechanically dimensioned in accessible text. |
| Model/drawing revision and correspondence to purchased board revision | `UNKNOWN` | No revision identifier is exposed on the e-Manual download listing or splash pages. |

## Packaging recommendation (provisional only)

A **published board-only reference rectangle of 25 × 66 mm** may be used to reserve a placeholder area, with provenance `MANUFACTURER_VERIFIED` limited strictly to the e-Manual board-dimension statement. Mark board thickness, full populated envelope, all mounting geometry, connector locations, insertion directions, cable bend radius, and service access as `UNKNOWN`; do not create guessed holes or exact keepout solids.

Before freezing the controller mount, acquire the actual ROBOTIS OpenRB-150 PDF/DWG and STEP/STL files and record their revision/date/hash. Verify drawing dimensions against the model, especially mounting pattern, PCB outline/thickness, underside components, USB access, each DYNAMIXEL plug, and the selected power-input arrangement. If the official file cannot be acquired, inspect a physical board and record measured values as `DESIGN_ASSUMPTION` until confirmed against ROBOTIS documentation. For any drawing, distinguish the installed terminal block from the alternate right-angle XT60 arrangement.

This is not a complete packaging envelope and is not suitable for releasing a controller carrier for fabrication.

## Sources and provenance

- **[R1] ROBOTIS e-Manual, OpenRB-150:** <https://emanual.robotis.com/docs/en/parts/controller/openrb-150/> (official manufacturer documentation; consulted 2026-10-12). Relevant headings: Overview, Specifications, Terminal VIN, XT60 Connector, DYNAMIXEL Ports, Connecting Power, Downloads.
- **[R2] ROBOTIS 2D drawing PDF download landing page:** <https://www.robotis.com/service/download.php?no=2120> (official ROBOTIS endpoint; landing page says download will start shortly; file not retrieved).
- **[R3] ROBOTIS STEP download landing page:** <https://www.robotis.com/service/download.php?no=2121> (official ROBOTIS endpoint; landing page says download will start shortly; file not retrieved).
- **[R4] ROBOTIS download center, Controller section:** <https://en.robotis.com/service/downloadpage.php?ca_id=7080> (official source lists OpenRB-150 STEP, PDF, and DWG options; does not identify a revision in accessible text).
- **Project evidence:** [01_reference_evidence.md](../../docs/01_reference_evidence.md), controller/power row and source registry; [04_components_and_manufacturing.md](../../docs/04_components_and_manufacturing.md), controller candidate row and release requirement.

### Retrieval note

Actual artifact attempts for the missing mechanical drawing/model were blocked: the ROBOTIS download endpoint returned only a “download will start shortly” landing page in the web reader, and a direct `curl -L` retrieval failed because host resolution was unavailable. A subsequent direct web-open of the same endpoint also reported it inaccessible. Consequently, no vendor file was added under `vendor/OpenRB150/`, and there are no file hashes or extracted drawing dimensions to report. The official OpenRB board-manager repository was not used as mechanical evidence; its public README identifies it as the board-manager software repository (Apache-2.0), not the controller mechanical-source package.
