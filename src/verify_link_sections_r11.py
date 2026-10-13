"""Read-only r11 preparation and bounded copied-solid screening. No auto-run.

Only prepare reads already-open documents (GUI thread). run never touches a
Document, opens/closes/saves native files, or changes source/instance geometry.
"""
import json
import math
from pathlib import Path
import verify_frame_revision_r09 as base
from verify_changed_revision_r10 import manifest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT/'cad/flexor_r11_robot.FCStd'
BASELINE = ROOT/'cad/flexor_r10_robot.FCStd'
VOLUME_TOL = 1e-5
BBOX_TOL = 1e-6


def affected_pairs(names, affected):
    """Generic unique unordered affected-pair union; count k*n-k*(k+1)/2."""
    names, affected = set(names), set(affected)
    if not affected <= names:
        raise ValueError('Affected IDs absent from physical identity set')
    pairs = sorted({tuple(sorted((a, b))) for a in affected for b in names if a != b})
    if len(pairs) != len(affected)*len(names)-len(affected)*(len(affected)+1)//2:
        raise RuntimeError('Pair enumeration incomplete')
    return pairs


def _solid(shape, name):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError(name+': invalid/null/nonsingle physical solid')
    if not math.isfinite(float(shape.Volume)) or float(shape.Volume) <= 0:
        raise RuntimeError(name+': nonfinite/nonpositive volume')
    base._bbox(shape)


def _native(doc):
    bodies = [o for o in doc.Objects if o.TypeId == 'PartDesign::Body']
    sketches = [o for o in doc.Objects if o.TypeId == 'Sketcher::SketchObject']
    members = {o.Name:o for b in bodies for o in [b]+list(b.Group)}
    bad = [n for n,o in members.items() if any(
        'invalid' in str(s).lower() or 'error' in str(s).lower() for s in o.State)]
    if not bodies or bad:
        raise RuntimeError('Native Body/member state invalid: '+str(bad))
    return {'body_count':len(bodies), 'body_member_count':len(members),
            'sketch_count':len(sketches),
            'fully_constrained_sketch_count':sum(bool(s.FullyConstrained) for s in sketches),
            'invalid_or_error_count':len(bad)}


def _capture(doc):
    import FreeCAD as App
    from robot_pose_r03 import _parameters
    ctrl = doc.PoseController
    links = {o.Name:o for o in doc.Objects if o.TypeId == 'App::Link'}
    sources = {o.LinkedObject.Name:o.LinkedObject for o in links.values()}
    result = {'native':_native(doc), 'parameters':_parameters(doc),
              'motion':json.loads(ctrl.MotionMap), 'instances':{}, 'sources':{},
              'controller':{k:getattr(ctrl,k,None) for k in
                            ('SpinePhaseRad','LegAnglesR03','WheelAngleR07')},
              'motion_config':json.loads(ctrl.PrescribedMotionConfigR07)}
    for name, o in links.items():
        result['instances'][name] = {'source':o.LinkedObject.Name,
            'placement':App.Placement(o.LinkPlacement), 'shape':o.Shape.copy()}
    for name, o in sources.items():
        result['sources'][name] = {'shape':o.Shape.copy(), 'placement':App.Placement(o.Placement),
            'part_number':o.PartNumber, 'numeric':base._numeric_properties(o), 'type':o.TypeId,
            'sketch_count':sum(s.TypeId=='Sketcher::SketchObject' for s in getattr(o,'Group',[])),
            'unconstrained':sum(not s.FullyConstrained for s in getattr(o,'Group',[])
                                if s.TypeId=='Sketcher::SketchObject'),
            'section':json.loads(o.SectionContract) if 'SectionContract' in o.PropertiesList else None}
    return result


def _compatible(config):
    result = dict(config)
    for key in ('revision','limits','spine_link_sections_r11'):
        result.pop(key,None)
    return result


def prepare(doc, baseline_doc, states=None, canonical=CANONICAL, expected_native_sha256=None):
    """Lead GUI read-only capture; pass open neutral r11/r10 docs explicitly.

    states defaults to all 1346 exact r10 inputs. A bounded subset must contain
    unchanged manifest dictionaries. Returned object has no Document handles.
    No recompute, native-file writes, open/close, or pose assignment occurs.
    """
    import FreeCAD as App
    from leg_motion_r07 import descriptor
    from verify_motion_package_r08 import DEPENDENCIES
    from verify_changed_revision_r10 import validate_freeze, FREEZE
    baseline_freeze=validate_freeze()
    paths = [Path(doc.FileName).resolve(), Path(baseline_doc.FileName).resolve()]
    if paths != [Path(canonical).resolve(),BASELINE.resolve()]:
        raise ValueError('Expected canonical r11 and unchanged r10 baseline documents')
    files = {str(p):base._sha(p) for p in paths}
    if expected_native_sha256 is not None and files[str(paths[0])] != expected_native_sha256:
        raise RuntimeError('Lead-frozen r11 disk SHA differs')
    before = [base._document_fingerprint(d) for d in (doc,baseline_doc)]
    config = json.loads((ROOT/'parameters/assembly_r11.json').read_text())
    old_config = json.loads((ROOT/'parameters/assembly_r10.json').read_text())
    if _compatible(config) != _compatible(old_config):
        raise RuntimeError('Legacy assembly configuration changed')
    contract = json.loads(doc.PoseController.LinkSectionsR11)
    if contract['parameters'] != config['spine_link_sections_r11']:
        raise RuntimeError('Native r11 section contract differs from parameter file')
    plan = manifest(); by_id = {s['sample_id']:s for s in plan['states']}
    states = plan['states'] if states is None else list(states)
    if not states or len({s['sample_id'] for s in states}) != len(states):
        raise ValueError('Empty/duplicate requested states')
    if any(s != by_id.get(s['sample_id']) for s in states):
        raise ValueError('Requested input differs from exact r10 manifest')
    current, old = _capture(doc), _capture(baseline_doc)
    descriptors = []
    for state in states:
        pp = descriptor(doc,state['theta'],state['leg_angles'],state['wheel_angle'],config)
        descriptors.append({'placements':{n:App.Placement(p) for n,p in pp['placements'].items()},
                            'shape_requests':json.loads(json.dumps(pp['shape_requests'],allow_nan=False)),
                            'guide_warnings':pp['guide_warnings']})
    if before != [base._document_fingerprint(d) for d in (doc,baseline_doc)]:
        raise RuntimeError('Document changed during read-only capture')
    if any(base._sha(p) != h for p,h in files.items()):
        raise RuntimeError('Native disk input changed during capture')
    inputs = [ROOT/'src'/n for n in sorted(set(tuple(baseline_freeze['dependency_sha256'])+DEPENDENCIES+('verify_link_sections_r11.py',
              'spine_link_sections_r11.py','verify_frame_revision_r09.py',
              'verify_changed_revision_r10.py','adaptive_volume_r07.py',
              'occt_adaptive_volume_r07.cpp')))]+[ROOT/'parameters/assembly_r11.json',ROOT/'parameters/assembly_r10.json',FREEZE,
              ROOT/'reports/verification/r08_motion_partitions/full_manifest.json']
    return {'current':current,'baseline':old,'contract':contract,'states':states,
            'descriptors':descriptors,'manifest_sha256':plan['sha256'],
            'full_manifest_count':plan['count'],'native_sha256':files,
            'dependency_sha256':{str(p.relative_to(ROOT)):base._sha(p) for p in inputs},
            'document_fingerprints':before,'capture_unchanged':True,
            'lead_frozen_sha256':expected_native_sha256}


def prove_identity(prepared):
    """Strict source AND placed geometry proof on detached copies only."""
    a,b = prepared['baseline'],prepared['current']; c = prepared['contract']
    changed,new = set(c['changed_existing']),set(c['new_instances'])
    old,names = set(a['instances']),set(b['instances']); affected = changed|new
    if (len(old)!=487 or len(names)!=503 or len(changed)!=16 or len(new)!=16 or
        changed&new or not changed<=old or old-names or names-old != new or
        c.get('retired_physical_instances')):
        raise RuntimeError('Unexpected r10/r11 physical identity migration')
    if a['parameters'] != b['parameters'] or a['controller'] != b['controller']:
        raise RuntimeError('Mechanism parameters or stored neutral pose changed')
    if any(abs(float(x['controller']['SpinePhaseRad']))>1e-12 for x in (a,b)):
        raise RuntimeError('Identity comparison requires neutral native documents')
    if _compatible(a['motion_config']) != _compatible(b['motion_config']):
        raise RuntimeError('Native legacy motion configuration changed')
    am,bm = a['motion'],b['motion']
    bars={n for n in changed if am.get(n,{}).get('kind')=='segment'}
    if len(bars)!=8 or len([n for n in bars if '_L3_' in n])!=4 or len([n for n in bars if '_L4_' in n])!=4:
        raise RuntimeError('Expected four handed L3 and four recessed L4 bars')
    permitted = {n for n in changed if n.startswith('SyncB') or '_Retainer' in n}
    if set(bm)-set(am) != new or set(am)-set(bm):
        raise RuntimeError('MotionMap physical migration differs')
    for n in am:
        if n not in permitted and am[n] != bm[n]:
            raise RuntimeError(n+': preserved MotionMap descriptor changed')
        if n in permitted and {k:v for k,v in am[n].items() if k not in ('y','length')} != {
            k:v for k,v in bm[n].items() if k not in ('y','length')}:
            raise RuntimeError(n+': descriptor changed outside axial stack')
    rows=[]; cache={}
    for n in sorted(names-affected):
        x,y=a['instances'][n],b['instances'][n]
        if x['source']!=y['source'] or base._matrix(x['placement'])!=base._matrix(y['placement']):
            raise RuntimeError(n+': unchanged identity/placement changed')
        sx,sy=a['sources'][x['source']],b['sources'][y['source']]
        for key in ('part_number','numeric','type'):
            if sx[key]!=sy[key]:raise RuntimeError(n+': source metadata changed: '+key)
        if base._matrix(sx['placement'])!=base._matrix(sy['placement']):
            raise RuntimeError(n+': source frame changed')
        if x['source'] not in cache:
            cache[x['source']]=base._strict_shape_identity(sx['shape'],sy['shape'],n+' source')
        rows.append({'instance':n,'source':x['source'],'source_geometry':cache[x['source']],
                     'placed_geometry':base._strict_shape_identity(x['shape'],y['shape'],n+' placed')})
    for n in sorted(changed):
        x,y=a['instances'][n],b['instances'][n]
        sx,sy=a['sources'][x['source']],b['sources'][y['source']]
        if sy['type']!='PartDesign::Body' or sy['unconstrained'] or not sy['sketch_count']:
            raise RuntimeError(n+': changed source lacks constrained native editability')
        if base._matrix(sx['placement'])!=base._matrix(sy['placement']):
            raise RuntimeError(n+': changed source-local frame moved')
        if n not in permitted and base._matrix(x['placement'])!=base._matrix(y['placement']):
            raise RuntimeError(n+': legacy bar/shaft placement moved')
    return {'status':'PASS_IDENTITY_ONLY','unchanged_count':len(rows),
            'unchanged_identity_sha256':base._digest(rows),'source_proof_count':len(cache),
            'affected':sorted(affected),'pair_count':len(affected_pairs(names,affected)),
            'native_editability':b['native']}


def section_screen(prepared):
    """Copied-source bore/leaf/floor probes; engineering retention remains unknown."""
    import FreeCAD as App
    import Part
    cfg=prepared['contract']['parameters']; current=prepared['current']; checked=[]
    for row in prepared['contract']['fork_sections']:
        name=row['source']; source=current['sources'][name]
        if source['section']!=row['section']:raise RuntimeError('Fork SectionContract differs')
        shape=source['shape'].copy()
        shape.Placement=source['placement'].inverse().multiply(shape.Placement)
        z0,z1=base._bbox(shape)[4:6]; length=source['numeric']['CenterDistance']
        for x in (3.,length+3.):
            probe=Part.makeCylinder(cfg['bearing_diameter_mm']/2,z1-z0+2,App.Vector(x,3,z0-1))
            common=shape.common(probe); volume=float(common.Volume)
            if not math.isfinite(volume) or (not common.isNull() and not common.isValid()) or volume>VOLUME_TOL:
                raise RuntimeError(name+': bearing envelope obstructed by leaf material')
            end='A' if x==3. else 'B'; lo,hi=row['section'][end]['added_cheek_local_z_bounds_mm']
            for z in (cfg['base_leaf_mm']/2,(lo+hi)/2):
                if not shape.isInside(App.Vector(x,3+cfg['link_bore_mm']/2+.2,z),1e-7,True):
                    raise RuntimeError(name+': expected native leaf material absent')
        checked.append(name)
    long_sources={current['instances'][n]['source'] for n in prepared['contract']['changed_existing'] if '_L4_' in n}
    for name in long_sources:
        src=current['sources'][name]; shape=src['shape'].copy()
        shape.Placement=src['placement'].inverse().multiply(shape.Placement)
        x=(base._bbox(shape)[0]+base._bbox(shape)[1])/2
        for z,inside in ((cfg['long_floor_mm']/2,True),
                         (cfg['long_floor_mm']+cfg['long_relief_depth_mm']/2,False)):
            if bool(shape.isInside(App.Vector(x,3,z),1e-7,True))!=inside:
                raise RuntimeError(name+': blind pocket/floor point probe failed')
    if len(checked)!=4 or len(long_sources)!=1:raise RuntimeError('Section probe coverage differs')
    return {'status':'PASS_LOCAL_PROBES_ONLY','fork_sources':checked,'long_sources':sorted(long_sources),
            'bearing_outer_race_retention':'UNVERIFIED','fits_thrust_loads':'UNVERIFIED'}


def _overlap(a,b):
    return all(a[i]<=b[i+1]+BBOX_TOL and b[i]<=a[i+1]+BBOX_TOL for i in (0,2,4))


def _proper_matrix(placement):
    values=base._matrix(placement)
    if not all(math.isfinite(v) for v in values):raise RuntimeError('Nonfinite placement')
    rows=[values[i:i+3] for i in (0,4,8)]
    if any(abs(sum(x*y for x,y in zip(rows[i],rows[j]))-(i==j))>1e-9
           for i in range(3) for j in range(3)):
        raise RuntimeError('Placement is not orthonormal')
    a,b,c=rows; determinant=(a[0]*(b[1]*c[2]-b[2]*c[1])-
        a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))
    if abs(determinant-1)>1e-9 or any(abs(x-y)>1e-9 for x,y in zip(values[12:],(0,0,0,1))):
        raise RuntimeError('Placement is not a proper rigid transform')
    return values


def run(prepared, stop_on_collision=True, progress_path=None):
    """Detached OCC screening; optional atomic filesystem progress, no document API.

    Rigid native validity is checked once; proper transforms preserve it. Bounds
    only reject disjoint pairs. All other decisions use actual OCC or an exact
    geometry/request + placement signature result, including cached collisions.
    """
    from leg_motion_r07 import regenerate_sources
    from verify_changed_revision_r10 import _transformed_box
    proof=prove_identity(prepared); current=prepared['current']
    names=set(current['instances']); pairs=affected_pairs(names,proof['affected'])
    report={'status':'RUNNING','identity':proof,'manifest_sha256':prepared['manifest_sha256'],
            'native_sha256':prepared['native_sha256'],'dependency_sha256':prepared['dependency_sha256'],
            'lead_frozen_sha256':prepared.get('lead_frozen_sha256'),
            'expected_sample_ids':[s['sample_id'] for s in prepared['states']],
            'pair_count':len(pairs),'pair_sha256':base._digest(pairs),'records':[],
            'collisions':[],'errors':[],'dynamic_sources_regenerated':0,'occ_checks':0,
            'cached_pair_checks':0,'exceptions':[],'continuous_clearance':False,'fabrication_release':False}
    source_cache={}; pair_cache={}
    def publish():
        report['samples_completed']=len(report['records'])
        if progress_path is not None:base._write(Path(progress_path),report)
    try:
        report['section_screen']=section_screen(prepared)
        native_boxes={}; native_hash={}
        for n,o in current['instances'].items():
            _solid(o['shape'],n); _proper_matrix(o['placement'])
            native_boxes[n]=base._bbox(o['shape']); native_hash[n]=base._brep_sha(o['shape'])
        if len(prepared['states'])!=len(prepared['descriptors']):raise RuntimeError('Descriptor count differs')
        for state,pp in zip(prepared['states'],prepared['descriptors']):
            if set(pp['placements'])!=names or not set(pp['shape_requests'])<=names:
                raise RuntimeError('Descriptor physical coverage differs')
            shapes={}; boxes={}; signatures={}; decisions=[]; counts={'bbox':0,'occ':0,'cached':0}
            for n in sorted(names):
                p=pp['placements'][n]; matrix=_proper_matrix(p); request=pp['shape_requests'].get(n)
                signatures[n]=(base._digest(request) if request else native_hash[n],matrix)
                boxes[n]=(base._dynamic_boxes(request,p)[0] if request else
                    [_transformed_box(native_boxes[n],p.multiply(current['instances'][n]['placement'].inverse()))])
            def actual_shape(n):
                if n not in shapes:
                    p=pp['placements'][n]; request=pp['shape_requests'].get(n)
                    if request:
                        shape=regenerate_sources(dict(pp,shape_requests={n:request}),source_cache)[n]
                        shape.Placement=p.multiply(shape.Placement)
                        report['dynamic_sources_regenerated']+=1
                        _solid(shape,n)
                    else:
                        native=current['instances'][n]; shape=native['shape'].copy()
                        shape.Placement=p.multiply(native['placement'].inverse()).multiply(shape.Placement)
                    shapes[n]=shape
                return shapes[n]
            for a,b in pairs:
                ba,bb=boxes[a],boxes[b]
                if ba is not None and bb is not None and all(not _overlap(x,y) for x in ba for y in bb):
                    counts['bbox']+=1;decisions.append('b');continue
                key=(a,b,signatures[a],signatures[b])
                if key in pair_cache:
                    v=pair_cache[key];counts['cached']+=1;report['cached_pair_checks']+=1;decisions.append('c')
                else:
                    sa,sb=actual_shape(a),actual_shape(b)
                    if not _overlap(base._bbox(sa),base._bbox(sb)):
                        counts['bbox']+=1;decisions.append('b');continue
                    common=sa.common(sb);v=float(common.Volume)
                    if not math.isfinite(v) or v<0 or (not common.isNull() and not common.isValid()):
                        raise RuntimeError('Invalid/nonfinite OCC common: '+a+' / '+b)
                    pair_cache[key]=v;counts['occ']+=1;report['occ_checks']+=1;decisions.append('o')
                if v>VOLUME_TOL:
                    report['collisions'].append({'sample_id':state['sample_id'],'a':a,'b':b,'volume_mm3':v})
            if sum(counts.values())!=len(pairs) or len(decisions)!=len(pairs):
                raise RuntimeError('Disjoint/exhaustive pair decision coverage incomplete')
            report['records'].append({'sample_id':state['sample_id'],'input_sha256':state['input_sha256'],
                'pair_count':len(pairs),'decision_sha256':base._digest(decisions),'counts':counts,
                'guide_warnings':pp['guide_warnings']})
            publish()
            if stop_on_collision and (report['collisions'] or pp['guide_warnings']):break
        full=manifest(); ids={r['sample_id'] for r in report['records']}
        complete=ids=={s['sample_id'] for s in full['states']} and len(report['records'])==1346
        failed=report['collisions'] or any(r['guide_warnings'] for r in report['records'])
        frozen=prepared.get('lead_frozen_sha256') is not None
        report['status']='FAIL' if failed else ('PASS_AFFECTED_1346_ONLY' if complete and frozen else 'PASS_BOUNDED_ONLY')
    except Exception as error:
        report['status']='ERROR';report['errors'].append(repr(error))
    report['disk_inputs_unchanged']=all(base._sha(p)==h for p,h in prepared['native_sha256'].items())
    report['dependencies_unchanged']=all(base._sha(ROOT/p)==h for p,h in prepared['dependency_sha256'].items())
    if not report['disk_inputs_unchanged'] or not report['dependencies_unchanged']:
        report['status']='FAIL_INPUT_CHANGED'
    publish()
    return report
