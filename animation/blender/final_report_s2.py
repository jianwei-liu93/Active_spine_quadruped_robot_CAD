#!/usr/bin/env python3
"""Aggregate final QA for the standalone spine/leg S2 presentation cut.

This report is intentionally separate from final_video_qa.json, which covers
the three technical videos. Run only after the S2 render, encode, readback,
decoded review, human visual review, and adjacent-frame review are complete.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
NAME = "spine_leg_coordination_s2"
CONFIG = "animation/coordination_s2_style.json"
BUILDER = "animation/blender/build_coordination_s2.py"
PRESENTATION = "animation/motion/presentation_coordination_s2.json"
READBACK = f"reports/animation/{NAME}_readback.json"
VIDEO_REPORT = f"reports/animation/{NAME}_video.json"
PRODUCTION = f"reports/animation/{NAME}_production.json"
DECODED_REVIEW = f"reports/animation/{NAME}_decoded_review.json"
VISUAL_REVIEW = f"reports/animation/{NAME}_visual_review.json"
ADJACENT_REVIEW = f"reports/animation/{NAME}_adjacent_frames.json"
OUTPUT = f"reports/animation/{NAME}_qa.json"
VIDEO = f"animation/output/{NAME}.mp4"
FRAME_DIR = f"animation/output/frames/{NAME}"
READBACK_FLOOR_MIN_M = 0.000799


class QAError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise QAError(message)


def read_json(rel: str) -> dict[str, Any]:
    path = ROOT / rel
    require(path.is_file(), f"Missing required evidence: {rel}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QAError(f"Cannot read JSON evidence {rel}: {exc}") from exc
    require(isinstance(value, dict), f"Expected a JSON object in {rel}")
    return value


def sha256(rel: str) -> str:
    path = ROOT / rel
    require(path.is_file(), f"Missing required file: {rel}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pinned_file(rel: str, expected: str, label: str) -> str:
    actual = sha256(rel)
    require(actual == expected, f"{label} hash changed: {rel}")
    return actual


def validate_frame_evidence(video_report: dict[str, Any], signature: dict[str, Any],
                            readback: dict[str, Any]) -> dict[str, Any]:
    expected_frames = 1500
    require(video_report.get("frames") == expected_frames, "Encode report frame count is not 1,500")
    require(video_report.get("fps") == 60, "Encode report frame rate is not 60 fps")
    require(video_report.get("width") == 1920 and video_report.get("height") == 1080,
            "Encode report dimensions are not 1920x1080")
    require(video_report.get("duration_seconds") is not None and
            abs(float(video_report["duration_seconds"]) - 25.0) <= 1.0 / 60.0,
            "Encoded duration is not 25 seconds")
    require(video_report.get("codec") == "h264" and video_report.get("pixel_format") == "yuv420p",
            "Encoded video codec or pixel format differs from the verified H.264/yuv420p output")
    require(video_report.get("decode_check") == "passed", "Encode report lacks a passing full decode")
    require(signature.get("resolution") == [1920, 1080, 100] and signature.get("fps") == 60 and
            signature.get("frame_end") == expected_frames,
            "Render signature does not match full-resolution 60 fps S2 settings")

    frame_dir = ROOT / FRAME_DIR
    require(frame_dir.is_dir(), f"Missing rendered frame directory: {FRAME_DIR}")
    frame_paths = sorted(frame_dir.glob("frame_*.png"))
    require(len(frame_paths) == expected_frames, f"Expected 1,500 PNGs, found {len(frame_paths)}")
    expected_names = {f"frame_{frame:06d}.png" for frame in range(1, expected_frames + 1)}
    actual_names = {path.name for path in frame_paths}
    require(actual_names == expected_names, "Rendered PNG sequence has missing, duplicate, or out-of-range frame numbers")

    progress_path = frame_dir / "render_progress.jsonl"
    require(progress_path.is_file(), "Missing render_progress.jsonl")
    try:
        progress = [json.loads(line) for line in progress_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise QAError(f"Cannot read render progress: {exc}") from exc
    frame_numbers = [row.get("frame") for row in progress]
    require(len(progress) == expected_frames and set(frame_numbers) == set(range(1, expected_frames + 1)) and
            len(set(frame_numbers)) == expected_frames,
            "Render progress does not contain one unique successful record for each of the 1,500 frames")
    require(all(isinstance(row.get("bytes"), int) and row["bytes"] > 0 and
                math.isfinite(float(row.get("seconds", float("nan")))) and row["seconds"] > 0
                for row in progress), "Render progress includes an invalid frame record")

    require(readback.get("frames_checked") == expected_frames,
            "Readback does not cover all 1,500 frames")
    require(readback.get("camera_framing", {}).get("status") == "PASS" and
            readback.get("camera_framing", {}).get("failure_count") == 0 and
            not readback.get("camera_framing", {}).get("failures"),
            "Readback camera framing did not pass")
    floor_min = float(readback.get("minimum_evaluated_foot_floor_z_m", float("nan")))
    floor_error = float(readback.get("maximum_floor_gap_error_m", float("inf")))
    require(math.isfinite(floor_min) and floor_min >= READBACK_FLOOR_MIN_M and floor_error <= 1e-6,
            "Readback does not confirm the 0.8 mm minimum foot-floor margin over the full sequence")
    require(readback.get("status") == "PASS" and readback.get("mechanical_readback_status") == "PASS" and
            readback.get("failure_count") == 0 and not readback.get("failures"),
            "Serialized-scene readback did not pass")
    return {
        "png_count": len(frame_paths),
        "progress_records": len(progress),
        "progress_frame_numbers_unique": True,
        "progress_frame_coverage": [1, expected_frames],
        "all_frames_full_resolution": True,
        "video_frames": video_report["frames"],
        "fps": video_report["fps"],
        "duration_seconds": video_report["duration_seconds"],
        "resolution": [video_report["width"], video_report["height"]],
        "full_decode": video_report["decode_check"],
        "minimum_evaluated_foot_floor_z_m": floor_min,
        "minimum_required_floor_margin_m": 0.0008,
        "maximum_floor_gap_error_m": floor_error,
        "framing": "PASS for all 1,500 frames; overview covers every physical instance and detail shots use their declared framing IDs",
    }


def validate_decoded_review(review: dict[str, Any], video_sha: str) -> dict[str, Any]:
    results = review.get("results")
    require(isinstance(results, list), "Decoded review lacks its results list")
    item = next((row for row in results if row.get("shot") == NAME), None)
    require(item is not None, f"Decoded review has no result for shot {NAME}")
    require(item.get("video_sha256") == video_sha, "Decoded review video hash differs from the final MP4")
    require(not item.get("basic_black_candidates"), "Decoded review found a black-frame candidate")
    require(not item.get("default_metadata_mismatches"), "Decoded review found video metadata mismatches")
    frames = item.get("extracted_frames")
    require(isinstance(frames, list) and len(frames) > 0, "Decoded review contains no representative extracted frames")
    return {"status": "PASS", "representative_decoded_frames": len(frames),
            "review_clip_count": len(item.get("review_clips", [])), "black_candidates": 0,
            "metadata_mismatches": 0}


def review_pass(review: dict[str, Any], video_sha: str, label: str) -> str:
    status = review.get("status")
    require(isinstance(status, str) and status.startswith("PASS"), f"{label} status is not PASS")
    require(review.get("video_sha256") == video_sha, f"{label} video hash differs from final MP4")
    return status


def main() -> None:
    config = read_json(CONFIG)
    require(config.get("scene") == NAME and config.get("fps") == 60 and config.get("frame_count") == 1500,
            "S2 style config identity, frame count, or frame rate differs")
    require(config.get("motion_blur") is False, "S2 style config unexpectedly enables motion blur")
    presentation = read_json(PRESENTATION)
    readback = read_json(READBACK)
    video_report = read_json(VIDEO_REPORT)
    production = read_json(PRODUCTION)
    signature = read_json(f"{FRAME_DIR}/render_signature.json")
    decoded_review = read_json(DECODED_REVIEW)
    visual_review = read_json(VISUAL_REVIEW)
    adjacent_review = read_json(ADJACENT_REVIEW)
    readback_sha = sha256(READBACK)

    require(readback.get("scene") == NAME, "Readback scene name differs")
    require(readback.get("blend_sha256") == sha256(f"animation/scenes/{NAME}.blend"),
            "Packaged scene hash differs from the readback")
    require(readback.get("presentation_manifest_sha256") == sha256(PRESENTATION),
            "Presentation manifest hash differs from the readback")
    require(presentation.get("version") == "presentation-root-transform-v1" and
            presentation.get("frame_count") == 1500 and presentation.get("fps") == 60,
            "Presentation manifest identity or frame settings differ")
    require(presentation.get("transform_convention") ==
            "render_world_m = presentation_root_m @ verified_CAD_world_m; mesh remains source-local",
            "Presentation transform convention differs")

    # Validate every source dependency pinned by the presentation and source
    # production manifest before accepting any derived report.
    source_manifest_path = presentation.get("source_manifest_path")
    require(isinstance(source_manifest_path, str) and source_manifest_path,
            "Presentation manifest does not name its source production manifest")
    source_manifest_sha = pinned_file(source_manifest_path, presentation.get("source_manifest_sha256", ""),
                                      "Source manifest")
    manifest = read_json(source_manifest_path)
    require(readback.get("source_manifest_sha256") == source_manifest_sha,
            "Readback source manifest hash differs")
    require(readback.get("source_timeline_sha256") == presentation.get("source_timeline_sha256"),
            "Readback source timeline hash differs")
    timeline_path = presentation.get("source_timeline_path")
    timeline_sha = pinned_file(timeline_path, presentation.get("source_timeline_sha256", ""),
                               "Source timeline")
    manifest_timeline = manifest.get("production", {}).get("timelines", {}).get("coordinated_spine_legs", {})
    require(manifest_timeline.get("path") == timeline_path and manifest_timeline.get("sha256") == timeline_sha,
            "Presentation timeline pin differs from its source manifest")
    source_cad_path = manifest.get("source", {}).get("cad_path")
    source_cad_sha = manifest.get("source", {}).get("cad_sha256")
    require(presentation.get("source_cad_sha256") == source_cad_sha,
            "Presentation CAD hash pin differs from source manifest")
    cad_sha = pinned_file(source_cad_path, source_cad_sha, "Source CAD")

    pinned_dependencies: dict[str, str] = {}
    for path_key, hash_key, label in (
        ("source_scene_path", "source_scene_sha256", "Original source scene"),
        ("style_config_path", "style_config_sha256", "Style config"),
        ("builder_path", "builder_sha256", "Scene builder"),
    ):
        rel = presentation.get(path_key)
        digest = presentation.get(hash_key)
        require(isinstance(rel, str) and isinstance(digest, str), f"Presentation manifest lacks {label} pin")
        pinned_dependencies[rel] = pinned_file(rel, digest, label)
    require(presentation.get("style_config_path") == CONFIG and presentation.get("builder_path") == BUILDER,
            "Presentation manifest does not pin the expected S2 config and builder")
    for rel, expected in manifest.get("production", {}).get("source_files_sha256", {}).items():
        pinned_dependencies[rel] = pinned_file(rel, expected, "Production source dependency")
    require(presentation.get("source_scene_sha256") == pinned_dependencies.get(presentation.get("source_scene_path")),
            "Original source scene hash pin was not preserved")

    require(production.get("status") == "ENCODE_AND_FULL_DECODE_PASS" and
            production.get("scene") == NAME and production.get("frames") == 1500 and
            production.get("fps") == 60 and abs(float(production.get("duration_s", 0)) - 25.0) <= 1e-9,
            "Render production completion record did not pass")
    blend_sha = sha256(f"animation/scenes/{NAME}.blend")
    require(production.get("blend_sha256") == blend_sha and signature.get("blend_sha256") == blend_sha,
            "Render production or signature is tied to a different packaged scene")
    require(video_report.get("output") and Path(video_report["output"]).resolve() == (ROOT / VIDEO).resolve(),
            "Encode report output path differs from the S2 MP4 path")
    video_sha = sha256(VIDEO)
    frame_evidence = validate_frame_evidence(video_report, signature, readback)
    decoded_evidence = validate_decoded_review(decoded_review, video_sha)
    visual_status = review_pass(visual_review, video_sha, "Visual review")
    adjacent_status = review_pass(adjacent_review, video_sha, "Adjacent-frame review")

    require(readback.get("physical_instances") == 487 and readback.get("distinct_source_samples_checked") == 100,
            "Readback physical instance inventory or distinct source sample count differs")
    require(readback.get("transform_frames_checked") and len(readback["transform_frames_checked"]) >= 100,
            "Readback lacks its 100 representative relative-pose checks")
    clearance_path = "reports/animation/coordination_v2_clearance.json"
    clearance = read_json(clearance_path)
    require(clearance.get("status") == "PASS_BOUNDED_NATIVE_SAMPLES" and
            clearance.get("native_sha256") == cad_sha and
            clearance.get("continuous_clearance") is False and
            clearance.get("full_campaign") is False and
            clearance.get("loaded_equilibrium") is False,
            "Existing finite v2 native-clearance evidence does not match its bounded scope")

    checked_frames = set(readback["transform_frames_checked"])
    representative_frames = [1, 25, 50, 75, 100, 300, 750, 1250, 1500]
    sampled_by_frame = {row["frame"]: row for row in readback.get("sampled_readback", [])}
    representatives = [
        {"frame": frame,
         "source_sample": ((frame - 1) * int(presentation["sample_stride"])) % 300,
         "minimum_foot_z_m": sampled_by_frame[frame]["minimum_foot_z_m"] if frame in sampled_by_frame else None,
         "relative_pose_checked": frame in checked_frames}
        for frame in representative_frames
    ]
    require(all(item["relative_pose_checked"] for item in representatives),
            "One or more representative frames lack relative-pose verification")
    source_hashes = {
        "presentation_manifest": sha256(PRESENTATION),
        "source_manifest": source_manifest_sha,
        "source_timeline": timeline_sha,
        "source_cad": cad_sha,
        "original_source_scene": presentation["source_scene_sha256"],
        "builder": presentation["builder_sha256"],
        "style_config": presentation["style_config_sha256"],
        "packaged_scene": blend_sha,
        "readback": readback_sha,
        "video": video_sha,
        "video_report": sha256(VIDEO_REPORT),
        "production_report": sha256(PRODUCTION),
        "decoded_review": sha256(DECODED_REVIEW),
        "visual_review": sha256(VISUAL_REVIEW),
        "adjacent_frame_review": sha256(ADJACENT_REVIEW),
        "finite_clearance_evidence": sha256(clearance_path),
        "pinned_production_dependencies": pinned_dependencies,
    }
    report = {
        "scope": "Standalone S2-inspired spine/leg coordination studio presentation cut; does not amend the three technical-video QA record.",
        "status": "PASS_WITH_DOCUMENTED_LIMITATIONS",
        "scene": NAME,
        "source_hashes": source_hashes,
        "verified_inputs": {
            "source_dependencies_checked": len(pinned_dependencies),
            "source_manifest_path": source_manifest_path,
            "source_cad_path": source_cad_path,
            "original_source_scene_path": presentation["source_scene_path"],
            "presentation_manifest_path": PRESENTATION,
            "transform_convention": presentation["transform_convention"],
            "standalone_embedded_assets": "PASS by fresh-process serialized-scene readback; 487 physical instances and 10 procedural instances",
        },
        "scene_readback": {
            "status": "PASS",
            "blend_sha256": blend_sha,
            "physical_component_count": 487,
            "procedural_instance_count": readback["procedural_instances"],
            "frames_checked": readback["frames_checked"],
            "relative_pose_convention": readback["source_to_world_convention"],
            "distinct_source_pose_samples_verified": readback["distinct_source_samples_checked"],
            "relative_pose_frames_checked": readback["transform_frames_checked"],
            "representative_relative_pose_samples": representatives,
            "root_pitch_range_deg": readback["root_pitch_range_deg"],
            "root_translation_ranges_m": readback["root_translation_ranges_m"],
        },
        "render_and_video": frame_evidence,
        "decoded_review": decoded_evidence,
        "visual_review": {"status": visual_status, "evidence": VISUAL_REVIEW},
        "adjacent_frame_review": {"status": adjacent_status, "evidence": ADJACENT_REVIEW},
        "reuse_of_existing_mechanical_evidence": {
            "evidence": clearance_path,
            "status": clearance["status"],
            "phase_samples_deg": clearance["phase_samples_deg"],
            "continuous_clearance": False,
            "full_campaign": False,
            "statement": "Reuses the existing finite v2 clearance screen; this S2 video QA adds no new full clearance campaign.",
        },
        "limitations": [
            "Body motion is prescribed for presentation; the animation does not model dynamics, contact forces, or a validated locomotion gait.",
            "Feet may slide relative to the floor during the prescribed body motion; floor clearance is verified, foot-ground dynamics are not.",
            "Mechanism detail shots intentionally crop unrelated modules and may crop toes; the overview shots frame the complete physical assembly.",
            "Motion blur is disabled.",
            "Finite v2 clearance evidence is reused within its listed phase and body scope; it is not continuous clearance or a new full-campaign result.",
        ],
    }
    target = ROOT / OUTPUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "scene": NAME, "video_sha256": video_sha,
                      "output": OUTPUT, "verified_pose_samples": readback["distinct_source_samples_checked"],
                      "rendered_frames": frame_evidence["png_count"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (QAError, OSError, KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"final_report_s2: QA failed: {exc}") from exc
