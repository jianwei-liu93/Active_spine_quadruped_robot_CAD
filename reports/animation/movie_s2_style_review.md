# Movie S2 presentation style review

## Scope and evidence

This is a visual reference review for presentation styling. I inspected the pre-extracted contact sheet and sampled frames for the local Movie S2 reference, and compared them with the current coordination contact sheet. The supplied reference metadata is 29.3293 s, 1920×1080, 29.97 fps. The sampled images support approximate shot ordering and visual treatment; they do not recover exact edit boundaries or the original motion/timing.

The motion work remains an illustrative kinematic presentation. Retain the verified v2 hip trajectory (69° full hip excursion and 18° hind backswing lag) and its explicit limitations. Do not imply simulated passive loads, physical ground contact, or locomotion dynamics.

## What is visible in the reference

- A black opening card introduces the project and the supplementary movie. The next sampled shot is a warm light-grey/beige studio scene with a large, oblique, full-robot hero view and a soft floor shadow.
- The edit moves from the hero view to a full-robot component breakdown with unobtrusive white labels near the lower edge, then to close views of the spine linkage and servo, a labelled hind-torso/leg mechanism, another tight linkage view, and a low, near-ground whole-body view. The sampled final view is an oblique close hero angle.
- The studio backdrop has a gentle warm-to-neutral gradient and a visible floor/horizon transition. Broad soft lighting gives the dark frames readable faces and makes the silver springs, fasteners, and white spine links stand out. Contact shadows ground the assembly in the detail and whole-body views. Some sampled motion frames show blur; this is a visible stylistic treatment, not evidence about the motion model.
- Labels use short white sans-serif text on translucent charcoal-grey rounded rectangles, with thin white leaders where needed. They identify specific parts without dominating the mechanism.

Approximate sampled positions from the reference contact sheet (not recovered shot cuts):

| Approximate sample | Visible content |
|---|---|
| ~1.5 s | Black title card and institutional marks |
| ~4.5–7.5 s | Warm studio whole-robot hero; then component labels |
| ~10.5–13.5 s | Spine linkage / servo macro views |
| ~16.5–19.5 s | Hind module and spring/cable labels; alternate close angle |
| ~22.5 s | Tight moving linkage detail |
| ~25.5–28.5 s | Low whole-body view, then oblique closing detail |

## Comparison with the current coordination sheet

The current [coordination contact sheet](spine_leg_coordination_contact_sheet.png) already shows that the prescribed spine and all four legs articulate, keeps the complete robot in frame, and states that passive loads are not simulated. Its pale cool-grey background, top-left header, small technical footer, cyan accents, and repeated wide views read as a clean engineering review plate. The sampled robot is relatively small within each panel, and there is little change of scale or camera angle across the sequence.

The reference offers a useful presentation treatment: warmer studio lighting, a larger subject, changing camera distance, macro mechanism shots, and a lower whole-body angle. The current event captions and trajectory annotations are valuable review evidence, but can be reduced or moved to a short opening/closing slate in a polished cut so they do not compete with close-up component labels.

## Recommended treatment for a feasible revision

1. **Use one warm studio set.** Replace the cool flat grey world with a light warm-grey floor and seamless background, with a subtle cream highlight behind the robot. Use a broad soft key and restrained fill so black parts retain edge detail. Add soft contact shadows under the feet and mechanism; keep the existing robot materials and make only modest contrast/roughness adjustments so silver hardware and white links read clearly. Avoid changing geometry or implying that the feet are physically supported by a simulated ground plane.
2. **Vary the camera in a short narrative.** Keep the current motion and trajectory. Reframe the early section as a large three-quarter whole-robot view, then use a spine close-up and a hind-module close-up, followed by a low side/oblique whole-body view and an ending hero angle. Use deliberate cuts or slow camera moves between these views. Preserve toe and mechanism clearance in every crop. The sampled reference suggests this order; its exact cut times are unknown.
3. **Reserve labels for explanatory shots.** Use compact white labels on translucent charcoal-grey rounded tags with thin leaders, matching the reference treatment. Limit each close-up to a few labels, such as spine servo/linkages or hind frame/hip servo/spring/winding wheel. Keep labels outside moving silhouettes and ensure leaders do not cross important joints. Keep the prescribed-motion/kinematic qualification visible in a restrained slate or persistent small caption.
4. **Keep motion treatment restrained.** If adding motion blur or shallow focus, apply it lightly and only as a rendering choice; keep the mechanism legible at key poses. Do not use blur, floor shadows, or camera framing to suggest validated contact, passive response, or forward locomotion.
5. **Separate review data from the cinematic view.** Preserve the current contact sheet as technical evidence. For a reference-inspired presentation cut, remove the repeated slider-like graphic and dense footer from the hero shots; retain concise event information in an opening/closing note or a companion review plate. Continue to identify the animation as prescribed/kinematic.

## Evidence paths

- Reference contact sheet: `reports/animation/previews/movie_s2_reference/contact.png`
- Sampled reference frames: `reports/animation/previews/movie_s2_reference/frame_01.png` through `frame_10.png`
- Current coordination contact sheet: `reports/animation/spine_leg_coordination_contact_sheet.png`
- Current motion visual review and limitations: `reports/animation/spine_leg_coordination_visual_review.json`
- Current scene/render summary: `reports/animation/spine_leg_coordination_scene.json`
