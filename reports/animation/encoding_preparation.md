# Animation video encoding preparation

**Status: encoder implementation and local smoke verification complete; AX2–AX4 footage not encoded.** No Blender render sequence was present when this preparation was done, so this report does not claim a robot video or final-video QA.

## Local encoder discovery

`ffmpeg` and `ffprobe` were absent from `PATH`, and Python could not import `imageio_ffmpeg` or `imageio`. A local scan found working Conda environment binaries with `libx264`; the encoder selected by the CLI was `/home/jianwei/miniforge3/envs/nerd/bin/ffmpeg` with its matching `ffprobe`. The reported version is FFmpeg 9.0.1 (`ffmpeg version 9.0.1 Copyright (c) 2000-2026 the FFmpeg developers`). The binary exposes `libx264`. A separate discovered environment (`scalingup_floating`) could not start because its `libopenh264.so.5` dependency was missing; automatic discovery skips tools that cannot report their version or available encoders. No tools were installed and no network lookup was used.

## Encoder and checks

[encode_verify.py](../../animation/blender/encode_verify.py) is a local Python CLI. It accepts a numbered PNG pattern, explicit first frame and frame count, 30 or 60 fps, and even output dimensions (default 1920×1080). It checks every requested PNG and its dimensions before encoding. It writes H.264 via `libx264`, uses `yuv420p` and MP4 `faststart`, and only replaces the destination after successful validation. An existing destination requires `--overwrite`.

Before accepting a file, it asks `ffprobe` to count decoded frames and inspect codec, dimensions, pixel format, frame rate and duration. It then decodes the complete MP4 with FFmpeg's error-exit mode. The successful smoke run used three temporary 64×64 PNGs at 30 fps and produced an H.264/yuv420p file with three frames and 0.100 s duration; ffprobe and full decode both passed. These synthetic frames only exercise the encoder path and are not robot imagery.

## Commands for the documented default shot lengths

These frame counts follow the approximate durations in `docs/20_animation_and_visualisation_pipeline.md`. Adjust the explicit count to the actual rendered sequence if its duration differs. Run from the repository root after each PNG sequence exists:

```bash
python animation/blender/encode_verify.py \
  --input-pattern animation/render/exploded_assembly/frame_%06d.png \
  --frame-count 720 --fps 30 \
  --output animation/output/exploded_assembly.mp4

python animation/blender/encode_verify.py \
  --input-pattern animation/render/active_spine_mechanism/frame_%06d.png \
  --frame-count 900 --fps 60 \
  --output animation/output/active_spine_mechanism.mp4

python animation/blender/encode_verify.py \
  --input-pattern animation/render/spine_leg_coordination/frame_%06d.png \
  --frame-count 1200 --fps 60 \
  --output animation/output/spine_leg_coordination.mp4
```

The default discovery checks `PATH`, an available `imageio_ffmpeg` binary, and local Conda/Miniforge environment binary directories; it chooses the newest working FFmpeg version with `libx264` and a matching `ffprobe`. On a machine whose bundle is elsewhere, pass both `--ffmpeg /path/to/ffmpeg` and `--ffprobe /path/to/ffprobe`. To continue using the same named output, add `--overwrite`; incomplete input sequences and failed verification leave any existing output intact.

## Scope boundary

This work prepares only PNG-sequence encoding and final-file validation. No Blender or FreeCAD application was called, no scene/CAD/shared configuration was changed, and no render was launched. The three production MP4s, their source frame counts, and their final visual review remain unverified until the matching sequences and scenes have been produced by the lead workflow.
