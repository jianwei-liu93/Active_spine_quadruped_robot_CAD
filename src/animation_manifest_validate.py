"""Standard-library validator for the compact AX1 pose manifest v1 contract.

The JSON Schema describes the structural shape; this module also checks the
cross-field and numeric invariants that JSON Schema cannot express. It has no
FreeCAD, NumPy, or jsonschema dependency.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


SCHEMA_VERSION = "1.0"
COMMAND_ORDER = ("spine_phase", "foreL_hip", "foreR_hip",
                 "hindL_hip", "hindR_hip", "hind_wheel")
LEG_TAGS = ("foreL", "foreR", "hindL", "hindR")
HIP_COMMAND_INDEX = {"foreL": 1, "foreR": 2, "hindL": 3, "hindR": 4}
REQUIRED_CABLE_ANCHORS = {"wheel_terminal", "shell_entry", "shell_exit",
                          "hip_entry", "hip_exit", "ankle_terminal"}
FRAME_IDS = ("neutral_v1", "smoke_1", "smoke_2")
PASSIVE_PROVENANCE = {"PRESCRIBED_KINEMATIC", "QUASISTATIC_MODEL",
                      "DYNAMIC_SIMULATION", "SOURCE_MEASURED"}
AXES = {"x": "forward", "y": "left", "z": "up"}
TOL_SO3 = 1e-8
TOL_SCALE = 1e-9
TOL_QUAT = 1e-8


class ManifestValidationError(ValueError):
    """Raised when a manifest violates the AX1 interface contract."""


def _fail(where, problem):
    raise ManifestValidationError(f"{where}: {problem}")


def _object(value, where, required, optional=()):
    if not isinstance(value, dict):
        _fail(where, "expected an object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing:
        _fail(where, "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        _fail(where, "unhandled fields: " + ", ".join(sorted(extra)))
    return value


def _string(value, where):
    if not isinstance(value, str) or not value.strip():
        _fail(where, "expected a non-empty string")
    return value


def _number(value, where):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(where, "expected a finite number")
    return float(value)


def _sequence(value, where, length=None):
    if not isinstance(value, list):
        _fail(where, "expected an array")
    if length is not None and len(value) != length:
        _fail(where, f"expected {length} entries, got {len(value)}")
    return value


def _walk_finite(value, where="manifest"):
    if isinstance(value, float) and not math.isfinite(value):
        _fail(where, "non-finite JSON number")
    if isinstance(value, dict):
        for key, child in value.items():
            _walk_finite(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_finite(child, f"{where}[{index}]")


def _mat4(value, where):
    rows = _sequence(value, where, 4)
    matrix = [_sequence(row, f"{where}[{i}]", 4) for i, row in enumerate(rows)]
    return [[_number(x, f"{where}[{i}][{j}]") for j, x in enumerate(row)]
            for i, row in enumerate(matrix)]


def _det3(r):
    return (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
            - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
            + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))


def _check_rotation(r, where):
    det_error = abs(_det3(r) - 1.0)
    orth_error = max(abs(sum(r[k][i] * r[k][j] for k in range(3)) - (1.0 if i == j else 0.0))
                       for i in range(3) for j in range(3))
    if det_error > TOL_SO3 or orth_error > TOL_SO3:
        _fail(where, f"rotation is not in SO(3) (orthogonality={orth_error:.3g}, |det-1|={det_error:.3g})")


def _quat_rotation(q, where):
    values = _sequence(q, where, 4)
    w, x, y, z = [_number(v, f"{where}[{i}]") for i, v in enumerate(values)]
    norm = math.sqrt(w*w + x*x + y*y + z*z)
    if abs(norm - 1.0) > TOL_QUAT:
        _fail(where, f"quaternion norm is {norm:.12g}, expected 1")
    return [[1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
            [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
            [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]]


def _hash(value, where):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdefABCDEF" for c in value):
        _fail(where, "expected a 64-character SHA-256 hex digest")


def _point3(value, where):
    point = _sequence(value, where, 3)
    return [_number(component, f"{where}[{i}]") for i, component in enumerate(point)]


def _owner_anchor(anchor, where, instance_by_id, require_name=True):
    required = ("name", "owner_instance_id", "owner_local_mm", "world_mm") if require_name else (
        "owner_instance_id", "owner_local_mm", "world_mm")
    optional = tuple(set(anchor) - set(required)) if isinstance(anchor, dict) else ()
    anchor = _object(anchor, where, required, optional)
    if "name" in anchor:
        _string(anchor["name"], where + ".name")
    owner_id = _string(anchor["owner_instance_id"], where + ".owner_instance_id")
    if owner_id not in instance_by_id:
        _fail(where + ".owner_instance_id", "unknown physical instance")
    _point3(anchor["owner_local_mm"], where + ".owner_local_mm")
    _point3(anchor["world_mm"], where + ".world_mm")
    return anchor


def _procedural_shape(shape, where, frame, instance_by_id):
    required = ("instance_id", "generator", "frame_id", "generator_module",
                "generator_source_sha256", "shape_parameters_sha256", "local_shape_sha256")
    shape = _object(shape, where, required,
                    tuple(set(shape) - set(required)) if isinstance(shape, dict) else ())
    iid = _string(shape["instance_id"], where + ".instance_id")
    if iid not in instance_by_id:
        _fail(where + ".instance_id", "unknown physical instance")
    if instance_by_id[iid]["geometry_kind"] != "length_route_dependent":
        _fail(where + ".instance_id", "procedural geometry must map to a length/route-dependent instance")
    if shape["frame_id"] != frame["frame_id"]:
        _fail(where + ".frame_id", "must identify its containing frame")
    if shape["generator"] not in ("spring", "cable"):
        _fail(where + ".generator", "unknown procedural geometry generator")
    _string(shape["generator_module"], where + ".generator_module")
    source_hashes = shape["generator_source_sha256"]
    if isinstance(source_hashes, str):
        _hash(source_hashes, where + ".generator_source_sha256")
    elif isinstance(source_hashes, dict) and source_hashes:
        for module_path, digest in source_hashes.items():
            _string(module_path, where + ".generator_source_sha256 key")
            _hash(digest, where + ".generator_source_sha256." + module_path)
    else:
        _fail(where + ".generator_source_sha256", "expected a SHA-256 string or non-empty module-to-SHA256 map")
    _hash(shape["shape_parameters_sha256"], where + ".shape_parameters_sha256")
    _hash(shape["local_shape_sha256"], where + ".local_shape_sha256")

    if shape["generator"] == "spring":
        required_spring = ("anchors", "coil_seats_world_mm", "axis_world", "coil_length_mm",
                           "free_length_mm", "kind")
        missing = set(required_spring) - shape.keys()
        if missing:
            _fail(where, "missing spring fields: " + ", ".join(sorted(missing)))
        anchors = _sequence(shape["anchors"], where + ".anchors")
        if len(anchors) < 2:
            _fail(where + ".anchors", "spring requires at least two anchors")
        for i, anchor in enumerate(anchors):
            _owner_anchor(anchor, f"{where}.anchors[{i}]", instance_by_id)
        seats = _sequence(shape["coil_seats_world_mm"], where + ".coil_seats_world_mm", 2)
        for i, seat in enumerate(seats):
            _point3(seat, f"{where}.coil_seats_world_mm[{i}]")
        _point3(shape["axis_world"], where + ".axis_world")
        coil_length = _number(shape["coil_length_mm"], where + ".coil_length_mm")
        free_length = _number(shape["free_length_mm"], where + ".free_length_mm")
        if coil_length <= 0 or free_length <= 0:
            _fail(where, "spring coil_length_mm and free_length_mm must be positive")
        if shape["kind"] not in ("extension", "compression"):
            _fail(where + ".kind", "unknown spring kind")
    else:
        required_cable = ("primitives", "route_local_mm", "ankle_anchor", "owner_anchors")
        missing = set(required_cable) - shape.keys()
        if missing:
            _fail(where, "missing cable fields: " + ", ".join(sorted(missing)))
        primitives = _sequence(shape["primitives"], where + ".primitives")
        if not primitives:
            _fail(where + ".primitives", "cable route must contain at least one primitive")
        for i, primitive in enumerate(primitives):
            primitive_where = f"{where}.primitives[{i}]"
            primitive = _object(primitive, primitive_where,
                                ("type", "start_world_mm", "end_world_mm"),
                                tuple(set(primitive) - {"type", "start_world_mm", "end_world_mm"})
                                if isinstance(primitive, dict) else ())
            if primitive["type"] not in ("line", "arc"):
                _fail(primitive_where + ".type", "unknown cable primitive kind")
            _point3(primitive["start_world_mm"], primitive_where + ".start_world_mm")
            _point3(primitive["end_world_mm"], primitive_where + ".end_world_mm")
            if primitive["type"] == "arc":
                if "mid_world_mm" not in primitive:
                    _fail(primitive_where, "arc primitive requires mid_world_mm")
                _point3(primitive["mid_world_mm"], primitive_where + ".mid_world_mm")
        if not isinstance(shape["route_local_mm"], dict) or not shape["route_local_mm"]:
            _fail(where + ".route_local_mm", "expected a non-empty route object")
        _owner_anchor(shape["ankle_anchor"], where + ".ankle_anchor", instance_by_id, require_name=False)
        owner_anchors = _sequence(shape["owner_anchors"], where + ".owner_anchors")
        names = []
        if len(owner_anchors) != len(REQUIRED_CABLE_ANCHORS):
            _fail(where + ".owner_anchors", "expected exactly six named cable owner anchors")
        for i, anchor in enumerate(owner_anchors):
            validated = _owner_anchor(anchor, f"{where}.owner_anchors[{i}]", instance_by_id)
            names.append(validated["name"])
        if set(names) != REQUIRED_CABLE_ANCHORS or len(set(names)) != len(names):
            _fail(where + ".owner_anchors", "must contain wheel_terminal, shell_entry, shell_exit, hip_entry, hip_exit, and ankle_terminal exactly once")
    return shape


def validate_manifest(data):
    """Validate AX1 payload semantics; return None or raise a useful error."""
    _walk_finite(data)
    root = _object(data, "manifest", ("schema_version", "source", "conventions",
                  "instances", "meshes", "instance_order", "frames"))
    if root["schema_version"] != SCHEMA_VERSION:
        _fail("schema_version", f"expected {SCHEMA_VERSION!r}")

    source = _object(root["source"], "source", ("cad_path", "cad_sha256", "cad_revision",
                    "parameter_files_sha256", "motion_map_sha256", "exporter_revision"))
    for key in ("cad_path", "cad_revision", "exporter_revision"):
        _string(source[key], "source." + key)
    for key in ("cad_sha256", "motion_map_sha256"):
        _hash(source[key], "source." + key)
    hashes = source["parameter_files_sha256"]
    if not isinstance(hashes, dict) or not hashes:
        _fail("source.parameter_files_sha256", "expected a non-empty path-to-SHA256 object")
    for path, digest in hashes.items():
        _string(path, "source.parameter_files_sha256 key")
        _hash(digest, "source.parameter_files_sha256." + path)

    conv = _object(root["conventions"], "conventions", ("world_axes", "axis_mapping", "handedness",
                    "cad_length_unit", "blender_length_unit", "angle_unit", "matrix_layout",
                    "vectors", "quaternion_order", "reference_pose_id"))
    if conv["world_axes"] != AXES:
        _fail("conventions.world_axes", "expected +X forward, +Y left, +Z up")
    fixed_conventions = {"axis_mapping": "identity", "handedness": "right", "cad_length_unit": "mm",
                         "blender_length_unit": "m", "angle_unit": "rad",
                         "matrix_layout": "row_major_nested_rows", "vectors": "column",
                         "quaternion_order": "wxyz"}
    for key, expected in fixed_conventions.items():
        if conv[key] != expected:
            _fail("conventions." + key, f"expected {expected!r}")
    reference_pose_id = _string(conv["reference_pose_id"], "conventions.reference_pose_id")

    instances = _sequence(root["instances"], "instances")
    meshes = _sequence(root["meshes"], "meshes")
    if not instances or not meshes:
        _fail("instances/meshes", "both arrays must be non-empty")
    instance_by_id, seen_names = {}, set()
    required_instance = ("instance_id", "freecad_object_name", "source_object_name", "part_number",
                         "mesh_id", "group", "motion_kind", "geometry_kind", "classification", "local_frame")
    for i, row in enumerate(instances):
        where = f"instances[{i}]"
        row = _object(row, where, required_instance)
        for field in required_instance:
            _string(row[field], where + "." + field)
        iid = row["instance_id"]
        if not iid.startswith("instance:") or iid != "instance:" + row["freecad_object_name"]:
            _fail(where + ".instance_id", "must equal 'instance:' + freecad_object_name")
        if iid in instance_by_id:
            _fail(where + ".instance_id", "duplicate instance id")
        if row["freecad_object_name"] in seen_names:
            _fail(where + ".freecad_object_name", "duplicate FreeCAD object name")
        if row["geometry_kind"] not in ("rigid", "length_route_dependent", "static_auxiliary"):
            _fail(where + ".geometry_kind", "unsupported geometry kind")
        if row["classification"] not in ("active", "passive", "fixed"):
            _fail(where + ".classification", "expected active, passive, or fixed")
        seen_names.add(row["freecad_object_name"])
        instance_by_id[iid] = row

    mesh_by_id = {}
    for i, row in enumerate(meshes):
        where = f"meshes[{i}]"
        row = _object(row, where, ("mesh_id", "local_units", "geometry_hash", "asset_status"),
                      ("local_geometry_status",))
        mesh_id = _string(row["mesh_id"], where + ".mesh_id")
        if mesh_id in mesh_by_id:
            _fail(where + ".mesh_id", "duplicate mesh id")
        if row["local_units"] != "mm":
            _fail(where + ".local_units", "AX1 source mesh coordinates must be in mm")
        _hash(row["geometry_hash"], where + ".geometry_hash")
        if row["asset_status"] != "NOT_EXPORTED_AX01":
            _fail(where + ".asset_status", "AX1 numeric prototype must not claim an exported mesh")
        if "local_geometry_status" in row:
            _string(row["local_geometry_status"], where + ".local_geometry_status")
        mesh_by_id[mesh_id] = row

    referenced_meshes = {row["mesh_id"] for row in instance_by_id.values()}
    unknown_meshes = referenced_meshes - mesh_by_id.keys()
    unused_meshes = mesh_by_id.keys() - referenced_meshes
    if unknown_meshes:
        _fail("instances.mesh_id", "unmapped mesh IDs: " + ", ".join(sorted(unknown_meshes)))
    if unused_meshes:
        _fail("meshes", "unreferenced mesh IDs: " + ", ".join(sorted(unused_meshes)))

    order = _sequence(root["instance_order"], "instance_order")
    if any(not isinstance(v, str) for v in order):
        _fail("instance_order", "expected instance ID strings")
    expected_order = sorted(instance_by_id)
    if order != expected_order:
        _fail("instance_order", "must contain each instance ID exactly once in sorted order")

    frames = _sequence(root["frames"], "frames", 3)
    if conv["reference_pose_id"] != FRAME_IDS[0]:
        _fail("conventions.reference_pose_id", f"expected {FRAME_IDS[0]!r}")
    previous_time = None
    previous_quats = None
    reference_command = None
    reference_transforms = None
    preceding_command = None
    required_frame = ("frame_id", "time_s", "commanded_order", "commanded_rad",
                      "prescribed_knees_rad", "passive_provenance", "transforms_mm",
                      "transforms_m", "quaternions_wxyz", "procedural_shapes")
    for frame_index, frame in enumerate(frames):
        where = f"frames[{frame_index}]"
        frame = _object(frame, where, required_frame, ("leg_angles_rad",))
        if frame["frame_id"] != FRAME_IDS[frame_index]:
            _fail(where + ".frame_id", f"expected {FRAME_IDS[frame_index]!r}")
        time_s = _number(frame["time_s"], where + ".time_s")
        if time_s != float(frame_index):
            _fail(where + ".time_s", "AX1 smoke samples must use times 0, 1, and 2 seconds")
        if previous_time is not None and time_s <= previous_time:
            _fail(where + ".time_s", "frame times must be strictly increasing")
        previous_time = time_s
        if frame["commanded_order"] != list(COMMAND_ORDER):
            _fail(where + ".commanded_order", "does not match the six-coordinate project order")
        command = _sequence(frame["commanded_rad"], where + ".commanded_rad", 6)
        for i, angle in enumerate(command):
            _number(angle, f"{where}.commanded_rad[{i}]")
        command_values = [float(angle) for angle in command]
        if frame["passive_provenance"] not in PASSIVE_PROVENANCE:
            _fail(where + ".passive_provenance", "unsupported passive-state provenance")

        knees = _object(frame["prescribed_knees_rad"], where + ".prescribed_knees_rad", LEG_TAGS)
        for tag in LEG_TAGS:
            _number(knees[tag], f"{where}.prescribed_knees_rad.{tag}")
        if "leg_angles_rad" in frame:
            leg_angles = _object(frame["leg_angles_rad"], where + ".leg_angles_rad", LEG_TAGS)
            for tag in LEG_TAGS:
                pair = _sequence(leg_angles[tag], f"{where}.leg_angles_rad.{tag}", 2)
                hip = _number(pair[0], f"{where}.leg_angles_rad.{tag}[0]")
                knee = _number(pair[1], f"{where}.leg_angles_rad.{tag}[1]")
                if abs(hip - command_values[HIP_COMMAND_INDEX[tag]]) > 1e-12:
                    _fail(f"{where}.leg_angles_rad.{tag}", "hip entry disagrees with commanded_rad")
                if abs(knee - float(knees[tag])) > 1e-12:
                    _fail(f"{where}.leg_angles_rad.{tag}", "knee entry disagrees with prescribed_knees_rad")

        mm_rows = _sequence(frame["transforms_mm"], where + ".transforms_mm", len(order))
        m_rows = _sequence(frame["transforms_m"], where + ".transforms_m", len(order))
        quats = _sequence(frame["quaternions_wxyz"], where + ".quaternions_wxyz", len(order))
        shape_rows = _sequence(frame["procedural_shapes"], where + ".procedural_shapes")
        current_quats = []
        current_transforms = []
        for i, (mm_payload, m_payload, quat) in enumerate(zip(mm_rows, m_rows, quats)):
            label = f"{where}[{order[i]}]"
            mm = _mat4(mm_payload, label + ".transforms_mm")
            metres = _mat4(m_payload, label + ".transforms_m")
            for matrix, suffix in ((mm, "mm"), (metres, "m")):
                bottom = matrix[3]
                if max(abs(bottom[j] - (1.0 if j == 3 else 0.0)) for j in range(4)) > 1e-12:
                    _fail(label + ".transforms_" + suffix, "invalid homogeneous bottom row")
                _check_rotation([row[:3] for row in matrix[:3]], label + ".transforms_" + suffix)
            for r in range(3):
                for c in range(3):
                    if abs(mm[r][c] - metres[r][c]) > TOL_SCALE:
                        _fail(label, "mm and m transforms have different rotations")
            for axis in range(3):
                if abs(metres[axis][3] - 0.001 * mm[axis][3]) > TOL_SCALE:
                    _fail(label, "metre translation is not 0.001 times millimetre translation")
            qrot = _quat_rotation(quat, label + ".quaternion_wxyz")
            rotation = [row[:3] for row in mm[:3]]
            if max(abs(qrot[r][c] - rotation[r][c]) for r in range(3) for c in range(3)) > TOL_QUAT:
                _fail(label + ".quaternion_wxyz", "quaternion rotation disagrees with transform")
            current_quats.append([float(x) for x in quat])
            current_transforms.append(mm)
            if previous_quats is not None:
                dot = sum(a * b for a, b in zip(previous_quats[i], current_quats[i]))
                if dot < -1e-12:
                    _fail(label + ".quaternion_wxyz", "quaternion sign flips between adjacent frames")

        seen_shape_ids = set()
        required_procedural = {iid for iid, row in instance_by_id.items()
                               if row["geometry_kind"] == "length_route_dependent"}
        for i, shape in enumerate(shape_rows):
            shape_where = f"{where}.procedural_shapes[{i}]"
            shape = _procedural_shape(shape, shape_where, frame, instance_by_id)
            iid = shape["instance_id"]
            if iid in seen_shape_ids:
                _fail(shape_where + ".instance_id", "duplicate procedural record for one instance in a frame")
            seen_shape_ids.add(iid)
        missing_shapes = required_procedural - seen_shape_ids
        if missing_shapes:
            _fail(where + ".procedural_shapes", "missing procedural state for: " + ", ".join(sorted(missing_shapes)))
        if frame_index == 0:
            reference_command = command_values
            reference_transforms = current_transforms
        else:
            if max(abs(a - b) for a, b in zip(command_values, reference_command)) <= 1e-12:
                _fail(where + ".commanded_rad", "smoke pose must differ from neutral")
            pose_delta = max(abs(current_transforms[i][r][c] - reference_transforms[i][r][c])
                             for i in range(len(order)) for r in range(4) for c in range(4))
            if pose_delta <= 1e-12:
                _fail(where + ".transforms_mm", "smoke pose transforms must differ from neutral")
            if preceding_command is not None and max(abs(a - b) for a, b in zip(command_values, preceding_command)) <= 1e-12:
                _fail(where + ".commanded_rad", "the two smoke samples must be distinct")
        preceding_command = command_values
        previous_quats = current_quats
    return None


def load_and_validate(path):
    """Load a JSON manifest and validate it, rejecting nonstandard NaN tokens."""
    def reject_constant(token):
        raise ManifestValidationError(f"invalid JSON numeric constant: {token}")

    with Path(path).open("r", encoding="utf-8") as stream:
        data = json.load(stream, parse_constant=reject_constant)
    validate_manifest(data)
    return data


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python src/animation_manifest_validate.py MANIFEST.json")
    try:
        load_and_validate(sys.argv[1])
    except (OSError, json.JSONDecodeError, ManifestValidationError) as exc:
        sys.exit(f"INVALID: {exc}")
    print("VALID AX1 pose manifest v1")
