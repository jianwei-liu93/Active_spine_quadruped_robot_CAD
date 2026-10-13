# Movie S2-inspired coordination presentation

Status: scene and fresh-process verification PASS; full video rendering in progress.

The source movie was inspected through sampled whole-robot, spine and hind-leg frames. The new cut uses a warm studio floor, soft shadows, graphite frames, light spine links, metallic springs and small white labels on charcoal backgrounds. Its shot order is overview (0–6 s), spine (6–12 s), hind mechanism (12–18 s), fore mechanism (18–22 s), and overview (22–25 s). Detail shots deliberately crop unrelated modules and may crop toe tips; the declared mechanism targets remain in frame. Overview shots retain every physical instance.

The user explicitly authorized illustrative whole-body motion. Every physical component remains under one rigid presentation root; `render_world = presentation_root @ verified_CAD_world`. CAD geometry, six commanded coordinates, separately prescribed knees, spine closure, redundant motor coupling, springs and cable shapes are preserved. No source component is independently moved for appearance.

The display uses every third sample of the verified 300-state cycle: 100 exact solver states per cycle at 60 fps, hence 0.6 Hz. It retains the approximately 69-degree full hip excursion and the 18-degree extension-to-hind-backswing event lag. The faster display changes timing, not the geometric path. Integer rendered frames consume existing exact samples; unverified subframe retiming/motion blur is disabled.

The added root has a prescribed +/-3-degree pitch and +/-8-mm fore-aft oscillation. Its vertical position follows the lowest rendered toe/foot surface plus an 0.8-mm minimum floor margin and a nonnegative prescribed flight gap of up to 25 mm. These are presentation assumptions, not recovered experimental motion. Feet can slide; no support forces, contact equilibrium, stability or locomotion speed is claimed. A persistent caption states “ILLUSTRATIVE KINEMATICS | Prescribed body motion; no dynamics.”

The new scene is `animation/scenes/spine_leg_coordination_s2.blend`; the new output will be `animation/output/spine_leg_coordination_s2.mp4`. The prior technical coordination video and its QA remain intact. The new scene is standalone and uses baked channels and shape keys, with no playback handlers or FreeCAD dependency.

Reproduce by first building the verified technical scene as described in `animation/README.md`. In the installed Blender MCP, import `build_coordination_s2` from `animation/blender` and call `build()`. Package with `package_scene.py -- spine_leg_coordination_s2`, then run `verify_coordination_s2.py` in a fresh Blender process. After preview inspection, `python3 animation/blender/render_coordination_s2.py` renders and encode/decode-verifies the cut. Review helpers are `video_review_s2.py` and `review_s2_sequences.py`.

Evidence: `spine_leg_coordination_s2_readback.json` checks all 1,500 root transforms, floor margins, procedural key samples and declared shot bounds, plus every physical component at all 100 distinct cycle states and selected later repeats. The manifest `animation/motion/presentation_coordination_s2.json` records source hashes, exact sample mapping and root transforms. Existing v2 native clearance/procedural evidence applies to the unchanged relative pose path; no new full clearance or dynamics campaign is claimed.
