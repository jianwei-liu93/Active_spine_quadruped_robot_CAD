# Bounded paper-motion retarget review

Reviewed 2026-10-13 after two native clearance failures reported by the lead. This is a source/kinematics review, not an independent native clearance execution. No canonical geometry or live application was changed.

## Finding

Keep the approximately 0.6 rad hip half-excursion and the hind backswing event lag of pi/10. The fore/hind anti-phase choice and CAD hip midpoints are reconstruction assumptions and are legitimate retarget variables. A failed assumed trajectory does not yet prove that the source-sized excursion is impossible in this assembly.

The source images inspected were `reports/tmp/pdf_motion_review/control-48.png` (S27), `supp-38.png` (S17), `running-49.png` (S28), and `main-06.png` (main Fig. 3). S27 supports roughly -0.1 to 1.1 rad commanded hip motion, hence approximately 68.75 degrees full excursion; the values are visually estimated, not a numeric command table. S17 draws the hip angle from a downward reference axis. CAD instead measures its thigh direction from +X toward +Z. These references cannot be copied numerically without a datum/sign mapping, and S17 alone does not establish the motor encoder zero used in S27.

S28 shows paired left/right contacts and sequential fore/hind footfalls. It does not identify an exact fore-hip servo phase relative to the hind hip. Main Fig. 3 primarily describes spine/hind-leg coordination. Setting fore phase to either zero or pi therefore remains a DESIGN_ASSUMPTION.

## Kinematic interpretation and next bounded test

`src/leg_geometry_r02.py` explicitly uses the same forward/downward chain convention for both fore and hind legs. Its former opposing-direction interpretation is superseded. The thigh and foot orientations are qh, and the shank orientation is qh+qk. Consequently there is no basis for adding pi merely because one module is a foreleg. The two torso rotations already contribute distinct time-varying world orientations.

Screen fore phase zero as a coherent candidate, keeping the hind waveform unchanged. Also screen midpoint values using the physically explicit family `qh_mean = -90 degrees + delta`, where delta is a declared CAD retarget offset. Means -60, -75 and -90 degrees correspond to delta +30, +15 and 0 degrees. The -90 datum centers the thigh about local downward vertical; it is not a recovered source encoder datum or a prediction that this value clears the hardware. A fore/hind pair may need distinct offsets because its segment lengths and mounting positions differ.

For `qh = mean - A*cos(cycle-lag)`, qh reaches its maximum at `cycle = pi+lag` and then decreases. Around a downward pointing thigh, decreasing qh moves its endpoint backward in the +X-forward CAD convention. This is consistent with defining hind backswing onset at pi+pi/10 when spine extension onset is cycle pi. Adding a constant midpoint preserves this event and the excursion.

The current adapter uses the same signal for hip and knee. Changing fore phase also changes fore knee phase; label this as a fore-leg prescribed phase change rather than a pure hip-phase experiment. The knee trajectory remains independently prescribed, not a spring-response solution. World foot contact timing cannot be inferred from hip phase alone because torso pitch, knee angle, foot shape and whole-body motion also matter.

## Acceptance and blocker boundary

Retain actual clip/cap and foot collisions as failures; do not enlarge exceptions, remove geometry or change native dimensions to clear a visualization. The reported failures at old means (-50/-40 degrees) and common -60 degrees with fore phase pi invalidate those sampled trajectories only. A candidate must pass the lead's exact native checks against all relevant leg/torso and inter-leg pairs, including its endpoints and neighborhoods of observed failures. Finite samples remain bounded evidence, not continuous clearance certification.

If the declared offset/phase family cannot accommodate the full excursion, report the actual named interference and pose as the blocker to this prescribed source-informed trajectory. Geometry changes would be a separate mechanical redesign; an untested smaller excursion or hidden collision is not an acceptable substitute for the requested result. A successful screened trajectory can be described as source-informed retargeted motion, with assumed fore phase, CAD datum, passive knees and presentation speed stated explicitly; it cannot be described as reproduction of the paper's loaded gait.
