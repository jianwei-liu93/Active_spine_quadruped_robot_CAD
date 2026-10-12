"""Copied actual-native full-robot spine sweep; supplemental FreeCADCmd use.

sweep(doc, 5) is coarse evidence; sweep(doc, 1) includes 361 prescribed poses.
The caller document is never moved, recomputed or saved. No FreeCADGui import.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time

import robot_pose_r03 as pose
from kinematics import spine, residuals

ROOT = Path(__file__).resolve().parents[1]
VOLUME_TOL = 1e-5
BBOX_TOL = 1e-6
REPROJECTION_TOL = 1e-6
BOUND_KEYS = tuple(axis + end for axis in 'XYZ' for end in ('Min', 'Max'))
FIXED_POINTS = frozenset(('O', 'A1', 'A2', 'E1', 'E2'))
PLANAR_KINDS = frozenset(('segment', 'point', 'axialrot', 'horn_screw',
                          'torso_r03', 'torso_offset_r03', 'torso_r03_offset',
                          'torso_r04_rigid', 'tendon_r03_wheel',
                          'tendon_r03_guide', 'tendon_r03_cable')) | pose.LEG_KINDS


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def _phases(step):
    step = float(step)
    if not math.isfinite(step) or not 0 < step <= 360:
        raise ValueError('step_deg must be finite and in (0,360]')
    # Always include both endpoints, including when step does not divide 360.
    phases = [i * step for i in range(int(math.ceil(360 / step)))
              if i * step < 360 - 1e-10]
    return phases + [360.0]


def _sample_phases(step, explicit=None):
    if explicit is None:return _phases(step),None
    requested=[float(v) for v in explicit]
    if not all(math.isfinite(v) and 0<=v<=360 for v in requested):
        raise ValueError('phase_values_deg must be finite and in [0,360]')
    requested=sorted(set(requested))
    return sorted(set([0.0]+requested)),requested


def _group(m):
    """Only declared rigid relationships; unclassified descriptors stay dynamic.

    Point hardware has circular axial native geometry. Its occupied shape,
    unlike its arbitrary axial rotation datum, rotates rigidly with its torso.
    Fixed leg angles include the installed coils and fixed guide lengths.
    """
    if m is None or m.get('kind')=='fixed':
        return ('fixed',)
    k = m.get('kind')
    if k == 'point':
        return ('fixed',) if m['point'] in FIXED_POINTS else ('joint', m['point'])
    if k in ('torso_r03', 'torso_offset_r03','torso_r03_offset','torso_r04_rigid'):
        return ('torso', m['torso'])
    if k in ('tendon_r03_wheel','tendon_r03_guide','tendon_r03_cable'):
        return ('torso',m.get('torso','hind'))
    if k in pose.LEG_KINDS:
        return ('torso', m['leg_type'])
    return None


def _bounds(shape):
    b = shape.BoundBox
    return tuple(float(getattr(b, key)) for key in BOUND_KEYS)


def _overlap(a, b, axes=(0, 2, 4)):
    return all(min(a[i+1], b[i+1]) - max(a[i], b[i]) > BBOX_TOL for i in axes)


def _world_copy(shape, initial, target):
    # o.Shape is already in world coordinates: never replace its Placement by
    # target directly, which would double-apply/misapply the native placement.
    copy = shape.copy()
    copy.Placement = target.multiply(initial.inverse()).multiply(shape.Placement)
    return copy


def sweep(doc, step_deg=5, output=None, phase_values_deg=None):
    """Return/write raw sampled intersections from copies of every App::Link.

    output defaults to reports/verification/r03_robot_spine_sweep.json.
    Its sibling <stem>_progress.json updates every ten completed samples.
    Errors write ERROR evidence and propagate; incomplete coverage never passes.
    PASS means sampled raw volume checks only, with leg coordinates held fixed.
    """
    import FreeCAD as App
    start = time.monotonic()
    output = Path(output or ROOT / 'reports/verification/r03_robot_spine_sweep.json')
    progress = output.with_name(output.stem + '_progress.json')
    phases, requested = _sample_phases(step_deg,phase_values_deg)
    report = {'revision': str(getattr(doc.DesignParameters,'Revision','r03')), 'status': 'RUNNING',
              'scope': 'Actual native App::Link world-shape copies; ' + ('partial explicit spine phases' if requested is not None else 'full spine cycle') + '; fixed saved leg angles; raw intersections without exceptions',
              'step_deg': float(step_deg), 'sample_degrees': phases,
              'requested_phase_values_deg':requested, 'actual_sample_degrees':phases,
              'coverage_scope':'full_step_cycle' if requested is None else 'partial_explicit',
              'requested_samples_total':len(phases) if requested is None else len(requested),
              'samples_total': len(phases), 'samples_completed': 0,
              'volume_tolerance_mm3': VOLUME_TOL,
              'bbox_overlap_tolerance_mm': BBOX_TOL,
              'reprojection_tolerance_mm': REPROJECTION_TOL,
              'document': {'name': doc.Name, 'file': doc.FileName},
              'raw_overlaps': [], 'errors': [],
              'limits': [
                  'Finite prescribed samples; no continuous clearance or minimum gap certificate.',
                  'Leg angles, spring source shapes and guide lengths are held fixed; no gait, tendon actuation, elastic equilibrium or loaded deformation.',
                  'Same-torso caching assumes the declared fixed leg geometry and circular axial point hardware; changing descriptor semantics requires revisiting the cache.',
                  'Mathematical closure residuals are not native bore-axis measurements; native joint/axis alignment is NOT_CHECKED here.',
                  'No fabrication or unverified supplier-interface certification.']}
    counts = Counter()
    worst = {}

    def publish(final=False):
        report['elapsed_seconds'] = time.monotonic() - start
        report['counts'] = dict(counts)
        report['raw_overlap_pairs'] = len(worst)
        report['raw_overlaps'] = sorted(worst.values(), key=lambda row: -row['intersection_mm3'])
        _write(progress, {k: v for k, v in report.items()
                          if k not in ('parts', 'raw_overlaps', 'sample_degrees')})
        if final:
            _write(output, report)

    try:
        controller = doc.getObject('PoseController')
        if controller is None:
            raise ValueError('PoseController is missing')
        motion = json.loads(controller.MotionMap)
        report['document_sha256']=(hashlib.sha256(Path(doc.FileName).read_bytes()).hexdigest()
                                   if doc.FileName and Path(doc.FileName).is_file() else None)
        report['motion_map_sha256'] = hashlib.sha256(controller.MotionMap.encode()).hexdigest()
        objs = [o for o in doc.Objects if o.TypeId == 'App::Link']
        if not objs:
            raise ValueError('No App::Link instances to verify')
        names = [o.Name for o in objs]
        original = {o.Name: o.Shape.copy() for o in objs}
        initial = {o.Name: App.Placement(o.LinkPlacement) for o in objs}
        original_bounds = {n: _bounds(original[n]) for n in names}
        report['parts'] = [{'instance': o.Name, 'source': o.LinkedObject.Name,
                            'valid': original[o.Name].isValid(),
                            'solids': len(original[o.Name].Solids),
                            'volume_mm3': float(original[o.Name].Volume)} for o in objs]
        report['instances'] = len(objs)
        report['motion_kinds'] = dict(Counter(m.get('kind', '<missing>') for m in motion.values()))
        report['leg_angles_rad'] = pose._angles(motion, controller)[1]
        p = pose._parameters(doc)
        current_phase = pose._number(controller.SpinePhaseRad)
        current_places = pose.placements(doc, current_phase)
        if set(current_places) != set(names):
            raise ValueError('placements must cover exactly every native App::Link')
        identity_error = mapping_error = 0.0
        for n in names:
            identity = _bounds(_world_copy(original[n], initial[n], initial[n]))
            projected = _bounds(_world_copy(original[n], initial[n], current_places[n]))
            identity_error = max(identity_error, max(abs(a-b) for a,b in zip(identity, original_bounds[n])))
            error = max(abs(a-b) for a,b in zip(projected, original_bounds[n]))
            mapping_error = max(mapping_error, error)
            if error > REPROJECTION_TOL:
                report.setdefault('reprojection_failures', []).append({'instance': n, 'max_bound_error_mm': error})
        report['neutral_reprojection'] = {
            'saved_phase_rad': current_phase,
            'identity_world_copy_max_bound_error_mm': identity_error,
            'saved_phase_descriptor_max_bound_error_mm': mapping_error,
            'status': 'PASS' if max(identity_error, mapping_error) <= REPROJECTION_TOL else 'FAIL',
            'scope': 'Copied world shapes reprojected at saved phase; theta=0 sampled separately if saved phase differs.'}
        if max(identity_error, mapping_error) > REPROJECTION_TOL:
            raise ValueError('Saved native placement/descriptor reprojection does not match bounds')

        groups = {n: _group(motion.get(n)) for n in names}
        pairs = [(a, b) for i, a in enumerate(names) for b in names[i+1:]]
        invariant = {(a,b) for a,b in pairs if groups[a] is not None and groups[a] == groups[b]}
        dynamic = [pair for pair in pairs if pair not in invariant]
        # Known descriptors preserve global Y. Validate this assumption against
        # actual posed bounds every phase; unclassified future kinds do not use it.
        stable_y = {n for n in names if n not in motion or motion[n].get('kind') in PLANAR_KINDS}
        report['pair_coverage'] = {'all_pairs': len(pairs), 'invariant_pairs': len(invariant),
                                   'dynamic_pairs': len(dynamic),
                                   'unclassified_motion_instances': [n for n in motion if _group(motion[n]) is None],
                                   'neutral_all_pairs_once': False}
        report['maximum_mathematical_spine_closure_residual_mm'] = 0.0
        report['native_axis_alignment'] = {'status': 'NOT_CHECKED', 'reason': 'Requires separate native bore/shaft-axis evidence.'}
        neutral_hits = []
        y_bounds = None
        for index, degrees in enumerate(phases):
            theta = math.radians(degrees)
            state = spine(theta, p)
            report['maximum_mathematical_spine_closure_residual_mm'] = max(
                report['maximum_mathematical_spine_closure_residual_mm'],
                max(abs(r) for r in residuals(state, p)))
            targets = pose.placements(doc, theta)
            if set(targets) != set(names):
                raise ValueError('Pose mapping coverage changed during sweep')
            shapes = {n: _world_copy(original[n], initial[n], targets[n]) for n in names}
            bounds = {n: _bounds(shapes[n]) for n in names}
            if y_bounds is None:
                y_bounds = {n: bounds[n][2:4] for n in stable_y}
            else:
                for n in stable_y:
                    if max(abs(a-b) for a,b in zip(bounds[n][2:4], y_bounds[n])) > REPROJECTION_TOL:
                        raise ValueError('Declared planar Y interval changed: ' + n)
            phase_pairs = pairs if index == 0 else dynamic
            counts['cached_invariant_pair_samples'] += 0 if index == 0 else len(invariant)
            phase_hits = 0
            for a,b in phase_pairs:
                counts['pair_samples_considered'] += 1
                ba, bb = bounds[a], bounds[b]
                if not _overlap(ba, bb, (2,)):
                    counts['y_interval_rejections'] += 1
                    continue
                if not _overlap(ba, bb, (0,4)):
                    counts['xz_bbox_rejections'] += 1
                    continue
                counts['narrowphase_tests'] += 1
                try:
                    volume = float(shapes[a].common(shapes[b]).Volume)
                    if not math.isfinite(volume):
                        raise ValueError('Nonfinite Boolean intersection volume')
                except Exception as exc:
                    report['errors'].append({'a': a, 'b': b, 'phase_deg': degrees,
                                             'error': type(exc).__name__ + ': ' + str(exc)})
                    raise
                if volume <= VOLUME_TOL:
                    continue
                phase_hits += 1
                key = (a,b)
                if index == 0:
                    neutral_hits.append({'a': a, 'b': b, 'intersection_mm3': volume})
                if key not in worst or volume > worst[key]['intersection_mm3']:
                    worst[key] = {'a': a, 'b': b, 'intersection_mm3': volume,
                                  'worst_phase_deg': degrees,
                                  'invariant_relative_pair': key in invariant}
            if index == 0:
                report['pair_coverage']['neutral_all_pairs_once'] = True
                report['neutral'] = {'phase_deg': 0.0, 'scope': 'All native instance pairs; no contact exceptions',
                                     'raw_overlaps': neutral_hits,
                                     'narrowphase_tests': counts['narrowphase_tests']}
            report['samples_completed'] = index + 1
            report['last_phase_deg'] = degrees
            report['last_phase_dynamic_or_neutral_overlap_pairs'] = phase_hits
            if (index + 1) % 10 == 0 or index == 0:
                publish()
        covered = counts['pair_samples_considered'] + counts['cached_invariant_pair_samples']
        report['pair_coverage']['pair_samples_covered_including_cache'] = covered
        report['pair_coverage']['pair_samples_expected'] = len(pairs) * len(phases)
        if covered != len(pairs) * len(phases):
            raise ValueError('Incomplete sampled pair coverage')
        valid = all(row['valid'] and row['solids'] == 1 and row['volume_mm3'] > 0 for row in report['parts'])
        report['status'] = 'PASS' if valid and not worst else 'FAIL'
        report['native_shapes_valid_one_solid'] = valid
        publish(final=True)
        print(json.dumps({'status': report['status'], 'samples': len(phases),
                          'overlap_pairs': len(worst), 'output': str(output),
                          'elapsed_seconds': report['elapsed_seconds']}), flush=True)
        return report
    except Exception as exc:
        report['status'] = 'ERROR'
        report['errors'].append({'error': type(exc).__name__ + ': ' + str(exc)})
        publish(final=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cad', type=Path, default=ROOT / 'cad/flexor_r03_robot.FCStd')
    parser.add_argument('--step-deg', type=float, default=5)
    parser.add_argument('--phase-values-deg',type=float,nargs='+',default=None)
    parser.add_argument('--output', type=Path, default=None)
    args = parser.parse_args(argv)
    import FreeCAD as App
    doc = App.openDocument(str(args.cad))
    try:
        result = sweep(doc, args.step_deg, args.output, args.phase_values_deg)
    finally:
        App.closeDocument(doc.Name)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
