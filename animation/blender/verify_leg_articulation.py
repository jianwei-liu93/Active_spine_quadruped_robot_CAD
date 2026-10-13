"""Verify that coordinated-scene leg motion is articulated relative to the torso.

Run in background Blender after opening the saved scene, for example:
    blender -b animation/scenes/spine_leg_coordination.blend \
      --python animation/blender/verify_leg_articulation.py -- \
      --report reports/animation/leg_articulation_readback.json

The verifier compares evaluated Blender object transforms with the scene's
versioned coordinated_spine_legs source timeline. It never edits the scene.
"""
import argparse
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[2]
SCENE_NAME = "spine_leg_coordination"
LEGS = ("foreL", "foreR", "hindL", "hindR")
KEY_FRAMES = (1, 76, 226)
TIMELINE_FRAME_COUNT = 300
ROTATION_TOLERANCE_RAD = 1.0e-4
POINT_TOLERANCE_MM = 0.02


def fail(message):
    raise AssertionError(message)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, help="JSON report output path")
    parser.add_argument("--manifest", help="Override the scene source_manifest")
    return parser.parse_args(argv)


def matrix_from_rows(rows):
    return Matrix(tuple(tuple(float(x) for x in row) for row in rows))


def rotation(matrix):
    # Blender may store scale in an object's matrix; remove it before comparing
    # orientation so the measurement is an actual rotation.
    return matrix.to_3x3().to_quaternion().normalized()


def quat_error(a, b):
    """Shortest angular distance between two orientations, in radians."""
    d = (a.inverted() @ b).normalized()
    return 2.0 * math.atan2(math.sqrt(d.x*d.x+d.y*d.y+d.z*d.z), abs(d.w))


def max_pair_excursion(track):
    return max(quat_error(a, b) for i, a in enumerate(track) for b in track[i + 1:])


def path_from_scene(scene, override):
    if override:
        candidate = Path(override)
        return candidate if candidate.is_absolute() else ROOT / candidate
    raw = scene.get("source_manifest") or scene.get("manifest_path")
    if raw:
        candidate = Path(str(raw))
        candidate = candidate if candidate.is_absolute() else ROOT / candidate
        if candidate.exists():
            return candidate
    # The existing package and the coordination-v2 package are both valid
    # source names. Prefer the v2 package if it is present in a v2 scene.
    candidates = (
        ROOT / "animation/motion/production_coordination_v2_r10.json",
        ROOT / "animation/motion/production_r10.json",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    fail("No source manifest found (scene source_manifest or production manifest)")


def object_map(scene):
    result = {}
    for obj in scene.objects:
        instance_id = obj.get("instance_id")
        if instance_id:
            if instance_id in result:
                fail("Duplicate instance_id in scene: " + str(instance_id))
            result[str(instance_id)] = obj
    return result


def local_bbox_center(obj):
    corners = [Vector(corner) for corner in obj.bound_box]
    return sum(corners, Vector()) / len(corners)


def series_for_timeline(path, count):
    result = []
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for frame, line in enumerate(stream, start=1):
            if frame > count:
                break
            result.append(json.loads(line))
    if len(result) < count:
        fail("Timeline has %d samples; expected at least %d" % (len(result), count))
    return result


def relative_rotation(frame_matrices, index_by_id, leg, proximal, distal):
    torso_id = "instance:Torso_" + ("fore" if leg.startswith("fore") else "hind")
    q_torso = rotation(frame_matrices[index_by_id[torso_id]])
    q_prox = rotation(frame_matrices[index_by_id["instance:" + leg + "_" + proximal]])
    q_dist = rotation(frame_matrices[index_by_id["instance:" + leg + "_" + distal]])
    return q_torso.inverted() @ q_prox, q_torso.inverted() @ q_dist, q_prox.inverted() @ q_dist


def main():
    args = parse_args()
    if SCENE_NAME not in bpy.data.scenes:
        fail("Required scene is missing: " + SCENE_NAME)
    scene = bpy.data.scenes[SCENE_NAME]
    bpy.context.window.scene = scene

    manifest_path = path_from_scene(scene, args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    timeline_info = manifest.get("production", {}).get("timelines", {}).get("coordinated_spine_legs")
    if not timeline_info:
        fail("Manifest has no production.timelines.coordinated_spine_legs entry")
    timeline_path = ROOT / timeline_info["path"]
    source = series_for_timeline(timeline_path, TIMELINE_FRAME_COUNT)

    objects = object_map(scene)
    order = manifest["instance_order"]
    index_by_id = {instance_id: index for index, instance_id in enumerate(order)}
    required = []
    for leg in LEGS:
        required.extend(("instance:Torso_" + ("fore" if leg.startswith("fore") else "hind"),
                         "instance:" + leg + "_thigh", "instance:" + leg + "_shank",
                         "instance:" + leg + "_FootPad"))
    required = sorted(set(required))
    missing = sorted(set(required) - set(order))
    if missing:
        fail("Manifest is missing required physical instances: " + ", ".join(missing))
    missing = sorted(set(required) - set(objects))
    if missing:
        fail("Scene is missing required instance_id objects: " + ", ".join(missing))

    # Build expected manifest matrices and local foot-pad center points.
    expected_matrices = []
    for sample in source:
        transforms = sample["transforms_m"]
        if len(transforms) != len(order):
            fail("Timeline transforms_m length does not match instance_order")
        expected_matrices.append([matrix_from_rows(rows) for rows in transforms])

    evaluated = {instance_id: [] for instance_id in required}
    for frame in range(1, TIMELINE_FRAME_COUNT + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for instance_id in required:
            evaluated[instance_id].append(objects[instance_id].matrix_world.copy())

    metrics = {}
    max_rotation_error = 0.0
    max_pad_error_mm = 0.0
    expected_hip_excursions = []
    expected_knee_excursions = []
    for leg in LEGS:
        torso_id = "instance:Torso_" + ("fore" if leg.startswith("fore") else "hind")
        thigh_id = "instance:" + leg + "_thigh"
        shank_id = "instance:" + leg + "_shank"
        pad_id = "instance:" + leg + "_FootPad"
        expected_hip, expected_knee, expected_shank_torso = [], [], []
        actual_hip, actual_knee, actual_shank_torso = [], [], []
        expected_pad, actual_pad = [], []
        local_center = local_bbox_center(objects[pad_id])

        for sample_index in range(TIMELINE_FRAME_COUNT):
            mats = expected_matrices[sample_index]
            torso_m = mats[index_by_id[torso_id]]
            thigh_m = mats[index_by_id[thigh_id]]
            shank_m = mats[index_by_id[shank_id]]
            pad_m = mats[index_by_id[pad_id]]
            eq_hip, eq_shank, eq_knee = relative_rotation(mats, index_by_id, leg, "thigh", "shank")
            expected_hip.append(eq_hip)
            expected_knee.append(eq_knee)
            expected_shank_torso.append(eq_shank)
            expected_pad.append(torso_m.inverted() @ (pad_m @ local_center))

            torso_a = rotation(evaluated[torso_id][sample_index])
            thigh_a = rotation(evaluated[thigh_id][sample_index])
            shank_a = rotation(evaluated[shank_id][sample_index])
            ah = torso_a.inverted() @ thigh_a
            ak = thigh_a.inverted() @ shank_a
            ass = torso_a.inverted() @ shank_a
            actual_hip.append(ah)
            actual_knee.append(ak)
            actual_shank_torso.append(ass)
            pad_a = evaluated[torso_id][sample_index].inverted() @ (
                evaluated[pad_id][sample_index] @ local_center)
            actual_pad.append(pad_a)

            for qa, qe in ((ah, eq_hip), (ak, eq_knee), (ass, eq_shank)):
                max_rotation_error = max(max_rotation_error, quat_error(qe, qa))
            max_pad_error_mm = max(max_pad_error_mm, (pad_a - expected_pad[-1]).length * 1000.0)

        hip_exc = max_pair_excursion(expected_hip)
        knee_exc = max_pair_excursion(expected_knee)
        actual_hip_exc = max_pair_excursion(actual_hip)
        actual_knee_exc = max_pair_excursion(actual_knee)
        expected_hip_excursions.append(hip_exc)
        expected_knee_excursions.append(knee_exc)
        if abs(actual_hip_exc - hip_exc) > ROTATION_TOLERANCE_RAD:
            fail("%s thigh excursion differs from manifest by %.9g rad" % (leg, abs(actual_hip_exc - hip_exc)))
        if abs(actual_knee_exc - knee_exc) > ROTATION_TOLERANCE_RAD:
            fail("%s knee excursion differs from manifest by %.9g rad" % (leg, abs(actual_knee_exc - knee_exc)))
        metrics[leg] = {
            "instance_ids": {"torso": torso_id, "thigh": thigh_id, "shank": shank_id, "foot_pad": pad_id},
            "torso_relative_thigh_rotation_excursion_rad": actual_hip_exc,
            "torso_relative_thigh_rotation_excursion_deg": math.degrees(actual_hip_exc),
            "thigh_relative_shank_knee_rotation_excursion_rad": actual_knee_exc,
            "thigh_relative_shank_knee_rotation_excursion_deg": math.degrees(actual_knee_exc),
            "torso_relative_shank_rotation_excursion_rad": max_pair_excursion(actual_shank_torso),
            "torso_relative_shank_rotation_excursion_deg": math.degrees(max_pair_excursion(actual_shank_torso)),
            "foot_pad_point_excursion_mm": max((a - b).length * 1000.0
                                                 for i, a in enumerate(actual_pad) for b in actual_pad[i + 1:]),
            "manifest_thigh_excursion_rad": hip_exc,
            "manifest_knee_excursion_rad": knee_exc,
            "key_frames": {},
        }
        for frame in KEY_FRAMES:
            i = frame - 1
            metrics[leg]["key_frames"][str(frame)] = {
                "torso_relative_thigh_rotation_from_frame1_rad": quat_error(actual_hip[0], actual_hip[i]),
                "thigh_relative_shank_rotation_from_frame1_rad": quat_error(actual_knee[0], actual_knee[i]),
                "torso_relative_foot_pad_center_mm": [round(float(x) * 1000.0, 6) for x in actual_pad[i]],
            }

    if max_rotation_error > ROTATION_TOLERANCE_RAD:
        fail("Relative articulation differs from coordinated source timeline: %.9g rad" % max_rotation_error)
    if max_pad_error_mm > POINT_TOLERANCE_MM:
        fail("Torso-relative foot-pad point differs from source timeline: %.9g mm" % max_pad_error_mm)
    if min(expected_hip_excursions) < math.radians(5.0):
        fail("Hip motion is effectively fixed relative to torso")
    if min(expected_knee_excursions) < math.radians(5.0):
        fail("Knee motion is effectively fixed relative to thigh")

    report = {
        "status": "PASS",
        "scene": SCENE_NAME,
        "blender": bpy.app.version_string,
        "blend_path": bpy.data.filepath,
        "blend_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
        "source_manifest": str(manifest_path.relative_to(ROOT)) if manifest_path.is_relative_to(ROOT) else str(manifest_path),
        "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "timeline_path": timeline_info["path"],
        "timeline_sha256_expected": timeline_info.get("sha256"),
        "timeline_sha256_actual": hashlib.sha256(timeline_path.read_bytes()).hexdigest(),
        "frames_checked": {"key_frames": list(KEY_FRAMES), "full_timeline_frames": TIMELINE_FRAME_COUNT},
        "comparison": "actual torso-local segment rotations and foot-pad center point vs manifest matrices",
        "max_relative_rotation_error_rad": max_rotation_error,
        "max_torso_relative_foot_pad_center_error_mm": max_pad_error_mm,
        "tolerances": {"rotation_rad": ROTATION_TOLERANCE_RAD, "point_mm": POINT_TOLERANCE_MM},
        "legs": metrics,
    }
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("LEG_ARTICULATION_PASS " + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
