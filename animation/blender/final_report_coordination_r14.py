#!/usr/bin/env python3
"""Aggregate final QA for the standalone r14 spine/leg coordination presentation cut.

This report is intentionally separate from final_video_qa.json, which covers
the three technical videos. Run only after the r14 render, encode, readback,
decoded review, human visual review, and adjacent-frame review are complete.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
NAME = "spine_leg_coordination_s2_r14"
CONFIG = "animation/coordination_s2_style_r14.json"
BUILDER = "animation/blender/build_coordination_s2_r14.py"
PRESENTATION = "animation/motion/presentation_coordination_s2_r14.json"
READBACK = f"reports/animation/{NAME}_readback.json"
VIDEO_REPORT = f"reports/animation/{NAME}_video.json"
PRODUCTION = f"reports/animation/{NAME}_production.json"
DECODED_REVIEW = f"reports/animation/{NAME}_decoded_review.json"
VISUAL_REVIEW = f"reports/animation/{NAME}_visual_review.json"
ADJACENT_REVIEW = f"reports/animation/{NAME}_adjacent_frames.json"
LEG_ARTICULATION = "reports/animation/leg_articulation_r14.json"
CLEARANCE = "reports/animation/coordination_r14_changed_clearance.json"
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
            "Render signature does not match full-resolution 60 fps r14 settings")

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


def validate_leg_articulation(report: dict[str, Any], manifest: dict[str, Any],
                              manifest_sha: str, manifest_path: str) -> dict[str, Any]:
    require(report.get("status") == "PASS", "r14 leg-articulation report did not pass")
    require(report.get("source_manifest") == manifest_path,
            "Leg-articulation report names a different production manifest")
    require(report.get("source_manifest_sha256") == manifest_sha,
            "Leg-articulation report is tied to a different production manifest revision")
    timeline = manifest.get("production", {}).get("timelines", {}).get("coordinated_spine_legs", {})
    require(report.get("timeline_path") == timeline.get("path") and
            report.get("timeline_sha256_expected") == timeline.get("sha256") and
            report.get("timeline_sha256_actual") == timeline.get("sha256"),
            "Leg-articulation report is tied to a different r14 coordinated timeline")
    legs = report.get("legs")
    required_legs = ("foreL", "foreR", "hindL", "hindR")
    require(isinstance(legs, dict) and all(leg in legs for leg in required_legs),
            "Leg-articulation report does not cover all four legs")
    measured = {}
    for leg in required_legs:
        row = legs[leg]
        hip = float(row.get("torso_relative_thigh_rotation_excursion_deg", float("nan")))
        knee = float(row.get("thigh_relative_shank_knee_rotation_excursion_deg", float("nan")))
        require(math.isfinite(hip) and hip > 60.0,
                f"{leg} hip excursion is not greater than 60 degrees")
        require(math.isfinite(knee) and knee > 0.0,
                f"{leg} knee articulation is not moving")
        measured[leg] = {"hip_excursion_deg": hip, "knee_excursion_deg": knee}
    return {"status": "PASS", "legs": measured, "evidence": LEG_ARTICULATION}


def validate_changed_clearance(clearance: dict[str, Any], cad_sha: str,
                               manifest: dict[str, Any]) -> dict[str, Any]:
    phase_samples = clearance.get("phase_samples_deg")
    records = clearance.get("records")
    scope = clearance.get("scope")
    affected = clearance.get("affected_instances")
    pair_count = clearance.get("pair_count_per_phase")
    require(clearance.get("status") == "PASS_BOUNDED_CHANGED_PAIRS" and
            clearance.get("native_sha256") == cad_sha and
            isinstance(phase_samples, list) and len(phase_samples) == 9 and
            len(set(phase_samples)) == 9 and isinstance(records, list) and len(records) == 9 and
            all(row.get("pairs_checked") == 32032 for row in records) and
            clearance.get("total_pairs_checked") == 288288 and
            isinstance(affected, list) and len(affected) == 77 and
            isinstance(scope, str) and "affected" in scope.lower() and "455" in scope and
            "at least one" in scope.lower() and "all pairs" not in scope.lower() and
            isinstance(pair_count, int) and pair_count == 32032 and
            pair_count * len(phase_samples) == 288288 and
            clearance.get("continuous_clearance") is False and
            clearance.get("full_campaign") is False and
            clearance.get("loaded_equilibrium") is False,
            "Changed-pair r14 clearance evidence does not match its native identity, scope, or 9-phase counts")
    require(phase_samples == [0, 18, 90, 135, 180, 198, 240, 270, 330] and
            [row.get('phase_deg') for row in records] == phase_samples and
            clearance.get('phases_completed') == 9 and
            clearance.get('overlaps') == [] and clearance.get('errors') == [] and
            all(row.get('status') == 'PASS' and row.get('overlaps') == [] and
                row.get('guide_warnings') == [] and row.get('physical_instances') == 455 and
                row.get('valid_single_finite_solids') == 455 and
                row.get('bbox_excluded', -1) + row.get('occ_checks', -1) == pair_count
                for row in records), 'Incomplete, failed or reordered clearance phase evidence')
    require(all(clearance.get(key) is True for key in
                ('native_file_unchanged', 'input_files_unchanged', 'document_unchanged', 'source_shapes_unchanged')) and
            clearance.get('fabrication_release') is False,
            'Clearance input preservation or qualification scope differs')
    profile_path = 'animation/coordination_paper_profile_v2.json'
    profile = manifest['production']['paper_motion_profile']
    require(clearance.get('profile') == profile == read_json(profile_path) and
            clearance.get('profile_sha256') == sha256(profile_path),
            'Clearance motion profile differs from production')
    frozen = clearance.get('input_files_sha256', {})
    require(bool(frozen) and frozen.get(profile_path) == clearance['profile_sha256'],
            'Clearance frozen-input manifest is missing')
    for rel, expected in frozen.items():
        pinned_file(rel, expected, 'Clearance input')
    neutral = manifest['frames'][0]['leg_angles_rad']
    for row in records:
        cycle = math.tau * profile['presentation_frequency_hz'] * (row['phase_deg'] / (360 * .2))
        expected_theta = cycle + profile['spine_phase_origin_rad']
        lag = profile['hind_backswing_lag_rad']
        expected_wheel = math.radians(45 + 45 * math.cos(cycle - lag))
        require(abs(row['theta_rad'] - expected_theta) <= 1e-12 and
                abs(row['wheel_angle_rad'] - expected_wheel) <= 1e-12,
                'Clearance spine/wheel input differs from the production profile')
        for tag, q in neutral.items():
            fore = tag.startswith('fore')
            signal = math.cos(cycle - lag + (profile['fore_phase_offset_rad'] if fore else 0.))
            hip = math.radians(profile['hip_cad_midpoints_deg']['fore' if fore else 'hind']) - profile['hip_half_excursion_rad'] * signal
            knee = q[1] + math.radians(profile['knee_half_excursion_deg']) * signal
            require(max(abs(a - b) for a, b in zip(row['leg_angles_rad'][tag], (hip, knee))) <= 1e-12,
                    'Clearance leg input differs from the production profile')
        payload = json.dumps([row['theta_rad'], row['leg_angles_rad'], row['wheel_angle_rad']],
                             sort_keys=True, allow_nan=False, separators=(',', ':')).encode()
        require(hashlib.sha256(payload).hexdigest() == row.get('input_sha256'),
                'Clearance phase input digest differs')
    return {
        "status": clearance["status"],
        "phase_samples_deg": phase_samples,
        "affected_instance_count": len(affected),
        "pairs_per_phase": pair_count,
        "total_changed_pair_checks": pair_count * len(phase_samples),
        "continuous_clearance": False,
        "full_campaign": False,
        "loaded_equilibrium": False,
        "profile_sha256": clearance['profile_sha256'],
        "frozen_inputs_checked": len(frozen),
    }


def main() -> None:
    config = read_json(CONFIG)
    require(config.get("scene") == NAME and config.get("fps") == 60 and config.get("frame_count") == 1500,
            "r14 S2 style config identity, frame count, or frame rate differs")
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
    require(presentation.get("version") == "presentation-root-transform-r14-v1" and
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
    require(manifest.get("source", {}).get("cad_revision") == "r14" and
            manifest.get("source", {}).get("cad_path") == "cad/flexor_r14_robot.FCStd",
            "Production manifest does not identify the r14 native CAD source")
    instances = manifest.get("instances", [])
    source_identity = manifest.get("production", {}).get("source_geometry_identity", {})
    require(len(manifest.get("instance_order", [])) == 455 and len(instances) == 455 and
            len({row.get("source_object_name") for row in instances}) == 108 and
            source_identity.get("status") == "PASS" and source_identity.get("sources_compared") == 108 and
            source_identity.get("canonical_cad_sha256") == source_cad_sha,
            "r14 production source identity did not pass for 108 sources")
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
            "Presentation manifest does not pin the expected r14 config and builder")
    for rel, expected in manifest.get("production", {}).get("source_files_sha256", {}).items():
        pinned_dependencies[rel] = pinned_file(rel, expected, "Production source dependency")
    for rel, expected in presentation.get('helper_files_sha256', {}).items():
        pinned_dependencies[rel] = pinned_file(rel, expected, 'Presentation helper dependency')
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
            "Encode report output path differs from the r14 MP4 path")
    video_sha = sha256(VIDEO)
    frame_evidence = validate_frame_evidence(video_report, signature, readback)
    decoded_evidence = validate_decoded_review(decoded_review, video_sha)
    visual_status = review_pass(visual_review, video_sha, "Visual review")
    adjacent_status = review_pass(adjacent_review, video_sha, "Adjacent-frame review")

    require(readback.get("physical_instances") == 455 and readback.get("distinct_source_samples_checked") == 100 and
            readback.get("procedural_instances") == 10,
            "Readback physical instance inventory or distinct source identity count differs")
    require(readback.get('procedural_shape_samples_checked') == 3000 and
            readback.get('maximum_evaluated_procedural_local_vertex_error_m', float('inf')) <= 1e-7 and
            readback.get('maximum_procedural_eval_time_error', float('inf')) <= 1e-4,
            'Stored/evaluated procedural shape or sample-time checks did not pass')
    require(readback.get("transform_frames_checked") and len(readback["transform_frames_checked"]) >= 100,
            "Readback lacks its 100 representative relative-pose checks")
    clearance_path = CLEARANCE
    clearance = read_json(clearance_path)
    clearance_evidence = validate_changed_clearance(clearance, cad_sha, manifest)
    articulation_report = read_json(LEG_ARTICULATION)
    require(Path(articulation_report.get('blend_path', '')).resolve() == (ROOT / presentation['source_scene_path']).resolve() and
            articulation_report.get('blend_sha256') == presentation['source_scene_sha256'],
            'Articulation evidence is tied to a different standalone source scene')
    articulation_evidence = validate_leg_articulation(
        articulation_report, manifest, source_manifest_sha, source_manifest_path)

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
        "leg_articulation_evidence": sha256(LEG_ARTICULATION),
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
            "source_identity": {"status": source_identity["status"],
                                "sources_compared": source_identity["sources_compared"]},
            "standalone_embedded_assets": "PASS by fresh-process serialized-scene readback; 455 physical instances and 10 procedural instances",
        },
        "scene_readback": {
            "status": "PASS",
            "blend_sha256": blend_sha,
            "physical_component_count": 455,
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
            **clearance_evidence,
            "statement": "The r14 screen checks affected pairs at nine finite phases; unaffected pairs, continuous clearance, full-campaign clearance, and loaded equilibrium are not certified.",
        },
        "leg_articulation": articulation_evidence,
        "limitations": [
            "Body motion is prescribed for presentation; the animation does not model dynamics, contact forces, or a validated locomotion gait.",
            "Feet may slide relative to the floor during the prescribed body motion; floor clearance is verified, foot-ground dynamics are not.",
            "Mechanism detail shots intentionally crop unrelated modules and may crop toes; the overview shots frame the complete physical assembly.",
            "Motion blur is disabled.",
            "Changed-pair r14 clearance evidence covers affected pairs at nine finite phases; it is not continuous clearance or a full all-pairs campaign.",
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
        raise SystemExit(f"final_report_coordination_r14: QA failed: {exc}") from exc
