# FLEXOR animation package

## r14 coordination update — 2026-10-14

The user requested regeneration with the current r14 design. The versioned output is `output/spine_leg_coordination_s2_r14.mp4`, with editable standalone project `scenes/spine_leg_coordination_s2_r14.blend`. **Production rendering is in progress; video QA is not yet complete.** Older r10 scenes/videos and their evidence remain unchanged.

The new cut consumes the SHA-pinned `cad/flexor_r14_robot.FCStd`: 455 physical instances and 108 source definitions, including the compact frame, organic A–B rockers forked only at B, revised torso mounting profiles and recessed B–C links. All 108 current source geometries passed strict comparison with saved BReps extracted from the canonical native file. Twenty raw serialization hashes differed from the AX01 header on the disposable export document; the original AX01 header remains intact and these differences are recorded alongside strict geometry identity. No CAD source geometry, placement, parameter, or native file was changed.

The existing paper-informed v2 trajectory is retained: approximately 68.75 degrees of full hip excursion, separately prescribed 20-degree full knee excursion, and independent 0–90-degree wheel motion. The 20-second source timeline has 1,201 solver-evaluated samples at 60 fps. The studio cut uses stride three to display 0.6 Hz for 25 seconds, with the previously authorized illustrative body pitch/translation and a persistent kinematic caption. Springs and cables have 300 baked procedural states per instance; cable slack remains a schematic dashed route, not a solved physical shape.

Actual pre-render checks pass: 455 separately identified instances and 98 rigid source meshes in saved-scene readback, shared rigid definitions, all 3,000 procedural shape samples, evaluated procedural surfaces, root-relative transforms, 1,500-frame floor/framing checks, and all four torso-relative leg articulations. A separate nine-phase screen checks 32,032 affected pairs per phase (288,288 decisions) with zero overlaps/warnings/errors. This is bounded changed-pair evidence; the neutral-leg r14 cycle screen and earlier r10 evidence do not certify continuous or complete coordinated-gait clearance. Mechanical fabrication blockers remain unchanged.

Blender's read-only absolute shape-key times accumulate float32 increments. The new builders bake `eval_time` from each stored `key.frame` value, rather than an assumed exact integer time grid. Readback verifies the stored-time convention, all key geometry, and evaluated procedural mesh error (maximum about 9.32e-9 m). The initial strict time-grid failure is retained in `reports/animation/spine_leg_coordination_s2_r14_readback_initial_keytime_failure.json`.

### Reproduce r14

Only the lead operates the live CAD/MCP session. Use a byte-identical disposable copy at `reports/tmp/r14_animation/flexor_r14_robot.FCStd` or the unchanged canonical document. Through installed FreeCAD MCP, import `src/animation_coordination_r14.py` and call `run(doc)`. It exports `geometry/r14/`, `motion/coordinated_spine_legs_r14.jsonl.gz` and `motion/production_coordination_r14.json`, with native/snapshot preservation guards. Validate with `python src/animation_production_validate.py animation/motion/production_coordination_r14.json`.

Through installed Blender MCP, add `animation/blender` to `sys.path`, import and call `build_coordination_r14.build()`. Package the saved source library in a separate process:

```bash
/snap/blender/current/blender -b animation/scenes/spine_leg_coordination_r14.blend --python animation/blender/package_scene.py -- spine_leg_coordination_r14
```

Then call `build_coordination_s2_r14.build()` through Blender MCP and package the studio scene:

```bash
/snap/blender/current/blender -b animation/scenes/spine_leg_coordination_s2_r14.blend --python animation/blender/package_scene.py -- spine_leg_coordination_s2_r14
/snap/blender/current/blender -b animation/scenes/spine_leg_coordination_s2_r14.blend --python animation/blender/verify_coordination_s2_r14.py
```

For articulation readback, reuse `verify_leg_articulation` in a fresh process with `SCENE_NAME='spine_leg_coordination_r14'` and report path `reports/animation/leg_articulation_r14.json`. The nine-pose supplemental FreeCADCmd screen calls `animation_coordination_screen_r14.run(canonical_path)`; it never saves or mutates the live document.

Use generic `render_frames.py --scene spine_leg_coordination_s2_r14 --preview --frames 1 26 51 76 451 801 1171 1411` for hash-named preview frames. After lead visual review and matching saved-scene readback, `python animation/blender/render_coordination_r14.py` resumes rendering with one GPU process, encodes H.264/yuv420p, and fully decodes the output. Large scenes and PNG caches remain local/ignored; new geometry/motion assets, final MP4 and compact evidence are tracked.

For decoded review, run `python animation/blender/video_review_coordination_r14.py --shot spine_leg_coordination_s2_r14 --events animation/review_events_r14.json --output-dir reports/animation/previews/r14_video_review`, followed by `python animation/blender/review_r14_sequences.py`. Lead inspection supplies the versioned visual/adjacent acceptance records. `python animation/blender/final_report_coordination_r14.py` fails closed until the full hash/readback/render/decode/visual/clearance/articulation chain passes. Its final release record is `reports/animation/spine_leg_coordination_s2_r14_qa.json`.

## Historical r10 package

The user authorized AX2–AX4 on 2026-10-13. Mechanical development remains at the verified r10 checkpoint; animation consumes that geometry and its existing motion interfaces. Source commit: `ddf84ab`. Work branch: `animation/flexor-r10-videos`.

**Complete: all three videos are rendered and verified, including the updated paper-informed coordination video with approximately 69 degrees of hip excursion.** See `reports/animation/final_video_qa.json` for source hashes, 2,820 rendered frames, timing, transform accuracy and documented limitations. Representative decoded contact sheets and adjacent-frame sequences have been inspected; event clips are available as review aids.

## Local assets

- `scenes/exploded_assembly.blend`: 24 s, 30 fps.
- `scenes/active_spine_mechanism.blend`: 15 s, 60 fps.
- `scenes/spine_leg_coordination.blend`: 20 s, 60 fps.
- Corresponding `output/*.mp4`: 1920 × 1080, H.264/yuv420p.
- `geometry/r10/*.json`: 97 distinct source-local rigid meshes, in metres.
- `motion/production_r10.json`: original release manifest.
- `motion/production_coordination_v2_r10.json`: updated coordination manifest with the versioned paper-informed profile; preserves the AX01 source/instance/frame contract.
- `motion/*_r10.jsonl.gz`: complete solver-evaluated trajectories, including one diagnostic endpoint excluded from rendering.
- `source_snapshot_r10.json`, `shot_config.json`: source provenance and presentation timing.

Large `.blend` files, native comparison meshes and numbered PNG caches stay local and are ignored by Git. They are reproducible from tracked geometry, motion and scripts. The final scenes contain their geometry and animation data; playback does not require FreeCAD, scripts, handlers, external assets or changed script-trust settings. The final files are standalone projects and open directly on the named animation scene.

## Mechanical meaning

The 487 physical instances remain separate, with stable `instance_id` custom properties; Blender may suffix object names when several project scenes are open. Collections add no transform. Mesh coordinates are metres, with supplied world transforms in metres applied once: +X forward, +Y left, +Z up, quaternion WXYZ. The two spine motors share one unwrapped crank phase and the existing closed linkage solution.

The coordinated v2 demonstration uses approximately 69 degrees of full hip excursion, derived from the Fig S27 target plot, with an 18-degree lag between spinal extension onset and hind-leg backswing. Four knees are separately prescribed through +/-10 degrees; the hind winding wheel independently spans 0–90 degrees. The presentation frequency is 0.2 Hz, slowed from the referenced 3.5-Hz trial. CAD hip datums (-60 degrees fore, -75 degrees hind), fore/hind signal phase and knee trajectories remain explicit assumptions, not recovered experimental commands. See `reports/animation/paper_motion_angle_reconciliation.md` and `animation/coordination_paper_profile_v2.json`.

It is a suspended kinematic demonstration, with no ground contact, translation, forces or loaded locomotion prediction. The wheel does not determine knee motion. The larger trajectory has new bounded native checks at nine critical phases, plus all 300 cycle frames for the previously colliding rigid pairs. These checks do not constitute continuous clearance or reuse the original full campaign. The original v1 trajectory and manifest remain preserved.

Springs use the native generator centerlines with fixed wire diameter and changing coil length, baked as source-local absolute shape keys. Cables are orange dashed routing guides; the exact physical slack shape is unresolved. The bounded native comparison checks spring surfaces and cable route reconstruction, not Boolean equivalence or physical cable coverage. The exploded overview freezes one valid assembled pose and moves intact elastic subassemblies; it is not a validated assembly instruction.

## Reproduce

Run from the repository root. Installed Blender GUI and background binary both report 5.2.2 LTS. The current local executable is `/snap/blender/current/blender`.

1. Validate exported assets without either GUI:

   ```bash
   python3 src/animation_production_validate.py animation/motion/production_r10.json
   ```

2. In the installed Blender MCP Python execution tool, set the repository's `animation/blender` directory on `sys.path`, import `build_scenes`, and call `build_scenes.build(name)` separately for the three names above. The persisted wrappers `animation/blender/mcp_build_*.py` do this; the coordination wrapper selects `motion/production_coordination_v2_r10.json`. `presentation_shots.py` is applied by the builder. This preserves unrelated scenes and writes isolated project files under `animation/scenes/`.

   The local bridge `animation/blender/mcp_client.py` invokes the already configured `uvx --offline mcp-for-blender` server. It requires a Python with the existing `mcp` package and a running Blender addon; it installs nothing. Set its configured command path for another workstation if needed.

3. Package each MCP-written isolated scene as a standalone project (repeat with the other names):

   ```bash
   /snap/blender/current/blender -b animation/scenes/active_spine_mechanism.blend --python animation/blender/package_scene.py -- active_spine_mechanism
   ```

   This background-only step leaves the live GUI's unrelated file and scenes intact. Check each packaged scene in a fresh process:

   ```bash
   /snap/blender/current/blender -b animation/scenes/active_spine_mechanism.blend --python animation/blender/verify_saved_scene.py -- active_spine_mechanism
   ```

4. Render or resume, one GPU process at a time:

   ```bash
   /snap/blender/current/blender -b animation/scenes/active_spine_mechanism.blend --python animation/blender/render_frames.py -- --scene active_spine_mechanism
   ```

   Substitute the other scene names. `--start N --end M` renders a bounded range. `--preview --frames 1 150 300` writes separate hash-named preview folders. Existing complete PNGs are skipped only if the saved-scene/render signature matches. If changing a scene, preserve or move its old frame folder before rendering the new version.

5. Encode and decode-verify (substitute 720/30 and 1200/60 for the other movies):

   ```bash
   python3 animation/blender/encode_verify.py --input-pattern animation/output/frames/active_spine_mechanism/frame_%06d.png --output animation/output/active_spine_mechanism.mp4 --frame-count 900 --fps 60
   ```

   The helper discovers local ffmpeg/ffprobe and validates every expected PNG, then checks dimensions, duration, codec, pixel format, frame rate, frame count and full video decoding. No audio is required.

## Evidence and limits

See `reports/animation/ax2_roundtrip.json`, `production_r10.json`, `procedural_surface_comparison.json`, each `*_readback.json`, each video verification report, and final QA. Original AX0/AX1 evidence remains intact. Canonical CAD and parameter hashes are pinned in the source snapshot and production manifest. Current fabrication blockers remain those recorded at the r10 checkpoint; video completion does not resolve them.

For compact decoded contact sheets and event clips:

```bash
python3 animation/blender/video_review.py --events animation/review_events.json
```

After the three visual review records have been written, `python3 animation/blender/final_report.py` verifies the saved-scene/render/video source hash chain and aggregates the actual execution evidence. `reports/animation/final_video_qa.json` is the release record. The verified playback scope is rendered integer frames; subframe retiming or motion blur requires resampling and validation.

To regenerate the v2 motion, the lead runs `animation_coordination_v2.run(read_only_r10_copy)` through the installed FreeCAD MCP, using `src/animation_coordination_v2.py`. Isolated native checks use `screen_clearance(native_path)` and `animation_coordination_clearance_v2.run(native_path)`. Native extrema examples use `animation_coordination_native_v2.run(native_path)` followed by `python3 animation/blender/compare_procedural_v2.py`. No canonical CAD save is needed.

The updated leg articulation report, `reports/animation/leg_articulation_v2.json`, measures actual segment motion relative to each torso at every cycle frame. The original small-excursion release QA is preserved as `reports/animation/final_video_qa_v1.json`; v2 has separate clearance, profile, native surface, all-frame camera framing and source evidence. The corrected coordination video is 20 seconds, 60 fps, 1920 × 1080; its editable project is `scenes/spine_leg_coordination.blend`.

## Movie S2-inspired studio cut

The user separately authorized illustrative body motion and a presentation closer to supplementary Movie S2. The new cut is `scenes/spine_leg_coordination_s2.blend` and `output/spine_leg_coordination_s2.mp4`: 25 seconds at 60 fps, with a warm floor, shadows, graphite/light-link materials, whole-body bounding and labelled spine/hind/fore mechanism shots. The full 1,500-frame video is rendered, encoded and fully decoded; scene, floor, framing and decoded-sample visual checks pass. The release evidence is `reports/animation/spine_leg_coordination_s2_qa.json`. The existing technical videos and their QA remain unchanged.

`coordination_s2_style.json` configures the cut. `motion/presentation_coordination_s2.json` maps every output frame to an existing verified CAD sample and one additional rigid presentation transform. Every third sample gives a 0.6-Hz display cycle; body pitch, fore-aft oscillation and vertical flight gap are illustrative assumptions. Floor proximity does not imply support forces or dynamic equilibrium. The persistent on-screen caption identifies the motion as illustrative kinematics.

In the installed Blender MCP, import `build_coordination_s2` from `animation/blender` and call `build()`. This consumes the existing verified technical scene. Package with `package_scene.py -- spine_leg_coordination_s2`, then run `verify_coordination_s2.py` in fresh Blender. After preview review, run `python3 animation/blender/render_coordination_s2.py`. The variant uses separate decoded-review and final QA helpers (`video_review_s2.py`, `review_s2_sequences.py`, `final_report_s2.py`). See `reports/animation/movie_s2_presentation.md` for the precise scope and intentional macro crops.
