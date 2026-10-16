"""Finite collision checks for additive r15 frame geometry.

This is a lead-only FreeCAD helper. It reuses the frozen r14 91-pose result
for unchanged geometry, checks only ``new_frame - old_frame`` at those poses,
and screens the complete new frame at nine coordinated paper-profile poses.
It returns a hash-bound report and never changes or saves the document.
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
VOLUME_TOL_MM3 = 1e-5
BBOX_TOL_MM = 1e-6
PAPER_PHASES_DEG = (0, 18, 90, 135, 180, 198, 240, 270, 330)
R14_REPORT = ROOT / 'reports/verification/r14_motion_91.json'
R14_PLAN = ROOT / 'reports/verification/r14_motion_plan_91.json'


def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _file_sha(path):
    return _sha_bytes(Path(path).read_bytes())


def _json_sha(value):
    return _sha_bytes(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                 allow_nan=False).encode('utf-8'))


def _shape_sha(shape):
    data = shape.exportBrepToString()
    return _sha_bytes(data.encode('utf-8') if isinstance(data, str) else data)


def _snapshot(doc):
    import animation_pose_export as ax
    return ax.snapshot(doc)


def _config_projection(value):
    projected = dict(value)
    projected.pop('revision', None)
    projected.pop('sculpted_geometry_r15', None)
    return projected


def _native_config(doc):
    controller = doc.getObject('PoseController')
    if controller is None or 'PrescribedMotionConfigR07' not in controller.PropertiesList:
        raise RuntimeError('PoseController prescribed-motion config is missing')
    value = getattr(controller, 'PrescribedMotionConfigR07')
    value = value.Value if hasattr(value, 'Value') else value
    if not value:
        raise RuntimeError('Native r15 controller config is empty')
    return json.loads(value)


def _links_and_sources(doc):
    links = {obj.Name: obj for obj in doc.Objects if obj.TypeId == 'App::Link'}
    sources = {obj.LinkedObject.Name: obj.LinkedObject for obj in links.values()}
    if len(links) != EXPECTED_INSTANCES or len(sources) != EXPECTED_SOURCES:
        raise RuntimeError('Expected 455 physical links and 108 used sources')
    if FRAME_INSTANCE not in links or FRAME_SOURCE not in sources:
        raise RuntimeError('Expected r15 lumbar instance/source missing')
    if links[FRAME_INSTANCE].LinkedObject.Name != FRAME_SOURCE:
        raise RuntimeError('LumbarIntegrated1 does not link the prescribed frame source')
    return links, sources


def _baseline_samples():
    """Validate immutable r14 evidence and return its exact 91 input rows."""
    report_bytes = R14_REPORT.read_bytes()
    report = json.loads(report_bytes)
    required = (report.get('status') == 'PASS_AFFECTED_FINITE_ONLY'
                and report.get('assembly_revision') == 'r14'
                and report.get('coverage_scope') ==
                '91 inclusive spine phases0..360deg at4deg, stored neutral legs and wheel0; affected pairs only'
                and report.get('requested_sample_count') == 91
                and report.get('samples_completed') == 91
                and report.get('expected_pair_decisions') == report.get('completed_pair_decisions')
                and report.get('all_requested_pair_decisions_complete') is True
                and not report.get('collisions') and not report.get('errors')
                and not report.get('exceptions'))
    if not required:
        raise RuntimeError('Historical r14 motion evidence is incomplete or not passing')
    plan_record = report.get('source_reports', {}).get(str(R14_PLAN.relative_to(ROOT)))
    if not plan_record or _file_sha(R14_PLAN) != plan_record.get('sha256'):
        raise RuntimeError('Historical r14 91-pose plan hash does not match its evidence record')
    raw = json.loads(R14_PLAN.read_bytes())
    if plan_record.get('raw_report') != raw:
        raise RuntimeError('Historical r14 embedded plan differs from the immutable plan file')
    states = raw.get('states')
    if not isinstance(states, list) or len(states) != 91:
        raise RuntimeError('Historical r14 plan must contain exactly 91 poses')
    for index, state in enumerate(states):
        degree = 4 * index
        if state.get('sample_id') != 'r14_spine_{:03d}'.format(degree):
            raise RuntimeError('Historical r14 phase identity is incomplete or reordered')
        if abs(float(state.get('theta', math.nan)) - math.radians(degree)) > 1e-12:
            raise RuntimeError('Historical r14 phase differs from the 4-degree cycle')
        if abs(float(state.get('wheel_angle', math.nan)) - 0.0) > 1e-12:
            raise RuntimeError('Historical r14 wheel state is not neutral')
        if set(state.get('leg_angles', {})) != {'foreL', 'foreR', 'hindL', 'hindR'}:
            raise RuntimeError('Historical r14 stored neutral leg-angle map is incomplete')
    return report, states


def _box_values(shape):
    box = shape.BoundBox
    values = tuple(float(getattr(box, key)) for key in
                   ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax'))
    if not all(math.isfinite(v) for v in values):
        raise RuntimeError('Nonfinite shape bound')
    return values


def _transform_bounds(bounds, transform, App):
    """Transform all eight corners of a conservative source/world AABB."""
    corners = []
    for x in (bounds[0], bounds[1]):
        for y in (bounds[2], bounds[3]):
            for z in (bounds[4], bounds[5]):
                point = transform.multVec(App.Vector(x, y, z))
                corners.append((float(point.x), float(point.y), float(point.z)))
    return (min(p[0] for p in corners), max(p[0] for p in corners),
            min(p[1] for p in corners), max(p[1] for p in corners),
            min(p[2] for p in corners), max(p[2] for p in corners))


def _bbox_disjoint(a, b):
    for axis in (0, 2, 4):
        if min(a[axis+1], b[axis+1]) + 2*BBOX_TOL_MM < max(a[axis], b[axis]):
            return True
    return False


def _world_native_shape(doc, name, target):
    obj = doc.getObject(name)
    shape = obj.Shape.copy()
    shape.Placement = target.multiply(obj.LinkPlacement.inverse()).multiply(shape.Placement)
    if not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError(name + ': native world copy is invalid/non-single-solid')
    return shape


def _world_local_shape(shape, target, label):
    result = shape.copy()
    result.Placement = target.multiply(result.Placement)
    if not result.isValid() or len(result.Solids) != 1:
        raise RuntimeError(label + ': regenerated world copy is invalid/non-single-solid')
    return result


def _screen_pairs(component_shapes, component_bounds, names, other_bounds,
                  other_shape_factory):
    """Record every component/link decision; exact common only after AABB gate."""
    bbox_excluded = occ_checks = 0
    hits = []
    shape_cache = {}
    for component_index, component in enumerate(component_shapes):
        bounds = component_bounds[component_index]
        for name in names:
            if _bbox_disjoint(bounds, other_bounds[name]):
                bbox_excluded += 1
                continue
            if name not in shape_cache:
                shape_cache[name] = other_shape_factory(name)
            common = component.common(shape_cache[name])
            if common.isNull():
                volume = 0.0
            else:
                if not common.isValid():
                    raise RuntimeError('Invalid OCC common for frame component/{}'.format(name))
                volume = float(common.Volume)
                if not math.isfinite(volume) or volume < 0:
                    raise RuntimeError('Invalid OCC common volume for frame component/{}'.format(name))
            occ_checks += 1
            if volume > VOLUME_TOL_MM3:
                hits.append({'component_index': component_index, 'instance': name,
                             'intersection_mm3': volume})
    expected = len(component_shapes) * len(names)
    if bbox_excluded + occ_checks != expected:
        raise RuntimeError('Component/link decision ledger is incomplete')
    return {'component_count': len(component_shapes), 'instance_count': len(names),
            'pair_decisions': expected, 'bbox_excluded': bbox_excluded,
            'exact_common_checks': occ_checks, 'forbidden_overlaps': hits,
            'status': 'FAIL' if hits else 'PASS_ADDITIVE_DELTA_FINITE_SAMPLE'}


def _kinematic_metrics(doc, theta, plan):
    import robot_pose_r03 as pose
    from kinematics import residuals, spine
    parameters = pose._parameters(doc)
    state = spine(theta, parameters)
    return {
        'spine_closure_max_residual_mm': max(abs(float(v)) for v in residuals(state, parameters)),
        'leg_closure_max_residual_mm': max((abs(float(v)) for leg in plan['state']['legs'].values()
                                              for v in leg['geometry']['loop_residuals_mm'].values()),
                                             default=0.0),
        'spine_min_branch_margin_mm': min(float(v) for v in state['margins_mm']),
        'guide_warnings': list(plan['guide_warnings']),
    }


def run(doc, old_frame_source, new_frame_source, config):
    """Run a bounded additive-delta check without mutating the frozen document.

    Preconditions: the lead has already completed the r14-to-r15 107-source
    identity gate. The old/new source objects are detached from that comparison;
    the current document is the saved, frozen r15 assembly.
    """
    import FreeCAD as App
    import animation_coordination_v2 as coordination
    import leg_motion_r07 as motion
    import animation_pose_export as ax

    if Path(getattr(doc, 'FileName', '')).name != 'flexor_r15_robot.FCStd':
        raise RuntimeError('run requires the saved flexor_r15_robot.FCStd document')
    if not isinstance(config, dict) or config.get('revision') != 'r15':
        raise ValueError('config must be the r15 assembly configuration')
    native_config = _native_config(doc)
    config_file = ROOT / 'parameters/assembly_r15.json'
    if config != native_config or config != json.loads(config_file.read_text()):
        raise RuntimeError('Selected config differs from native controller or r15 parameter file')
    r14_config = json.loads((ROOT / 'parameters/assembly_r14.json').read_text())
    if _config_projection(r14_config) != _config_projection(config):
        raise RuntimeError('r15 changed configuration beyond revision/sculpted geometry metadata')

    baseline, samples = _baseline_samples()
    before = _snapshot(doc)
    native_path = Path(doc.FileName)
    if not native_path.is_file():
        raise RuntimeError('Saved r15 native file is required for hash-bound evidence')
    native_sha = _file_sha(native_path)
    links, sources = _links_and_sources(doc)
    if not old_frame_source.Shape.isValid() or len(old_frame_source.Shape.Solids) != 1:
        raise RuntimeError('Detached r14 lumbar source is invalid/non-single-solid')
    if not new_frame_source.Shape.isValid() or len(new_frame_source.Shape.Solids) != 1:
        raise RuntimeError('Detached r15 lumbar source is invalid/non-single-solid')
    if old_frame_source.Name != FRAME_SOURCE or new_frame_source.Name != FRAME_SOURCE:
        raise RuntimeError('Detached old/new frame source identity mismatch')
    old_shape = old_frame_source.Shape.copy(copyGeom=True, copyMesh=False)
    new_shape = new_frame_source.Shape.copy(copyGeom=True, copyMesh=False)
    if tuple(old_frame_source.Placement.toMatrix().A) != tuple(new_frame_source.Placement.toMatrix().A):
        raise RuntimeError('r14/r15 frame source-local placement changed')
    removed = old_shape.cut(new_shape)
    added = new_shape.cut(old_shape)
    removed_volume = 0.0 if removed.isNull() else float(removed.Volume)
    added_volume = 0.0 if added.isNull() else float(added.Volume)
    volume_delta = float(new_shape.Volume) - float(old_shape.Volume)
    if not all(math.isfinite(v) for v in (removed_volume, added_volume, volume_delta)):
        raise RuntimeError('Nonfinite old/new/delta frame volume')
    if removed_volume > VOLUME_TOL_MM3:
        raise RuntimeError('r15 frame removes old material: {:.12g} mm3'.format(removed_volume))
    if added.isNull() or not added.isValid() or added_volume <= VOLUME_TOL_MM3:
        raise RuntimeError('Additive frame delta is null, invalid, or below volume tolerance')
    if abs(volume_delta - (added_volume - removed_volume)) > 5*VOLUME_TOL_MM3:
        raise RuntimeError('B-rep boolean volume accounting does not close')
    delta_parts = list(added.Solids)
    if not delta_parts or any(not part.isValid() or float(part.Volume) <= VOLUME_TOL_MM3
                              for part in delta_parts):
        raise RuntimeError('Additive delta contains invalid/empty component solids')

    import hashlib as _hashlib
    def request_key(value):
        return _hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                           allow_nan=False).encode('utf-8')).hexdigest()

    cache = {}
    delta_rows = []
    max_spine = max_leg = 0.0
    min_margin = float('inf')
    previous_request_key = None
    neutral_generated = None
    neutral_keys = None
    names = sorted(name for name in links if name != FRAME_INSTANCE)
    if len(names) != EXPECTED_INSTANCES - 1:
        raise RuntimeError('Expected exactly 454 unchanged physical instances')

    for index, sample in enumerate(samples):
        theta = float(sample['theta'])
        plan = motion.descriptor(doc, theta, sample['leg_angles'],
                                 float(sample['wheel_angle']), config)
        request_digest = request_key(plan['shape_requests'])
        if index == 0:
            neutral_keys = {name: request_key(value) for name, value in plan['shape_requests'].items()}
            neutral_generated = motion.regenerate_sources(plan, cache)
        elif request_digest != previous_request_key:
            raise RuntimeError('Neutral 91-pose procedural source requests changed in local geometry')
        previous_request_key = request_digest
        frame_target = plan['placements'][FRAME_INSTANCE]
        components = []
        component_bounds = []
        for part in delta_parts:
            world = part.copy()
            world.Placement = frame_target.multiply(world.Placement)
            components.append(world)
            component_bounds.append(_box_values(world))

        other_bounds = {}
        for name in names:
            obj = links[name]
            target = plan['placements'][name]
            if name in neutral_generated:
                local = neutral_generated[name]
                other_bounds[name] = _transform_bounds(_box_values(local), target, App)
            else:
                relative = target.multiply(obj.LinkPlacement.inverse())
                other_bounds[name] = _transform_bounds(_box_values(obj.Shape), relative, App)
        world_cache = {}

        def other_shape(name):
            if name in neutral_generated:
                return _world_local_shape(neutral_generated[name], plan['placements'][name], name)
            return _world_native_shape(doc, name, plan['placements'][name])

        clearance = _screen_pairs(components, component_bounds, names, other_bounds, other_shape)
        kinematic = _kinematic_metrics(doc, theta, plan)
        max_spine = max(max_spine, kinematic['spine_closure_max_residual_mm'])
        max_leg = max(max_leg, kinematic['leg_closure_max_residual_mm'])
        min_margin = min(min_margin, kinematic['spine_min_branch_margin_mm'])
        delta_rows.append({'sample_id': sample['sample_id'], 'phase_deg': 4*index,
                           'theta_rad': theta, 'procedural_request_sha256': request_digest,
                           **kinematic, **clearance})
        if clearance['forbidden_overlaps'] or kinematic['guide_warnings']:
            break
        if index % 15 == 0:
            print('R15_DELTA_SCREEN', sample['sample_id'], clearance['status'],
                  clearance['exact_common_checks'], flush=True)

    # Full-frame checks at selected coordinated paper poses establish coverage
    # outside the stored-neutral r14 trajectory. Pair checks remain bbox-pruned.
    paper_rows = []
    frequency = float(coordination.PROFILE['presentation_frequency_hz'])
    with coordination.paper_descriptor_context():
        for degree in PAPER_PHASES_DEG:
            t = degree / (360.0 * frequency)
            theta, angles, wheel = coordination.trajectory('coordinated_spine_legs', t,
                                                            samples[0]['leg_angles'])
            plan = motion.descriptor(doc, theta, angles, wheel, config)
            generated = motion.regenerate_sources(plan, cache)
            frame_target = plan['placements'][FRAME_INSTANCE]
            frame = _world_local_shape(new_shape, frame_target, FRAME_INSTANCE)
            frame_bounds = _box_values(frame)
            other_bounds = {}
            for name in names:
                obj = links[name]
                target = plan['placements'][name]
                if name in generated:
                    other_bounds[name] = _transform_bounds(_box_values(generated[name]), target, App)
                else:
                    relative = target.multiply(obj.LinkPlacement.inverse())
                    other_bounds[name] = _transform_bounds(_box_values(obj.Shape), relative, App)
            exact_cache = {}
            bbox_excluded = occ_checks = 0
            overlaps = []
            for name in names:
                if _bbox_disjoint(frame_bounds, other_bounds[name]):
                    bbox_excluded += 1
                    continue
                if name in generated:
                    other = _world_local_shape(generated[name], plan['placements'][name], name)
                else:
                    other = _world_native_shape(doc, name, plan['placements'][name])
                common = frame.common(other)
                if common.isNull():
                    volume = 0.0
                else:
                    if not common.isValid():
                        raise RuntimeError('Invalid full-frame common at paper pose {}'.format(degree))
                    volume = float(common.Volume)
                    if not math.isfinite(volume) or volume < 0:
                        raise RuntimeError('Invalid full-frame common volume at paper pose {}'.format(degree))
                occ_checks += 1
                if volume > VOLUME_TOL_MM3:
                    overlaps.append({'instance': name, 'intersection_mm3': volume})
            if bbox_excluded + occ_checks != len(names):
                raise RuntimeError('Full-frame paper-pose pair ledger is incomplete')
            kinematic = _kinematic_metrics(doc, theta, plan)
            paper_rows.append({'profile_phase_deg': degree, 'time_s': t,
                               'theta_rad': float(theta), 'leg_angles_rad': angles,
                               'wheel_angle_rad': float(wheel), 'frame_source_sha256': _shape_sha(new_shape),
                               'pair_count': len(names), 'bbox_excluded': bbox_excluded,
                               'exact_common_checks': occ_checks,
                               'forbidden_overlaps': overlaps,
                               'status': 'FAIL' if overlaps else 'PASS_FULL_FRAME_FINITE_SAMPLE',
                               **kinematic})
            max_spine = max(max_spine, kinematic['spine_closure_max_residual_mm'])
            max_leg = max(max_leg, kinematic['leg_closure_max_residual_mm'])
            min_margin = min(min_margin, kinematic['spine_min_branch_margin_mm'])
            if overlaps or kinematic['guide_warnings']:
                break

    if _snapshot(doc) != before:
        raise RuntimeError('Delta screen mutated the native FreeCAD document')
    if _file_sha(native_path) != native_sha:
        raise RuntimeError('Delta screen changed the saved native file')
    identity_rows = {'instance_count': len(links), 'source_count': len(sources),
                     'changed_instance': FRAME_INSTANCE, 'changed_source': FRAME_SOURCE,
                     'precondition': 'Lead must run the r14-to-r15 identity helper first; this helper does not re-prove 107 source identities.'}
    closure_pass = max_spine <= 1e-6 and max_leg <= 1e-6 and min_margin > 0
    delta_pass = len(delta_rows) == 91 and all(row['status'] == 'PASS_ADDITIVE_DELTA_FINITE_SAMPLE'
                                                for row in delta_rows)
    paper_pass = len(paper_rows) == len(PAPER_PHASES_DEG) and all(
        row['status'] == 'PASS_FULL_FRAME_FINITE_SAMPLE' for row in paper_rows)
    return {
        'status': 'PASS_BOUNDED_ADDITIVE_DELTA_R15' if closure_pass and delta_pass and paper_pass else 'FAIL',
        'native_sha256': native_sha,
        'r14_report_sha256': _file_sha(R14_REPORT),
        'r14_plan_sha256': _file_sha(R14_PLAN),
        'r15_config_sha256': _file_sha(config_file),
        'r15_config_projection_sha256': _json_sha(_config_projection(config)),
        'frame_source_sha256': {'r14': _shape_sha(old_shape), 'r15': _shape_sha(new_shape)},
        'frame_volume_mm3': {'r14': float(old_shape.Volume), 'r15': float(new_shape.Volume),
                             'added_delta': added_volume, 'removed_delta': removed_volume,
                             'volume_difference': volume_delta,
                             'added_solid_count': len(delta_parts),
                             'density_kg_m3_assumption': 1000.0,
                             'added_mass_kg_assumption': added_volume * 1e-6},
        'identity_inventory': identity_rows,
        'delta_cycle': {'phase_degrees': list(range(0, 361, 4)),
                        'pair_scope': 'Each actual added-delta solid against all 454 other physical instances',
                        'records': delta_rows,
                        'pair_decisions': sum(row['pair_decisions'] for row in delta_rows),
                        'bbox_excluded': sum(row['bbox_excluded'] for row in delta_rows),
                        'exact_common_checks': sum(row['exact_common_checks'] for row in delta_rows),
                        'forbidden_overlaps': [hit for row in delta_rows for hit in row['forbidden_overlaps']]},
        'paper_profile_full_frame': {'phase_degrees': list(PAPER_PHASES_DEG),
                        'profile_sha256': _file_sha(coordination.PROFILE_PATH),
                        'pair_scope': 'Complete new frame against all 454 other physical instances',
                        'records': paper_rows,
                        'forbidden_overlaps': [hit for row in paper_rows for hit in row['forbidden_overlaps']]},
        'kinematic_summary': {'max_spine_closure_residual_mm': max_spine,
                              'max_leg_loop_residual_mm': max_leg,
                              'minimum_spine_branch_margin_mm': min_margin,
                              'closure_gate_pass': closure_pass},
        'document_unchanged': True, 'native_file_unchanged': True,
        'continuous_clearance': False, 'full_historical_campaign': False,
        'loaded_equilibrium': False, 'strength_or_fatigue_qualification': False,
        'helper_sha256': {'verify_sculpted_delta_r15.py': _file_sha(Path(__file__)),
                          'leg_motion_r07.py': _file_sha(ROOT/'src/leg_motion_r07.py'),
                          'animation_coordination_v2.py': _file_sha(ROOT/'src/animation_coordination_v2.py'),
                          'animation_pose_export.py': _file_sha(ROOT/'src/animation_pose_export.py')},
        'limitations': ['The r14 result is reused only for its recorded 91 affected-pair poses after the separate identity gate.',
                        'Additive-delta cycle checks do not recompute the unchanged r14 frame portion.',
                        'The nine paper-profile poses screen the complete new frame against all 454 instances.',
                        'Finite samples do not prove continuous clearance or loaded performance.',
                        'PA12 mass uses an explicit density assumption of 1000 kg/m3.'],
    }
