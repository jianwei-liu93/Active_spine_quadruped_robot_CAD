"""Focused malformed-payload checks for the AX1 manifest validator."""
import copy
import unittest

from src.animation_manifest_validate import ManifestValidationError, validate_manifest


IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
HASHES = {"spring_wire_r03.py": "f" * 64, "compression_spring_r07.py": "1" * 64}


def spring_record(frame_id, length_mm, instance_id="instance:LinkB"):
    anchor = lambda name, x: {"name": name, "owner_instance_id": "instance:LinkA",
                              "owner_local_mm": [x, 0.0, 0.0], "world_mm": [x, 0.0, 0.0]}
    return {
        "instance_id": instance_id, "generator": "spring", "frame_id": frame_id,
        "generator_module": "spring_wire_r03", "generator_source_sha256": dict(HASHES),
        "shape_parameters_sha256": "2" * 64, "local_shape_sha256": "3" * 64,
        "anchors": [anchor("seat_a", 0.0), anchor("seat_b", length_mm)],
        "coil_seats_world_mm": [[0.0, 0.0, 0.0], [length_mm, 0.0, 0.0]],
        "axis_world": [1.0, 0.0, 0.0], "coil_length_mm": length_mm,
        "free_length_mm": length_mm + 2.0, "kind": "extension",
    }


def cable_record(frame_id):
    anchor = lambda name: {"name": name, "owner_instance_id": "instance:LinkA",
                           "owner_local_mm": [1.0, 2.0, 3.0], "world_mm": [4.0, 5.0, 6.0]}
    names = ("wheel_terminal", "shell_entry", "shell_exit", "hip_entry", "hip_exit", "ankle_terminal")
    return {
        "instance_id": "instance:LinkB", "generator": "cable", "frame_id": frame_id,
        "generator_module": "build_tendon_r03", "generator_source_sha256": dict(HASHES),
        "shape_parameters_sha256": "2" * 64, "local_shape_sha256": "3" * 64,
        "primitives": [
            {"type": "line", "start_world_mm": [0.0, 0.0, 0.0], "end_world_mm": [1.0, 0.0, 0.0]},
            {"type": "arc", "start_world_mm": [1.0, 0.0, 0.0], "mid_world_mm": [1.5, 1.0, 0.0], "end_world_mm": [2.0, 0.0, 0.0]},
        ],
        "route_local_mm": {"side": 1, "points": [[0.0, 0.0, 0.0]]},
        "ankle_anchor": anchor("ankle_terminal"),
        "owner_anchors": [anchor(name) for name in names],
    }


def valid_manifest():
    app_names = ("LinkA", "LinkB")
    instance_ids = ["instance:" + name for name in app_names]
    return {
        "schema_version": "1.0",
        "source": {
            "cad_path": "cad/flexor.FCStd", "cad_sha256": "a" * 64,
            "cad_revision": "r08", "parameter_files_sha256": {"parameters/assembly.json": "b" * 64},
            "motion_map_sha256": "c" * 64, "exporter_revision": "deadbeef",
        },
        "conventions": {
            "world_axes": {"x": "forward", "y": "left", "z": "up"},
            "axis_mapping": "identity", "handedness": "right", "cad_length_unit": "mm",
            "blender_length_unit": "m", "angle_unit": "rad", "matrix_layout": "row_major_nested_rows",
            "vectors": "column", "quaternion_order": "wxyz", "reference_pose_id": "neutral_v1",
        },
        "instances": [
            {"instance_id": instance_ids[0], "freecad_object_name": app_names[0], "source_object_name": "SourceA",
             "part_number": "P-001", "mesh_id": "mesh:A", "group": "foreL", "motion_kind": "rigid",
             "geometry_kind": "rigid", "classification": "active", "local_frame": "LinkA_local"},
            {"instance_id": instance_ids[1], "freecad_object_name": app_names[1], "source_object_name": "SourceB",
             "part_number": "P-002", "mesh_id": "mesh:B", "group": "hindL", "motion_kind": "spring",
             "geometry_kind": "length_route_dependent", "classification": "passive", "local_frame": "LinkB_local"},
        ],
        "meshes": [
            {"mesh_id": "mesh:A", "local_units": "mm", "geometry_hash": "d" * 64,
             "asset_status": "NOT_EXPORTED_AX01", "local_geometry_status": "SOURCE_LOCAL_UNVERIFIED"},
            {"mesh_id": "mesh:B", "local_units": "mm", "geometry_hash": "e" * 64,
             "asset_status": "NOT_EXPORTED_AX01"},
        ],
        "instance_order": sorted(instance_ids),
        "frames": [],
    }


def add_frames(manifest):
    for i, (frame_id, time_s) in enumerate(zip(("neutral_v1", "smoke_1", "smoke_2"), (0.0, 1.0, 2.0))):
        shift = float(i)
        a = copy.deepcopy(IDENTITY)
        b = copy.deepcopy(IDENTITY)
        a[0][3] = shift
        b[1][3] = -2 * shift
        manifest["frames"].append({
            "frame_id": frame_id, "time_s": time_s,
            "commanded_order": ["spine_phase", "foreL_hip", "foreR_hip", "hindL_hip", "hindR_hip", "hind_wheel"],
            "commanded_rad": [shift, 0, 0, 0, 0, 0],
            "prescribed_knees_rad": {"foreL": 0, "foreR": 0, "hindL": 0, "hindR": 0},
            "leg_angles_rad": {"foreL": [0, 0], "foreR": [0, 0], "hindL": [0, 0], "hindR": [0, 0]},
            "passive_provenance": "PRESCRIBED_KINEMATIC",
            "transforms_mm": [a, b],
            "transforms_m": [[row[:] for row in a], [row[:] for row in b]],
            "quaternions_wxyz": [[1, 0, 0, 0], [1, 0, 0, 0]],
            "procedural_shapes": [spring_record(frame_id, 42.0 + shift)],
        })
    for frame in manifest["frames"]:
        for mm, metres in zip(frame["transforms_mm"], frame["transforms_m"]):
            for axis in range(3):
                metres[axis][3] = 0.001 * mm[axis][3]


class AnimationManifestValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = valid_manifest()
        add_frames(self.data)

    def assert_invalid(self, data, fragment):
        with self.assertRaisesRegex(ManifestValidationError, fragment):
            validate_manifest(data)

    def test_accepts_complete_numeric_ax1_payload(self):
        self.assertIsNone(validate_manifest(self.data))

    def test_rejects_duplicate_instance_identity(self):
        data = copy.deepcopy(self.data)
        data["instances"][1]["instance_id"] = data["instances"][0]["instance_id"]
        data["instances"][1]["freecad_object_name"] = data["instances"][0]["freecad_object_name"]
        self.assert_invalid(data, "duplicate instance id")

    def test_rejects_unsorted_or_incomplete_transform_order(self):
        data = copy.deepcopy(self.data)
        data["instance_order"] = list(reversed(data["instance_order"]))
        self.assert_invalid(data, "sorted order")

    def test_rejects_missing_transform_row(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["transforms_mm"].pop()
        self.assert_invalid(data, "expected 2 entries")

    def test_rejects_non_rotation_matrix(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["transforms_mm"][0][0][0] = 1.1
        self.assert_invalid(data, "not in SO\(3\)")

    def test_rejects_inconsistent_mm_to_m_translation(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["transforms_m"][0][0][3] += 0.01
        self.assert_invalid(data, "0.001 times")

    def test_rejects_quaternion_disagreement_and_sign_flip(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["quaternions_wxyz"][0] = [0, 1, 0, 0]
        self.assert_invalid(data, "disagrees with transform")
        data = copy.deepcopy(self.data)
        data["frames"][1]["quaternions_wxyz"][0] = [-1, 0, 0, 0]
        self.assert_invalid(data, "sign flips")

    def test_rejects_unordered_times_and_wrong_frame_count(self):
        data = copy.deepcopy(self.data)
        data["frames"][2]["time_s"] = 0.5
        self.assert_invalid(data, "times 0, 1, and 2")
        data = copy.deepcopy(self.data)
        data["frames"].pop()
        self.assert_invalid(data, "expected 3 entries")

    def test_rejects_degenerate_smoke_sample(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["commanded_rad"] = list(data["frames"][0]["commanded_rad"])
        self.assert_invalid(data, "smoke pose must differ from neutral")

    def test_rejects_missing_procedural_state(self):
        data = copy.deepcopy(self.data)
        data["frames"][2]["procedural_shapes"] = []
        self.assert_invalid(data, "missing procedural state")

    def test_rejects_knee_and_full_leg_state_mismatch(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["prescribed_knees_rad"]["hindL"] = 0.2
        self.assert_invalid(data, "knee entry disagrees")

    def test_rejects_full_leg_hip_mismatch(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["leg_angles_rad"]["foreL"][0] = 0.2
        self.assert_invalid(data, "hip entry disagrees with commanded_rad")

    def test_accepts_complete_cable_procedural_state(self):
        data = copy.deepcopy(self.data)
        for frame in data["frames"]:
            frame["procedural_shapes"] = [cable_record(frame["frame_id"])]
        self.assertIsNone(validate_manifest(data))

    def test_covers_ten_dynamic_instances_in_every_smoke_frame(self):
        data = copy.deepcopy(self.data)
        template_instance = data["instances"][1]
        template_mesh = data["meshes"][1]
        for suffix in "CDEFGHIJK":
            name = "Link" + suffix
            mesh_id = "mesh:" + suffix
            instance = copy.deepcopy(template_instance)
            instance.update(instance_id="instance:" + name, freecad_object_name=name,
                            source_object_name="Source" + suffix, part_number="P-00" + suffix,
                            mesh_id=mesh_id)
            mesh = copy.deepcopy(template_mesh)
            mesh.update(mesh_id=mesh_id)
            mesh["geometry_hash"] = format(ord(suffix), "02x") * 32
            data["instances"].append(instance)
            data["meshes"].append(mesh)
            for frame in data["frames"]:
                mm = copy.deepcopy(frame["transforms_mm"][1])
                mm[0][3] += ord(suffix)
                metres = copy.deepcopy(mm)
                for axis in range(3):
                    metres[axis][3] *= 0.001
                frame["transforms_mm"].append(mm)
                frame["transforms_m"].append(metres)
                frame["quaternions_wxyz"].append([1, 0, 0, 0])
                frame["procedural_shapes"].append(spring_record(frame["frame_id"], 42.0,
                                                                  "instance:" + name))
        data["instance_order"] = sorted(row["instance_id"] for row in data["instances"])
        self.assertIsNone(validate_manifest(data))
        data["frames"][1]["procedural_shapes"].pop()
        self.assert_invalid(data, "missing procedural state")

    def test_rejects_empty_and_unknown_procedural_records(self):
        data = copy.deepcopy(self.data)
        data["frames"][1]["procedural_shapes"] = [{}]
        self.assert_invalid(data, "missing fields")
        data = copy.deepcopy(self.data)
        data["frames"][1]["procedural_shapes"][0]["generator"] = "mesh_stretch"
        self.assert_invalid(data, "unknown procedural geometry generator")

    def test_rejects_unexported_mesh_claim_and_unknown_fields(self):
        data = copy.deepcopy(self.data)
        data["meshes"][0]["asset_status"] = "EXPORTED"
        self.assert_invalid(data, "must not claim an exported mesh")
        data = copy.deepcopy(self.data)
        data["mystery"] = True
        self.assert_invalid(data, "unhandled fields")


if __name__ == "__main__":
    unittest.main()
