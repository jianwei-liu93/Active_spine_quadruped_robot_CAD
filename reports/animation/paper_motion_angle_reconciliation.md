# Paper-informed coordination revision

The user rejected the original small leg excursion and the proposed 10-degree revision. The replacement uses the source figures rather than treating the old demonstration bounds as physical joint limits.

## Evidence and mapping

- Main paper p7 defines phase lag as the delay between onset of spinal extension and hind-leg backswing; the chosen optimum is pi/10. Its p9 describes paired synchronized forelegs and paired synchronized hind legs in an adapted bounding gait.
- Supplement p48, Fig S27, shows a dashed hip command approximately -0.1 to 1.1 rad, hence about 1.2 rad (68.8 degrees) full excursion. These are plot readings, not an exact numeric control table. The replacement uses a 0.6-rad half excursion. The approximately 0.5-rad encoder midpoint is not applied as a CAD anatomical angle.
- Supplement p37, Fig S16, gives 0.42..0.84 rad hip amplitudes for the unified-model sweep. That is a separate experiment and is not substituted for the S27 prototype command.
- Supplement p38, Fig S17, distinguishes hip/knee geometric frames. Fig3's theta_mk denotes a knee-actuation coordinate; it must not be applied directly to the geometric knee or confused with a loaded knee angle.
- Supplement p49, Fig S28, shows sequential fore/hind contacts. Footfall sequence does not recover a numeric fore/hind hip servo phase. The former pi offset was rejected during native collision checks; the revised same-phase signals remain an explicit assumption in the existing same-direction leg coordinates.

The revised animation uses CAD hip midpoints of -60 degrees (fore) and -75 degrees (hind), equivalently -90 degrees plus +30/+15-degree offsets from downward vertical. The original -50/-40-degree means produced clip/cap contact under the larger excursion. The second -60/-60-degree candidate with opposed fore phase still produced clip/cap and fore/hind foot intersections. Both rejected native cases and the all-frame observed-pair failure are preserved in the named `*_fail.json` reports. The full source-inspired excursion is retained. The selected same-phase candidate cleared the observed rigid pairs at 60 coarse phases, with 4.292 mm minimum separation, then all 300 render-cycle phases with zero intersection. Whole leg/tendon-versus-assembly native checks at nine critical phases are recorded separately. This is bounded visualization screening, not continuous clearance or hardware qualification.

The zero calibration and fore phase are explicit retargeting assumptions because the paper encoder-to-CAD datum and exact foreleg command phase are unavailable. The fore phase change also changes its separately prescribed knee signal; it is not presented as a pure hip-phase experiment. Native CAD geometry and the saved neutral pose are unchanged. Paper-to-CAD hip sign is reversed: increasing source angle from the downward vertical describes a posterior swing, whereas increasing CAD thigh angle advances the thigh toward +X. Therefore qh = qh_mid - 0.6*cos(cycle_phase - lag + fore_offset). Left/right legs of each pair share this phase.

The exact linkage solver locates maximum extension at crank 60.986993 degrees: this maximizes the fore-minus-hind torso orientation. Maximum flexion and the next onset of extension occur half a cycle later. Start the animation at this maximum extension. Hind backswing starts at cycle phase pi + pi/10, when CAD qh begins decreasing from its forward extreme. This measures an 18-degree event delay rather than adding pi/10 blindly to every waveform.

At 0.2-Hz presentation speed the event delay is 0.25 seconds. S27's 3.5-Hz trial is shown 17.5 times slower in the visualization. No running speed, contact, stability or force prediction is made.

## Unresolved inputs and physical checks

Exact foreleg servo phase, motor-zero calibration and passive knee trajectories are unavailable as numeric source data. Four knees retain explicitly prescribed +/-10-degree states, with dependent ankles supplied by the existing closed leg geometry. The common winding wheel retains its route-supported 0..90-degree interval as an independent prescribed command. Knee motion is not inferred from wheel rotation or shown as a loaded equilibrium solution.

The larger hip trajectory exceeds the historical +/-15-degree demonstration intervals. Those intervals were screening bounds, not manufacturer hard stops. The new adapter disables that candidate-only check privately during read-only export, while preserving all geometry, closure, spring and guide checks. Bounded native leg/tendon-versus-assembly interference screening is recorded separately; the old full clearance campaign is not claimed for this new path.

The original release remains recoverable in Git; the original coordinated editable scene is archived locally. Canonical CAD remains unchanged. The versioned profile is `animation/coordination_paper_profile_v2.json`; the actual sampling adapter is `src/animation_coordination_v2.py`. A Sol/medium source-review worker supplied partial matching observations but then encountered model capacity; the lead completed this reconciliation and inspected the source pages directly.

An Astra/low independent review is recorded in `paper_gait_feasibility_review.md`; it identified that existing leg coordinates already share the same forward/down convention and did not justify an opposing fore phase. This was reviewed before selecting the candidate.

## Executed v2 evidence

- `production_coordination_v2.json`: 1,201 serialized states, 487 physical instances, loop matrix residual 2.49e-14 and maximum anchor residual 3.36e-14 mm. Sampling leaves the source document and canonical CAD unchanged.
- `coordination_v2_clearance.json`: all leg/tendon-versus-assembly pairs screened at cycle phases 0, 18, 90, 135, 180, 198, 240, 270 and 330 degrees; 5,184 exact native Boolean checks, no positive-volume intersections or guide warnings. Scope is finite sampled poses.
- `coordination_v2_observed_pairs_300.json`: 12 named clip/cap and fore/hind foot pairs checked at every render-cycle frame, no positive-volume intersections.
- `coordination_v2_events.json`: measured extension onset at cycle sample 150 and hind backswing onset at 165, an 18-degree / 0.25-second presentation delay; all four hip excursions 68.754935 degrees.
- `leg_articulation_v2.json`: the reopened Blender scene matches the exported torso-relative thigh/shank rotations and foot-pad positions at all 300 cycle frames.
- `procedural_surface_comparison_v2.json`: eight spring records at the two prescribed leg extrema pass the existing 0.05-mm finite surface-probe tolerance, worst measured error 0.02851 mm. Two cable records measure native route reconstruction only; dashed guides do not assert physical slack or solid coverage.

The first complete v2 render was rejected during decoded review because larger leg excursions caused toe cropping in oblique shots. `coordination_v2_framing_rejected.json` preserves that diagnostic. Presentation-only camera widening and recentering then passed `coordination_v2_framing.json` at all 1,200 frames using evaluated physical-instance bounds; native geometry and motion exports were not altered.
