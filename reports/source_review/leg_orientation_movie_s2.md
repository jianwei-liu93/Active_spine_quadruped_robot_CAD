# Leg orientation audit — corrected by labeled Figure E

**CORRECTED / prior opposing-direction claim SUPERSEDED.** Both fore and hind leg chains have the same sagittal zigzag sense in the supplied labeled Figure E: hip-to-knee and ankle-to-toe point forward/down; knee-to-ankle points rearward/down. The prior audit incorrectly converted the shared page orientation into opposite anatomical leg directions. Its hind `(-140°, +100°)` suggestion, hind `−60°` horn-bend suggestion, and instruction to reverse both old chains are withdrawn. The user explicitly confirms the common direction. Keep hind attached to E1/negative X and fore attached to E2/positive X; these torso identities do not require sagittal reversal of a leg.

This amendment inspected the three attachments below directly. It changes this report only; no CAD, pose, native bore, spring or interference verification was performed. Requested reviewer routing remains inherited Sol/high; actual routing is not observable.

## Direct labeled evidence

| Source | Observed labels and geometry | Interpretation |
|---|---|---|
| Annotated Figure E, `/tmp/codex-clipboard-796a3d94-63e3-45c2-b942-39809cc06860.png`, 641×371 | Pelvic torso on image-left; thoracic torso on image-right. Green overlays explicitly trace both hip/knee/ankle/toe chains. | Anatomical front is image-right in this labeled whole-robot view. Both chains share the same sagittal zigzag direction. |
| Movie S2 still, `/tmp/codex-clipboard-4228bc0e-ace5-46d4-b2cf-1e136f95b00f.png`, 1248×704 | “Hind torso with elastic legs” on image-left; “Front torso with elastic legs” on image-right; lumbar mechanism between. | Confirms anatomical identities in this view. Near/far legs and partially hidden pivots make it unsuitable for extracting exact planar joint angles. |
| Main Figure 1A, `/tmp/codex-clipboard-e5f6e8fa-5941-4bf4-afaa-7b7716f1e720.png`, 1140×477 | Hind torso frame/leg servo on image-left, front torso frame/foreleg servo on image-right. Visible three-segment legs differ in proportions and detailed mounting. | Supports the same anatomical assignment, and shows why fore and hind should remain distinct source geometries despite their common directional sense. |

Approximate pixel centers on the **green overlays of Figure E**, with origin at image top-left:

| Leg | H | K | A | F | Ordered directions |
|---|---|---|---|---|---|
| Hind / pelvic | (170,151) | (219,216) | (158,265) | (200,329) | right/down; left/down; right/down |
| Fore / thoracic | (456,152) | (478,206) | (408,235) | (444,343) | right/down; left/down; right/down |

These are visual annotations to identify the chain, not metric measurements. Perspective and torso flexion prevent turning these slopes directly into neutral CAD angles. The supplied Movie S2 still is identified by its attachment rather than an asserted exact timestamp; the previously extracted approximately 7 s view has matching torso labels.

## Retained source observations and corrected interpretation

The original Movie S2 file is `/home/jianwei/freeCAD_projects/active_spine_robot_paper/sciadv.aed5603_movies_s1_to_s14/aed5603_movie_s2.mp4`. During its orbit, the labeled front module changes from image-right in the early whole view to image-left around the 26.5–29 s front-module view. Image +X therefore cannot be treated globally as robot +X. This camera fact remains valid; it does **not** imply reversing the anatomical direction of one leg at assembly.

The earlier S17 inspection (original SI PDF page 38, local render `/tmp/spine-source-review/sm-38.png`) traced both isolated panels in the same image zigzag sense. That is consistent with the corrected common direction when installed as shown by labeled Figure E. The previous extra inference that these panels “must be installed” with opposite world-X directions was incorrect.

S19 identifies the knee as Ok rather than the short spring-lever tip O3. The second ankle pivot A1 is distinct from toe F. Preserve these named bodies when comparing geometry. The local offsets O1 from K and A1 from A lie opposite the thigh/toe vector; neither a cable direction-change point delta5 nor an isolated coordinate arrow establishes anatomical rear. The prior use of that arrow to label image-right as rear was unsupported.

The uncrossed lower coupling remains consistent with a long foot generally parallel to its proximal segment: `alpha_foot = qh`, `qa = −qk`, `kappa = 0`. The source provides no reason here to introduce a π foot flip. Direction correction must preserve the physical loop and attachment identities.

## Candidate consequence and remaining assumptions

The lead reports the updated candidate seeds as hind `(qh,qk)=(-40°,-100°)`, fore `(-50°,-90°)`, with world +X forward and +Z up. Both give thigh/toe forward/down and shank rearward/down. Their unequal angles and unequal link lengths preserve distinct fore/hind geometry. These exact angle values are **DESIGN_ASSUMPTION**, not angles measured from the Figure E overlay or oblique movie.

The lead's current `+60°` horn bends on both legs and torso-local hip offsets hind `−27 mm`, fore `+24 mm` are also candidate implementation assumptions. This source amendment does not certify the bend magnitude, hidden horn keying, hip offset, supplier dimensions, or direct torque interface. Do not revive the superseded opposing-direction seeds when interpreting old screenshots, generated reports, or previously extracted frame notes.

Required lead checks after rebuilding:

1. Save a true side view with +X/front labeled and mark actual native H/K/A/F/O1/A1/O2/O3 centers. Both H→K and A→F must have positive X and negative Z in their neutral torso-local frames; both K→A must have negative X and negative Z.
2. Retain hind/fore torso identity, their different link dimensions, and the hind knee/wheel motor arrangement. Do not swap modules or reflect the Y-side copies into opposite sagittal directions.
3. Recheck actual bore centers, lower-loop branch and horn-offset identities; regenerate length-dependent springs/cables from the corrected geometry before neutral and full-robot sampled interference verification.
4. Keep display-pose source fidelity, prescribed candidate angles, loaded equilibrium and unresolved bought-part interfaces as distinct evidence categories.
