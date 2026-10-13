"""Fresh-process S2 readback: Blender -b scene.blend --python this_file.py.

Measures the serialized presentation and finite prescribed CAD samples only.
This is not a dynamics, contact-force, locomotion, or fabrication validation.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
SCENE = 'spine_leg_coordination_s2'
SOURCE = 'animation/motion/production_coordination_v2_r10.json'
PRESENTATION = 'animation/motion/presentation_coordination_s2.json'
REPORT = ROOT / 'reports/animation/spine_leg_coordination_s2_readback.json'
POSITION_TOL_M = 0.00002
AXIS_TOL_RAD = 0.0001
FLOOR_TOL_M = 0.000001
FRAMES = 1500
failures = []
framing_failures = []


def check(condition, message, **details):
    if not condition:
        failures.append(dict(message=message, **details))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def matrix_error(a, b):
    return max(abs(a[r][c] - b[r][c]) for r in range(4) for c in range(4))


def rigid_error(m):
    r = m.to_3x3()
    identity = r.transposed() @ r
    return max(abs(identity[i][j] - (i == j)) for i in range(3) for j in range(3)), r.determinant()


def bounds_for(scene, deps, selected):
    bounds = [float('inf'), float('inf'), -float('inf'), -float('inf')]
    behind = False
    for obj in selected:
        evaluated = obj.evaluated_get(deps)
        for corner in evaluated.bound_box:
            point = world_to_camera_view(scene, scene.camera, evaluated.matrix_world @ Vector(corner))
            behind |= point.z <= 0
            bounds = [min(bounds[0], point.x), min(bounds[1], point.y),
                      max(bounds[2], point.x), max(bounds[3], point.y)]
    return bounds, behind


def run():
    scene = bpy.data.scenes.get(SCENE)
    if scene is None:
        raise RuntimeError('Required scene is missing: ' + SCENE)
    if bpy.context.window:
        bpy.context.window.scene = scene
    source_path, presentation_path = ROOT / SOURCE, ROOT / PRESENTATION
    manifest = json.loads(source_path.read_text())
    presentation = json.loads(presentation_path.read_text())
    timeline_info = manifest['production']['timelines']['coordinated_spine_legs']
    timeline_path = ROOT / timeline_info['path']
    source_hash, timeline_hash = sha(source_path), sha(timeline_path)
    check(scene.get('source_manifest') == SOURCE, 'Scene source manifest differs')
    check(scene.get('presentation_manifest') == PRESENTATION, 'Scene presentation manifest differs')
    check(timeline_hash == timeline_info['sha256'], 'Source timeline hash differs')
    check(presentation.get('source_cad_sha256') == manifest['source']['cad_sha256'],
          'Presentation CAD hash differs from source manifest')
    check(sha(ROOT / manifest['source']['cad_path']) == manifest['source']['cad_sha256'],
          'Native CAD file hash differs from immutable source manifest')
    # Explicit content hashes bind the presentation to its immutable CAD inputs.
    source_hashes = presentation.get('source_hashes', {})
    recorded_source = presentation.get('source_manifest_sha256', source_hashes.get(SOURCE))
    recorded_timeline = presentation.get('source_timeline_sha256', presentation.get('timeline_sha256', source_hashes.get(timeline_info['path'])))
    check(recorded_source == source_hash, 'Presentation source manifest hash differs or is missing')
    check(recorded_timeline == timeline_hash, 'Presentation timeline hash differs or is missing')
    for path_key, hash_key in [('source_scene_path', 'source_scene_sha256'),
                               ('style_config_path', 'style_config_sha256'),
                               ('builder_path', 'builder_sha256')]:
        path = ROOT / presentation[path_key]
        check(path.is_file() and sha(path) == presentation[hash_key],
              'Presentation dependency hash differs', path=presentation[path_key])
    for path, expected in manifest['production'].get('source_files_sha256', {}).items():
        check((ROOT / path).is_file() and sha(ROOT / path) == expected,
              'Source dependency hash differs', path=path)
    check(presentation.get('frame_count') == FRAMES, 'Presentation frame_count differs')
    check(presentation.get('sample_stride') == 3, 'Presentation sample stride differs')
    check(scene.frame_start == 1 and scene.frame_end == FRAMES, 'Scene frame range differs')
    check(scene.render.fps / scene.render.fps_base == 60, 'Scene playback rate differs')
    rows = presentation['frames']
    check(len(rows) == FRAMES, 'Presentation row count differs', count=len(rows))
    if len(rows) != FRAMES:
        raise RuntimeError('Incomplete presentation frame manifest')
    with gzip.open(timeline_path, 'rt') as stream:
        cycle = [json.loads(next(stream)) for _ in range(300)]
    physical = [o for o in scene.objects if 'instance_id' in o]
    objects = {o['instance_id']: o for o in physical}
    check(len(physical) == len(objects) == 487, 'Instance IDs duplicated or count differs')
    check(set(objects) == set(manifest['instance_order']), 'Physical instance coverage differs')
    root = scene.objects.get('FLEXOR S2 illustrative body root')
    if root is None:
        raise RuntimeError('Presentation body root missing')
    check(root.parent is None, 'Presentation root has an unexpected parent')
    check(all(o.parent == root for o in physical), 'Physical instance is not directly parented to presentation root')
    check(all(matrix_error(o.matrix_parent_inverse, Matrix.Identity(4)) <= 1e-8 for o in physical),
          'Nonidentity physical matrix_parent_inverse')
    check(len([o for o in scene.objects if o.name == root.name]) == 1, 'Presentation root is not unique')
    check(not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post,
          'Playback depends on frame-change handlers')
    mesh_rows = {row['mesh_id']: row for row in manifest['meshes'] if row['asset_status'] == 'EXPORTED'}
    mesh_data = {}
    for mesh_id, row in mesh_rows.items():
        path = ROOT / row['path']
        check(sha(path) == row['sha256'], 'Geometry asset hash differs', mesh_id=mesh_id)
        mesh_data[mesh_id] = json.loads(path.read_text())
    max_local_vertex_error = 0.0
    verified_meshes = set()
    procedural = []
    feet = []
    for item in manifest['instances']:
        iid = item['instance_id']
        if iid not in objects:
            continue
        obj = objects[iid]
        check(obj.type == 'MESH', 'Physical instance is not a mesh', instance_id=iid)
        check(obj.get('source_id') == item['source_object_name'], 'Physical source identity differs', instance_id=iid)
        check(obj.get('geometry_kind') == item['geometry_kind'], 'Geometry kind differs', instance_id=iid)
        if item['geometry_kind'] != 'rigid':
            procedural.append(obj)
            keys = obj.data.shape_keys
            check(keys is not None and not keys.use_relative and len(keys.key_blocks) == 301,
                  'Procedural absolute shape-key inventory differs', instance_id=iid)
        else:
            raw = mesh_data[item['mesh_id']]
            check(len(obj.data.vertices) == len(raw['vertices_m']), 'Rigid mesh vertex count differs', instance_id=iid)
            check(len(obj.data.polygons) == len(raw['triangles']), 'Rigid mesh face count differs', instance_id=iid)
            check(not obj.modifiers, 'Rigid mesh has unverified modifiers', instance_id=iid)
            mesh_key = (obj.data.as_pointer(), item['mesh_id'])
            if mesh_key not in verified_meshes:
                verified_meshes.add(mesh_key)
                for vertex, expected in zip(obj.data.vertices, raw['vertices_m']):
                    max_local_vertex_error = max(max_local_vertex_error, (vertex.co - Vector(expected)).length)
                check(all(tuple(face.vertices) == tuple(expected) for face, expected in zip(obj.data.polygons, raw['triangles'])),
                      'Rigid mesh topology differs', instance_id=iid)
        if iid.lower().endswith(('_foot', '_footpad')):
            feet.append(obj)
    check(max_local_vertex_error <= 1e-7, 'Rigid source-local vertices differ', maximum_m=max_local_vertex_error)
    check(len(procedural) == 10, 'Procedural instance count differs')
    check(len(feet) == 8, 'Foot/footpad instance count differs')
    # First 100 output frames cover every distinct stride-three source sample.
    transform_frames = set(range(1, 101)) | {149, 300, 500, 750, 1000, 1250, 1499, 1500}
    max_position_error = max_axis_error = max_root_error = max_shape_time_error = 0.0
    min_floor = float('inf')
    max_gap_error = 0.0
    pitch_values, translations = [], []
    framing_bounds = [1.0, 1.0, 0.0, 0.0]
    frame_checks = []
    for frame, row in enumerate(rows, 1):
        sample = ((frame - 1) * 3) % 300
        check(row['frame'] == frame and row['source_sample'] == sample,
              'Presentation source mapping differs', frame=frame)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        actual_root = root.evaluated_get(deps).matrix_world.copy()
        expected_root = Matrix(row['root_transform_m'])
        root_err = matrix_error(actual_root, expected_root)
        max_root_error = max(max_root_error, root_err)
        ortho_err, determinant = rigid_error(actual_root)
        check(root_err <= 1e-6 and ortho_err <= 1e-6 and abs(determinant - 1) <= 1e-6,
              'Root matrix mismatch or nonrigid root', frame=frame, matrix_error=root_err,
              orthonormal_error=ortho_err, determinant=determinant)
        check(max(abs(actual_root[3][i] - (i == 3)) for i in range(4)) <= 1e-8,
              'Root homogeneous row differs', frame=frame)
        pitch = math.atan2(actual_root[0][2], actual_root[0][0])
        pitch_values.append(pitch)
        pitch_rotation = Matrix.Rotation(pitch, 3, 'Y')
        check(max(abs(actual_root[r][c] - pitch_rotation[r][c]) for r in range(3) for c in range(3)) <= 1e-6,
              'Illustrative root has a rotation other than sagittal pitch', frame=frame)
        check(abs(actual_root.translation.y) <= 1e-6 and abs(actual_root.translation.x) <= .008 + 1e-6,
              'Illustrative root lateral/fore-aft translation exceeds prescribed limits', frame=frame)
        translations.append(list(actual_root.translation))
        inv_root = actual_root.inverted()
        if frame in transform_frames:
            for index, iid in enumerate(manifest['instance_order']):
                if iid not in objects:
                    continue
                actual = inv_root @ objects[iid].evaluated_get(deps).matrix_world
                expected = Matrix(cycle[sample]['transforms_m'][index])
                max_position_error = max(max_position_error, (actual.translation - expected.translation).length)
                for col in range(3):
                    a, b = actual.to_3x3().col[col], expected.to_3x3().col[col]
                    max_axis_error = max(max_axis_error, math.atan2(a.cross(b).length, a.dot(b)))
                ortho, det = rigid_error(actual)
                check(ortho <= 1e-5 and abs(det - 1) <= 1e-5,
                      'Root-relative instance rotation or scale differs', frame=frame, instance_id=iid)
        for obj in procedural:
            if obj.data.shape_keys:
                error = abs(obj.data.shape_keys.eval_time - 10 * (sample + 1))
                max_shape_time_error = max(max_shape_time_error, error)
        foot_min = float('inf')
        for obj in feet:
            evaluated = obj.evaluated_get(deps)
            mesh = evaluated.to_mesh()
            try:
                foot_min = min(foot_min, min((evaluated.matrix_world @ v.co).z for v in mesh.vertices))
            finally:
                evaluated.to_mesh_clear()
        min_floor = min(min_floor, foot_min)
        # floor_gap_m is total minimum mesh clearance, including the 0.8 mm margin.
        expected_gap = float(row['floor_gap_m'])
        max_gap_error = max(max_gap_error, abs(foot_min - expected_gap))
        check(expected_gap >= 0.0008 - FLOOR_TOL_M, 'Prescribed floor gap lacks clearance', frame=frame)
        check(foot_min >= -FLOOR_TOL_M and abs(foot_min - expected_gap) <= FLOOR_TOL_M,
              'Evaluated foot floor clearance differs', frame=frame,
              actual_minimum_m=foot_min, prescribed_gap_m=expected_gap)
        shot = row['shot']
        selected = physical if shot == 'overview' else []
        if 'framing_instance_ids' in row:
            ids = row['framing_instance_ids']
            missing = sorted(set(ids) - set(objects))
            if missing:
                framing_failures.append(dict(frame=frame, shot=shot, message='Unknown framing instance IDs', instance_ids=missing))
            selected = [objects[iid] for iid in ids if iid in objects]
            if shot == 'overview' and set(ids) != set(objects):
                framing_failures.append(dict(frame=frame, shot=shot, message='Overview framing inventory does not cover all instances'))
        elif shot != 'overview':
            target_groups = row.get('target_groups', [row['target_group']] if 'target_group' in row else [])
            selected = [o for o in physical if o.get('group') in target_groups]
        if selected:
            bounds, behind = bounds_for(scene, deps, selected)
            framing_bounds = [min(framing_bounds[0], bounds[0]), min(framing_bounds[1], bounds[1]),
                              max(framing_bounds[2], bounds[2]), max(framing_bounds[3], bounds[3])]
            if behind or bounds[0] < .025 or bounds[1] < .08 or bounds[2] > .975 or bounds[3] > .9:
                framing_failures.append(dict(frame=frame, shot=shot, normalized_bounds=bounds,
                                             behind_camera=behind, checked_instances=len(selected)))
        elif shot != 'overview':
            framing_failures.append(dict(frame=frame, shot=shot, message='Detail target group metadata missing or empty'))
        if frame in transform_frames:
            frame_checks.append(dict(frame=frame, source_sample=sample, minimum_foot_z_m=foot_min))
    check(max_position_error <= POSITION_TOL_M, 'Root-relative CAD position mismatch', maximum_m=max_position_error)
    check(max_axis_error <= AXIS_TOL_RAD, 'Root-relative CAD axis mismatch', maximum_rad=max_axis_error)
    check(max_shape_time_error <= 1e-4, 'Procedural sample evaluation differs', maximum=max_shape_time_error)
    check(max(abs(v) for v in pitch_values) <= math.radians(3) + 1e-6, 'Illustrative pitch exceeds 3 degrees')
    check(max(v[0] for v in translations) - min(v[0] for v in translations) <= .016 + 1e-6,
          'Illustrative fore/aft travel exceeds +/-8 mm')
    return dict(scene=SCENE, blender=bpy.app.version_string, reopened_in_fresh_process=True,
                source_manifest_sha256=source_hash, source_timeline_sha256=timeline_hash,
                presentation_manifest_sha256=sha(presentation_path), blend_sha256=sha(bpy.data.filepath),
                physical_instances=len(physical), procedural_instances=len(procedural),
                frames_checked=FRAMES, transform_frames_checked=sorted(transform_frames),
                distinct_source_samples_checked=100, sampled_readback=frame_checks,
                source_to_world_convention='Blender_world = illustrative_root_world @ CAD_world_m; verified inverse(root) @ instance_world',
                maximum_root_matrix_error=max_root_error, maximum_root_relative_position_error_mm=max_position_error * 1000,
                maximum_root_relative_axis_error_rad=max_axis_error,
                maximum_rigid_local_vertex_error_m=max_local_vertex_error,
                maximum_procedural_eval_time_error=max_shape_time_error,
                minimum_evaluated_foot_floor_z_m=min_floor, maximum_floor_gap_error_m=max_gap_error,
                root_pitch_range_deg=[math.degrees(min(pitch_values)), math.degrees(max(pitch_values))],
                root_translation_ranges_m=[[min(v[i] for v in translations), max(v[i] for v in translations)] for i in range(3)],
                camera_framing=dict(status='FAIL' if framing_failures else 'PASS',
                                    failure_count=len(framing_failures), safe_rectangle=[.025, .08, .975, .9],
                                    checked_screen_extents=framing_bounds, failures=framing_failures,
                                    scope='All physical bounds for overview; declared framing_instance_ids (or target groups) for intentional detail crops'))


report = dict(scope='Finite serialized illustrative kinematic motion verification only; no dynamics, loaded gait, contact-force, locomotion performance, or fabrication claims.',
              freecad_needed=False, playback_handlers_needed=False)
try:
    report.update(run())
except Exception as error:
    failures.append(dict(message='Readback could not complete', exception_type=type(error).__name__, detail=str(error)))
report.update(status='FAIL' if failures or framing_failures else 'PASS',
              mechanical_readback_status='FAIL' if failures else 'PASS',
              failure_count=len(failures), failures=failures)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print('S2_SCENE_READBACK', json.dumps({
    'status': report['status'], 'mechanical_readback_status': report['mechanical_readback_status'],
    'failure_count': len(failures), 'camera_failure_count': len(framing_failures),
    'first_failures': failures[:3], 'first_camera_failures': framing_failures[:3],
    'report_path': str(REPORT),
}), flush=True)
if report['status'] != 'PASS':
    raise SystemExit(1)
