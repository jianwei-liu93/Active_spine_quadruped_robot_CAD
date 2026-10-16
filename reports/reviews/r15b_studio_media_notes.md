# r15b studio README media preparation

The r15b README media helper is `animation/blender/build_readme_media_r15b.py`. It is a source-only adapter for the completed studio cut and its release QA. The helper requires `animation/output/spine_leg_coordination_s2_r15b.mp4`, `reports/animation/spine_leg_coordination_s2_r15b_qa.json` with `PASS_WITH_DOCUMENTED_LIMITATIONS`, matching `video` and `source_cad` hashes, and `cad/flexor_r15b_robot.FCStd`.

The GIF output is versioned as `docs/media/spine_leg_coordination_r15b.gif`; its manifest is `docs/media/manifest_r15b.json`. The helper takes the first 100 source frames at 60 fps as one overview cycle, samples them to 30 frames at 18 fps, and scales to 960 × 540. It checks complete Pillow and ffmpeg decoding, duration, infinite looping, distinct motion samples, and the 8 MiB size limit. Optional stills are sourced from `reports/views/r15b_robot_isometric.png` and `reports/views/r15b_AB_isolated.png`, producing `robot_assembled_r15b.png` and `rocker_r15b.png` when those source captures exist.

`animation/review_events_r15b.json` marks the centers of the five existing 25-second studio sections: whole-robot overview from 0–6 s, spine detail from 6–12 s, hind mechanism from 12–18 s, fore mechanism from 18–22 s, and final overview from 22–25 s. These are decoded-review event centers, not claims that review has been performed.

At preparation time, the r15b MP4 and release QA report are absent. No rendering, encoding, GIF generation, still-image conversion, README edit, or CAD/Blender operation was performed. Run the helper only after the video and QA record are complete.
