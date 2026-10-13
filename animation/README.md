# r10 animation package

The user authorized AX2–AX4 on 2026-10-13. Mechanical development remains at the verified r10 checkpoint; animation consumes that geometry and its existing motion interfaces. Source commit: `ddf84ab`. Work branch: `animation/flexor-r10-videos`.

Production is in progress. Final video completion is established by the encoding/readback reports and final QA report, not by the existence of scene-building scripts.

## Local assets

- `scenes/exploded_assembly.blend`: 24 s, 30 fps.
- `scenes/active_spine_mechanism.blend`: 15 s, 60 fps.
- `scenes/spine_leg_coordination.blend`: 20 s, 60 fps.
- Corresponding `output/*.mp4`: 1920 × 1080, H.264/yuv420p.
- `geometry/r10/*.json`: 97 distinct source-local rigid meshes, in metres.
- `motion/production_r10.json`: extends the existing AX01 manifest without changing its source/instance/frame contract.
- `motion/*_r10.jsonl.gz`: complete solver-evaluated trajectories, including one diagnostic endpoint excluded from rendering.
- `source_snapshot_r10.json`, `shot_config.json`: source provenance and presentation timing.

Large `.blend` files, native comparison meshes and numbered PNG caches stay local and are ignored by Git. They are reproducible from tracked geometry, motion and scripts. The final scenes contain their geometry and animation data; playback does not require FreeCAD, scripts, handlers, external assets or changed script-trust settings. The final files are standalone projects and open directly on the named animation scene.

## Mechanical meaning

The 487 physical instances remain separate, with stable `instance_id` custom properties; Blender may suffix object names when several project scenes are open. Collections add no transform. Mesh coordinates are metres, with supplied world transforms in metres applied once: +X forward, +Y left, +Z up, quaternion WXYZ. The two spine motors share one unwrapped crank phase and the existing closed linkage solution.

The coordinated demonstration reuses `combined_spine_gait` inputs from `src/verify_motion_package_r07.py`: hips ±5°, separately prescribed knees ±5° (hind opposite), and an independently prescribed 0–90° hind wheel. The presentation frequency is 0.2 Hz. It is a suspended kinematic demonstration, with no ground contact, translation, forces or loaded locomotion prediction. The wheel does not determine knee motion. Existing r10 finite clearance evidence is reused for this trajectory; no new full clearance campaign was launched.

Springs use the native generator centerlines with fixed wire diameter and changing coil length, baked as source-local absolute shape keys. Cables are orange dashed routing guides; the exact physical slack shape is unresolved. The bounded native comparison checks spring surfaces and cable route reconstruction, not Boolean equivalence or physical cable coverage. The exploded overview freezes one valid assembled pose and moves intact elastic subassemblies; it is not a validated assembly instruction.

## Reproduce

Run from the repository root. Installed Blender GUI and background binary both report 5.2.2 LTS. The current local executable is `/snap/blender/current/blender`.

1. Validate exported assets without either GUI:

   ```bash
   python3 src/animation_production_validate.py animation/motion/production_r10.json
   ```

2. In the installed Blender MCP Python execution tool, set the repository's `animation/blender` directory on `sys.path`, import `build_scenes`, and call `build_scenes.build(name)` separately for the three names above. The persisted wrappers `animation/blender/mcp_build_*.py` do this. `presentation_shots.py` is applied by the builder. This preserves unrelated scenes and writes isolated project files under `animation/scenes/`.

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
