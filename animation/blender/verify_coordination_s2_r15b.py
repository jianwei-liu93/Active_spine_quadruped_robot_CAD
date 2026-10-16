"""Fresh-process S2 readback: Blender -b scene.blend --python this_file.py.

Measures the serialized presentation and finite prescribed CAD samples only.
This is not a dynamics, contact-force, locomotion, or fabrication validation.
"""
import gzip
import hashlib
import json
import math
import struct
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector
from procedural_geometry import spring_mesh, cable_mesh

ROOT = Path(__file__).resolve().parents[2]
SCENE = 'spine_leg_coordination_s2_r15b'
SOURCE = 'animation/motion/production_coordination_r15b.json'
PRESENTATION = 'animation/motion/presentation_coordination_s2_r15b.json'
REPORT = ROOT / 'reports/animation/spine_leg_coordination_s2_r15b_readback.json'
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
    # The validator must be launched against the saved .blend in a new batch
    # process. A live-session exec cannot establish serialized readback.
    opened_path = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    python_index = sys.argv.index('--python') if '--python' in sys.argv else -1
    opened_from_cli = opened_path is not None and any(
        Path(arg).resolve() == opened_path for arg in sys.argv[1:python_index]
        if arg.lower().endswith('.blend'))
    standalone_validator = python_index >= 0 and python_index + 1 < len(sys.argv) and (
        Path(sys.argv[python_index + 1]).resolve() == Path(__file__).resolve())
    fresh_process_readback = bool(bpy.app.background and opened_from_cli and standalone_validator
                                  and opened_path.is_file())
    check(fresh_process_readback,
          'Readback requires Blender -b saved_scene.blend --python this_validator.py')
    source_path, presentation_path = ROOT / SOURCE, ROOT / PRESENTATION
    manifest = json.loads(source_path.read_text())
    presentation = json.loads(presentation_path.read_text())
    check(manifest['source']['cad_revision'] == 'r15b', 'Source CAD revision differs')
    check(len({item['source_object_name'] for item in manifest['instances']}) == 108,
          'Source definition count differs')
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
    for path, expected in presentation.get('helper_files_sha256', {}).items():
        check((ROOT / path).is_file() and sha(ROOT / path) == expected,
              'Presentation helper dependency hash differs', path=path)
    check(set(presentation.get('helper_files_sha256', {})) == {
        'animation/blender/build_scenes.py', 'animation/blender/procedural_geometry.py',
        'animation/blender/build_coordination_r15b.py'}, 'Presentation helper hashes missing')
    for path, expected in manifest['production'].get('source_files_sha256', {}).items():
        check((ROOT / path).is_file() and sha(ROOT / path) == expected,
              'Source dependency hash differs', path=path)
    check(presentation.get('frame_count') == FRAMES, 'Presentation frame_count differs')
    check(presentation.get('sample_stride') == 3, 'Presentation sample stride differs')
    check(scene.frame_start == 1 and scene.frame_end == FRAMES, 'Scene frame range differs')
    check(scene.render.fps / scene.render.fps_base == 60, 'Scene playback rate differs')
    check(scene.render.resolution_x == 1920 and scene.render.resolution_y == 1080
          and scene.render.resolution_percentage == 100, 'Scene resolution differs from full 1080p')
    rows = presentation['frames']
    check(len(rows) == FRAMES, 'Presentation row count differs', count=len(rows))
    if len(rows) != FRAMES:
        raise RuntimeError('Incomplete presentation frame manifest')
    # The production export contains four cycles plus the endpoint (1201
    # samples); the studio scene serializes the first 300-sample cycle.
    # Count the full file without retaining the unused later cycles.
    cycle = []
    timeline_samples = 0
    with gzip.open(timeline_path, 'rt') as stream:
        for line in stream:
            if timeline_samples < 300:
                cycle.append(json.loads(line))
            timeline_samples += 1
    check(timeline_samples == timeline_info['sample_count'],
          'Source timeline sample count differs from manifest',
          count=timeline_samples, expected=timeline_info['sample_count'])
    if len(cycle) != 300:
        raise RuntimeError('Source timeline lacks the first 300-sample cycle')
    physical = [o for o in scene.objects if 'instance_id' in o]
    objects = {o['instance_id']: o for o in physical}
    check(len(physical) == len(objects) == 455, 'Instance IDs duplicated or count differs')
    check(set(objects) == set(manifest['instance_order']), 'Physical instance coverage differs')
    root = scene.objects.get('FLEXOR S2 r15b illustrative body root')
    if root is None:
        raise RuntimeError('Presentation body root missing')
    check(root.parent is None, 'Presentation root has an unexpected parent')
    check(all(o.parent == root for o in physical), 'Physical instance is not directly parented to presentation root')
    check(all(matrix_error(o.matrix_parent_inverse, Matrix.Identity(4)) <= 1e-8 for o in physical),
          'Nonidentity physical matrix_parent_inverse')
    check([o for o in scene.objects if o.type == 'EMPTY'] == [root], 'Presentation root is not the only root empty')
    check(not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post,
          'Playback depends on frame-change handlers')
    floors = [o for o in scene.objects if o.get('presentation_floor') == 'r15b']
    check(len(floors) == 1, 'Presentation floor is missing or duplicated')
    if len(floors) == 1:
        floor = floors[0]
        check(floor.type == 'MESH' and floor.parent is None and not floor.hide_render,
              'Presentation floor is not an independent visible mesh')
        check(not floor.animation_data and not floor.modifiers and not floor.constraints,
              'Presentation floor is animated or modified')
        check(all(abs((floor.matrix_world @ vertex.co).z) <= FLOOR_TOL_M
                  for vertex in floor.data.vertices), 'Presentation floor is not at z=0')
    check(presentation.get('floor_z_m') == 0., 'Presentation floor height differs')
    mesh_rows = {row['mesh_id']: row for row in manifest['meshes'] if row['asset_status'] == 'EXPORTED'}
    mesh_data = {}
    for mesh_id, row in mesh_rows.items():
        path = ROOT / row['path']
        check(sha(path) == row['sha256'], 'Geometry asset hash differs', mesh_id=mesh_id)
        mesh_data[mesh_id] = json.loads(path.read_text())
    max_local_vertex_error = 0.0
    verified_meshes = set()
    procedural = []
    rigid_meshes = {}
    max_procedural_vertex_error = 0.0
    procedural_samples_checked = 0
    feet = []
    for item in manifest['instances']:
        iid = item['instance_id']
        if iid not in objects:
            continue
        obj = objects[iid]
        check(obj.type == 'MESH', 'Physical instance is not a mesh', instance_id=iid)
        check(not obj.modifiers and not obj.constraints, 'Physical instance has modifiers or constraints', instance_id=iid)
        check(obj.get('source_id') == item['source_object_name'], 'Physical source identity differs', instance_id=iid)
        check(obj.get('geometry_kind') == item['geometry_kind'], 'Geometry kind differs', instance_id=iid)
        if item['geometry_kind'] != 'rigid':
            procedural.append(obj)
            keys = obj.data.shape_keys
            check(keys is not None and not keys.use_relative and len(keys.key_blocks) == 301,
                  'Procedural absolute shape-key inventory differs', instance_id=iid)
        else:
            previous = rigid_meshes.setdefault(item['mesh_id'], obj.data.as_pointer())
            check(previous == obj.data.as_pointer(), 'Rigid instances do not share their source mesh', instance_id=iid)
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
    check(len(rigid_meshes) == 98, 'Distinct rigid source mesh count differs')
    check(len(feet) == 8, 'Foot/footpad instance count differs')
    # Match Blender 5.2's deterministic float32 absolute-key positions. Their
    # RNA frame values are read-only; playback addresses the stored values.
    f32 = lambda value: struct.unpack('f', struct.pack('f', value))[0]
    normalized_time = f32(0.)
    expected_key_times = []
    for _ in range(300):
        normalized_time = f32(normalized_time + f32(.1))
        expected_key_times.append(f32(normalized_time * 100.))
    for sample, source_frame in enumerate(cycle):
        records = {row['instance_id']: row for row in source_frame['procedural_shapes']}
        check(set(records) == {o['instance_id'] for o in procedural},
              'Procedural source coverage differs', source_sample=sample)
        for obj in procedural:
            record = records[obj['instance_id']]
            vertices, faces = spring_mesh(record) if record['generator'] == 'spring' else cable_mesh(record)
            keys = obj.data.shape_keys
            if keys is None or len(keys.key_blocks) != 301:
                continue
            key = keys.key_blocks[sample + 1]
            expected_time = expected_key_times[sample]
            check(abs(key.frame - expected_time) <= 1e-6,
                  'Procedural key sample time differs', instance_id=obj['instance_id'], source_sample=sample)
            check(len(key.data) == len(vertices), 'Procedural vertex count differs', instance_id=obj['instance_id'])
            check(len(obj.data.polygons) == len(faces) and
                  all(tuple(p.vertices) == tuple(f) for p, f in zip(obj.data.polygons, faces)),
                  'Procedural topology differs', instance_id=obj['instance_id'], source_sample=sample)
            for vertex, expected in zip(key.data, vertices):
                max_procedural_vertex_error = max(max_procedural_vertex_error, (vertex.co - Vector(expected)).length)
            procedural_samples_checked += 1
    check(max_procedural_vertex_error <= 1e-7, 'Procedural source-local vertices differ',
          maximum_m=max_procedural_vertex_error)
    check(procedural_samples_checked == 3000, 'Procedural shape sample coverage differs')
    # First 100 output frames cover every distinct stride-three source sample.
    transform_frames = set(range(1, 101)) | {149, 300, 500, 750, 1000, 1250, 1499, 1500}
    max_position_error = max_axis_error = max_root_error = max_shape_time_error = 0.0
    max_evaluated_procedural_error = 0.0
    min_floor = float('inf')
    max_gap_error = 0.0
    pitch_values, translations = [], []
    framing_bounds = [1.0, 1.0, 0.0, 0.0]
    frame_checks = []
    # Rotation excursion is measured in each leg's own moving torso frame,
    # so root bobbing and spine motion cannot impersonate leg articulation.
    articulation_ids = {
        'instance:' + leg + '_' + segment: 'instance:Torso_' + ('fore' if leg.startswith('fore') else 'hind')
        for leg in ('foreL', 'foreR', 'hindL', 'hindR')
        for segment in ('thigh', 'shank', 'Foot')
    }
    check(set(articulation_ids).issubset(objects) and set(articulation_ids.values()).issubset(objects),
          'Leg articulation inventory missing')
    articulation_reference = {}
    articulation_excursions = {iid: 0. for iid in articulation_ids}
    articulation_samples = 0
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
        if frame <= 100:
            articulation_samples += 1
            for iid, torso_id in articulation_ids.items():
                if iid not in objects or torso_id not in objects:
                    continue
                torso_world = objects[torso_id].evaluated_get(deps).matrix_world
                limb_world = objects[iid].evaluated_get(deps).matrix_world
                relative_rotation = (torso_world.inverted() @ limb_world).to_3x3()
                baseline = articulation_reference.setdefault(iid, relative_rotation.copy())
                delta = baseline.transposed() @ relative_rotation
                sine = Vector((delta[2][1] - delta[1][2], delta[0][2] - delta[2][0],
                               delta[1][0] - delta[0][1])).length / 2
                cosine = (sum(delta[i][i] for i in range(3)) - 1) / 2
                angle = math.atan2(sine, cosine)
                articulation_excursions[iid] = max(articulation_excursions[iid], angle)
        for obj in procedural:
            if obj.data.shape_keys:
                error = abs(obj.data.shape_keys.eval_time - obj.data.shape_keys.key_blocks[sample + 1].frame)
                max_shape_time_error = max(max_shape_time_error, error)
                if frame in transform_frames:
                    record = next(r for r in cycle[sample]['procedural_shapes'] if r['instance_id'] == obj['instance_id'])
                    vertices, _ = spring_mesh(record) if record['generator'] == 'spring' else cable_mesh(record)
                    evaluated = obj.evaluated_get(deps)
                    mesh = evaluated.to_mesh()
                    try:
                        check(len(mesh.vertices) == len(vertices), 'Evaluated procedural vertex count differs', frame=frame, instance_id=obj['instance_id'])
                        for vertex, expected in zip(mesh.vertices, vertices):
                            max_evaluated_procedural_error = max(max_evaluated_procedural_error, (vertex.co - Vector(expected)).length)
                    finally:
                        evaluated.to_mesh_clear()
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
    check(max_evaluated_procedural_error <= 1e-7, 'Evaluated procedural geometry differs from source sample', maximum_m=max_evaluated_procedural_error)
    check(max(abs(v) for v in pitch_values) <= math.radians(3) + 1e-6, 'Illustrative pitch exceeds 3 degrees')
    check(max(v[0] for v in translations) - min(v[0] for v in translations) <= .016 + 1e-6,
          'Illustrative fore/aft travel exceeds +/-8 mm')
    check(articulation_samples == 100, 'Leg articulation sample coverage differs')
    for iid, excursion in articulation_excursions.items():
        check(excursion > math.radians(1), 'Leg segment lacks torso-relative articulation',
              instance_id=iid, maximum_excursion_deg=math.degrees(excursion))
    return dict(scene=SCENE, blender=bpy.app.version_string,
                reopened_in_fresh_process=fresh_process_readback,
                opened_blend_path=str(opened_path),
                render_resolution=[scene.render.resolution_x, scene.render.resolution_y],
                leg_articulation=dict(distinct_source_samples_checked=articulation_samples,
                                      reference='First stride-three sample; each segment relative to its own moving torso',
                                      minimum_required_excursion_deg=1.,
                                      maximum_rotation_excursion_deg={iid: math.degrees(value)
                                                                     for iid, value in articulation_excursions.items()}),
                source_manifest_sha256=source_hash, source_timeline_sha256=timeline_hash,
                presentation_manifest_sha256=sha(presentation_path), blend_sha256=sha(bpy.data.filepath),
                physical_instances=len(physical), procedural_instances=len(procedural),
                frames_checked=FRAMES, transform_frames_checked=sorted(transform_frames),
                source_timeline_samples=timeline_samples, serialized_cycle_samples=len(cycle),
                distinct_source_samples_checked=100, sampled_readback=frame_checks,
                source_to_world_convention='Blender_world = illustrative_root_world @ CAD_world_m; verified inverse(root) @ instance_world',
                maximum_root_matrix_error=max_root_error, maximum_root_relative_position_error_mm=max_position_error * 1000,
                maximum_root_relative_axis_error_rad=max_axis_error,
                maximum_rigid_local_vertex_error_m=max_local_vertex_error,
                maximum_procedural_local_vertex_error_m=max_procedural_vertex_error,
                procedural_shape_samples_checked=procedural_samples_checked,
                distinct_rigid_meshes=len(rigid_meshes),
                maximum_procedural_eval_time_error=max_shape_time_error,
                maximum_evaluated_procedural_local_vertex_error_m=max_evaluated_procedural_error,
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
