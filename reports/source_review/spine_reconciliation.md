# Spine source visual reconciliation

Reviewed 2026-10-11 against the original local paper and supplement. **r01 has the correct abstract link graph, but its guide/output geometry and physical packaging differ substantially from the illustrated source.** This is a source review only; no FreeCAD inspection, CAD modification, clearance certification, or fabrication release was performed. Requested routing: Sol/high; actual model/effort routing is not independently observable.

## Sources actually inspected

- Main paper, printed/PDF p. 3 Fig. 1 (whole robot and torso segmentation), p. 5 Fig. 2 (spine architecture and end poses); nearby text pp. 4 and 16.
- Supplement PDF p. 30 Fig. S9 (both complete panels), pp. 38-40 Figs. S17-S19 (leg/cable arrangements), p. 65 Table S1. Relevant kinematic/fabrication text pp. 7-13 and 16-17 was also read.
- Local originals: `active_spine_robot_paper/2026_Unlocking fast robotic locomotor propulsion throughdynamic spine-leg synergy.pdf` and the corresponding `_sm.pdf`, outside this repository. Rendered with system `/usr/bin/pdftoppm`; temporary images remain in `/tmp/spine-source-review/`. No paper images or PDFs were added to the repository. Movies were present but were not reviewed in this bounded task.

## Required geometric corrections

Use the source sketch's horizontal X and vertical Y as planar CAD X and Z for the following statements; assigning anatomical front/rear and motor phase requires a separate explicit map.

| Item | Original source evidence | Consequence for r01 |
|---|---|---|
| Guide heights | S9 places C1 on an upper horizontal guide and C2 on a lower horizontal guide. E1, O, E2 share the middle horizontal line. C1 is approximately level with A1 and C2 with A2. | Replace the coincident `guide_z_mm=0` construction with separate nonzero, opposite-height guide datums. An initial magnitude near 8-9 mm is visually supported, but is not a reported dimension. |
| Output branch 1 | In S9A/B, D1 lies above E1; its short C1-D1 connector sits at the upper guide. | r01 at theta=0 has D1=(-38.926,-16.944) mm and E1=(-45,0) mm: the rocker points below its pivot. Select the upper assembled branch. |
| Output branch 2 | D2 lies below E2; its short C2-D2 connector sits at the lower guide. | r01 at theta=0 has D2=(43.925,17.968) mm and E2=(45,0) mm: the rocker points above its pivot. Select the lower assembled branch. |
| Crank-rocker branches | S9 has B1 above and B2 below the middle line, with independently hinged G0-B1 and G0-B2 rods. | Preserve that separation and independence. r01's theta=0 B1/B2 sides agree qualitatively. |
| Output proportions | C-D is a short connector; E-D is a longer, nearly vertical end rocker. | r01 L5=25 mm and L6=18 mm reverse this source proportion and create a much larger output-stage triangle. HE=45 mm also spreads the fixed outputs farther apart. |
| Drive | Main Fig. 1/2 shows a central servo/horn crank arrangement. Supplement pp. 16-17 explicitly screws a metal printed crank to the spine servo horn. | The r01 external 22-tooth spur stage is an engineering deviation, not a recovered source feature. A source-faithful revision should restore direct horn-to-crank actuation with real horn mounting geometry. |
| Frame and synchronization | Fig. 1A/2A shows a compact, open, shaped lumbar structure with integrated upper/lower sliding slots and thin transverse members between opposite linkages. Fabrication text specifies integrated servo slots/joint holes and metal synchronization shafts. | Replace the wide layered deck, tall walls and gear-supported packaging with a compact frame organized around the actual servo, guide and hinge datums. Keep real separate links and lateral stacks, but avoid using large platform spacing to solve joint layering. |

For the current `circles(C,E,...)` candidate ordering, `D_branch=1` reverses both r01 output-side errors at its theta=0 seed. This index is implementation-dependent: the revised seed must instead be checked by D1 above E1 and D2 below E2 and then continued through the cycle. A branch index alone is not a source certificate.

## Provisional dimensions from the sketch

The S9 drawing is a kinematic illustration, not a fabrication drawing. Approximate center picking in both panels gives the following reconstruction seeds. These must remain `DESIGN_ASSUMPTION` with a visual-estimate source, even where scaled from a paper-reported length.

| Quantity | Visual estimate | Basis and limitation |
|---|---|---|
| Guide magnitude h | roughly 8-9 mm | Guide centers align approximately with A1/A2; their height relative to O is about Hy. |
| HE=abs(E1.x)=abs(E2.x) | roughly 32-34 mm | O-E is about 1.1 times the horizontal O-A offset Hx=30 mm. |
| L5=L10 | roughly 5-7 mm | Short C-D connector is about 0.17-0.22 Hx. Very short center distances make this estimate sensitive to center picking. |
| L6=L11 | roughly 9-11 mm | E-D rocker is about one-third Hx. |

As a reproducibility check, S9B center picks in a crop at original 2400-pixel page height gave O≈(1094,382), A1≈(1317,316), E1≈(851,382), C1≈(893,318), D1≈(854,307). The crop origin was (120,120) pixels in the full page render. Hx gives approximately 7.43 pixels/mm; Hy and L4 give approximately 7.62 and 7.46 pixels/mm. These mutually similar scale estimates support the coarse ranges, without making the illustration dimensionally authoritative. S9A independently gives the same approximate short-connector/longer-rocker proportions.

The guide height is a specific source ambiguity: S4/S7 are consistent with the visually aligned guide/A heights under one interpretation, but the supplement separately defines h and S30 uses Hy-h. Therefore h=Hy=8.66 mm is a reasonable initial assumption, not a proven equality or `PAPER_REPORTED` value. Preserve that discrepancy while solving the actual linkage.

The optimization vector explicitly reports [Hx,Hy,L1,L2,L3,L4]=[30,8.66,5,30,24.1215,45.7876] mm and a 9.29-degree maximum output error (supplement p. 13). It does **not** report numerical L5, L6 or HE. L5/L6/HE should be fitted together to the illustrated assembled branch and output range, then assessed for closure and physical packaging. Neither the 120-degree total spinal bending range in main p. 4 nor the complementary end angles in Fig. 2 uniquely determines those missing dimensions.

## Physical layout and boundaries of visual evidence

The supplement reports a 1.9 mm diameter, 8 mm long protruding crank drive pin and bearings with 2 mm ID/4 mm OD. These are `PAPER_REPORTED` dimensions. They do not establish the diameter of every transverse synchronization shaft, bearing width, running fit, horn pattern or clamp geometry. The shaft-count wording describes three such metal shafts on each side; it does not by itself provide an unambiguous joint-by-joint global shaft BOM. Recover that map from a revision-specific mechanism layout before detailing retention.

Upper/lower slider interfaces are rounded rectangular copper rings on the inner and outer sides of the frame's sliding joints, with bearings and minimal clearance (supplement pp. 16-17). The source supports a compact captured slot arrangement; it gives no numeric running clearance, slot profile, end-stop reserve or bearing stack width. These must be designed and checked rather than measured from line thickness or rendered gaps.

Figs. S17-S19 support compact direct shoulder/hip horn mounts, three-segment legs, distinct tension/compression springs, and the common hind-knee winding wheel/cable path. S19 routes the active cable through two changes in direction before its leg attachment; the visible central winding wheel is not a spine transmission gear. Keep those hind-torso cable volumes in the packaging check.

Table S1 reports the whole-robot envelope 110 mm length, 99 mm width, 84 mm height and 338 g. The 99 mm width includes the complete robot and does not authorize a 99 mm lumbar platform or determine the spacing between linkage planes. The illustrated organic frame contours, thin link profiles, shaft spans and servo orientation can constrain a visual reconstruction; exact frame wall thicknesses, tool access, material clearances, connector reserves and fastening stacks remain engineering choices.

Only this report was authored. No shared parameters, source modules or CAD files were changed.
