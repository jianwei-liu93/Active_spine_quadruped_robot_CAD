"""Build a limited r15 geometry interoperability preview from the r14 scene.

The source .blend is loaded as a library and is never saved back. Only the
LumbarIntegrated1 object's mesh is replaced, from a source-local, metre-unit
r15 mesh export. The 300-frame r14 prescribed-motion samples remain intact.

Run ``build(ROOT, R14_LIBRARY_PATH)`` from Blender's Python environment.
``render(OUTDIR)`` renders 60 samples (source frames 1, 6, ..., 296) as PNGs;
it does not encode a movie.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy


SCENE_NAME = "r15_geometry_interoperability_preview"
MANIFEST_REL = Path("animation/motion/geometry_preview_r15.json")
SOURCE_SCENE_NAME = "spine_leg_coordination_r14"
TARGET_INSTANCE_ID = "instance:LumbarIntegrated1"
TARGET_SOURCE_NAME = "FRM_LUMBAR_COMPACT_CAGE_r12"
R14_CAD_SHA256 = "7e4d8fbf239bde96e9ef63c4cdbe3001427e37b1358739cc3a2a0a990610eb87"
EXPECTED_SOURCE_SCENE_SHA256 = "15b2d86dc69c410c99f88a6f74f9e3039970b0b588316dcd08401494060ba285"


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path(root, value):
    path = Path(value)
    return path if path.is_absolute() else Path(root) / path


def _load_manifest(root):
    manifest_path = Path(root) / MANIFEST_REL
    if not manifest_path.is_file():
        raise FileNotFoundError("Required r15 geometry preview manifest is missing: %s" % manifest_path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = (
        "source_cad_sha256", "ax01_path", "ax01_sha256", "identity_report_path",
        "identity_report_sha256", "r14_library_sha256", "changed_mesh",
        "unchanged_geometry_proof",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("r15 preview manifest missing fields: %s" % ", ".join(missing))
    r15_native_path = Path(root) / "cad" / "flexor_r15_robot.FCStd"
    if not r15_native_path.is_file() or _sha256(r15_native_path) != data["source_cad_sha256"]:
        raise ValueError("r15 source_cad_sha256 does not match the saved r15 native candidate")
    proof = data["unchanged_geometry_proof"]
    if not isinstance(proof, dict):
        raise ValueError("unchanged_geometry_proof must be a structured identity-evidence record")

    identity_path = _path(root, data["identity_report_path"])
    if _sha256(identity_path) != data["identity_report_sha256"]:
        raise ValueError("r15 identity report SHA-256 mismatch")
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    native_hashes = identity.get("native_files_sha256", {})
    if identity.get("status") != "PASS_R15_IDENTITY_ONLY":
        raise ValueError("Identity report must be PASS_R15_IDENTITY_ONLY")
    if native_hashes.get("r14") != R14_CAD_SHA256 or native_hashes.get("r15") != data["source_cad_sha256"]:
        raise ValueError("Identity report native file hashes do not match the pinned r14 and current r15 CAD files")
    if identity.get("changed_sources") != [TARGET_SOURCE_NAME] or identity.get("changed_instances") != ["LumbarIntegrated1"]:
        raise ValueError("Identity report must show only the lumbar source and LumbarIntegrated1 changed")
    if identity.get("instance_count") != 455 or identity.get("source_definition_count") != 108:
        raise ValueError("Identity report inventory must remain 455 instances and 108 source definitions")
    if identity.get("strict_unchanged_source_count") != 107:
        raise ValueError("Identity report must strictly verify the 107 unchanged source definitions")

    ax01_path = _path(root, data["ax01_path"])
    if _sha256(ax01_path) != data["ax01_sha256"]:
        raise ValueError("r15 AX0/AX1 payload SHA-256 mismatch")
    ax01 = json.loads(ax01_path.read_text(encoding="utf-8"))
    ax01_source_sha = ax01.get("source", {}).get("cad_sha256")
    if ax01_source_sha != data["source_cad_sha256"]:
        raise ValueError("AX0/AX1 payload is not bound to the current r15 native candidate")
    if len(ax01.get("instances", [])) != 455 or len(ax01.get("instance_order", [])) != 455:
        raise ValueError("AX0/AX1 payload must retain all 455 physical instances")
    if len(ax01.get("frames", [])) != 3:
        raise ValueError("AX0/AX1 payload must include neutral and two non-neutral poses")
    return data, manifest_path


def _load_scene_from_library(library_path):
    if not library_path.is_file():
        raise FileNotFoundError("r14 Blender scene library is missing: %s" % library_path)
    if _sha256(library_path) != EXPECTED_SOURCE_SCENE_SHA256:
        raise ValueError("r14 Blender scene library SHA-256 differs from the pinned source")
    if SCENE_NAME in bpy.data.scenes:
        existing = bpy.data.scenes[SCENE_NAME]
        if not existing.get("r15_preview_builder"):
            raise RuntimeError("A scene named %r exists and is not owned by this helper" % SCENE_NAME)
        bpy.data.scenes.remove(existing)

    with bpy.data.libraries.load(str(library_path), link=False) as (data_from, data_to):
        if SOURCE_SCENE_NAME not in data_from.scenes:
            raise ValueError("Pinned r14 library has no scene %r" % SOURCE_SCENE_NAME)
        data_to.scenes = [SOURCE_SCENE_NAME]
    if len(data_to.scenes) != 1 or data_to.scenes[0] is None:
        raise RuntimeError("Blender did not load the requested r14 scene")
    scene = data_to.scenes[0]
    if scene.get("source_cad_sha256") != R14_CAD_SHA256:
        raise ValueError("Loaded r14 scene is not bound to the pinned CAD source")
    scene.name = SCENE_NAME
    return scene


def _validate_scene(scene, data):
    instances = [obj for obj in scene.objects if "instance_id" in obj]
    ids = [obj["instance_id"] for obj in instances]
    if len(instances) != 455 or len(set(ids)) != 455:
        raise ValueError("r14 source scene must contain 455 unique physical instance IDs")
    if scene.frame_start != 1 or scene.frame_end != 300 or scene.render.fps != 60:
        raise ValueError("r14 source scene must preserve frames 1..300 at 60 fps")
    source_ids = {obj.get("source_id") for obj in instances}
    if len(source_ids) != 108:
        raise ValueError("r14 source scene must retain 108 source definitions")
    rigid_source_ids = {
        obj.get("source_id") for obj in instances
        if obj.get("geometry_kind") == "rigid"
    }
    procedural_instances = [obj for obj in instances if obj.get("geometry_kind") != "rigid"]
    if len(rigid_source_ids) != 98 or len(procedural_instances) != 10:
        raise ValueError("r14 source inventory no longer matches 98 rigid sources + 10 procedural instances")
    targets = [obj for obj in instances if obj.get("instance_id") == TARGET_INSTANCE_ID]
    if len(targets) != 1:
        raise ValueError("Expected exactly one physical instance %r" % TARGET_INSTANCE_ID)
    target = targets[0]
    mesh_record = data["changed_mesh"]
    source_id = str(target.get("source_id", ""))
    mesh_source = str(mesh_record["source_object"])
    normalized_source_id = source_id.removeprefix("mesh:")
    normalized_mesh_source = mesh_source.removeprefix("mesh:")
    if normalized_source_id != normalized_mesh_source or normalized_mesh_source != TARGET_SOURCE_NAME:
        raise ValueError("Changed mesh source_object does not match the target instance source_id")
    return instances, target


def _make_mesh(root, record):
    for field in ("path", "sha256", "mesh_id", "source_object"):
        if field not in record:
            raise ValueError("changed_mesh is missing %r" % field)
    asset_path = _path(root, record["path"])
    if _sha256(asset_path) != record["sha256"]:
        raise ValueError("r15 changed mesh asset SHA-256 mismatch")
    asset = json.loads(asset_path.read_text(encoding="utf-8"))
    vertices = asset.get("vertices_m")
    triangles = asset.get("triangles")
    if vertices is None or triangles is None:
        raise ValueError("Hashed changed mesh asset must contain vertices_m and triangles")
    if "vertices_m" in record and vertices != record["vertices_m"]:
        raise ValueError("Manifest vertices_m differ from the hashed geometry asset")
    if "triangles" in record and triangles != record["triangles"]:
        raise ValueError("Manifest changed_mesh arrays differ from the hashed geometry asset")
    if len(vertices) < 4 or len(triangles) < 4:
        raise ValueError("Changed mesh is empty or too small to form a solid preview")
    for vertex in vertices:
        if len(vertex) != 3 or not all(math.isfinite(float(c)) for c in vertex):
            raise ValueError("Changed mesh contains a non-finite or malformed vertex")
    for tri in triangles:
        if len(tri) != 3 or any(not isinstance(i, int) or i < 0 or i >= len(vertices) for i in tri):
            raise ValueError("Changed mesh contains a malformed triangle index")
    mesh = bpy.data.meshes.new("r15 " + str(record["mesh_id"]))
    mesh.from_pydata(vertices, [], triangles)
    mesh.update(calc_edges=True)
    if len(mesh.vertices) != len(vertices) or len(mesh.polygons) != len(triangles):
        bpy.data.meshes.remove(mesh)
        raise RuntimeError("Blender changed the mesh vertex or triangle count")
    return mesh


def _relabel_r15(scene):
    for obj in scene.objects:
        if obj.type != "FONT":
            continue
        body = obj.data.body
        body = body.replace("FLEXOR r14 /", "FLEXOR r15 /")
        body = body.replace("r14 CAD reconstruction | Passive loads not simulated",
                            "r15 lumbar geometry | r14 prescribed motion; passive loads not simulated")
        if body != obj.data.body:
            obj.data.body = body
    scene["preview_label"] = "r15 geometry interoperability preview"
    scene["motion_provenance"] = "Prescribed kinematics inherited from r14; passive loads not simulated"


def build(root, r14_library_path):
    """Load a separate r14 scene, replace one local mesh, and save a new .blend."""
    root = Path(root).resolve()
    data, manifest_path = _load_manifest(root)
    library_path = Path(r14_library_path).resolve()
    if _sha256(library_path) != data["r14_library_sha256"]:
        raise ValueError("r14 library hash does not match the r15 preview manifest")
    scene = _load_scene_from_library(library_path)
    instances, target = _validate_scene(scene, data)
    old_data = target.data
    before_world = {}
    for frame in (1, 6, 296):
        scene.frame_set(frame)
        before_world[frame] = target.matrix_world.copy()

    new_mesh = _make_mesh(root, data["changed_mesh"])
    new_mesh.materials.clear()
    for material in old_data.materials:
        if material is not None:
            new_mesh.materials.append(material)
    target.data = new_mesh
    target["mesh_id"] = data["changed_mesh"]["mesh_id"]
    target["cad_sha256"] = data["source_cad_sha256"]

    for frame in (1, 6, 296):
        scene.frame_set(frame)
        if max(abs(target.matrix_world[row][col] - before_world[frame][row][col])
               for row in range(4) for col in range(4)) > 1e-10:
            raise RuntimeError("Replacing source-local geometry changed the target's baked pose")
    if target.data is not new_mesh or len([o for o in instances if o.get("instance_id") == TARGET_INSTANCE_ID]) != 1:
        raise RuntimeError("Only the intended physical instance may receive the r15 mesh")

    scene.name = SCENE_NAME
    scene["r15_preview_builder"] = "preview_geometry_r15.py"
    scene["r15_manifest_path"] = str(manifest_path.relative_to(root))
    scene["r15_manifest_sha256"] = _sha256(manifest_path)
    scene["source_cad_sha256"] = data["source_cad_sha256"]
    scene["baseline_r14_cad_sha256"] = R14_CAD_SHA256
    scene["r15_identity_report_sha256"] = data["identity_report_sha256"]
    scene["r15_ax01_path"] = data["ax01_path"]
    scene["r15_changed_mesh_sha256"] = data["changed_mesh"]["sha256"]
    scene["r15_r14_library_sha256"] = data["r14_library_sha256"]
    scene["r15_ax01_sha256"] = data["ax01_sha256"]
    scene["r15_identity_status"] = "PASS_R15_IDENTITY_ONLY"
    scene["physical_instances"] = 455
    scene["source_definitions"] = 108
    scene["preview_samples"] = 60
    scene["preview_source_frames"] = "1,6,...,296"
    _relabel_r15(scene)
    scene.frame_set(1)

    output_path = root / "animation" / "scenes" / (SCENE_NAME + ".blend")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.data.libraries.write(str(output_path), {scene}, fake_user=True, compress=True)
    result = {
        "scene": SCENE_NAME,
        "path": str(output_path),
        "physical_instances": len(instances),
        "source_definitions": 108,
        "target_instance": TARGET_INSTANCE_ID,
        "target_mesh_id": data["changed_mesh"]["mesh_id"],
        "mesh_vertices": len(new_mesh.vertices),
        "mesh_triangles": len(new_mesh.polygons),
        "source_frames": list(range(1, 297, 5)),
        "rendered": False,
    }
    print("R15_GEOMETRY_PREVIEW_BUILT", json.dumps(result), flush=True)
    return result


def render(outdir):
    """Render the active r15 preview as 60 PNG frames for a 12 fps, 5 s cut."""
    scene = bpy.data.scenes.get(SCENE_NAME)
    if scene is None or not scene.get("r15_preview_builder"):
        raise RuntimeError("Open the standalone r15 geometry preview before rendering")
    if scene.frame_start != 1 or scene.frame_end != 300 or scene.render.fps != 60:
        raise ValueError("Preview timeline must remain at 300 samples / 60 fps")
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    paths = []
    source_frames = list(range(1, 297, 5))
    for output_frame, source_frame in enumerate(source_frames, start=1):
        scene.frame_set(source_frame)
        path = outdir / ("r15_preview_%04d.png" % output_frame)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        paths.append(str(path))
    record = {
        "status": "RENDERED_PNG_SEQUENCE",
        "scene": SCENE_NAME,
        "frames": len(paths),
        "source_frames": source_frames,
        "output_fps": 12,
        "duration_seconds": 5,
        "resolution": [640, 480],
        "movie_encoded": False,
        "images": paths,
    }
    (outdir / "render_manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("R15_GEOMETRY_PREVIEW_RENDERED", json.dumps({k: v for k, v in record.items() if k != "images"}), flush=True)
    return record
