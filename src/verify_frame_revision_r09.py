"""Read-only r09 affected-frame verification; execution requires lead freeze.

No automatic execution, saves, pose assignments or shared source mutations.
The r08 complete campaign is reused only after strict unchanged-instance proof.
Partial frame partitions never establish a whole-r09 PASS.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/verification/r09_frame_partitions'
FREEZE = OUT / 'freeze.json'
IDENTITY = OUT / 'identity.json'
FRAME = 'LumbarIntegrated1'
RETIRED = ('LumbarIntegrated_1',) + tuple(
    ['FixedLumbarTie'+str(j) for j in range(4)] +
    ['FixedTieScrew'+str(j)+s for j in range(4) for s in ('__1', '_1')])
VOLUME_TOL = 1e-5
BBOX_TOL = 1e-5
REL_VOLUME_TOL = 1e-6
EXTRA_DEPENDENCIES = ('spine_frame_r09.py', 'verify_frame_revision_r09.py',
                      'adaptive_volume_r07.py', 'occt_adaptive_volume_r07.cpp')


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def _motion_configuration(value):
    """Permit only descriptive revision text and the new frame subtree."""
    result = dict(value)
    for key in ('revision', 'limits'):
        if key in result and not isinstance(result[key], str):
            raise RuntimeError('Expected descriptive string config field: '+key)
        result.pop(key, None)
    result.pop('lumbar_frame_r09', None)
    return result


def _numeric_properties(obj):
    values = {}
    for key in obj.PropertiesList:
        value = getattr(obj, key)
        if isinstance(value, (bool, int, float)):
            values[key] = value
        elif hasattr(value, 'Value') and isinstance(value.Value, (int, float)):
            values[key] = float(value.Value)
    return values


def manifest():
    """Pure enumeration, exactly985 frozen inputs plus361 fixed-leg phases."""
    from verify_motion_package_r08 import manifest as original_manifest
    from leg_motion_r07 import pose_states
    stored_path = ROOT / 'reports/verification/r08_motion_partitions/full_manifest.json'
    stored = json.loads(stored_path.read_text())
    original = original_manifest('full')
    if _digest(stored) != _digest(original) or original['count'] != 985:
        raise RuntimeError('Stored r08 full manifest differs from current authoritative enumeration')
    states = [dict(s) for s in original['states']]
    config = json.loads((ROOT/'parameters/assembly_r08.json').read_text())
    neutral = {tag: row['angles_rad'] for tag, row in pose_states(config=config)['legs'].items()}
    for degree in range(361):
        state = {'sample_id': 'frame_spine_'+str(degree).zfill(3),
                 'label': 'fixed_leg_spine_'+str(degree), 'trajectory': 'fixed_leg_spine',
                 'theta': math.radians(degree), 'leg_angles': neutral, 'wheel_angle': 0.}
        state['input_sha256'] = _digest({k: state[k] for k in ('theta', 'leg_angles', 'wheel_angle')})
        states.append(state)
    if len(states) != 1346 or len({s['sample_id'] for s in states}) != 1346:
        raise RuntimeError('Coverage IDs are not complete/unique')
    return {'count': len(states), 'states': states, 'sha256': _digest(states),
            'r08_manifest_sha256': original['sha256'], 'r08_full_manifest_file_sha256': _sha(stored_path),
            'original_985_sample_ids': [s['sample_id'] for s in original['states']],
            'fixed_leg_361_sample_ids': [s['sample_id'] for s in states[985:]],
            'scope': '985 original full inputs plus361 integer spine phases with neutral legs/wheel0; neutral duplicate retained',
            'continuous_clearance': False}


def capture_freeze(native, expected_sha256):
    """Lead-authorized explicit freeze; never opens/mutates any CAD document."""
    from verify_motion_package_r08 import validate_freeze, DEPENDENCIES, FREEZE as OLD_FREEZE
    validate_freeze()
    native = Path(native).resolve()
    if _sha(native) != expected_sha256:
        raise RuntimeError('r09 native does not match lead-supplied SHA')
    plan = manifest()
    record = {'native_path': str(native), 'native_sha256': expected_sha256,
              'r08_freeze_sha256': _sha(OLD_FREEZE),
              'config_r08_sha256': _sha(ROOT/'parameters/assembly_r08.json'),
              'config_r09_sha256': _sha(ROOT/'parameters/assembly_r09.json'),
              'dependency_sha256': {n: _sha(ROOT/'src'/n) for n in sorted(set(DEPENDENCIES+EXTRA_DEPENDENCIES))},
              'manifest_sha256': plan['sha256'],
              'r08_full_manifest_file_sha256': plan['r08_full_manifest_file_sha256']}
    _write(FREEZE, record)
    return record


def validate_freeze():
    from verify_motion_package_r08 import validate_freeze as old_validate, FREEZE as OLD_FREEZE
    old_validate()
    record = json.loads(FREEZE.read_text())
    checks = {_sha(record['native_path']) == record['native_sha256'],
              _sha(OLD_FREEZE) == record['r08_freeze_sha256'],
              _sha(ROOT/'parameters/assembly_r08.json') == record['config_r08_sha256'],
              _sha(ROOT/'parameters/assembly_r09.json') == record['config_r09_sha256'],
              manifest()['sha256'] == record['manifest_sha256'],
              _sha(ROOT/'reports/verification/r08_motion_partitions/full_manifest.json') == record['r08_full_manifest_file_sha256']}
    if checks != {True} or any(_sha(ROOT/'src'/n) != h for n, h in record['dependency_sha256'].items()):
        raise RuntimeError('Lead-frozen input/dependency changed')
    return record


def _brep_sha(shape):
    data = shape.exportBrepToString()
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def _matrix(placement):
    return tuple(placement.toMatrix().A)


def _bbox(shape):
    box = shape.BoundBox
    values = tuple(float(getattr(box, k)) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
    if not all(math.isfinite(v) for v in values):
        raise RuntimeError('Nonfinite actual-shape bounding box')
    return values


def _strict_shape_identity(old, new, label):
    """Exact BREP or all strict Boolean/adaptive-volume/bbox fallback gates."""
    for shape in (old, new):
        if not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError(label+': invalid/non-single solid')
    a, b = _brep_sha(old), _brep_sha(new)
    if a == b:
        return {'method': 'exact_brep', 'old_sha256': a, 'new_sha256': b}
    from adaptive_volume_r07 import validate_solids
    differences = (float(old.cut(new).Volume), float(new.cut(old).Volume))
    if not all(math.isfinite(v) for v in differences) or max(differences) > VOLUME_TOL:
        raise RuntimeError(label+': bidirectional Boolean difference exceeds1e-5mm3: '+str(differences))
    if max(abs(x-y) for x, y in zip(_bbox(old), _bbox(new))) > BBOX_TOL:
        raise RuntimeError(label+': bbox differs by more than1e-5mm')
    adaptive = validate_solids(new, [old], ROOT, [label],
                               volume_rel_tol=REL_VOLUME_TOL, bbox_abs_tol_mm=BBOX_TOL)
    return {'method': 'strict_boolean_adaptive_bbox', 'old_sha256': a, 'new_sha256': b,
            'bidirectional_difference_mm3': differences, 'adaptive_comparison': adaptive}


def _document_fingerprint(doc):
    from verify_motion_package_r08 import _native_fingerprint
    from robot_pose_r03 import _parameters
    controller = doc.getObject('PoseController')
    values = {}
    for key in ('SpinePhaseRad','LegAnglesR03','WheelAngleR07','PrescribedMotionConfigR07'):
        if key in controller.PropertiesList:
            value = getattr(controller, key)
            values[key] = float(value.Value) if hasattr(value, 'Value') else value
    return _digest({'physical_native': _native_fingerprint(doc),
                    'pose_parameters': _parameters(doc), 'controller': values})


def prove_identity():
    """Read-only CAD proof; called explicitly by lead before partition runs."""
    import FreeCAD as App
    from robot_pose_r03 import _parameters
    from verify_motion_package_r08 import validate_freeze as old_validate
    freeze = validate_freeze()
    native8 = ROOT/'cad/flexor_r08_robot.FCStd'
    files_before = {str(p): _sha(p) for p in (native8, Path(freeze['native_path']))}
    docs = []
    record = {'status': 'ERROR', 'freeze_sha256': _sha(FREEZE),
              'identity_merge': {'LumbarIntegrated_1': FRAME}, 'retired_instances': RETIRED,
              'records': [], 'errors': []}
    fingerprints = []
    try:
        old_validate()
        old = App.openDocument(str(native8)); docs.append(old)
        new = App.openDocument(freeze['native_path']); docs.append(new)
        fingerprints = [_document_fingerprint(d) for d in docs]
        a = {o.Name: o for o in old.Objects if o.TypeId == 'App::Link'}
        b = {o.Name: o for o in new.Objects if o.TypeId == 'App::Link'}
        if len(a) != 486 or len(b) != 473 or set(a)-set(b) != set(RETIRED) or set(b)-set(a):
            raise RuntimeError('Exact retired physical identity set/count mismatch')
        unchanged = sorted(set(b)-{FRAME})
        if len(unchanged) != 472:
            raise RuntimeError('Expected472 unchanged non-frame instances')
        if _matrix(a[FRAME].LinkPlacement) != _matrix(b[FRAME].LinkPlacement):
            raise RuntimeError('Retained frame placement changed')
        if b[FRAME].LinkedObject.PartNumber != 'FRM_LUMBAR_MONOLITHIC_CAGE_r09':
            raise RuntimeError('Unexpected r09 frame part number')
        if _parameters(old) != _parameters(new):
            raise RuntimeError('Native mechanism/pose parameters changed')
        mm8 = json.loads(old.PoseController.MotionMap)
        mm9 = json.loads(new.PoseController.MotionMap)
        if {k:v for k,v in mm8.items() if k not in RETIRED} != mm9:
            raise RuntimeError('MotionMap changed outside explicitly retired IDs')
        for key in ('SpinePhaseRad','LegAnglesR03','WheelAngleR07'):
            if getattr(old.PoseController,key,None) != getattr(new.PoseController,key,None):
                raise RuntimeError('Neutral pose controller changed: '+key)
        for key in ('PrescribedMotionConfigR07',):
            va, vb = getattr(old.PoseController,key,None), getattr(new.PoseController,key,None)
            if (va is None) != (vb is None) or (va is not None and _motion_configuration(json.loads(va)) != _motion_configuration(json.loads(vb))):
                raise RuntimeError('Native prescribed motion numerics changed')
        cfg8 = json.loads((ROOT/'parameters/assembly_r08.json').read_text())
        cfg9 = json.loads((ROOT/'parameters/assembly_r09.json').read_text())
        # Only frame revision is allowed a new numeric configuration subtree.
        cfg9.pop('lumbar_frame_r09', None)
        if _motion_configuration(cfg8) != _motion_configuration(cfg9):
            raise RuntimeError('Leg/mechanism/assembly numerics changed')
        source_cache = {}
        for name in unchanged:
            x, y = a[name], b[name]
            if _matrix(x.LinkPlacement) != _matrix(y.LinkPlacement):
                raise RuntimeError(name+': neutral placement changed')
            if x.LinkedObject.Name != y.LinkedObject.Name or x.LinkedObject.PartNumber != y.LinkedObject.PartNumber:
                raise RuntimeError(name+': source identity/part number changed')
            if _matrix(x.LinkedObject.Placement) != _matrix(y.LinkedObject.Placement):
                raise RuntimeError(name+': source-local placement changed')
            if _numeric_properties(x.LinkedObject) != _numeric_properties(y.LinkedObject):
                raise RuntimeError(name+': source numerical properties changed')
            key = (x.LinkedObject.Name, y.LinkedObject.Name)
            if key not in source_cache:
                source_cache[key] = _strict_shape_identity(x.LinkedObject.Shape, y.LinkedObject.Shape, name)
            record['records'].append({'instance': name, 'source': x.LinkedObject.Name,
                                      'placement_exact': True, 'geometry': source_cache[key],
                                      'placed_geometry': _strict_shape_identity(x.Shape, y.Shape, name+' placed')})
        from verify_motion_package_r08 import _native_fingerprint
        record['r08_campaign_geometry_sha256'] = _native_fingerprint(old)
        record.update({'status': 'PASS_IDENTITY_ONLY', 'unchanged_count': len(unchanged),
                       'unchanged_instances': unchanged, 'geometry_sha256_r08': fingerprints[0],
                       'geometry_sha256_r09': fingerprints[1], 'native_r09_sha256': freeze['native_sha256'],
                       'native_r08_sha256': files_before[str(native8)],
                       'motion_map_exact_after_retirement': True, 'pose_and_configuration_numerics_exact': True})
    except Exception as error:
        record['errors'].append(repr(error))
    finally:
        record['native_files_unchanged'] = all(_sha(p) == h for p,h in files_before.items())
        record['documents_unchanged'] = bool(fingerprints) and fingerprints == [_document_fingerprint(d) for d in docs]
        try:
            validate_freeze()
        except Exception as error:
            record['errors'].append(repr(error))
        if record['errors'] or not record['native_files_unchanged'] or not record['documents_unchanged']:
            record['status'] = 'FAIL_IDENTITY'
        _write(IDENTITY, record)
        for doc in docs:
            App.closeDocument(doc.Name)
    return record


def _identity_gate():
    freeze = validate_freeze()
    proof = json.loads(IDENTITY.read_text())
    if (proof['status'] != 'PASS_IDENTITY_ONLY' or proof['unchanged_count'] != 472 or
            proof['freeze_sha256'] != _sha(FREEZE) or
            proof['native_r09_sha256'] != freeze['native_sha256']):
        raise RuntimeError('Coherent strict472-instance identity proof required')
    return freeze, proof


def _overlap(a, b):
    # Strict disjointness only: no bbox tolerance may hide positive overlap.
    return all(min(a[i+1], b[i+1]) >= max(a[i], b[i]) for i in (0,2,4))


def _placed_box(box, placement):
    import FreeCAD as App
    if not all(math.isfinite(v) for v in box):
        raise RuntimeError('Nonfinite conservative generator bound')
    corners = [placement.multVec(App.Vector(*q))
               for q in itertools.product(*[(box[i],box[i+1]) for i in (0,2,4)])]
    values = tuple(v for axis in range(3) for v in
                   (min(q[axis] for q in corners), max(q[axis] for q in corners)))
    if not all(math.isfinite(v) for v in values):
        raise RuntimeError('Nonfinite transformed generator bound')
    return values


def _dynamic_boxes(request, placement):
    """Proven conservative generator bounds; never approximate narrowphase."""
    if request['generator'] == 'spring':
        length = request['length_mm']
        if request['kind'] == 'compression':
            # compression_spring_r07.validate requires OD4/seat interval ±1e-5.
            box = (-2.00001,2.00001,-2.00001,2.00001,-.00001,length+.00001)
            basis = 'compression generator validated OD4 and0..length envelope, expanded1e-5mm'
        elif request['kind'] == 'extension':
            # OD4 helix; hook centers x<=2.75 with radius.25 cylinders extended.05;
            # end torus major1.25/minor.25 reaches ±1.5 in its XZ plane.
            box = (-3.1,3.1,-3.1,3.1,-1.6,length+1.6)
            basis = 'extension helix/hook/torus analytic containment; radial3.1mm/end1.6mm; normalization bbox shift<=1e-5'
        else:
            return None, 'unsupported spring kind: actual regeneration required'
        return [_placed_box(box, placement)], basis
    if request['generator'] == 'cable':
        boxes = []
        for primitive in request['route']['primitives']:
            if primitive['length_mm'] < 1e-10:
                continue
            if primitive['type'] == 'line':
                low = [min(a,b)-.15 for a,b in zip(primitive['start'],primitive['end'])]
                high = [max(a,b)+.15 for a,b in zip(primitive['start'],primitive['end'])]
            elif primitive['type'] == 'arc':
                # Full circle sphere bounds every directed/multiturn arc generated
                # by rotation of the actual start vector; no chord approximation.
                radius = math.dist(primitive['start'], primitive['center'])+.15
                low = [v-radius for v in primitive['center']]
                high = [v+radius for v in primitive['center']]
            else:
                return None, 'unknown cable primitive: actual regeneration required'
            boxes.append(_placed_box(tuple(v for i in range(3) for v in (low[i],high[i])), placement))
        if not boxes:
            raise RuntimeError('Empty cable route bound')
        return boxes, 'per-primitive line/full-arc-circle bounds expanded actual wire radius0.15mm'
    return None, 'unknown generator: actual regeneration required'


def run_partition(partition, partitions):
    """Explicit lead-run supplemental CLI, frame vs472others only, read-only."""
    import FreeCAD as App
    from leg_motion_r07 import descriptor, regenerate_sources
    if not isinstance(partitions,int) or not 1 <= partitions <= 24 or not 0 <= partition < partitions:
        raise ValueError('Expected partition in0..partitions-1, partitions1..24')
    freeze, proof = _identity_gate()
    plan = manifest(); states = plan['states'][partition::partitions]
    start = time.monotonic(); doc = None; cache = {}; pair_cache = {}; fingerprint = None
    report = {'status': 'RUNNING', 'partition': partition, 'partitions': partitions,
              'manifest_sha256': plan['sha256'], 'freeze_sha256': _sha(FREEZE),
              'identity_sha256': _sha(IDENTITY), 'native_sha256': freeze['native_sha256'],
              'dependency_sha256': freeze['dependency_sha256'],
              'expected_sample_ids': [s['sample_id'] for s in states], 'records': [],
              'counterpart_instances': proof['unchanged_instances'], 'pairs_per_pose': 472,
              'occ_checks': 0, 'cached_pair_checks': 0, 'errors': [], 'overlaps': [],
              'volume_tolerance_mm3': VOLUME_TOL, 'exceptions': [],
              'exclusion_basis': {'rigid': 'strict disjoint actual placed-solid AABBs only',
                                  'dynamic': 'generator-proven conservative world boxes; actual exact regeneration otherwise'},
              'continuous_clearance': False, 'loaded_equilibrium': False, 'fabrication_release': False}
    output = OUT/('part_'+str(partition)+'.json')
    def publish():
        report['elapsed_seconds'] = time.monotonic()-start
        report['samples_completed'] = len(report['records'])
        _write(output, report)
    try:
        doc = App.openDocument(freeze['native_path'])
        fingerprint = _document_fingerprint(doc)
        if fingerprint != proof['geometry_sha256_r09']:
            raise RuntimeError('Loaded document differs from identity proof')
        config = json.loads((ROOT/'parameters/assembly_r09.json').read_text())
        frame = doc.getObject(FRAME).Shape.copy(); frame_box = _bbox(frame)
        if not frame.isValid() or len(frame.Solids) != 1:
            raise RuntimeError('New frame must be one valid solid')
        ground = _matrix(doc.getObject(FRAME).LinkPlacement)
        names = proof['unchanged_instances']
        expected_names = set(names)|{FRAME}
        for state in states:
            pp = descriptor(doc, state['theta'], state['leg_angles'], state['wheel_angle'], config)
            if set(pp['placements']) != expected_names or _matrix(pp['placements'][FRAME]) != ground:
                raise RuntimeError('Descriptor coverage or grounded-frame placement changed')
            row = {'sample_id': state['sample_id'], 'input_sha256': state['input_sha256'],
                   'input': state, 'status': 'PASS_AFFECTED_FRAME_ONLY', 'pair_coverage': 0,
                   'rigid_disjoint': [], 'dynamic_disjoint': [], 'narrowphase': [],
                   'guide_warnings': pp['guide_warnings']}
            if pp['guide_warnings']:
                row['status'] = 'FAIL_GUIDE_TRAVEL'
            for name in names:
                placement = pp['placements'][name]
                request = pp['shape_requests'].get(name)
                if request:
                    boxes, basis = _dynamic_boxes(request, placement)
                    if boxes is not None and all(not _overlap(frame_box, box) for box in boxes):
                        row['dynamic_disjoint'].append({'instance': name, 'basis': basis, 'world_boxes_mm': boxes})
                        row['pair_coverage'] += 1
                        continue
                    sparse = dict(pp, shape_requests={name: request})
                    shape = regenerate_sources(sparse, cache)[name]
                    shape.Placement = placement.multiply(shape.Placement)
                    signature = (_digest(request), _matrix(placement))
                else:
                    obj = doc.getObject(name)
                    shape = obj.Shape.copy()
                    shape.Placement = placement.multiply(obj.LinkPlacement.inverse()).multiply(shape.Placement)
                    signature = ('native:'+obj.LinkedObject.Name, _matrix(placement))
                if not shape.isValid() or len(shape.Solids) != 1:
                    raise RuntimeError(name+': actual placed shape invalid/non-single solid')
                if not _overlap(frame_box, _bbox(shape)):
                    row['rigid_disjoint'].append(name)
                    row['pair_coverage'] += 1
                    continue
                key = (name, signature)
                if key in pair_cache:
                    volume = pair_cache[key]; report['cached_pair_checks'] += 1
                else:
                    common = frame.common(shape)
                    volume = float(common.Volume)
                    if not math.isfinite(volume) or (not common.isNull() and not common.isValid()):
                        raise RuntimeError(name+': invalid/nonfinite Boolean intersection')
                    pair_cache[key] = volume; report['occ_checks'] += 1
                row['narrowphase'].append({'instance': name, 'intersection_mm3': volume, 'actual_solid': True})
                row['pair_coverage'] += 1
                if volume > VOLUME_TOL:
                    row['status'] = 'FAIL_COLLISION'
                    report['overlaps'].append({'a': FRAME, 'b': name, 'sample_id': state['sample_id'], 'intersection_mm3': volume})
            if row['pair_coverage'] != 472:
                raise RuntimeError('Incomplete affected-frame pair coverage')
            report['records'].append(row); publish()
        report['status'] = 'PASS_AFFECTED_FRAME_ONLY' if all(r['status']=='PASS_AFFECTED_FRAME_ONLY' for r in report['records']) else 'FAIL'
    except Exception as error:
        report['status'] = 'ERROR'; report['errors'].append(repr(error))
    finally:
        report['geometry_sha256_before'] = fingerprint
        report['geometry_sha256_after'] = _document_fingerprint(doc) if doc is not None else None
        report['document_unchanged'] = doc is not None and fingerprint == report['geometry_sha256_after']
        report['native_sha256_after'] = _sha(freeze['native_path'])
        report['native_unchanged'] = report['native_sha256_after'] == freeze['native_sha256']
        try:
            validate_freeze()
            if _sha(IDENTITY) != report['identity_sha256']:
                raise RuntimeError('Identity proof changed during partition')
        except Exception as error:
            report['errors'].append(repr(error))
        if report['errors'] or not report['document_unchanged'] or not report['native_unchanged']:
            report['status'] = 'FAIL_INPUT_OR_MUTATION'
        publish()
        if doc is not None:
            App.closeDocument(doc.Name)
    return report


def collect(partitions):
    """Whole finite-sample PASS needs r08 full PASS + identity + affected union."""
    freeze, proof = _identity_gate(); plan = manifest()
    paths = [OUT/('part_'+str(i)+'.json') for i in range(partitions)]
    indexed_reports = [(i, json.loads(p.read_text())) for i,p in enumerate(paths) if p.exists()]
    reports = [p for i,p in indexed_reports]
    completed = [r['sample_id'] for p in reports for r in p['records']]
    expected = [s['sample_id'] for s in plan['states']]
    baseline_path = ROOT/'reports/verification/r08_motion_partitions/full_summary.json'
    baseline = json.loads(baseline_path.read_text())
    from verify_motion_package_r08 import FREEZE as OLD_FREEZE
    old_freeze = json.loads(OLD_FREEZE.read_text())
    required_coherence = {'native_sha256','geometry_sha256_before','config_sha256','manifest_sha256','freeze_sha256','dependencies','current_freeze'}
    baseline_pass = (baseline.get('status') == 'PASS' and baseline.get('samples_expected') == 985 and
                     baseline.get('records_found') == 985 and not baseline.get('missing_sample_ids') and
                     not baseline.get('duplicate_sample_ids') and not baseline.get('failed_records') and
                     not baseline.get('baseline_overlaps') and
                     set(baseline.get('hash_coherence', {})) >= required_coherence and
                     all(baseline['hash_coherence'][k] is True for k in required_coherence) and
                     baseline.get('geometry_sha256_before') == proof['r08_campaign_geometry_sha256'] and
                     baseline.get('config_sha256') == old_freeze['config_sha256'] and
                     len(baseline.get('partition_statuses', {})) == baseline.get('partitions_expected') and
                     all(v == 'PASS' for v in baseline['partition_statuses'].values()) and
                     baseline.get('manifest', {}).get('sha256') == plan['r08_manifest_sha256'] and
                     baseline.get('native_sha256') == old_freeze['native_sha256'] and
                     baseline.get('freeze_sha256') == _sha(OLD_FREEZE))
    expected_inputs = {s['sample_id']: s['input_sha256'] for s in plan['states']}
    coherence = all(p.get('freeze_sha256')==_sha(FREEZE) and p.get('identity_sha256')==_sha(IDENTITY) and
                    p.get('manifest_sha256')==plan['sha256'] and p.get('native_sha256')==freeze['native_sha256'] and
                    p.get('dependency_sha256')==freeze['dependency_sha256'] and p.get('partitions')==partitions and
                    p.get('partition')==i and p.get('expected_sample_ids')==[s['sample_id'] for s in plan['states'][i::partitions]]
                    for i,p in indexed_reports)
    records_ok = all(r['status']=='PASS_AFFECTED_FRAME_ONLY' and r['pair_coverage']==472 and
                     r['input_sha256']==expected_inputs.get(r['sample_id']) and
                     _digest({k:r['input'][k] for k in ('theta','leg_angles','wheel_angle')})==r['input_sha256']
                     for p in reports for r in p['records'])
    complete = len(reports)==partitions and len(completed)==len(expected) and set(completed)==set(expected) and len(completed)==len(set(completed))
    affected_pass = complete and coherence and records_ok and all(p['status']=='PASS_AFFECTED_FRAME_ONLY' and p['document_unchanged'] and p['native_unchanged'] and not p['overlaps'] and not p['errors'] for p in reports)
    result = {'status': 'PASS' if baseline_pass and affected_pass else 'INCOMPLETE_OR_FAIL',
              'scope': 'Finite-sample collision reuse only; primary MCP/S9/AX and engineering gates remain separate',
              'r08_full_985_pass': baseline_pass, 'identity_472_pass': proof['status']=='PASS_IDENTITY_ONLY',
              'affected_frame_1346_pass': affected_pass, 'hash_coherence': coherence,
              'expected_sample_ids': expected, 'completed_sample_ids': completed,
              'missing_sample_ids': sorted(set(expected)-set(completed)),
              'duplicate_sample_ids': sorted(n for n in set(completed) if completed.count(n)>1),
              'r08_summary_sha256': _sha(baseline_path), 'identity_sha256': _sha(IDENTITY),
              'freeze_sha256': _sha(FREEZE), 'manifest_sha256': plan['sha256'],
              'continuous_clearance': False, 'loaded_equilibrium': False, 'fabrication_release': False}
    validate_freeze(); _write(OUT/'summary.json', result)
    return result
