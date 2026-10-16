#!/usr/bin/env python3
"""Build small r15b README previews from verified outputs; no CAD/Blender writes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from encode_verify import discover_encoder, run

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "docs/media"
VIDEO = ROOT / "animation/output/spine_leg_coordination_s2_r15b.mp4"
QA = ROOT / "reports/animation/spine_leg_coordination_s2_r15b_qa.json"
CAD = ROOT / "cad/flexor_r15b_robot.FCStd"
IMAGES = {
    "robot_assembled_r15b.png": "reports/views/r15b_robot_isometric.png",
    "rocker_r15b.png": "reports/views/r15b_AB_isolated.png",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
            "bytes": path.stat().st_size}


def build() -> dict:
    if not VIDEO.is_file() or not QA.is_file():
        missing = [path.relative_to(ROOT).as_posix() for path in (VIDEO, QA) if not path.is_file()]
        raise FileNotFoundError("r15b README media is not ready; missing: " + ", ".join(missing))
    qa = json.loads(QA.read_text())
    if qa.get("status") != "PASS_WITH_DOCUMENTED_LIMITATIONS":
        raise ValueError("r15b video release QA has not passed")
    for name, path in (("video", VIDEO), ("source_cad", CAD)):
        if digest(path) != qa.get("source_hashes", {}).get(name):
            raise ValueError(f"Changed or unbound r15b release input: {name}")

    ffmpeg, _, version = discover_encoder(None, None)
    MEDIA.mkdir(parents=True, exist_ok=True)
    images = []
    for output_name, source_name in IMAGES.items():
        source = ROOT / source_name
        if not source.is_file():
            continue
        output = MEDIA / output_name
        with Image.open(source) as image:
            image = image.convert("RGB")
            image.thumbnail((1280, 880), getattr(Image, "Resampling", Image).LANCZOS)
            image.save(output, optimize=True)
            images.append({"source": record(source), "output": record(output),
                           "size_px": list(image.size), "changes": "RGB conversion and downscale only"})

    # The first 100 frames at 60 fps are one complete overview cycle. They do
    # not cross a camera cut, and the repeated endpoint is excluded.
    gif = MEDIA / "spine_leg_coordination_r15b.gif"
    filters = (
        "[0:v]trim=start_frame=0:end_frame=100,setpts=PTS-STARTPTS,"
        "fps=18,scale=960:540:flags=lanczos,split[a][b];"
        "[a]palettegen=max_colors=256:stats_mode=diff[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=3[out]"
    )
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
         "-i", str(VIDEO), "-filter_complex", filters, "-map", "[out]",
         "-an", "-loop", "0", "-threads", "1", str(gif)])
    durations = []
    samples = []
    with Image.open(gif) as image:
        if image.size != (960, 540) or image.n_frames != 30 or image.info.get("loop") != 0:
            raise ValueError("Unexpected GIF dimensions, cycle frame count or loop mode")
        for index in range(image.n_frames):
            image.seek(index)
            image.load()
            durations.append(image.info.get("duration", 0))
            if index in (0, 7, 15, 22, 29):
                samples.append(image.convert("RGB").copy())
    duration = sum(durations) / 1000
    if abs(duration - 100 / 60) > 0.03 or any(value <= 0 for value in durations):
        raise ValueError(f"Invalid GIF cycle timing: {duration}")
    changes = [sum(ImageStat.Stat(ImageChops.difference(samples[0], sample)).mean)
               for sample in samples[1:]]
    if min(changes) <= 0:
        raise ValueError("GIF motion samples unexpectedly identical")
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-xerror", "-nostdin",
         "-i", str(gif), "-f", "null", "-"])
    if gif.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("README GIF exceeds the 8 MiB preview budget")

    manifest = {
        "schema": "flexor.readme-media.v1", "revision": "r15b",
        "generator": record(Path(__file__)), "source_cad": record(CAD),
        "source_video": record(VIDEO), "release_qa": record(QA),
        "images": images, "gif": {
            **record(gif), "size_px": [960, 540], "frames": 30,
            "duration_seconds": duration, "loop": "infinite", "target_fps": 18,
            "source_frame_range_zero_based": [0, 99], "source_fps": 60,
            "source_cycle_seconds": 100 / 60, "ffmpeg_version": version,
            "decode_check": "PASS_PILLOW_AND_FFMPEG", "timing_check": "PASS",
            "motion_sample_check": "PASS_DISTINCT_FRAMES",
            "scope": "One existing r15b studio overview cycle; illustrative prescribed kinematics",
        },
        "geometry_or_motion_modified": False,
    }
    (MEDIA / "manifest_r15b.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {"gif": manifest["gif"], "image_count": len(images)}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
