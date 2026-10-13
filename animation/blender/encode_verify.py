#!/usr/bin/env python3
"""Encode a numbered PNG sequence to H.264 MP4 and verify the result.

No Blender or FreeCAD APIs are used here. The frame count is explicit so that
partial or stale render sequences cannot silently define the movie duration.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


class EncodeError(RuntimeError):
    pass


def run(args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except OSError as exc:
        raise EncodeError(f"Could not run {args[0]}: {exc}") from exc
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise EncodeError(f"Command failed ({result.returncode}): {' '.join(args)}\n{detail}")
    return result


def _candidate_pairs() -> list[tuple[str, str]]:
    """Find local ffmpeg/ffprobe pairs, including imageio and Conda bundles."""
    pairs: list[tuple[str, str]] = []

    def add(ffmpeg: str | Path | None, ffprobe: str | Path | None = None) -> None:
        if not ffmpeg:
            return
        ffmpeg_path = shutil.which(str(ffmpeg)) or str(ffmpeg)
        sibling_probe = Path(ffmpeg_path).with_name("ffprobe")
        probe_path = (shutil.which(str(ffprobe)) if ffprobe else None) or (
            str(ffprobe) if ffprobe else (str(sibling_probe) if sibling_probe.is_file() else None)
        )
        if probe_path and (ffmpeg_path, probe_path) not in pairs:
            pairs.append((ffmpeg_path, probe_path))

    add(shutil.which("ffmpeg"), shutil.which("ffprobe"))
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        add(imageio_ffmpeg.get_ffmpeg_exe(), shutil.which("ffprobe"))
    except (ImportError, RuntimeError, OSError):
        pass

    roots: set[Path] = set()
    for value in (os.environ.get("CONDA_PREFIX"), sys.prefix):
        if value:
            prefix = Path(value)
            roots.add(prefix)
            if prefix.parent.name == "envs":
                roots.add(prefix.parent)
    home = Path.home()
    for manager in ("miniforge3", "miniconda3", "anaconda3"):
        roots.add(home / manager / "envs")
    for root in sorted(roots, key=str):
        if root.name == "envs" and root.is_dir():
            for binary in sorted(root.glob("*/bin/ffmpeg")):
                add(binary)
        else:
            add(root / "bin/ffmpeg")
            add(root / "Library/bin/ffmpeg.exe")
    return pairs


def discover_encoder(explicit_ffmpeg: str | None, explicit_ffprobe: str | None) -> tuple[str, str, str]:
    pairs = [(explicit_ffmpeg, explicit_ffprobe)] if explicit_ffmpeg else _candidate_pairs()
    problems: list[str] = []
    usable: list[tuple[int, str, str, str]] = []
    for ffmpeg, ffprobe in pairs:
        if not ffmpeg or not ffprobe:
            continue
        version = run([ffmpeg, "-version"], check=False)
        probe_version = run([ffprobe, "-version"], check=False)
        if version.returncode or probe_version.returncode:
            problems.append(f"{ffmpeg}: tool failed to start or report version")
            continue
        encoder_list = run([ffmpeg, "-hide_banner", "-encoders"], check=False)
        if encoder_list.returncode or not re.search(r"\blibx264\b", encoder_list.stdout + encoder_list.stderr):
            problems.append(f"{ffmpeg}: libx264 encoder is unavailable")
            continue
        version_line = version.stdout.splitlines()[0].strip()
        major = int(re.search(r"ffmpeg version\s+(\d+)", version_line).group(1)) if re.search(r"ffmpeg version\s+(\d+)", version_line) else 0
        usable.append((major, str(ffmpeg), str(ffprobe), version_line))
    if usable:
        _, ffmpeg, ffprobe, version_line = max(usable, key=lambda item: item[0])
        return ffmpeg, ffprobe, version_line
    if explicit_ffmpeg and not explicit_ffprobe:
        raise EncodeError("--ffmpeg requires a matching --ffprobe, or omit both for automatic discovery")
    why = "; ".join(problems) if problems else "no usable local ffmpeg/ffprobe pair found"
    raise EncodeError(f"H.264 encoding tools unavailable: {why}")


def sequence_paths(pattern: str, first_frame: int, frame_count: int) -> list[Path]:
    matches = list(re.finditer(r"%0(\d+)d", pattern))
    if len(matches) != 1:
        raise EncodeError("Input pattern must contain exactly one printf frame field, such as frame_%06d.png")
    match = matches[0]
    digits = int(match.group(1))
    if digits < 1 or digits > 18:
        raise EncodeError("Frame-number padding in the pattern must be between 1 and 18 digits")
    prefix, suffix = pattern[:match.start()], pattern[match.end():]
    paths = [Path(f"{prefix}{number:0{digits}d}{suffix}")
             for number in range(first_frame, first_frame + frame_count)]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        preview = ", ".join(missing[:5])
        more = f" (and {len(missing) - 5} more)" if len(missing) > 5 else ""
        raise EncodeError(f"Missing {len(missing)} expected PNG frame(s): {preview}{more}")
    return paths


def inspect_pngs(paths: Sequence[Path], width: int, height: int) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise EncodeError("Pillow is required to validate PNG dimensions; use the project Python with Pillow") from exc
    for path in paths:
        try:
            with Image.open(path) as image:
                if image.format != "PNG":
                    raise EncodeError(f"Expected PNG data in {path}, found {image.format}")
                image.verify()
            with Image.open(path) as image:
                if image.size != (width, height):
                    raise EncodeError(f"{path} is {image.width}x{image.height}; expected {width}x{height}")
                image.load()
        except EncodeError:
            raise
        except Exception as exc:
            raise EncodeError(f"Invalid PNG frame {path}: {exc}") from exc


def encode_and_verify(args: argparse.Namespace) -> dict[str, object]:
    if args.fps not in (30, 60):
        raise EncodeError("Frame rate must be 30 or 60 fps")
    if args.frame_count < 1 or args.first_frame < 0:
        raise EncodeError("Frame count must be positive and first frame must be nonnegative")
    if args.width < 2 or args.height < 2 or args.width % 2 or args.height % 2:
        raise EncodeError("Width and height must be positive even numbers for yuv420p")

    frames = sequence_paths(args.input_pattern, args.first_frame, args.frame_count)
    inspect_pngs(frames, args.width, args.height)
    ffmpeg, ffprobe, version = discover_encoder(args.ffmpeg, args.ffprobe)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.overwrite:
        raise EncodeError(f"Output already exists: {output}; pass --overwrite to replace it")

    temp_fd, temp_name = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=".mp4", dir=output.parent)
    os.close(temp_fd)
    temp_output = Path(temp_name)
    temp_output.unlink()  # ffmpeg will create the target itself.
    try:
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-framerate", str(args.fps), "-start_number", str(args.first_frame),
            "-i", args.input_pattern, "-frames:v", str(args.frame_count),
            "-map", "0:v:0", "-an", "-c:v", "libx264", "-preset", args.preset,
            "-crf", str(args.crf), "-pix_fmt", "yuv420p", "-r", str(args.fps),
            "-threads", "1", "-map_metadata", "-1", "-movflags", "+faststart",
            "-f", "mp4", str(temp_output),
        ]
        run(command)

        probe = run([
            ffprobe, "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_read_frames,duration",
            "-show_entries", "format=format_name,duration,size", "-of", "json", str(temp_output),
        ])
        try:
            metadata = json.loads(probe.stdout)
            stream = metadata["streams"][0]
            decoded_frames = int(stream["nb_read_frames"])
            rate = stream["avg_frame_rate"]
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise EncodeError(f"ffprobe returned incomplete video metadata: {probe.stdout.strip()}") from exc
        if stream.get("codec_name") != "h264":
            raise EncodeError(f"Expected H.264 codec, found {stream.get('codec_name')!r}")
        if (stream.get("width"), stream.get("height")) != (args.width, args.height):
            raise EncodeError(f"Encoded dimensions are {stream.get('width')}x{stream.get('height')}, expected {args.width}x{args.height}")
        if stream.get("pix_fmt") != "yuv420p":
            raise EncodeError(f"Expected yuv420p pixel format, found {stream.get('pix_fmt')!r}")
        if rate != f"{args.fps}/1":
            raise EncodeError(f"Expected {args.fps}/1 fps, found {rate!r}")
        if decoded_frames != args.frame_count:
            raise EncodeError(f"Encoded frame count is {decoded_frames}; expected {args.frame_count}")
        duration = float(metadata.get("format", {}).get("duration", stream.get("duration", 0)))
        expected_duration = args.frame_count / args.fps
        if abs(duration - expected_duration) > 1.0 / args.fps:
            raise EncodeError(f"Duration is {duration:.6f}s; expected approximately {expected_duration:.6f}s")

        # Full sequential decode catches corrupt packets even when the header probes cleanly.
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-xerror", "-nostdin",
             "-i", str(temp_output), "-map", "0:v:0", "-f", "null", "-"])
        os.replace(temp_output, output)
        return {
            "output": str(output), "ffmpeg": ffmpeg, "ffprobe": ffprobe,
            "ffmpeg_version": version, "frames": decoded_frames, "fps": args.fps,
            "width": args.width, "height": args.height, "codec": "h264",
            "pixel_format": "yuv420p", "duration_seconds": duration,
            "decode_check": "passed",
        }
    finally:
        temp_output.unlink(missing_ok=True)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-pattern", required=True, help="Numbered PNG pattern, e.g. renders/shot_%%06d.png")
    p.add_argument("--output", required=True, help="Destination MP4")
    p.add_argument("--frame-count", required=True, type=int, help="Exact number of frames to encode")
    p.add_argument("--first-frame", type=int, default=1, help="First numbered frame (default: 1)")
    p.add_argument("--fps", required=True, type=int, choices=(30, 60), help="Output frame rate")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--crf", type=int, default=18, help="libx264 quality (0-51; default: 18)")
    p.add_argument("--preset", choices=("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"), default="medium")
    p.add_argument("--ffmpeg", help="Explicit local ffmpeg path; requires --ffprobe too")
    p.add_argument("--ffprobe", help="Explicit local matching ffprobe path")
    p.add_argument("--overwrite", action="store_true", help="Replace an existing output after the new file validates")
    return p


def main() -> int:
    args = parser().parse_args()
    if not 0 <= args.crf <= 51:
        parser().error("--crf must be between 0 and 51")
    try:
        report = encode_and_verify(args)
    except EncodeError as exc:
        print(f"encode_verify: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
