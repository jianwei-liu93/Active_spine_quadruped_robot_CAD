"""Read-only r15 identity and bounded motion checks for the sculpted lumbar.

Lead-only FreeCAD API.  The functions neither save nor mutate either document;
``motion`` evaluates detached world-copy B-reps and returns a hash-bound,
finite-sample report.  They do not write reports or launch verification jobs.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRAME_INSTANCE = 'LumbarIntegrated1'
FRAME_SOURCE = 'FRM_LUMBAR_COMPACT_CAGE_r12'
EXPECTED_INSTANCES = 455
EXPECTED_SOURCES = 108
OVERLAP_TOL_MM3 = 1e-5
BBOX_TOL_MM = 1e-6
PAPER_PHASES_DEG = (0, 18, 90, 135, 180, 198, 240, 270, 330)


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _file_sha(path):
    return _sha_bytes(Path(path).read_bytes())


def _json_digest(value):
    return _sha_bytes(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                 allow_nan=False).encode('utf-8'))


def _shape_sha(shape):
    value = shape.exportBrepToString()
    return _sha_bytes(value.encode() if isinstance(value, str) else value)


def _matrix(placement):
    return [float(value) for value in placement.toMatrix().A]


def _matrix_error(a, b):
    return max(abs(x-y) for x, y in zip(a, b))


def _native_config(doc, fallback_path):
    controller = doc.getObject('PoseController')
    if controller is None or 'PrescribedMotionConfigR07' not in controller.PropertiesList:
        raise RuntimeError('PoseController.PrescribedMotionConfigR07 is missing')
    value = getattr(controller, 'PrescribedMotionConfigR07')
    value = value.Value if hasattr(value, 'Value') else value
    if value:
        return json.loads(value)
    return json.loads(Path(fallback_path).read_text())


def _configuration_projection(value):
    projected = dict(value)
    projected.pop('revision', None)
    projected.pop('sculpted_geometry_r15', None)
    return projected


def _numeric_properties(obj):
    result = {}
    for key in obj.PropertiesList:
        value = getattr(obj, key)
        if isinstance(value, bool):
            result[key] = value
        elif isinstance(value, (int, float)):
            result[key] = value
        elif hasattr(value, 'Value') and isinstance(value.Value, (int, float)):
            result[key] = float(value.Value)
    return result


def _link_map(doc):
    links = {obj.Name: obj for obj in doc.Objects if obj.TypeId == 'App::Link'}
    if len(links) != EXPECTED_INSTANCES:
        raise RuntimeError('Expected 455 unique App::Link instances; got {}'.format(len(links)))
    sources = {obj.LinkedObject.Name: obj.LinkedObject for obj in links.values()}
    if len(sources) != EXPECTED_SOURCES:
        raise RuntimeError('Expected 108 used source definitions; got {}'.format(len(sources)))
    if FRAME_INSTANCE not in links or FRAME_SOURCE not in sources:
        raise RuntimeError('Expected r15 lumbar source/instance identity is missing')
    return links, sources


def _doc_file_sha(doc):
    path = getattr(doc, 'FileName', '')
    if not path or not Path(path).is_file():
        raise RuntimeError('Document must be saved before hash-bound verification')
    return _file_sha(path)


def identity(old_doc, new_doc, *, old_config=None, new_config=None):
    """Prove only the lumbar source B-rep changed between r14 and r15.

    The old/new docs must already be open in the lead's FreeCAD session. Config
    mappings may be supplied explicitly; by default the tracked assembly r14
    and r15 JSON files are used. Unchanged source shapes are detached without
    triangulation and compared with the project's strict shape-identity gate.
    """
    import animation_pose_export as ax
    from verify_frame_revision_r09 import _strict_shape_identity

    old_path = getattr(old_doc, 'FileName', '')
    new_path = getattr(new_doc, 'FileName', '')
    if Path(old_path).name != 'flexor_r14_robot.FCStd':
        raise RuntimeError('Old document must be the saved r14 checkpoint')
    if Path(new_path).name != 'flexor_r15_robot.FCStd':
        raise RuntimeError('New document must be the saved r15 candidate')
    old_file_sha, new_file_sha = _doc_file_sha(old_doc), _doc_file_sha(new_doc)
    old_snapshot, new_snapshot = ax.snapshot(old_doc), ax.snapshot(new_doc)
    old_links, old_sources = _link_map(old_doc)
    new_links, new_sources = _link_map(new_doc)
    if set(old_links) != set(new_links):
        raise RuntimeError('r15 physical instance names differ from r14')
    if set(old_sources) != set(new_sources):
        raise RuntimeError('r15 source definition names differ from r14')

    old_config = old_config if old_config is not None else _native_config(
        old_doc, ROOT/'parameters/assembly_r14.json')
    new_config = new_config if new_config is not None else _native_config(
        new_doc, ROOT/'parameters/assembly_r15.json')
    old_native_config = _native_config(old_doc, ROOT/'parameters/assembly_r14.json')
    new_native_config = _native_config(new_doc, ROOT/'parameters/assembly_r15.json')
    if old_config != old_native_config or new_config != new_native_config:
        raise RuntimeError('Supplied assembly config differs from native controller config')
    old_config_file = ROOT/'parameters/assembly_r14.json'
    new_config_file = ROOT/'parameters/assembly_r15.json'
    if old_config != json.loads(old_config_file.read_text()) or new_config != json.loads(new_config_file.read_text()):
        raise RuntimeError('Native/selected assembly config differs from its revisioned parameter file')
    if old_config.get('revision') != 'r14' or new_config.get('revision') != 'r15':
        raise RuntimeError('Assembly config revisions must be r14 and r15')
    if _configuration_projection(old_config) != _configuration_projection(new_config):
        raise RuntimeError('r15 changed config fields outside revision/sculpted_geometry_r15')

    changed_sources = []
    source_rows = []
    for name in sorted(old_sources):
        a, b = old_sources[name], new_sources[name]
        old_part_number, new_part_number = str(a.PartNumber), str(b.PartNumber)
        if old_part_number != new_part_number and name != FRAME_SOURCE:
            raise RuntimeError(name + ': PartNumber changed')
        if _matrix(a.Placement) != _matrix(b.Placement):
            raise RuntimeError(name + ': source-local frame changed')
        old_brep, new_brep = a.Shape.copy(copyGeom=True, copyMesh=False), b.Shape.copy(copyGeom=True, copyMesh=False)
        old_sha, new_sha = _shape_sha(old_brep), _shape_sha(new_brep)
        if name == FRAME_SOURCE:
            changed_sources.append(name)
            if not new_brep.isValid() or len(new_brep.Solids) != 1:
                raise RuntimeError('Changed lumbar source must be one valid solid')
            if old_sha == new_sha:
                raise RuntimeError('Prescribed lumbar source has no recorded B-rep change')
            geometry_check = {'method': 'changed_source_recorded',
                              'old_brep_sha256': old_sha, 'new_brep_sha256': new_sha,
                              'brep_sha_changed': old_sha != new_sha}
        else:
            # Serialization/recompute may alter the B-rep byte stream without
            # changing geometry. Always run the established strict comparator.
            geometry_check = _strict_shape_identity(old_brep, new_brep, name)
            if geometry_check.get('method') not in ('exact_brep', 'strict_boolean_adaptive_bbox'):
                raise RuntimeError(name + ': strict unchanged-source gate did not run')
            if _numeric_properties(a) != _numeric_properties(b):
                raise RuntimeError(name + ': unchanged source numeric properties changed')
        source_rows.append({'source': name,
                            'old_part_number': old_part_number,
                            'new_part_number': new_part_number,
                            'old_brep_sha256': old_sha, 'new_brep_sha256': new_sha,
                            'prescribed_changed_source': name == FRAME_SOURCE,
                            'brep_sha_changed': old_sha != new_sha,
                            'geometry_check': geometry_check})
    if changed_sources != [FRAME_SOURCE]:
        raise RuntimeError('Expected only lumbar source to change; got ' + repr(changed_sources))

    changed_instances = []
    max_link_matrix_error = 0.0
    for name in sorted(old_links):
        a, b = old_links[name], new_links[name]
        if a.LinkedObject.Name != b.LinkedObject.Name:
            raise RuntimeError(name + ': linked source identity changed')
        error = _matrix_error(_matrix(a.LinkPlacement), _matrix(b.LinkPlacement))
        max_link_matrix_error = max(max_link_matrix_error, error)
        if error > 0.0:
            raise RuntimeError(name + ': LinkPlacement changed')
        if a.LinkedObject.Name in changed_sources:
            changed_instances.append(name)
    if changed_instances != [FRAME_INSTANCE]:
        raise RuntimeError('Expected only LumbarIntegrated1 to use changed geometry; got ' + repr(changed_instances))

    import robot_pose_r03 as pose
    old_pose_parameters, new_pose_parameters = pose._parameters(old_doc), pose._parameters(new_doc)
    if old_pose_parameters != new_pose_parameters:
        raise RuntimeError('Native mechanism/pose parameters changed')
    old_controller, new_controller = old_doc.getObject('PoseController'), new_doc.getObject('PoseController')
    old_motion_map, new_motion_map = old_controller.MotionMap, new_controller.MotionMap
    if json.loads(old_motion_map) != json.loads(new_motion_map):
        raise RuntimeError('MotionMap changed')
    controller_values = ('SpinePhaseRad', 'LegAnglesR03', 'WheelAngleR07')
    for key in controller_values:
        if getattr(old_controller, key) != getattr(new_controller, key):
            raise RuntimeError('Controller pose parameter changed: ' + key)
    if _configuration_projection(old_native_config) != _configuration_projection(new_native_config):
        raise RuntimeError('Native prescribed-motion config changed outside r15 sculpted geometry')

    if ax.snapshot(old_doc) != old_snapshot or ax.snapshot(new_doc) != new_snapshot:
        raise RuntimeError('Identity comparison mutated a native document')
    if _doc_file_sha(old_doc) != old_file_sha or _doc_file_sha(new_doc) != new_file_sha:
        raise RuntimeError('Identity comparison changed a native file')
    return {
        'status': 'PASS_R15_IDENTITY_ONLY',
        'native_files_sha256': {'r14': old_file_sha, 'r15': new_file_sha},
        'configuration_sha256': {'r14': _file_sha(old_config_file), 'r15': _file_sha(new_config_file)},
        'configuration_projection_sha256': _json_digest(_configuration_projection(new_config)),
        'motion_map_sha256': _sha_bytes(new_motion_map.encode() if isinstance(new_motion_map, str) else new_motion_map),
        'instance_count': len(new_links), 'source_definition_count': len(new_sources),
        'changed_sources': changed_sources, 'changed_instances': changed_instances,
        'retired_instances': [], 'new_instances': [],
        'maximum_link_placement_matrix_error': max_link_matrix_error,
        'strict_unchanged_source_count': len(source_rows)-len(changed_sources),
        'source_checks': source_rows,
        'native_pose_parameters_equal': True, 'motion_map_equal': True,
        'controller_pose_parameters_equal': True, 'document_unchanged': True,
        'native_files_unchanged': True,
        'helper_sha256': {'verify_sculpted_r15.py': _file_sha(Path(__file__)),
                          'verify_frame_revision_r09.py': _file_sha(ROOT/'src/verify_frame_revision_r09.py'),
                          'animation_pose_export.py': _file_sha(ROOT/'src/animation_pose_export.py')},
        'scope': 'Identity and exact saved native/source comparison only; no mechanism or strength qualification',
    }


def _bounds(shape):
    box = shape.BoundBox
    result = [float(getattr(box, key)) for key in
              ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax')]
    if not all(math.isfinite(value) for value in result):
        raise RuntimeError('Nonfinite world-shape bounding box')
    return result


def _bbox_disjoint(a, b):
    for i in (0, 2, 4):
        if min(a[i+1], b[i+1]) + 2*BBOX_TOL_MM < max(a[i], b[i]):
            return True
    return False


def _pairs(names, selected):
    selected = set(selected)
    return [(a, b) for i, a in enumerate(names) for b in names[i+1:]
            if a in selected or b in selected]


def _neutral(doc):
    controller = doc.getObject('PoseController')
    legs = getattr(controller, 'LegAnglesR03')
    legs = json.loads(legs) if isinstance(legs, str) else legs
    wheel = getattr(controller, 'WheelAngleR07')
    wheel = float(wheel.Value if hasattr(wheel, 'Value') else wheel)
    return legs, wheel


def _shape_pair_screen(shapes, pairs):
    bounds = {name: _bounds(shapes[name]) for name in shapes}
    bbox_excluded = occ_checks = 0
    forbidden = []
    for a, b in pairs:
        if _bbox_disjoint(bounds[a], bounds[b]):
            bbox_excluded += 1
            continue
        common = shapes[a].common(shapes[b])
        if common.isNull():
            volume = 0.0
        else:
            if not common.isValid():
                raise RuntimeError('Invalid OCC common for pair {}/{}'.format(a, b))
            volume = float(common.Volume)
            if not math.isfinite(volume) or volume < 0:
                raise RuntimeError('Invalid OCC intersection volume for {}/{}'.format(a, b))
        occ_checks += 1
        if volume > OVERLAP_TOL_MM3:
            forbidden.append({'a': a, 'b': b, 'intersection_mm3': volume})
    if bbox_excluded + occ_checks != len(pairs):
        raise RuntimeError('Pair ledger is incomplete')
    return {'pair_count': len(pairs), 'bbox_excluded': bbox_excluded,
            'occ_checks': occ_checks, 'forbidden_overlaps': forbidden,
            'status': 'FAIL' if forbidden else 'PASS_FINITE_SAMPLE'}


def _pose_metrics(doc, theta, plan):
    import robot_pose_r03 as pose
    from kinematics import residuals, spine
    state = spine(theta, pose._parameters(doc))
    spine_error = max(abs(float(value)) for value in residuals(state, pose._parameters(doc)))
    leg_errors = [abs(float(value))
                  for leg in plan['state']['legs'].values()
                  for value in leg['geometry']['loop_residuals_mm'].values()]
    return {'spine_closure_max_residual_mm': spine_error,
            'leg_closure_max_residual_mm': max(leg_errors, default=0.0),
            'spine_min_branch_margin_mm': min(float(v) for v in state['margins_mm']),
            'guide_warnings': list(plan['guide_warnings'])}


def motion(doc, config, phases=361):
    """Screen frame-vs-all over the integer cycle and selected paper poses.

    ``phases`` is an inclusive sample count on a 360-degree spine cycle; the
    required 361 gives one sample per integer degree including both endpoints.
    Each of the nine paper-profile pose samples screens the changed lumbar
    frame against all 454 other physical instances. All exact OCC checks after
    bbox pruning are retained as per-sample ledgers.
    """
    import animation_coordination_v2 as coordination
    import animation_pose_export as ax
    import leg_motion_r07 as leg_motion

    if not isinstance(phases, int) or phases != 361:
        raise ValueError('r15 motion gate requires phases=361 inclusive integer-degree samples')
    if not isinstance(config, dict) or config.get('revision') != 'r15':
        raise ValueError('motion config must be the r15 assembly configuration mapping')
    native_config = _native_config(doc, ROOT/'parameters/assembly_r15.json')
    if config != native_config:
        raise RuntimeError('Motion config differs from the r15 native controller config')
    native_sha = _doc_file_sha(doc)
    config_sha = _json_digest(config)
    before = ax.snapshot(doc)
    links, sources = _link_map(doc)
    names = sorted(links)
    if not all(links[n].LinkedObject.Name == FRAME_SOURCE for n in (FRAME_INSTANCE,)):
        raise RuntimeError('LumbarIntegrated1 does not link the expected r15 source')
    neutral, neutral_wheel = _neutral(doc)
    cache = {}
    frame_pairs = _pairs(names, (FRAME_INSTANCE,))
    if len(frame_pairs) != EXPECTED_INSTANCES - 1:
        raise RuntimeError('Expected exactly 454 changed-frame pairs per cycle phase')
    rows = []
    max_spine = max_leg = 0.0
    min_margin = float('inf')
    for degree in range(361):
        theta = math.radians(degree)
        shapes, plan = leg_motion.copied_shapes(doc, theta, neutral, neutral_wheel,
                                               config=config, cache=cache)
        if set(shapes) != set(names):
            raise RuntimeError('Neutral cycle shape coverage differs from the 455 native instances')
        pose = _pose_metrics(doc, theta, plan)
        max_spine = max(max_spine, pose['spine_closure_max_residual_mm'])
        max_leg = max(max_leg, pose['leg_closure_max_residual_mm'])
        min_margin = min(min_margin, pose['spine_min_branch_margin_mm'])
        clearance = _shape_pair_screen(shapes, frame_pairs)
        rows.append({'phase_deg': degree, 'theta_rad': theta,
                     'shape_count': len(shapes), **pose, **clearance})
        if degree % 30 == 0:
            print('R15_FRAME_SCREEN', degree, clearance['status'],
                  clearance['occ_checks'], flush=True)
        if clearance['forbidden_overlaps'] or pose['guide_warnings']:
            break

    paper_rows = []
    profile = coordination.PROFILE
    frequency = float(profile['presentation_frequency_hz'])
    with coordination.paper_descriptor_context():
        for degree in PAPER_PHASES_DEG:
            t = degree / (360.0 * frequency)
            theta, angles, wheel = coordination.trajectory('coordinated_spine_legs', t, neutral)
            shapes, plan = leg_motion.copied_shapes(doc, theta, angles, wheel,
                                                   config=config, cache=cache)
            if set(shapes) != set(names):
                raise RuntimeError('Paper pose shape coverage differs from the 455 native instances')
            pose = _pose_metrics(doc, theta, plan)
            max_spine = max(max_spine, pose['spine_closure_max_residual_mm'])
            max_leg = max(max_leg, pose['leg_closure_max_residual_mm'])
            min_margin = min(min_margin, pose['spine_min_branch_margin_mm'])
            clearance = _shape_pair_screen(shapes, frame_pairs)
            paper_rows.append({'profile_phase_deg': degree, 'time_s': t,
                               'theta_rad': float(theta), 'leg_angles_rad': angles,
                               'wheel_angle_rad': float(wheel), 'shape_count': len(shapes),
                               **pose, **clearance})
            if clearance['forbidden_overlaps'] or pose['guide_warnings']:
                break

    if ax.snapshot(doc) != before:
        raise RuntimeError('r15 motion screen mutated the native document')
    if _doc_file_sha(doc) != native_sha:
        raise RuntimeError('r15 motion screen changed the native file')
    closure_pass = max_spine <= 1e-6 and max_leg <= 1e-6 and min_margin > 0
    cycle_pass = len(rows) == phases and all(row['status'] == 'PASS_FINITE_SAMPLE' for row in rows)
    paper_pass = len(paper_rows) == len(PAPER_PHASES_DEG) and all(
        row['status'] == 'PASS_FINITE_SAMPLE' for row in paper_rows)
    return {
        'status': 'PASS_BOUNDED_R15' if closure_pass and cycle_pass and paper_pass else 'FAIL',
        'native_sha256': native_sha, 'configuration_sha256': config_sha,
        'motion_map_sha256': _sha_bytes(doc.PoseController.MotionMap.encode()),
        'geometry_source_sha256': {name: _shape_sha(src.Shape) for name, src in sorted(sources.items())},
        'changed_instance': FRAME_INSTANCE, 'changed_source': FRAME_SOURCE,
        'cycle': {'phase_samples_deg': list(range(361)),
                  'scope': 'Changed lumbar instance versus all other physical instances; neutral legs and stored wheel state',
                  'pair_manifest_sha256': _json_digest(frame_pairs),
                  'pairs_per_phase': len(frame_pairs), 'records': rows,
                  'total_bbox_exclusions': sum(row['bbox_excluded'] for row in rows),
                  'total_occ_checks': sum(row['occ_checks'] for row in rows),
                  'forbidden_overlaps': [hit for row in rows for hit in row['forbidden_overlaps']]},
        'paper_profile_poses': {'phase_samples_deg': list(PAPER_PHASES_DEG),
                  'profile_sha256': _file_sha(coordination.PROFILE_PATH),
                  'scope': 'Changed lumbar instance versus all other physical instances; prescribed kinematic poses',
                  'pair_manifest_sha256': _json_digest(frame_pairs),
                  'records': paper_rows,
                  'total_bbox_exclusions': sum(row['bbox_excluded'] for row in paper_rows),
                  'total_occ_checks': sum(row['occ_checks'] for row in paper_rows),
                  'forbidden_overlaps': [hit for row in paper_rows for hit in row['forbidden_overlaps']]},
        'kinematic_summary': {'max_spine_closure_residual_mm': max_spine,
                              'max_leg_loop_residual_mm': max_leg,
                              'minimum_spine_branch_margin_mm': min_margin,
                              'closure_gate_pass': closure_pass},
        'document_unchanged': True, 'native_file_unchanged': True,
        'continuous_clearance': False, 'full_historical_campaign': False,
        'loaded_equilibrium': False, 'strength_or_fatigue_qualification': False,
        'helper_sha256': {'verify_sculpted_r15.py': _file_sha(Path(__file__)),
                          'leg_motion_r07.py': _file_sha(ROOT/'src/leg_motion_r07.py'),
                          'animation_coordination_v2.py': _file_sha(ROOT/'src/animation_coordination_v2.py'),
                          'animation_pose_export.py': _file_sha(ROOT/'src/animation_pose_export.py')},
        'limitations': ['Finite sampled poses do not prove continuous clearance.',
                        'Paper-profile leg, cable and spring poses are prescribed, not loaded dynamics.',
                        'This bounded changed-frame screen is not structural qualification.'],
    }
