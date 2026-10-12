"""Read-only r10 changed-pair verification, requiring explicit lead SHA freeze.

Preparation has no side effects. A final finite-sample PASS requires the frozen
r08 campaign, strict466-instance identity, and all9996 affected pairs at1346
exact inputs. No CAD save, pose assignment, source mutation or automatic launch.
"""
import hashlib
import json
import math
from pathlib import Path
import time

import verify_frame_revision_r09 as base

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/verification/r10_changed_partitions'
FREEZE = OUT/'freeze.json'
IDENTITY = OUT/'identity.json'
WHOLE_Y = OUT/'whole_cycle_y.json'
RETIRED = base.RETIRED
CHANGED_EXISTING = ('LumbarIntegrated1','Torso_fore','Torso_hind',
                    'Link1_L4_1','Link1_L4__1','Link2_L4_1','Link2_L4__1')
NEW = tuple('CentralE'+str(i)+'_'+component for i in (1,2)
            for component in ('Pin','Bearing0','Bearing1','Washer0','Washer1','Retainer0','Retainer1'))
AFFECTED = tuple(sorted(CHANGED_EXISTING+NEW))
VOLUME_TOL = 1e-5
BBOX_TOL = 1e-6
EXTRA_DEPENDENCIES = ('verify_changed_revision_r10.py','verify_frame_revision_r09.py',
                      'spine_frame_r09.py','spine_frame_r10.py','torso_attachment_r10.py',
                      'spine_bar_profile_r10.py','central_joint_hardware_r10.py',
                      'adaptive_volume_r07.py','occt_adaptive_volume_r07.cpp')
_sha = base._sha
_digest = base._digest
_write = base._write
_matrix = base._matrix
_bbox = base._bbox


def _native_state_guard(doc):
    """Reject cached solids whose native Body/features report Invalid or Error.

    Inspection is read-only: no recompute can hide a persisted feature failure.
    Include sketches and other group members, even unused historical Bodies.
    """
    bodies = [o for o in doc.Objects if o.TypeId == 'PartDesign::Body']
    pending = list(bodies); checked = {}; failures = []
    while pending:
        obj = pending.pop()
        if obj.Name in checked:
            continue
        states = [str(value) for value in obj.State]
        checked[obj.Name] = states
        if any('invalid' in value.lower() or 'error' in value.lower() for value in states):
            failures.append({'name':obj.Name,'type':obj.TypeId,'state':states})
        pending.extend(getattr(obj, 'Group', []))
    if not bodies:
        raise RuntimeError('Native state guard found no PartDesign Bodies')
    if failures:
        raise RuntimeError('Invalid/Error native Body feature state: '+json.dumps(failures,sort_keys=True))
    return {'status':'PASS_NATIVE_STATE_ONLY','body_count':len(bodies),
            'body_and_member_count':len(checked),'invalid_or_error_count':0}


def manifest():
    """Pure exact985+361 enumeration; never import FreeCAD or launch a job."""
    return base.manifest()


def affected_pairs(names):
    """Each unordered changed/other or changed/changed pair occurs once."""
    names = set(names)
    if len(names) != 487 or not set(AFFECTED) <= names:
        raise RuntimeError('Expected487 physical IDs including exact21 affected IDs')
    pairs = sorted({tuple(sorted((a,b))) for a in AFFECTED for b in names if b != a})
    if len(pairs) != 9996:
        raise RuntimeError('Expected9996 unique affected pairs')
    return pairs


def _compatible_config(config):
    result = dict(config)
    for key in ('revision','limits'):
        if key in result and not isinstance(result[key],str):
            raise RuntimeError('Expected descriptive config string: '+key)
        result.pop(key,None)
    for key in ('lumbar_frame_r09','central_attachment_r10','plate_profile_r10','bar_profile_r10'):
        result.pop(key,None)
    return result


def capture_freeze(native, expected_sha256):
    """Explicit lead operation; native must already have its final disk SHA."""
    from verify_motion_package_r08 import validate_freeze, DEPENDENCIES, FREEZE as OLD_FREEZE
    validate_freeze()
    native = Path(native).resolve()
    if _sha(native) != expected_sha256:
        raise RuntimeError('Lead-supplied r10 native SHA does not match')
    plan = manifest()
    record = {'revision':'r10','native_path':str(native),'native_sha256':expected_sha256,
              'r08_freeze_sha256':_sha(OLD_FREEZE),
              'config_r08_sha256':_sha(ROOT/'parameters/assembly_r08.json'),
              'config_r10_sha256':_sha(ROOT/'parameters/assembly_r10.json'),
              'dependency_sha256':{n:_sha(ROOT/'src'/n) for n in sorted(set(DEPENDENCIES+EXTRA_DEPENDENCIES))},
              'manifest_sha256':plan['sha256'],
              'original_full_manifest_file_sha256':plan['r08_full_manifest_file_sha256'],
              'baseline_evidence_sha256':{str(p.relative_to(ROOT)):_sha(p) for p in sorted(
                  list((ROOT/'reports/verification/r08_motion_partitions').glob('*_part_*.json')) +
                  [ROOT/'reports/verification/r08_motion_partitions'/n for n in
                   ('full_summary.json','coarse_summary.json','cage_spine_361.json')])},
              'baseline_cage_driver_sha256':_sha(ROOT/'reports/tmp/motion_package_r08/cage_partition_driver.py'),
              'expected_instances':487,'expected_used_sources':107,'unchanged_count':466,
              'changed_existing':CHANGED_EXISTING,'new_instances':NEW}
    _write(FREEZE,record)
    return record


def validate_freeze():
    from verify_motion_package_r08 import validate_freeze as old_validate, FREEZE as OLD_FREEZE
    old_validate()
    record = json.loads(FREEZE.read_text())
    tests = [_sha(record['native_path']) == record['native_sha256'],
             _sha(OLD_FREEZE) == record['r08_freeze_sha256'],
             _sha(ROOT/'parameters/assembly_r08.json') == record['config_r08_sha256'],
             _sha(ROOT/'parameters/assembly_r10.json') == record['config_r10_sha256'],
             manifest()['sha256'] == record['manifest_sha256'],
             _sha(ROOT/'reports/verification/r08_motion_partitions/full_manifest.json') == record['original_full_manifest_file_sha256']]
    tests.append(_sha(ROOT/'reports/tmp/motion_package_r08/cage_partition_driver.py') == record['baseline_cage_driver_sha256'])
    tests.extend(_sha(ROOT/n)==h for n,h in record['baseline_evidence_sha256'].items())
    if not all(tests) or any(_sha(ROOT/'src'/n) != h for n,h in record['dependency_sha256'].items()):
        raise RuntimeError('Frozen native/config/manifest/helper input changed')
    return record


def prove_identity():
    """Strict r08→r10 source AND placed geometry proof for all466 unaffected IDs."""
    import FreeCAD as App
    from robot_pose_r03 import _parameters
    from verify_motion_package_r08 import _native_fingerprint
    freeze = validate_freeze()
    native8 = ROOT/'cad/flexor_r08_robot.FCStd'
    files_before = {str(p):_sha(p) for p in (native8,Path(freeze['native_path']))}
    docs = []; fingerprints = []
    record = {'status':'ERROR','freeze_sha256':_sha(FREEZE),'retired_instances':RETIRED,
              'changed_existing':CHANGED_EXISTING,'new_instances':NEW,
              'records':[],'errors':[],'continuous_clearance':False}
    try:
        old = App.openDocument(str(native8));docs.append(old)
        new = App.openDocument(freeze['native_path']);docs.append(new)
        fingerprints = [base._document_fingerprint(d) for d in docs]
        record['native_state_guard'] = {'r08':_native_state_guard(old),'r10':_native_state_guard(new)}
        a = {o.Name:o for o in old.Objects if o.TypeId=='App::Link'}
        b = {o.Name:o for o in new.Objects if o.TypeId=='App::Link'}
        if len(a)!=486 or len(b)!=487 or set(a)-set(b)!=set(RETIRED) or set(b)-set(a)!=set(NEW):
            raise RuntimeError('Exact physical identity migration differs from contract')
        used = {o.LinkedObject.Name for o in b.values()}
        library = {o.Name for o in new.getObject('PartsLibrary').Group}
        if len(used)!=107 or not used<=library:
            raise RuntimeError('Expected107 used source definitions, all included in PartsLibrary')
        record['used_source_count'] = len(used)
        record['library_definition_count'] = len(library)
        record['unused_library_sources'] = sorted(library-used)
        unchanged = sorted(set(b)-set(AFFECTED))
        if len(unchanged)!=466:
            raise RuntimeError('Expected466 unchanged r08→r10 physical instances')
        if _parameters(old)!=_parameters(new):
            raise RuntimeError('Frozen mechanism/branch/native parameter values changed')
        mm8 = json.loads(old.PoseController.MotionMap)
        mm10 = json.loads(new.PoseController.MotionMap)
        if {n:m for n,m in mm8.items() if n not in RETIRED} != {n:m for n,m in mm10.items() if n not in NEW}:
            raise RuntimeError('Existing473 MotionMap descriptors changed')
        moving_new = {n for n in NEW if '_Bearing' not in n}
        if set(mm10)-set(mm8)!=moving_new:
            raise RuntimeError('Unexpected new motion descriptors or missing central moving hardware')
        for name in moving_new:
            m = mm10[name]
            if m['kind']!='torso_r04_rigid' or m['torso']!=('hind' if name.startswith('CentralE1_') else 'fore') or 'local_placement_json' not in m:
                raise RuntimeError(name+': central hardware must follow the existing E torso output')
        for key in ('SpinePhaseRad','LegAnglesR03','WheelAngleR07'):
            if getattr(old.PoseController,key,None)!=getattr(new.PoseController,key,None):
                raise RuntimeError('Native neutral pose changed: '+key)
        for doc in docs:
            if abs(float(doc.PoseController.SpinePhaseRad))>1e-12:
                raise RuntimeError('Identity input must be neutral')
        key = 'PrescribedMotionConfigR07'
        va,vb = getattr(old.PoseController,key,None),getattr(new.PoseController,key,None)
        if (va is None)!=(vb is None) or (va is not None and _compatible_config(json.loads(va))!=_compatible_config(json.loads(vb))):
            raise RuntimeError('Native leg/wheel configuration changed')
        cfg8 = json.loads((ROOT/'parameters/assembly_r08.json').read_text())
        cfg10 = json.loads((ROOT/'parameters/assembly_r10.json').read_text())
        if _compatible_config(cfg8)!=_compatible_config(cfg10):
            raise RuntimeError('Legacy assembly/leg/kinematic config changed')
        source_cache = {}
        for name in sorted(set(a)&set(b)):
            if _matrix(a[name].LinkPlacement)!=_matrix(b[name].LinkPlacement):
                raise RuntimeError(name+': legacy neutral placement changed')
        for name in unchanged:
            x,y = a[name],b[name]
            if x.LinkedObject.Name!=y.LinkedObject.Name or x.LinkedObject.PartNumber!=y.LinkedObject.PartNumber:
                raise RuntimeError(name+': unchanged source identity/part number differs')
            if _matrix(x.LinkedObject.Placement)!=_matrix(y.LinkedObject.Placement) or base._numeric_properties(x.LinkedObject)!=base._numeric_properties(y.LinkedObject):
                raise RuntimeError(name+': unchanged source frame/numerical properties differ')
            key = (x.LinkedObject.Name,y.LinkedObject.Name)
            if key not in source_cache:
                source_cache[key] = base._strict_shape_identity(x.LinkedObject.Shape,y.LinkedObject.Shape,name+' source')
            record['records'].append({'instance':name,'source':x.LinkedObject.Name,'placement_exact':True,
                                      'source_geometry':source_cache[key],
                                      'placed_geometry':base._strict_shape_identity(x.Shape,y.Shape,name+' placed')})
        source_names = {'LumbarIntegrated1':'FRM_LUMBAR_MONOLITHIC_CAGE_r09',
                        'Torso_fore':'TORSO_FORE_TRANSVERSE_FRAME_r06','Torso_hind':'TORSO_HIND_TRANSVERSE_FRAME_r06'}
        for name in CHANGED_EXISTING:
            obj = b[name];expected_name = source_names.get(name,'SPN_r02_L4')
            expected_pn = ('FRM_LUMBAR_MONOLITHIC_CAGE_r10' if name=='LumbarIntegrated1' else
                           expected_name+'_r10' if name.startswith('Torso_') else 'SPN_LONG_BC_RELIEVED_r10')
            if (obj.LinkedObject.Name!=expected_name or obj.LinkedObject.Revision!='r10' or
                    obj.LinkedObject.PartNumber!=expected_pn or obj.LinkedObject.TypeId!='PartDesign::Body'):
                raise RuntimeError(name+': unexpected changed native source/revision/part number')
            if _matrix(a[name].LinkedObject.Placement)!=_matrix(obj.LinkedObject.Placement):
                raise RuntimeError(name+': changed source-local frame moved')
            if any(not o.FullyConstrained for o in obj.LinkedObject.Group if o.TypeId=='Sketcher::SketchObject'):
                raise RuntimeError(name+': changed native profile is not fully constrained')
        for obj in b.values():
            if not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
                raise RuntimeError(obj.Name+': invalid or nonsingle native physical solid')
        pairs = affected_pairs(b)
        record.update({'status':'PASS_IDENTITY_ONLY','unchanged_count':466,'unchanged_instances':unchanged,
                       'all_instance_names':sorted(b),'affected_instances':AFFECTED,'affected_pair_count':len(pairs),
                       'affected_pair_sha256':_digest(pairs),'used_sources':sorted(used),
                       'native_r08_sha256':files_before[str(native8)],'native_r10_sha256':freeze['native_sha256'],
                       'r08_campaign_geometry_sha256':_native_fingerprint(old),
                       'geometry_sha256_r08':fingerprints[0],'geometry_sha256_r10':fingerprints[1],
                       'existing_motion_and_parameters_exact':True})
    except Exception as error:
        record['errors'].append(repr(error))
    finally:
        record['native_files_unchanged'] = all(_sha(p)==h for p,h in files_before.items())
        record['documents_unchanged'] = bool(fingerprints) and fingerprints==[base._document_fingerprint(d) for d in docs]
        try:
            validate_freeze()
        except Exception as error:
            record['errors'].append(repr(error))
        if record['errors'] or not record['native_files_unchanged'] or not record['documents_unchanged']:
            record['status']='FAIL_IDENTITY'
        _write(IDENTITY,record)
        for doc in docs:
            App.closeDocument(doc.Name)
    return record


def _identity_gate():
    freeze = validate_freeze();proof = json.loads(IDENTITY.read_text())
    if (proof['status']!='PASS_IDENTITY_ONLY' or proof['unchanged_count']!=466 or
            proof['freeze_sha256']!=_sha(FREEZE) or proof['native_r10_sha256']!=freeze['native_sha256'] or
            len(proof['all_instance_names'])!=487 or proof['affected_pair_count']!=9996 or
            proof['native_files_unchanged'] is not True or proof['documents_unchanged'] is not True):
        raise RuntimeError('Coherent strict466-instance identity proof required')
    return freeze,proof


def _overlap(a,b):
    return all(min(a[i+1],b[i+1])-max(a[i],b[i])>BBOX_TOL for i in (0,2,4))


def _transformed_box(box, placement):
    """Analytic corner-extrema of a box under an exact rigid placement matrix."""
    a = _matrix(placement);result = []
    for row in range(3):
        low = high = a[4*row+3]
        for axis in range(3):
            q = a[4*row+axis]
            u,v = q*box[2*axis],q*box[2*axis+1]
            low += min(u,v);high += max(u,v)
        result.extend((low-BBOX_TOL,high+BBOX_TOL))
    if not all(math.isfinite(v) for v in result):
        raise RuntimeError('Nonfinite transformed bound')
    return tuple(result)


def prepare_whole_cycle_y():
    """Read-only exact1346-descriptor prepass; no spring/cable solid generation.

    Unions are finite-ledger bounds, never a continuous-motion claim. Rigid
    sagittal motion retains a small transverse interval; all intervals are
    calculated from actual native bounds and actual matrices without rounding.
    Dynamic intervals use frozen generator containment, or disable exclusion.
    """
    import FreeCAD as App
    from leg_motion_r07 import descriptor
    freeze,proof = _identity_gate();plan = manifest();doc = None;fingerprint = None
    report = {'status':'RUNNING','freeze_sha256':_sha(FREEZE),'identity_sha256':_sha(IDENTITY),
              'manifest_sha256':plan['sha256'],'states_expected':1346,'states_completed':0,
              'input_sha256_by_sample_id':{},'y_bounds_mm':{},'errors':[],
              'basis':'Finite1346 input union of native rigid AABBs under exact placements and generator-proven dynamic bounds; no rounding; bbox expanded1e-6',
              'continuous_clearance':False}
    try:
        doc = App.openDocument(freeze['native_path']);fingerprint = base._document_fingerprint(doc)
        report['native_state_guard'] = _native_state_guard(doc)
        if fingerprint!=proof['geometry_sha256_r10']:
            raise RuntimeError('Loaded r10 document differs from identity proof')
        names = proof['all_instance_names'];boxes = {n:_bbox(doc.getObject(n).Shape) for n in names}
        initial = {n:doc.getObject(n).LinkPlacement for n in names}
        bounds = {n:[math.inf,-math.inf] for n in names};unbounded = set()
        config = json.loads((ROOT/'parameters/assembly_r10.json').read_text())
        for state in plan['states']:
            pp = descriptor(doc,state['theta'],state['leg_angles'],state['wheel_angle'],config)
            if set(pp['placements'])!=set(names) or pp['guide_warnings']:
                raise RuntimeError('Descriptor coverage/guide guard failed')
            if _matrix(pp['placements']['LumbarIntegrated1'])!=_matrix(initial['LumbarIntegrated1']):
                raise RuntimeError('Fixed frame moved')
            for name in names:
                if name in unbounded:
                    continue
                placement = pp['placements'][name];request = pp['shape_requests'].get(name)
                if request:
                    world_boxes,basis = base._dynamic_boxes(request,placement)
                    if world_boxes is None:
                        unbounded.add(name);continue
                else:
                    world_boxes = [_transformed_box(boxes[name],placement.multiply(initial[name].inverse()))]
                bounds[name][0] = min(bounds[name][0],*(b[2]-BBOX_TOL for b in world_boxes))
                bounds[name][1] = max(bounds[name][1],*(b[3]+BBOX_TOL for b in world_boxes))
            report['input_sha256_by_sample_id'][state['sample_id']] = state['input_sha256']
            report['states_completed'] += 1
        report['y_bounds_mm'] = {n:None if n in unbounded else bounds[n] for n in names}
        pairs = affected_pairs(names)
        excluded = [i for i,(a,b) in enumerate(pairs) if a not in unbounded and b not in unbounded and
                    (bounds[a][1]<bounds[b][0] or bounds[b][1]<bounds[a][0])]
        report.update({'status':'PASS_BOUNDS_ONLY','pairs':pairs,'pair_sha256':_digest(pairs),
                       'whole_cycle_disjoint_pair_indices':excluded,'whole_cycle_disjoint_pair_count':len(excluded),
                       'actual_pair_candidates_per_pose':len(pairs)-len(excluded)})
    except Exception as error:
        report['status']='ERROR';report['errors'].append(repr(error))
    finally:
        report['document_unchanged'] = doc is not None and fingerprint==base._document_fingerprint(doc)
        report['native_unchanged'] = _sha(freeze['native_path'])==freeze['native_sha256']
        try:
            validate_freeze()
        except Exception as error:
            report['errors'].append(repr(error))
        if report['errors'] or not report['document_unchanged'] or not report['native_unchanged']:
            report['status']='FAIL_BOUNDS_OR_MUTATION'
        _write(WHOLE_Y,report)
        if doc is not None:
            App.closeDocument(doc.Name)
    return report


def _bounds_gate():
    freeze,proof = _identity_gate();bounds = json.loads(WHOLE_Y.read_text());plan = manifest()
    if (bounds['status']!='PASS_BOUNDS_ONLY' or bounds['states_completed']!=1346 or
            bounds['freeze_sha256']!=_sha(FREEZE) or bounds['identity_sha256']!=_sha(IDENTITY) or
            bounds['manifest_sha256']!=plan['sha256'] or bounds['pair_sha256']!=proof['affected_pair_sha256'] or
            _digest(bounds['pairs'])!=proof['affected_pair_sha256'] or
            bounds['document_unchanged'] is not True or bounds['native_unchanged'] is not True or
            bounds['input_sha256_by_sample_id']!={s['sample_id']:s['input_sha256'] for s in plan['states']}):
        raise RuntimeError('Coherent complete conservative finite-cycle bound ledger required')
    if set(bounds['y_bounds_mm'])!=set(proof['all_instance_names']):
        raise RuntimeError('Whole-cycle bound instance coverage differs')
    for interval in bounds['y_bounds_mm'].values():
        if interval is not None and (len(interval)!=2 or not all(math.isfinite(v) for v in interval) or interval[0]>interval[1]):
            raise RuntimeError('Invalid/nonfinite whole-cycle Y interval')
    expected_excluded = []
    for i,(a,b) in enumerate(bounds['pairs']):
        ya,yb = bounds['y_bounds_mm'][a],bounds['y_bounds_mm'][b]
        if ya is not None and yb is not None and (ya[1]<yb[0] or yb[1]<ya[0]):
            expected_excluded.append(i)
    if expected_excluded!=bounds['whole_cycle_disjoint_pair_indices']:
        raise RuntimeError('Whole-cycle exclusion ledger differs from recorded conservative intervals')
    return freeze,proof,bounds


def _decision_masks_complete(masks, pair_count=9996):
    """Exact compressed per-pair ledger; categories must be disjoint/exhaustive."""
    if set(masks)!={'whole_cycle_y','pose_bbox','actual_boolean'}:
        return False
    values = [int(masks[k],16) for k in ('whole_cycle_y','pose_bbox','actual_boolean')]
    expected = (1<<pair_count)-1
    return (all(v>=0 and not v&~expected for v in values) and
            not values[0]&values[1] and not values[0]&values[2] and not values[1]&values[2] and
            values[0]|values[1]|values[2]==expected)


def run_partition(partition, partitions):
    """Explicit read-only CLI; call only after native freeze/identity/Y prepass."""
    import FreeCAD as App
    from leg_motion_r07 import descriptor,regenerate_sources
    if not isinstance(partitions,int) or not 1<=partitions<=24 or not 0<=partition<partitions:
        raise ValueError('Expected partition0..n-1,n1..24; lead launcher max6 concurrent')
    freeze,proof,bounds = _bounds_gate();plan = manifest();states = plan['states'][partition::partitions]
    pairs = [tuple(p) for p in bounds['pairs']]
    excluded = set(bounds['whole_cycle_disjoint_pair_indices'])
    whole_mask = sum(1<<i for i in excluded)
    report = {'status':'RUNNING','partition':partition,'partitions':partitions,
              'freeze_sha256':_sha(FREEZE),'identity_sha256':_sha(IDENTITY),'whole_y_sha256':_sha(WHOLE_Y),
              'manifest_sha256':plan['sha256'],'native_sha256':freeze['native_sha256'],
              'dependency_sha256':freeze['dependency_sha256'],'pair_sha256':_digest(pairs),
              'pair_count':9996,'whole_cycle_y_disjoint_pairs':len(excluded),
              'affected_instances':AFFECTED,'expected_sample_ids':[s['sample_id'] for s in states],
              'records':[],'errors':[],'overlaps':[],'occ_checks':0,'cached_pair_checks':0,
              'dynamic_sources_regenerated':0,'volume_tolerance_mm3':VOLUME_TOL,'bbox_tolerance_mm':BBOX_TOL,
              'exceptions':[],'continuous_clearance':False,'loaded_equilibrium':False,'fabrication_release':False}
    start = time.monotonic();doc = None;fingerprint = None;source_cache = {};pair_cache = {}
    output = OUT/('part_'+str(partition)+'.json')
    def publish():
        report['samples_completed'] = len(report['records'])
        report['elapsed_seconds'] = time.monotonic()-start
        _write(output,report)
    try:
        doc = App.openDocument(freeze['native_path']);fingerprint = base._document_fingerprint(doc)
        report['native_state_guard'] = _native_state_guard(doc)
        if fingerprint!=proof['geometry_sha256_r10']:
            raise RuntimeError('Loaded native differs from identity proof')
        names = proof['all_instance_names'];initial = {n:doc.getObject(n).LinkPlacement for n in names}
        native_boxes = {n:_bbox(doc.getObject(n).Shape) for n in names}
        native_signature = {}
        for name in names:
            obj = doc.getObject(name)
            if not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
                raise RuntimeError(name+': native source invalid/non-single solid')
            native_signature[name] = base._brep_sha(obj.Shape)
        config = json.loads((ROOT/'parameters/assembly_r10.json').read_text())
        for state in states:
            pp = descriptor(doc,state['theta'],state['leg_angles'],state['wheel_angle'],config)
            if set(pp['placements'])!=set(names) or _matrix(pp['placements']['LumbarIntegrated1'])!=_matrix(initial['LumbarIntegrated1']):
                raise RuntimeError('Descriptor identity coverage/fixed frame guard failed')
            world_boxes = {};signatures = {};shapes = {};masks = {'whole_cycle_y':whole_mask,'pose_bbox':0,'actual_boolean':0}
            for name in names:
                request = pp['shape_requests'].get(name);placement = pp['placements'][name]
                signatures[name] = (_digest(request) if request else native_signature[name],_matrix(placement))
                if request:
                    world_boxes[name] = base._dynamic_boxes(request,placement)[0]
                else:
                    world_boxes[name] = [_transformed_box(native_boxes[name],placement.multiply(initial[name].inverse()))]
            def actual_shape(name):
                if name not in shapes:
                    placement = pp['placements'][name];request = pp['shape_requests'].get(name)
                    if request:
                        shape = regenerate_sources(dict(pp,shape_requests={name:request}),source_cache)[name]
                        shape.Placement = placement.multiply(shape.Placement)
                        report['dynamic_sources_regenerated'] += 1
                    else:
                        shape = doc.getObject(name).Shape.copy()
                        shape.Placement = placement.multiply(initial[name].inverse()).multiply(shape.Placement)
                    # Rigid transforms preserve the already-validated native solid.
                    # regenerate_sources validates every generated local solid itself.
                    shapes[name] = shape
                return shapes[name]
            row = {'sample_id':state['sample_id'],'input_sha256':state['input_sha256'],'input':state,
                   'status':'PASS_CHANGED_PAIRS_ONLY','guide_warnings':pp['guide_warnings'],
                   'narrowphase':[],'pair_count':9996}
            if pp['guide_warnings']:
                row['status']='FAIL_GUIDE_TRAVEL'
            for i,(a,b) in enumerate(pairs):
                if i in excluded:
                    continue
                ba,bb = world_boxes[a],world_boxes[b]
                if ba is not None and bb is not None and all(not _overlap(x,y) for x in ba for y in bb):
                    masks['pose_bbox'] |= 1<<i;continue
                sa,sb = actual_shape(a),actual_shape(b)
                if not _overlap(_bbox(sa),_bbox(sb)):
                    masks['pose_bbox'] |= 1<<i;continue
                key = (a,b,signatures[a],signatures[b])
                if key in pair_cache:
                    volume = pair_cache[key];report['cached_pair_checks'] += 1
                else:
                    common = sa.common(sb);volume = float(common.Volume)
                    if not math.isfinite(volume) or (not common.isNull() and not common.isValid()):
                        raise RuntimeError('Invalid/nonfinite actual Boolean: '+a+' / '+b)
                    pair_cache[key] = volume;report['occ_checks'] += 1
                masks['actual_boolean'] |= 1<<i
                row['narrowphase'].append({'pair_index':i,'a':a,'b':b,'intersection_mm3':volume,'actual_solid':True})
                if volume>VOLUME_TOL:
                    row['status']='FAIL_COLLISION'
                    report['overlaps'].append({'a':a,'b':b,'sample_id':state['sample_id'],'intersection_mm3':volume})
            row['pair_decision_masks'] = {k:hex(v) for k,v in masks.items()}
            if not _decision_masks_complete(row['pair_decision_masks']):
                raise RuntimeError('Affected pair decision ledger incomplete/overlapping')
            report['records'].append(row);publish()
        report['status'] = 'PASS_CHANGED_PAIRS_ONLY' if len(report['records'])==len(states) and all(r['status']=='PASS_CHANGED_PAIRS_ONLY' for r in report['records']) else 'FAIL'
    except Exception as error:
        report['status']='ERROR';report['errors'].append(repr(error))
    finally:
        report['geometry_sha256_before'] = fingerprint
        report['geometry_sha256_after'] = base._document_fingerprint(doc) if doc is not None else None
        report['document_unchanged'] = doc is not None and fingerprint==report['geometry_sha256_after']
        report['native_sha256_after'] = _sha(freeze['native_path'])
        report['native_unchanged'] = report['native_sha256_after']==freeze['native_sha256']
        try:
            validate_freeze()
            if _sha(IDENTITY)!=report['identity_sha256'] or _sha(WHOLE_Y)!=report['whole_y_sha256']:
                raise RuntimeError('Proof/bound ledger changed during partition')
        except Exception as error:
            report['errors'].append(repr(error))
        if report['errors'] or not report['document_unchanged'] or not report['native_unchanged']:
            report['status']='FAIL_INPUT_OR_MUTATION'
        publish()
        if doc is not None:
            App.closeDocument(doc.Name)
    return report


def _baseline_gate(proof):
    """Read and verify original summary/partition guards, never recollect r08."""
    from verify_motion_package_r08 import FREEZE as OLD_FREEZE
    old = json.loads(OLD_FREEZE.read_text());folder = ROOT/'reports/verification/r08_motion_partitions'
    hashes = {};ok = True
    for stage,count,summary_name in (('full',985,'full_summary.json'),('coarse',105,'coarse_summary.json'),
                                     ('cage_spine',361,'cage_spine_361.json')):
        path = folder/summary_name;summary = json.loads(path.read_text());hashes[path.name] = _sha(path)
        ok = ok and (summary.get('status')=='PASS' and summary.get('samples_expected')==count and
                     summary.get('records_found',summary.get('samples_completed'))==count and
                     summary.get('native_sha256')==old['native_sha256'] and
                     summary.get('config_sha256')==old['config_sha256'] and
                     summary.get('freeze_sha256')==_sha(OLD_FREEZE) and
                     summary.get('geometry_sha256_before')==proof['r08_campaign_geometry_sha256'] and
                     bool(summary.get('hash_coherence')) and all(v is True for v in summary['hash_coherence'].values()))
        for key in ('missing_sample_ids','extra_sample_ids','duplicate_sample_ids','failed_records','overlaps','errors','baseline_overlaps'):
            ok = ok and not summary.get(key)
        statuses = summary.get('partition_statuses',{});completed = [];input_rows = []
        ok = ok and bool(statuses) and all(v=='PASS' for v in statuses.values())
        for index,status in statuses.items():
            partition_path = folder/(stage+'_part_'+str(index)+'.json')
            partition = json.loads(partition_path.read_text());hashes[partition_path.name] = _sha(partition_path)
            ok = ok and (partition.get('status')=='PASS' and partition.get('document_unchanged') is True and
                         partition.get('native_file_unchanged') is True and partition.get('native_sha256')==old['native_sha256'] and
                         partition.get('config_sha256')==old['config_sha256'] and partition.get('freeze_sha256')==_sha(OLD_FREEZE) and
                         partition.get('dependency_sha256')==old['dependency_sha256'] and
                         partition.get('geometry_sha256_before')==proof['r08_campaign_geometry_sha256'] and
                         not partition.get('errors') and not partition.get('overlaps') and not partition.get('baseline_overlaps'))
            if stage=='cage_spine':
                driver = ROOT/'reports/tmp/motion_package_r08/cage_partition_driver.py'
                ok = ok and partition.get('driver_unchanged') is True and partition.get('driver_sha256')==_sha(driver)
            for row in partition.get('records',[]):
                ok = ok and row.get('status')=='PASS'
                completed.append(row['sample_id']);input_rows.append(row)
        expected = ({'cage_'+str(i).zfill(3) for i in range(361)} if stage=='cage_spine' else
                    {s['sample_id'] for s in summary.get('manifest',{}).get('states',[])})
        ok = ok and len(completed)==count and len(set(completed))==count and set(completed)==expected
        if stage=='full':
            plan = manifest()
            ok = ok and summary.get('manifest',{}).get('sha256')==plan['r08_manifest_sha256']
            expected_inputs = {s['sample_id']:s for s in plan['states'][:985]}
            ok = ok and all(r['input_sha256']==expected_inputs[r['sample_id']]['input_sha256'] and
                            _digest(r['input'])==_digest(expected_inputs[r['sample_id']]) for r in input_rows)
    return bool(ok),hashes


def collect(partitions):
    if not isinstance(partitions,int) or not 1<=partitions<=24:
        raise ValueError('Expected1..24 partitions')
    freeze,proof,bounds = _bounds_gate();plan = manifest()
    indexed = [(i,json.loads(p.read_text())) for i in range(partitions)
               for p in [OUT/('part_'+str(i)+'.json')] if p.exists()]
    reports = [p for i,p in indexed];records = [r for p in reports for r in p['records']]
    expected = {s['sample_id']:s for s in plan['states']};completed = [r['sample_id'] for r in records]
    coherent = all(p['partition']==i and p['partitions']==partitions and
                   p['freeze_sha256']==_sha(FREEZE) and p['identity_sha256']==_sha(IDENTITY) and
                   p['whole_y_sha256']==_sha(WHOLE_Y) and p['manifest_sha256']==plan['sha256'] and
                   p['native_sha256']==freeze['native_sha256'] and p['dependency_sha256']==freeze['dependency_sha256'] and
                   p['pair_sha256']==bounds['pair_sha256'] and p['pair_count']==9996 and
                   p['expected_sample_ids']==[s['sample_id'] for s in plan['states'][i::partitions]]
                   for i,p in indexed)
    whole_mask = sum(1<<i for i in bounds['whole_cycle_disjoint_pair_indices'])
    pair_list = bounds['pairs']
    def narrow_ledger_ok(row):
        bits = 0
        for item in row['narrowphase']:
            i = item['pair_index']
            if not 0<=i<9996 or bits&(1<<i) or [item['a'],item['b']]!=pair_list[i]:
                return False
            if item['actual_solid'] is not True or not math.isfinite(item['intersection_mm3']) or item['intersection_mm3']>VOLUME_TOL:
                return False
            bits |= 1<<i
        return (bits==int(row['pair_decision_masks']['actual_boolean'],16) and
                int(row['pair_decision_masks']['whole_cycle_y'],16)==whole_mask)
    records_ok = all(r['status']=='PASS_CHANGED_PAIRS_ONLY' and r['pair_count']==9996 and
                     r['sample_id'] in expected and _digest(r['input'])==_digest(expected[r['sample_id']]) and
                     r['input_sha256']==expected[r['sample_id']]['input_sha256'] and
                     _decision_masks_complete(r['pair_decision_masks']) and narrow_ledger_ok(r) for r in records)
    complete = (len(reports)==partitions and len(completed)==1346 and len(set(completed))==1346 and set(completed)==set(expected))
    changed_pass = complete and coherent and records_ok and all(p['status']=='PASS_CHANGED_PAIRS_ONLY' and p['document_unchanged'] and p['native_unchanged'] and not p['overlaps'] and not p['errors'] for p in reports)
    baseline_pass,baseline_hashes = _baseline_gate(proof)
    result = {'status':'PASS' if baseline_pass and changed_pass else 'INCOMPLETE_OR_FAIL',
              'scope':'Finite-sample raw collision reuse only; primary native/S9/AX and engineering gates remain separate',
              'baseline_r08_full985_coarse105_cage361_pass':baseline_pass,'strict466_identity_pass':True,
              'changed_pair1346_pass':changed_pass,'affected_pair_count':9996,'hash_coherence':coherent,
              'expected_sample_ids':list(expected),'completed_sample_ids':completed,
              'missing_sample_ids':sorted(set(expected)-set(completed)),
              'duplicate_sample_ids':sorted(n for n in set(completed) if completed.count(n)>1),
              'freeze_sha256':_sha(FREEZE),'identity_sha256':_sha(IDENTITY),'whole_y_sha256':_sha(WHOLE_Y),
              'manifest_sha256':plan['sha256'],'baseline_summary_sha256':baseline_hashes,
              'continuous_clearance':False,'loaded_equilibrium':False,'fabrication_release':False}
    validate_freeze();_write(OUT/'summary.json',result)
    return result
