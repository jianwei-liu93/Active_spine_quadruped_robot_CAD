"""Aggregate executed video QA after all scene renders and reviews exist.

The exploded and active-spine scenes retain the original r10 production
manifest. The coordinated gait scene uses its v2 manifest and must carry
matching render, native-screening, and articulation evidence.
"""
from pathlib import Path
import hashlib
import json
import statistics


ROOT = Path(__file__).resolve().parents[2]
BASE_MANIFEST = "animation/motion/production_r10.json"
COORDINATION_V2_MANIFEST = "animation/motion/production_coordination_v2_r10.json"


def load(rel):
    return json.loads((ROOT / rel).read_text())


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def assert_manifest_sources(manifest):
    """Reject stale producer/profile inputs before trusting derived evidence."""
    for rel, digest in manifest["production"]["source_files_sha256"].items():
        assert sha(rel) == digest, f"stale source for {manifest['_path']}: {rel}"


base_manifest = load(BASE_MANIFEST)
base_manifest["_path"] = BASE_MANIFEST
assert_manifest_sources(base_manifest)
snapshot = load("reports/animation/frozen_scenes.json")
assert sha(base_manifest["source"]["cad_path"]) == base_manifest["source"]["cad_sha256"] == snapshot["canonical_cad_sha256"]

scene_manifests = {}
results = []
for frozen in snapshot["scenes"]:
    name = Path(frozen["path"]).stem
    assert sha(frozen["path"]) == frozen["sha256"], f"stale frozen scene: {name}"

    readback = load(f"reports/animation/{name}_readback.json")
    scene_report = load(f"reports/animation/{name}_scene.json")
    assert readback["status"] == "PASS" and readback["blend_sha256"] == frozen["sha256"]
    assert scene_report["path"] == frozen["path"]

    # Use explicit per-scene provenance when the producer recorded it. The v2
    # coordination manifest is the required fallback for the coordinated shot.
    fallback = COORDINATION_V2_MANIFEST if name == "spine_leg_coordination" else BASE_MANIFEST
    manifest_path = readback.get("source_manifest") or scene_report.get("source_manifest") or fallback
    expected_manifest = COORDINATION_V2_MANIFEST if name == "spine_leg_coordination" else BASE_MANIFEST
    assert manifest_path == expected_manifest, f"unexpected source manifest for {name}: {manifest_path}"
    manifest = load(manifest_path)
    manifest["_path"] = manifest_path
    manifest_hash = sha(manifest_path)
    for evidence in (readback, scene_report):
        declared_path = evidence.get("source_manifest")
        if declared_path is not None:
            assert declared_path == expected_manifest, f"wrong source manifest in {name} evidence"
        declared = evidence.get("source_manifest_sha256")
        if declared is not None:
            assert declared == manifest_hash, f"stale source manifest hash in {name}"
    assert_manifest_sources(manifest)
    scene_manifests[name] = {"path": manifest_path, "sha256": manifest_hash}

    signature = load(f"animation/output/frames/{name}/render_signature.json")
    assert signature["blend_sha256"] == frozen["sha256"]
    video_report = load(f"reports/animation/{name}_video.json")
    assert video_report["decode_check"] == "passed" and video_report["width"] == 1920 and video_report["height"] == 1080
    review = load(f"reports/animation/{name}_decoded_review.json")
    item = next(x for x in review["results"] if x["shot"] == name)
    assert not item["basic_black_candidates"] and not item["default_metadata_mismatches"]
    video_path = f"animation/output/{name}.mp4"
    video_hash = sha(video_path)
    assert video_hash == item["video_sha256"]
    visual = load(f"reports/animation/{name}_visual_review.json")
    assert visual["status"].startswith("PASS") and visual["video_sha256"] == video_hash

    rows = [json.loads(line) for line in (ROOT / "animation/output/frames" / name / "render_progress.jsonl").read_text().splitlines()]
    assert len({x["frame"] for x in rows}) == video_report["frames"]
    seconds = [x["seconds"] for x in rows]
    results.append({
        "scene": name,
        "source_manifest": manifest_path,
        "source_manifest_sha256": manifest_hash,
        "blend_path": frozen["path"],
        "blend_sha256": frozen["sha256"],
        "video_path": video_path,
        "video_sha256": video_hash,
        "video_bytes": (ROOT / video_path).stat().st_size,
        "frames": video_report["frames"],
        "fps": video_report["fps"],
        "duration_s": video_report["duration_seconds"],
        "resolution": [video_report["width"], video_report["height"]],
        "decode": "PASS",
        "saved_scene_readback": "PASS",
        "visual_review": visual["status"],
        "representative_decoded_frames": len(item["extracted_frames"]),
        "review_clip_count": len(item["review_clips"]),
        "black_candidates": 0,
        "render_seconds_sum": sum(seconds),
        "median_seconds_per_frame": statistics.median(seconds),
        "mean_seconds_per_frame_excluding_startup": statistics.mean(seconds[1:]),
        "png_cache_bytes": sum(x["bytes"] for x in rows),
        "physical_instances": readback["physical_instances"],
        "max_sampled_world_vertex_error_mm": readback["max_imported_world_vertex_error_mm"],
    })


# The original r10 mechanical source claim remains tied to its original
# manifest and applies to the exploded and active-spine scenes. The v2 gait
# profile is an animation source change; it does not change the CAD claim.
base_scene_names = {"exploded_assembly", "active_spine_mechanism"}
assert base_scene_names.issubset(scene_manifests)
assert all(scene_manifests[n]["path"] == BASE_MANIFEST for n in base_scene_names)
v2 = load(COORDINATION_V2_MANIFEST)
v2["_path"] = COORDINATION_V2_MANIFEST
v2_hash = sha(COORDINATION_V2_MANIFEST)
assert scene_manifests["spine_leg_coordination"] == {"path": COORDINATION_V2_MANIFEST, "sha256": v2_hash}
assert v2["source"]["cad_sha256"] == base_manifest["source"]["cad_sha256"]

profile_path = "animation/coordination_paper_profile_v2.json"
profile_hash = sha(profile_path)
assert v2["production"]["source_files_sha256"][profile_path] == profile_hash
assert load(profile_path) == v2["production"]["paper_motion_profile"]

v2_timeline = v2["production"]["timelines"]["coordinated_spine_legs"]
assert sha(v2_timeline["path"]) == v2_timeline["sha256"], "v2 timeline differs from its production manifest"
clearance = load("reports/animation/coordination_v2_clearance.json")
assert clearance["status"] == "PASS_BOUNDED_NATIVE_SAMPLES", "v2 bounded native clearance screening did not pass"
assert clearance["profile_sha256"] == profile_hash
assert clearance["profile"] == v2["production"]["paper_motion_profile"]
assert clearance["native_sha256"] == v2["source"]["cad_sha256"]
assert clearance["continuous_clearance"] is False and clearance["full_campaign"] is False
assert clearance["loaded_equilibrium"] is False
assert clearance["records"] and all(r["status"] == "PASS" and not r["overlaps"] for r in clearance["records"])

observed = load("reports/animation/coordination_v2_observed_pairs_300.json")
assert observed["status"] == "PASS" and observed["samples"] == 300
assert observed["native_sha256"] == v2["source"]["cad_sha256"]
assert observed["profile_sha256"] == profile_hash
assert observed["profile"] == v2["production"]["paper_motion_profile"]
assert observed["pairs"]
assert observed["overlaps"] == []
assert observed["continuous_clearance"] is False

articulation = load("reports/animation/leg_articulation_v2.json")
coordination_frozen = next(x for x in snapshot["scenes"] if Path(x["path"]).stem == "spine_leg_coordination")
coordination_readback = load("reports/animation/spine_leg_coordination_readback.json")
coordination_scene = load("reports/animation/spine_leg_coordination_scene.json")
coordination_blend_hash = coordination_frozen["sha256"]
framing = load("reports/animation/coordination_v2_framing.json")
assert framing["status"] == "PASS" and framing["frames"] == 1200
assert framing["blend_sha256"] == coordination_blend_hash and framing["violations"] == []
assert articulation["status"] == "PASS" and articulation["scene"] == "spine_leg_coordination"
assert articulation["source_manifest"] == COORDINATION_V2_MANIFEST
assert articulation["source_manifest_sha256"] == v2_hash
assert articulation["blend_sha256"] == coordination_blend_hash
assert coordination_readback["blend_sha256"] == coordination_blend_hash
assert coordination_scene.get("packaged_blend_sha256", coordination_blend_hash) == coordination_blend_hash
assert coordination_readback.get("source_manifest", COORDINATION_V2_MANIFEST) == COORDINATION_V2_MANIFEST
assert coordination_scene.get("source_manifest", COORDINATION_V2_MANIFEST) == COORDINATION_V2_MANIFEST
assert articulation["timeline_path"] == v2_timeline["path"]
assert articulation["timeline_sha256_expected"] == v2_timeline["sha256"]
assert articulation["timeline_sha256_actual"] == v2_timeline["sha256"]
assert sha(articulation["timeline_path"]) == v2_timeline["sha256"]
events = load("reports/animation/coordination_v2_events.json")
assert events["status"] == "PASS" and events["timeline_sha256"] == v2_timeline["sha256"]
assert events["manifest_sha256"] == v2_hash
procedural_v2 = load("reports/animation/procedural_surface_comparison_v2.json")
assert procedural_v2["source_hashes"]["production_timeline_sha256"] == v2_timeline["sha256"]
assert procedural_v2["spring_record_count"] == procedural_v2["spring_finite_probe_pass_count"] == 8

coordination_checks = {
    "trajectory_validation": "reports/animation/production_coordination_v2.json",
    "all_frame_camera_bounds": "reports/animation/coordination_v2_framing.json",
    "event_validation": "reports/animation/coordination_v2_events.json",
    "native_procedural_comparison": "reports/animation/procedural_surface_comparison_v2.json",
    "source_manifest": COORDINATION_V2_MANIFEST,
    "source_manifest_sha256": v2_hash,
    "profile_path": profile_path,
    "profile_sha256": profile_hash,
    "timeline_path": v2_timeline["path"],
    "timeline_sha256": v2_timeline["sha256"],
    "native_clearance": {
        "status": "PASS_BOUNDED_NATIVE_SAMPLES",
        "evidence": "reports/animation/coordination_v2_clearance.json",
        "phase_samples_deg": clearance["phase_samples_deg"],
        "native_sha256": clearance["native_sha256"],
        "continuous_clearance": False,
        "full_campaign": False,
    },
    "observed_rigid_pairs": {
        "status": "PASS",
        "evidence": "reports/animation/coordination_v2_observed_pairs_300.json",
        "samples": observed["samples"],
        "rigid_pairs_checked": len(observed["pairs"]),
        "native_sha256": observed["native_sha256"],
    },
    "leg_articulation": {
        "status": "PASS",
        "evidence": "reports/animation/leg_articulation_v2.json",
        "blend_sha256": articulation["blend_sha256"],
        "max_relative_rotation_error_rad": articulation["max_relative_rotation_error_rad"],
        "max_torso_relative_foot_pad_center_error_mm": articulation["max_torso_relative_foot_pad_center_error_mm"],
    },
}

source_snapshot = load("animation/source_snapshot_r10.json")
report = {
    "date": "2026-10-13",
    "AX2": "PASS",
    "AX3": "PASS",
    "AX4": "PASS_WITH_DOCUMENTED_LIMITATIONS",
    "cad_revision": "r10",
    "mechanical_source_commit": source_snapshot["source_git_commit"],
    "mechanical_source_cad_sha256": base_manifest["source"]["cad_sha256"],
    "mechanical_source_hash_scope": "Original r10 CAD and parameter hashes plus the original production_r10.json source manifest; this claim applies to exploded_assembly and active_spine_mechanism. The coordinated video uses a separate v2 animation profile/source manifest.",
    "original_mechanical_source_hashes_unchanged": True,
    "source_to_world_transform_verified": True,
    "runtime": load("reports/animation/blender_render_runtime.json"),
    "videos": results,
    "coordination_v2": coordination_checks,
    "timeline_validation": "reports/animation/production_offline_validation.json",
    "native_procedural_comparison": "reports/animation/procedural_surface_comparison.json",
    "limitations": [
        "Prescribed kinematics, with separate prescribed knees and independently prescribed winding wheel; no passive loads or dynamic locomotion simulated.",
        "Cables are dashed routing guides; physical slack geometry remains unresolved.",
        "Baked motion is verified at rendered integer frame times; subframe retiming or motion blur requires resampling/validation.",
        "Exploded sequence is a presentation overview with intentional isolation cuts, not a verified assembly/service instruction. Peripheral geometry can cross the graphics area briefly during detail-camera transitions.",
        "Finite spring surface probes and source mesh tolerance support rendered approximation, not BRep equivalence.",
        "The v2 native clearance result is bounded to its listed phases and checked bodies; the 300-sample observed-pair report covers only its named rigid clip/cap and fore/hind foot pairs. Neither establishes continuous or full-campaign clearance.",
        "Existing manufacturing blockers and finite r10 clearance scopes are unchanged.",
        "Large editable Blender projects and native comparison/frame caches are local ignored artifacts; tracked sources reproduce them.",
    ],
}
(ROOT / "reports/animation/final_video_qa.json").write_text(json.dumps(report, indent=2) + "\n")

snapshot["render_status"] = "COMPLETE_ENCODE_DECODE_AND_REVIEW"
(ROOT / "reports/animation/frozen_scenes.json").write_text(json.dumps(snapshot, indent=2) + "\n")
for result in results:
    p = ROOT / "reports/animation" / (result["scene"] + "_scene.json")
    data = json.loads(p.read_text())
    data["render_status"] = "COMPLETE_ENCODE_DECODE_AND_REVIEW"
    data["packaged_blend_sha256"] = result["blend_sha256"]
    data["source_manifest"] = result["source_manifest"]
    data["source_manifest_sha256"] = result["source_manifest_sha256"]
    data["video_sha256"] = result["video_sha256"]
    p.write_text(json.dumps(data, indent=2) + "\n")

print(json.dumps({
    "AX4": report["AX4"],
    "videos": len(results),
    "frames": sum(x["frames"] for x in results),
    "render_seconds": sum(x["render_seconds_sum"] for x in results),
    "coordination_v2": coordination_checks,
}, indent=2))
