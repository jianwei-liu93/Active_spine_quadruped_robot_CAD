#!/usr/bin/env python3
"""Extract compact review aids from final animation MP4s.

This helper checks media metadata and decodability, then creates contact sheets
and short clips. It does not decide whether the imagery is visually acceptable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from encode_verify import EncodeError, discover_encoder, run


SHOTS: dict[str, dict[str, Any]] = {
    "exploded_assembly": {"duration": 24.0, "fps": 30, "frames": 720},
    "active_spine_mechanism": {"duration": 15.0, "fps": 60, "frames": 900},
    "spine_leg_coordination": {"duration": 20.0, "fps": 60, "frames": 1200},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(path: Path, ffprobe: str) -> dict[str, Any]:
    result = run([
        ffprobe, "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries",
        "stream=codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_read_frames,duration",
        "-show_entries", "format=format_name,duration,size", "-of", "json", str(path),
    ])
    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        return {
            "codec": stream.get("codec_name"), "width": int(stream["width"]),
            "height": int(stream["height"]), "pixel_format": stream.get("pix_fmt"),
            "r_frame_rate": stream.get("r_frame_rate"),
            "avg_frame_rate": stream.get("avg_frame_rate"),
            "frame_count": int(stream["nb_read_frames"]),
            "duration_seconds": float(data.get("format", {}).get("duration", stream.get("duration", 0))),
            "size_bytes": int(data.get("format", {}).get("size", path.stat().st_size)),
            "format": data.get("format", {}).get("format_name"),
        }
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EncodeError(f"ffprobe returned incomplete metadata for {path}: {result.stdout.strip()}") from exc


def validate_media(meta: dict[str, Any], expected: dict[str, Any], path: Path) -> list[str]:
    problems = []
    for field, wanted in (("frame_count", expected["frames"]), ("avg_frame_rate", f'{expected["fps"]}/1')):
        if meta.get(field) != wanted:
            problems.append(f"{field}={meta.get(field)!r}, expected {wanted!r} for {path.name}")
    if meta.get("codec") != "h264":
        problems.append(f"codec={meta.get('codec')!r}, expected 'h264'")
    if meta.get("pixel_format") != "yuv420p":
        problems.append(f"pixel_format={meta.get('pixel_format')!r}, expected 'yuv420p'")
    return problems


def load_events(path: Path | None, shot: str, duration: float) -> list[dict[str, Any]]:
    if path is None:
        # Generic checkpoints only. Replace these with shot-plan event times to
        # center review clips on actual camera cuts, extrema, assembly stages,
        # and motion-loop seams.
        return [
            {"label": label, "seconds": min(max(fraction * duration, 0.0), max(0.0, duration - 0.05))}
            for label, fraction in (("opening", 0.02), ("quarter", 0.25), ("midpoint", 0.50),
                                    ("three_quarter", 0.75), ("closing_seam", 0.98))
        ]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get(shot, [])
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        raise EncodeError(f"Could not read event config {path}: {exc}") from exc
    if not isinstance(raw, list):
        raise EncodeError(f"Events for {shot} must be a JSON list")
    result = []
    labels = set()
    for item in raw:
        if not isinstance(item, dict) or "label" not in item:
            raise EncodeError(f"Each {shot} event needs a label and seconds or frame")
        label = re.sub(r"[^A-Za-z0-9_-]+", "_", str(item["label"])).strip("_")[:40]
        if not label or label in labels:
            raise EncodeError(f"Event labels for {shot} must be nonempty and unique")
        labels.add(label)
        if "frame" in item:
            seconds = (int(item["frame"]) - 1) / SHOTS[shot]["fps"]
        elif "seconds" in item:
            seconds = float(item["seconds"])
        else:
            raise EncodeError(f"Event {label!r} needs seconds or frame")
        if not math.isfinite(seconds) or seconds < 0 or seconds >= duration:
            raise EncodeError(f"Event {label!r} time {seconds!r} is outside the video")
        result.append({"label": label, "seconds": seconds})
    return result


def timecode(seconds: float) -> str:
    return f"{seconds:.3f}s"


def representative_times(events: list[dict[str, Any]], duration: float, count: int = 12) -> list[dict[str, Any]]:
    chosen = sorted(events, key=lambda event: event["seconds"])
    if len(chosen) > count:
        indices = sorted({round(i * (len(chosen) - 1) / (count - 1)) for i in range(count)})
        chosen = [chosen[i] for i in indices]
    labels = {event["label"] for event in chosen}
    for i in range(count * 3):
        if len(chosen) >= count:
            break
        seconds = (i + 0.5) * duration / (count * 3)
        if all(abs(event["seconds"] - seconds) > duration / (count * 3) for event in chosen):
            label = f"sample_{len(chosen) + 1:02d}"
            while label in labels:
                label += "x"
            labels.add(label)
            chosen.append({"label": label, "seconds": seconds})
    if len(chosen) < count:
        for i in range(count):
            seconds = (i + 0.5) * duration / count
            if all(abs(event["seconds"] - seconds) > 0.001 for event in chosen):
                chosen.append({"label": f"uniform_{i + 1:02d}", "seconds": seconds})
            if len(chosen) == count:
                break
    return sorted(chosen[:count], key=lambda event: event["seconds"])


def black_frame_status(path: Path) -> dict[str, Any]:
    from PIL import Image, ImageStat

    with Image.open(path) as image:
        gray = image.convert("L")
        mean_luma = float(ImageStat.Stat(gray).mean[0])
        histogram = gray.histogram()
        dark_pixels = sum(histogram[:10])
        dark_fraction = dark_pixels / max(1, image.width * image.height)
    return {
        "mean_luma_0_255": round(mean_luma, 3),
        "fraction_pixels_below_10": round(dark_fraction, 6),
        "basic_black_candidate": mean_luma < 5.0 and dark_fraction > 0.95,
    }


def extract_frame(ffmpeg: str, video: Path, seconds: float, target: Path) -> None:
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", f"{seconds:.6f}",
         "-i", str(video), "-frames:v", "1", "-y", str(target)])
    if not target.is_file() or target.stat().st_size == 0:
        raise EncodeError(f"Frame extraction produced no image at {seconds:.3f}s in {video}")


def write_sheet(images: list[tuple[Path, str]], target: Path, width: int, height: int) -> dict[str, Any]:
    from PIL import Image, ImageDraw, ImageFont

    thumb_width = 480
    thumb_height = round(thumb_width * height / width)
    label_height = 30
    gap = 12
    cols, rows = 4, 3
    sheet = Image.new("RGB", (cols * thumb_width + (cols + 1) * gap,
                              rows * (thumb_height + label_height) + (rows + 1) * gap),
                      (28, 32, 38))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    frame_records = []
    for index, (path, label) in enumerate(images[:12]):
        row, col = divmod(index, cols)
        x = gap + col * thumb_width
        y = gap + row * (thumb_height + label_height)
        with Image.open(path) as image:
            dims = list(image.size)
            resampling = getattr(Image, "Resampling", Image)
            thumb = image.convert("RGB").resize((thumb_width, thumb_height), resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw.text((x, y + thumb_height + 5), label, fill=(238, 241, 244), font=font)
        frame_records.append({"label": label, "source_width": dims[0], "source_height": dims[1]})
    sheet.save(target, format="PNG", optimize=True)
    return {"path": str(target), "width": sheet.width, "height": sheet.height,
            "frame_count": len(frame_records), "frames": frame_records}


def extract_clip(ffmpeg: str, ffprobe: str, video: Path, event: dict[str, Any], duration: float,
                 target: Path) -> dict[str, Any]:
    clip_len = min(duration, float(event.get("clip_duration", 2.0)))
    start = min(max(0.0, event["seconds"] - clip_len / 2), max(0.0, duration - clip_len))
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", f"{start:.6f}",
         "-i", str(video), "-t", f"{clip_len:.6f}", "-map", "0:v:0", "-an", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-y", str(target)])
    meta_result = run([ffprobe, "-v", "error", "-count_frames", "-select_streams", "v:0",
                       "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames",
                       "-of", "json", str(target)], check=False)
    if meta_result.returncode:
        raise EncodeError(f"Could not probe review clip {target}: {meta_result.stderr.strip()}")
    try:
        stream = json.loads(meta_result.stdout)["streams"][0]
        clip_frames = int(stream["nb_read_frames"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EncodeError(f"Review clip metadata is incomplete: {target}") from exc
    return {"path": str(target), "event": event["label"], "event_seconds": event["seconds"],
            "start_seconds": start, "duration_seconds": clip_len, "frame_count": clip_frames,
            "width": int(stream["width"]), "height": int(stream["height"]),
            "avg_frame_rate": stream["avg_frame_rate"]}


def review_shot(shot: str, video: Path, expected: dict[str, Any], out_dir: Path,
                events_path: Path | None, ffmpeg: str, ffprobe: str, clip_duration: float) -> dict[str, Any]:
    if not video.is_file():
        raise EncodeError(f"Video is missing: {video}")
    meta = probe(video, ffprobe)
    duration = meta["duration_seconds"]
    if duration <= 0:
        raise EncodeError(f"Video duration is not positive: {video}")
    events = load_events(events_path, shot, duration)
    if clip_duration != 2.0:
        # Keep one consistent clip length, still clipped at file boundaries.
        clip_len = clip_duration
    else:
        clip_len = 2.0

    shot_dir = out_dir / shot
    shot_dir.mkdir(parents=True, exist_ok=True)
    review_dir = shot_dir / "clips"
    review_dir.mkdir(parents=True, exist_ok=True)
    selected = representative_times(events, duration)
    images: list[tuple[Path, str]] = []
    extracted: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix=f"{shot}_review_") as temp_dir:
        temp = Path(temp_dir)
        for index, event in enumerate(selected, 1):
            image_path = temp / f"frame_{index:02d}.png"
            extract_frame(ffmpeg, video, event["seconds"], image_path)
            from PIL import Image

            with Image.open(image_path) as image:
                dims = (image.width, image.height)
            if dims != (meta["width"], meta["height"]):
                raise EncodeError(f"Extracted frame dimensions {dims} disagree with video metadata {meta}")
            black = black_frame_status(image_path)
            images.append((image_path, f"{event['label']} · {timecode(event['seconds'])}"))
            extracted.append({"label": event["label"], "seconds": event["seconds"],
                              "width": dims[0], "height": dims[1], "black_check": black})

        contact = write_sheet(images, shot_dir / f"{shot}_contact_sheet.png", meta["width"], meta["height"])
        clip_events = events[:5]
        clips = []
        for event in clip_events:
            # Extract clips directly around the supplied/selected event center.
            clip = dict(event)
            clip["clip_duration"] = clip_len
            clip_record = extract_clip(ffmpeg, ffprobe, video, clip, duration,
                                      review_dir / f"{shot}_{event['label']}.mp4")
            clips.append(clip_record)

    validation = validate_media(meta, expected, video)
    return {
        "shot": shot, "video": str(video), "video_sha256": sha256(video),
        "video_metadata": meta, "expected_defaults": expected,
        "default_metadata_mismatches": validation,
        "events_source": str(events_path) if events_path else "generic duration checkpoints; supply event JSON for shot-specific extrema/transitions",
        "extracted_frames": extracted, "contact_sheet": contact,
        "basic_black_candidates": [item["label"] for item in extracted if item["black_check"]["basic_black_candidate"]],
        "review_clips": clips,
        "visual_acceptance": "not assessed; inspect the contact sheet and review clips",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-dir", default="animation/output", help="Directory with the three final MP4 files")
    parser.add_argument("--output-dir", default="reports/animation/previews/video_review")
    parser.add_argument("--events", help="Optional JSON mapping shot names to named frame/second checkpoints")
    parser.add_argument("--clip-duration", type=float, default=2.0)
    parser.add_argument("--shot", choices=("all", *SHOTS), default="all")
    parser.add_argument("--input", help="Override MP4 path when reviewing one --shot")
    args = parser.parse_args()
    if args.clip_duration <= 0:
        parser.error("--clip-duration must be positive")
    if args.input and args.shot == "all":
        parser.error("--input requires one named --shot")
    try:
        ffmpeg, ffprobe, version = discover_encoder(None, None)
        video_dir = Path(args.video_dir)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        selected = [args.shot] if args.shot != "all" else list(SHOTS)
        events_path = Path(args.events) if args.events else None
        reports = []
        failures = []
        for shot in selected:
            video = Path(args.input) if args.input else video_dir / f"{shot}.mp4"
            try:
                result = review_shot(shot, video, SHOTS[shot], output_dir, events_path,
                                     ffmpeg, ffprobe, args.clip_duration)
                reports.append(result)
                if result["default_metadata_mismatches"]:
                    failures.append({"shot": shot, "metadata_mismatches": result["default_metadata_mismatches"]})
            except (EncodeError, OSError, ValueError) as exc:
                failures.append({"shot": shot, "error": str(exc)})
        report = {
            "encoder": {"ffmpeg": ffmpeg, "ffprobe": ffprobe, "version": version},
            "output_directory": str(output_dir.resolve()), "results": reports, "failures": failures,
            "visual_acceptance": "not assessed; generated contact sheets/clips and black-frame heuristics are review aids only",
        }
        report_path = output_dir / "video_review_report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1 if failures else 0
    except EncodeError as exc:
        print(f"video_review: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
