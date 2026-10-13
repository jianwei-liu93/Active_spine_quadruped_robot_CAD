"""Read-only r12/r10 capture and detached copied-solid verification. No auto-run.

Only prepare accesses explicitly supplied, already-open neutral Documents.
run never recomputes, poses, opens, closes or saves a native document. The lead
must execute runtime gates; source presence and static checks are not evidence.
"""
import json
import math
from pathlib import Path
import verify_frame_revision_r09 as base
from verify_link_sections_r11 import (_capture, _native, _solid, _overlap,
                                      _proper_matrix, affected_pairs)
from verify_changed_revision_r10 import manifest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT/'cad/flexor_r12_robot.FCStd'
BASELINE = ROOT/'cad/flexor_r10_robot.FCStd'
VOLUME_TOL = 1e-5
BBOX_TOL = 1e-6


def _compatible(config):
    result=dict(config)
    for key in ('revision','limits','center_frame_r12','spine_bar_r12','torso_contours_r12'):
        result.pop(key,None)
    return result



def _native_config_comparison(old, current):
    """Exact motion inputs; expose historical native metadata refresh separately.

    leg_motion_r07 consumes parameters/leg_geometry; states is retained as an
    additional command-contract invariant. Full r12 disk/native equality and
    compatible r10/r12 disk configuration remain independent prepare gates.
    Geometry/source identity gates do not use this metadata allowance.
    """
    motion_keys=('parameters','leg_geometry','states')
    if any(key not in old or key not in current or old[key]!=current[key] for key in motion_keys):
        raise RuntimeError('Native motion parameters, leg geometry or command states changed')
    changes=[]
    def compare(a,b,path):
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(set(a)|set(b)):
                child=path+[key]
                if key not in a:
                    changes.append({'path':child,'baseline_present':False,'current_present':True,'current':b[key]})
                elif key not in b:
                    changes.append({'path':child,'baseline_present':True,'current_present':False,'baseline':a[key]})
                else:compare(a[key],b[key],child)
        elif a!=b:
            changes.append({'path':path,'baseline_present':True,'current_present':True,'baseline':a,'current':b})
    compare({k:v for k,v in old.items() if k not in motion_keys},
            {k:v for k,v in current.items() if k not in motion_keys},[])
    return {'status':'PASS_EXACT_NATIVE_MOTION_PROJECTION','exact_preserved_keys':list(motion_keys),
        'baseline_native_configuration_sha256':base._digest(old),
        'current_native_configuration_sha256':base._digest(current),
        'historical_native_metadata_refresh':changes,
        'scope':'Historical native config metadata may predate canonical r10 geometry; all source/world identity gates remain strict'}


def _native_capture(doc):
    from verify_changed_revision_r10 import _native_state_guard
    result=_capture(doc)
    result['native']['recursive_guard']=_native_state_guard(doc)
    sketches=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject']
    if any(not o.FullyConstrained for o in sketches):
        raise RuntimeError('Every native sketch must be fully constrained')
    features={}
    for body in (o for o in doc.Objects if o.TypeId=='PartDesign::Body'):
        _solid(body.Shape,body.Name)
        for member in body.Group:
            if member.TypeId.startswith('PartDesign::') and hasattr(member,'Shape'):
                _solid(member.Shape,member.Name)
                features[member.Name]={'type':member.TypeId,'numeric':base._numeric_properties(member)}
    result['native_features']=features
    json.dumps({'features':features,'source_numeric':{n:v['numeric'] for n,v in result['sources'].items()}},allow_nan=False)
    return result


def _default_states(current, revision='r12'):
    legs=json.loads(current['controller']['LegAnglesR03'])
    wheel=float(current['controller']['WheelAngleR07'])
    states=[]
    for degree in range(0,361,4):
        row={'sample_id':revision+'_spine_'+str(degree).zfill(3),
             'label':'neutral_legs_spine_'+str(degree),'trajectory':revision+'_fixed_leg_spine',
             'theta':math.radians(degree),'leg_angles':legs,'wheel_angle':wheel}
        row['input_sha256']=base._digest({k:row[k] for k in ('theta','leg_angles','wheel_angle')})
        states.append(row)
    return states


def prepare(doc, baseline_doc, states=None, canonical=None, expected_native_sha256=None):
    """Lead GUI read-only capture of actual neutral r12/r13/r14 and canonical r10.

    Default: inclusive 0..360deg at 4deg, 91 states including actual neutral,
    with controller-stored neutral legs/wheel. Optional states must be exact
    unchanged dictionaries from the existing 1346-state r10 manifest.
    Returns detached copied shapes/placements and serializable data only.
    """
    import FreeCAD as App
    from leg_motion_r07 import descriptor
    from verify_motion_package_r08 import DEPENDENCIES
    from verify_changed_revision_r10 import validate_freeze, FREEZE
    baseline_freeze=validate_freeze()
    revision=str(doc.PoseController.ParameterRevision)
    if revision not in ('r12','r13','r14'):
        raise ValueError('Expected r12, r13 or r14 assembly revision')
    if canonical is None:canonical=ROOT/('cad/flexor_'+revision+'_robot.FCStd')
    config_path=ROOT/('parameters/assembly_'+revision+'.json')
    paths=[Path(doc.FileName).resolve(),Path(baseline_doc.FileName).resolve()]
    if paths != [Path(canonical).resolve(),BASELINE.resolve()]:
        raise ValueError('Expected saved '+revision+' and canonical r10 native documents')
    hashes={str(p):base._sha(p) for p in paths}
    if expected_native_sha256 is not None and hashes[str(paths[0])]!=expected_native_sha256:
        raise RuntimeError('Lead-frozen '+revision+' native SHA differs')
    before=[base._document_fingerprint(d) for d in (doc,baseline_doc)]
    config=json.loads(config_path.read_text())
    if config['revision']!=revision:raise RuntimeError('Assembly disk revision differs from native controller')
    old_config=json.loads((ROOT/'parameters/assembly_r10.json').read_text())
    if _compatible(config)!=_compatible(old_config):
        raise RuntimeError('Mechanism/legacy configuration differs')
    current,old=_native_capture(doc),_native_capture(baseline_doc)
    if current['motion_config'] != config:
        raise RuntimeError('Actual native prescribed config differs from '+config_path.name)
    contract=json.loads(doc.PoseController.CompactFrameR12)
    detail=json.loads(doc.PoseController.BarDetailR12)
    if detail['parameters']!=config['spine_bar_r12']:
        raise RuntimeError('Native BarDetailR12 differs from exact r12 configuration')
    default=states is None
    plan=manifest()
    if default:
        states=_default_states(current,revision)
    else:
        states=list(states);by_id={s['sample_id']:s for s in plan['states']}
        if any(s != by_id.get(s.get('sample_id')) for s in states):
            raise ValueError('Optional input differs from exact r10 manifest')
    if not states or len({s['sample_id'] for s in states})!=len(states):
        raise ValueError('Empty or duplicate requested states')
    json.dumps(states,allow_nan=False)
    descriptors=[]
    for state in states:
        pp=descriptor(doc,state['theta'],state['leg_angles'],state['wheel_angle'],config)
        descriptors.append({'placements':{n:App.Placement(p) for n,p in pp['placements'].items()},
            'shape_requests':json.loads(json.dumps(pp['shape_requests'],allow_nan=False)),
            'guide_warnings':list(pp['guide_warnings'])})
    if before != [base._document_fingerprint(d) for d in (doc,baseline_doc)]:
        raise RuntimeError('Document changed during read-only capture')
    if any(base._sha(p)!=h for p,h in hashes.items()):
        raise RuntimeError('Native disk inputs changed during capture')
    dependencies=set(baseline_freeze['dependency_sha256'])|set(DEPENDENCIES)|{
        'verify_compact_revision_r12.py','verify_link_sections_r11.py','verify_frame_revision_r09.py',
        'verify_changed_revision_r10.py','adaptive_volume_r07.py','occt_adaptive_volume_r07.cpp',
        'compact_spine_stack_r12.py','spine_frame_r12.py','spine_bars_r12.py',
        'torso_contours_r12.py','build_robot_r12.py','kinematics.py'}
    if revision in ('r13','r14'):dependencies.add('build_robot_'+revision+'.py')
    inputs=[ROOT/'src'/n for n in sorted(dependencies)]+[
        ROOT/'parameters/assembly_r12.json',ROOT/'parameters/assembly_r10.json',FREEZE,
        ROOT/'parameters/candidate_r02.json',
        ROOT/'reports/verification/r08_motion_partitions/full_manifest.json']
    if config_path not in inputs:inputs.append(config_path)
    return {'assembly_revision':revision,'configuration_path':str(config_path.relative_to(ROOT)),'current':current,'baseline':old,'contract':contract,'bar_detail':detail,'config':config,
        'states':states,'descriptors':descriptors,'manifest_sha256':base._digest(states),
        'r10_manifest_sha256':plan['sha256'],'full_manifest_count':plan['count'],
        'native_sha256':hashes,'dependency_sha256':{str(p.relative_to(ROOT)):base._sha(p) for p in inputs},
        'document_fingerprints':before,'capture_unchanged':True,
        'lead_frozen_sha256':expected_native_sha256,
        'coverage_scope':'91 inclusive spine states 0..360deg/4deg with actual stored neutral legs/wheel'
            if default else 'Exact selected r10 manifest states only'}


def prove_identity(prepared):
    a,b=prepared['baseline'],prepared['current'];c=prepared['contract']
    old,names=set(a['instances']),set(b['instances'])
    detail=prepared['bar_detail'];new=set(detail['new_instances'])
    retired=set(c['retired_physical_instances']);stack=set(c['changed_existing'])
    bars={n for n,o in a['instances'].items() if o['source'] in ('SPN_r02_L3','SPN_r02_L4')}
    axial={'SyncB1','SyncB2'}|{k+s+'_Retainer'+('1' if s=='_1' else '0')
        for k in ('B1','B2') for s in ('_1','__1')}
    expected_detail=bars|axial|{'ThroughA1','ThroughA2'}
    if set(detail['changed_existing'])!=expected_detail:
        raise RuntimeError('BarDetailR12 existing-ID migration differs')
    expected_new={k+s+'_'+end for k in ('B1','B2') for s in ('_1','__1')
        for end in ('ForkOuterBearing','ForkOuterSpacer')}
    if new!=expected_new:raise RuntimeError('Expected exact8 B-only fork bearing/spacer IDs')
    changed=stack|bars|axial|{'Torso_fore','Torso_hind'}
    affected=changed|new
    expected_stack={'LumbarIntegrated1'}|{'Through'+k for k in ('A1','A2','C1','C2')}
    expected_stack|={n for n in old if n.startswith('GuideLiner')}
    for k in ('D1','D2'):
        for suffix,side in (('_1',1),('__1',-1)):
            expected_stack|={k+suffix+'_Pin',k+suffix+'_Retainer'+('1' if side==1 else '0')}
    for k in ('A1','A2','C1','C2'):
        for suffix,side in (('_1',1),('__1',-1)):
            prefix=k+suffix
            expected_stack.add(prefix+'_Retainer'+('1' if side==1 else '0'))
            if k.startswith('A'):
                expected_stack|={prefix+'_CaptureCap',prefix+'_OuterBearing',prefix+'_OuterSpacer'}
            else:
                expected_stack|={prefix+'_CaptureWasher',prefix+'_Bearing2'}
                outer=[prefix+'_Spacer'+str(i) for i in (0,1)
                    if abs(a['motion'][prefix+'_Spacer'+str(i)]['length']-3.)<1e-6]
                if len(outer)!=1:raise RuntimeError('Expected unique baseline outer C spacer')
                expected_stack.update(outer)
    if stack!=expected_stack or len(stack)!=53:
        raise RuntimeError('CompactFrameR12 changed-existing inventory differs from exact stack migration')
    expected_retired={k+s+'_'+end for k in ('E1','E2') for s in ('_1','__1')
        for end in ('Pin','Bearing0','Bearing1','TorsoBearing','Spacer0','TorsoSpacer','Retainer0','Retainer1')}
    expected_retired|={k+s+'_'+end for k in ('D1','D2') for s in ('_1','__1') for end in ('Bearing1','Spacer0')}
    if (len(old)!=487 or len(names)!=455 or names-old!=new or old-names!=retired or
        retired!=expected_retired or c['new_physical_instances'] or not changed<=names or
        len(bars)!=8 or any(sum(a['instances'][n]['source']=='SPN_r02_'+k for n in bars)!=4 for k in ('L3','L4'))):
        raise RuntimeError('Unexpected r10 -> r12 physical migration (487 -> 455;40 retired;8 new)')
    if a['parameters']!=b['parameters'] or a['controller']!=b['controller']:
        raise RuntimeError('Mechanism parameters or actual stored neutral pose changed')
    if any(abs(float(x['controller']['SpinePhaseRad']))>1e-12 for x in (a,b)):
        raise RuntimeError('Identity proof requires actual neutral native documents')
    native_config_comparison=_native_config_comparison(a['motion_config'],b['motion_config'])
    am,bm=a['motion'],b['motion']
    if set(bm)-set(am)!=new or set(am)-set(bm)!=(retired&set(am)):
        raise RuntimeError('MotionMap retirement differs')
    for n in new:
        key=n[:2];bearing=n.endswith('Bearing');side=-1 if '__1_' in n else 1
        y=(25.8 if key.startswith('A') else 36.) if bearing else (26.7 if key.startswith('A') else 36.9)
        expected={'kind':'point','point':key,'y':side*y,'length':1.2 if bearing else .6}
        if bm[n]!=expected:raise RuntimeError(n+': new hardware descriptor differs')
    for n in set(bm)-new:
        strip=lambda row:{k:v for k,v in row.items() if k not in ('y','length')}
        if (n not in (stack|axial) and am[n]!=bm[n]) or (n in (stack|axial) and strip(am[n])!=strip(bm[n])):
            raise RuntimeError(n+': MotionMap changed outside permitted axial y/length')
    rows=[];cache={}
    for n in sorted(names-affected):
        x,y=a['instances'][n],b['instances'][n]
        if x['source']!=y['source'] or base._matrix(x['placement'])!=base._matrix(y['placement']):
            raise RuntimeError(n+': unchanged physical identity/frame changed')
        sx,sy=a['sources'][x['source']],b['sources'][y['source']]
        for key in ('part_number','numeric','type'):
            if sx[key]!=sy[key]:raise RuntimeError(n+': source metadata differs: '+key)
        if base._matrix(sx['placement'])!=base._matrix(sy['placement']):
            raise RuntimeError(n+': source-local placement differs')
        if x['source'] not in cache:
            cache[x['source']]=base._strict_shape_identity(sx['shape'],sy['shape'],n+' source')
        rows.append({'instance':n,'source':x['source'],'source_geometry':cache[x['source']],
            'placed_geometry':base._strict_shape_identity(x['shape'],y['shape'],n+' world')})
    for n in changed:
        x,y=a['instances'][n],b['instances'][n]
        sx,sy=a['sources'][x['source']],b['sources'][y['source']]
        if sy['type']!='PartDesign::Body' or not sy['sketch_count'] or sy['unconstrained']:
            raise RuntimeError(n+': native constrained Body required')
        if base._matrix(sx['placement'])!=base._matrix(sy['placement']):
            raise RuntimeError(n+': source-local frame changed')
        if n not in (stack|axial) and base._matrix(x['placement'])!=base._matrix(y['placement']):
            raise RuntimeError(n+': torso/bar instance frame changed')
    if not {'SpineMotor1','SpineMotor_1'}<=names-changed:
        raise RuntimeError('Both spine motors must be strictly unchanged')
    if b['instances']['LumbarIntegrated1']['source']!='FRM_LUMBAR_COMPACT_CAGE_r12':
        raise RuntimeError('Wrong compact frame source binding')
    if base._matrix(a['instances']['LumbarIntegrated1']['placement'])!=base._matrix(b['instances']['LumbarIntegrated1']['placement']):
        raise RuntimeError('Ground frame binding moved')
    if 'LumbarIntegrated1' in bm:
        raise RuntimeError('Grounded frame unexpectedly driven')
    return {'status':'PASS_IDENTITY_ONLY','unchanged_count':len(rows),
        'unchanged_identity_sha256':base._digest(rows),'source_proof_count':len(cache),
        'affected':sorted(affected),'changed_existing':sorted(changed),'retired':sorted(retired),'new_count':len(new),
        'pair_count':len(affected_pairs(names,affected)),'native_editability':b['native'],
        'strictly_unchanged_motors':['SpineMotor1','SpineMotor_1'],
        'native_configuration_comparison':native_config_comparison}


def _near(actual,expected,label,tol=1e-6):
    if not math.isfinite(float(actual)) or abs(float(actual)-expected)>tol:
        raise RuntimeError(label+': '+str(actual)+' != '+str(expected))


def _local(src):
    shape=src['shape'].copy()
    shape.Placement=src['placement'].inverse().multiply(shape.Placement)
    return shape



def _organic_outline(shape,length,label):
    """Actual copied-solid main-leaf section: four nominal tangent circles."""
    import FreeCAD as App
    import Part
    wires=shape.slice(App.Vector(0,0,1),.6)
    if not wires:raise RuntimeError(label+': main-leaf section is empty')
    outer=max(wires,key=lambda w:float(w.Length))
    if not outer.isClosed():raise RuntimeError(label+': organic outline is open')
    radius=4.;half=3.;dx=length/2
    cy=(dx*dx-(radius-half)**2)/(2*(radius-half));sr=cy-half
    expected=[(3.,3.,radius),(length+3.,3.,radius),
        (3.+dx,3.+cy,sr),(3.+dx,3.-cy,sr)]
    seen=set();ends=[]
    for i,edge in enumerate(outer.Edges):
        curve=edge.Curve
        if not isinstance(curve,Part.Circle):raise RuntimeError(label+': organic boundary contains a noncircular edge')
        actual=(float(curve.Center.x),float(curve.Center.y),float(curve.Radius))
        chosen=min(range(4),key=lambda j:math.dist(actual,expected[j]))
        if math.dist(actual,expected[chosen])>1e-5:raise RuntimeError(label+': organic circle differs from frozen eye/waist dimensions')
        seen.add(chosen)
        for param in (edge.FirstParameter,edge.LastParameter):
            point=edge.valueAt(param);tangent=edge.tangentAt(param)
            if tangent.Length<1e-12:raise RuntimeError(label+': zero boundary tangent')
            ends.append((i,point,tangent))
    if seen!=set(range(4)):raise RuntimeError(label+': four organic eye/waist circles not all present')
    worst=0.
    for i,point,tangent in ends:
        matches=[q for q in ends if q[0]!=i and (q[1]-point).Length<1e-5]
        if len(matches)!=1:raise RuntimeError(label+': organic section junction is not unique/closed')
        other=matches[0][2];error=1-abs(tangent.dot(other)/(tangent.Length*other.Length))
        if not math.isfinite(error) or error>1e-8:raise RuntimeError(label+': organic arc junction lacks tangent continuity')
        worst=max(worst,error)
    return {'section_local_z_mm':.6,'unique_circular_arcs':4,'waist_mm':6.,
        'eye_diameter_mm':8.,'maximum_tangent_unit_dot_error':worst,
        'scope':'Actual main-leaf outer section only; fork leaf/root checked with separate probes'}


def section_screen(prepared):
    import FreeCAD as App
    import Part
    cur=prepared['current'];cfg=prepared['config'];c=prepared['contract'];rows=[]
    frame=cur['instances']['LumbarIntegrated1']
    box=base._bbox(frame['shape'])
    _near(box[2],-39.4,'Frame Ymin');_near(box[3],39.4,'Frame Ymax')
    _near(c['ground_transverse_span_mm'],78.8,'Contract frame span')
    _near(c['housing_transverse_span_mm'],56.8,'Contract housing span')
    fsrc=cur['sources'][frame['source']];local=_local(fsrc);bounds=base._bbox(local)
    _near(bounds[4],-11.,'Frame source Zmin');_near(bounds[5],67.8,'Frame source Zmax')
    for j in (0,1):
        feature=cur['native_features'][frame['source']+'_ContinuousCrosswall'+str(j)]
        _near(feature['numeric']['Length'],56.8,'Housing native crosswall length')
    for n,m in cur['motion'].items():
        if n in c['changed_existing'] and n.startswith(('C1_','C2_','D1_','D2_')):
            placed=base._bbox(cur['instances'][n]['shape'])
            _near((placed[2]+placed[3])/2,m['y'],n+' actual world axial center')
        if n.startswith(('C1_','C2_')) and n.endswith('_Bearing2'):
            _near(abs(m['y']),38.6,n+' Y');_near(m['length'],1.2,n+' length')
        if n.startswith(('C1_','C2_')) and n in c['changed_existing'] and '_Spacer' in n:
            _near(m['length'],1.4,n+' length');_near(abs(m['y']),37.3,n+' Y')
            sb=base._bbox(_local(cur['sources'][cur['instances'][n]['source']]))
            _near(sb[5]-sb[4],1.4,n+' actual spacer source length')
        if n.startswith(('D1_','D2_')) and n.endswith('_Pin'):
            _near(m['length'],24.,n+' length');_near(abs(m['y']),25.6,n+' center')
            sh=_local(cur['sources'][cur['instances'][n]['source']])
            z0,z1=base._bbox(sh)[4:6];_near(z1-z0,24.,n+' actual source length')
        if n.startswith(('D1_','D2_')) and n in c['changed_existing'] and '_Retainer' in n:
            _near(abs(m['y']),37.1,n+' clip center')
    for key in ('L4',):
        name='SPN_r02_'+key;src=cur['sources'][name];shape=_local(src)
        length=cur['parameters']['L4_mm'];box=base._bbox(shape)
        for value,expected,label in ((box[2],-1.,'Ymin'),(box[3],7.,'Ymax'),
            (box[4],0.,'Zmin'),(box[5],1.2,'Zmax')):_near(value,expected,name+label)
        axes=[]
        for face in shape.Faces:
            surf=face.Surface
            if isinstance(surf,Part.Cylinder) and abs(float(surf.Radius)-2.025)<1e-6:
                if abs(surf.Axis.z)/surf.Axis.Length>1-1e-8:
                    axes.append((float(surf.Center.x),float(surf.Center.y)))
        for x in (3.,length+3.):
            if min((math.dist((x,3.),q) for q in axes),default=math.inf)>1e-6:
                raise RuntimeError(name+': actual bore cylindrical surface absent')
            probe=Part.makeCylinder(2.025,3.2,App.Vector(x,3,-1))
            common=shape.common(probe)
            if not common.isNull() and not common.isValid():raise RuntimeError(name+': invalid bore intersection')
            if not math.isfinite(float(common.Volume)) or float(common.Volume)>VOLUME_TOL:
                raise RuntimeError(name+': bore blocked')
        # The continuous leaf extends through all tested heights; no cheeks or fork.
        for x in (3.,3.+length*.25,3.+length*.5,3.+length*.75,length+3.):
            for y in (-.2,6.2):
                for z in (.1,.3,.6,.9,1.1):
                    if not shape.isInside(App.Vector(x,y,z),1e-7,True):
                        raise RuntimeError(name+': continuous leaf material missing')
        if key=='L4':
            for z,inside in ((.3,True),(.599,True),(.601,False),(.9,False)):
                if bool(shape.isInside(App.Vector(3+length/2,3,z),1e-7,True))!=inside:
                    raise RuntimeError(name+': .6mm blind-pocket floor failed')
        rows.append({'source':name,'bores_mm':[[3.,3.],[length+3.,3.]],
            'width_mm':8.,'thickness_mm':1.2,'single_leaf':True})
    if cfg['spine_bar_r12'].get('fork_end')!='B':raise RuntimeError('Fork end must be B only')
    _near(cfg['spine_bar_r12']['waist_width_mm'],6.,'Organic waist config')
    depth,reach=(8.,10.) if prepared['assembly_revision']=='r14' else (3.5,5.5)
    _near(cfg['spine_bar_r12']['terminal_opening_depth_mm'],depth,'Fork opening config')
    _near(cfg['spine_bar_r12']['terminal_reach_mm'],reach,'Fork reach config')
    terminal_rows=[]
    terminal_contract={r['instance']:r for r in prepared['bar_detail']['terminal_sections']}
    if len(terminal_contract)!=4:raise RuntimeError('Expected four distinct terminal section records')
    for n in prepared['bar_detail']['changed_existing']:
        if '_L3_' not in n:continue
        inst=cur['instances'][n];m=cur['motion'][n]
        side=1 if m['y']>0 else -1;branch=1 if m['a']=='A1' else 2
        expected_name='SPN_AB_TERMINAL_r12_B'+str(branch)+('_POS' if side>0 else '_NEG')
        if inst['source']!=expected_name:raise RuntimeError(n+': wrong handed terminal source')
        src=cur['sources'][expected_name];shape=_local(src);length=src['numeric']['CenterDistance']
        record=terminal_contract[n]
        if record['source']!=expected_name or record['section']!=src['section'] or record['motion']!=m:
            raise RuntimeError(n+': actual source section differs from BarDetailR12')
        bounds=base._bbox(shape)
        for value,expected,label in ((bounds[0],-1.,'Xmin'),(bounds[1],length+7.,'Xmax'),
            (bounds[2],-1.,'Ymin'),(bounds[3],7.,'Ymax')):_near(value,expected,expected_name+label)
        if set(src['section'])!={'B'}:raise RuntimeError(expected_name+': only B may have a fork')
        for x in (3.,length+3.):
            probe=Part.makeCylinder(2.025,bounds[5]-bounds[4]+2,App.Vector(x,3,bounds[4]-1))
            common=shape.common(probe)
            if (not common.isNull() and not common.isValid()) or not math.isfinite(float(common.Volume)) or float(common.Volume)>VOLUME_TOL:
                raise RuntimeError(expected_name+': A/B through-bearing bore obstructed')
            axes=[]
            for face in shape.Faces:
                surf=face.Surface
                if isinstance(surf,Part.Cylinder) and abs(float(surf.Radius)-2.025)<1e-6:
                    if abs(surf.Axis.z)/surf.Axis.Length>1-1e-8:
                        axes.append((float(surf.Center.x),float(surf.Center.y)))
            if min((math.dist((x,3.),q) for q in axes),default=math.inf)>1e-6:
                raise RuntimeError(expected_name+': actual A/B bore cylindrical surface absent')
        for end,x,inward,target in (('B',length+3.,-1,36.),):
            zc=.6+side*(abs(m['y'])-target);lo,hi=zc-.6,zc+.6
            _near(bounds[4],min(0.,lo),expected_name+' sourceZmin')
            _near(bounds[5],max(1.2,hi),expected_name+' sourceZmax')
            section=src['section'][end]
            for value,expected in zip(section['added_cheek_local_z_bounds_mm'],(lo,hi)):
                _near(value,expected,expected_name+' '+end+' section bounds')
            _near(section['opening_depth_from_pivot_mm'],depth,expected_name+' opening')
            _near(section['maximum_inward_reach_mm'],reach,expected_name+' reach')
            _near(section['added_cheek_world_abs_y_mm'],target,expected_name+' cheek axial center')
            probe=Part.makeCylinder(2.025,bounds[5]-bounds[4]+2,App.Vector(x,3,bounds[4]-1))
            common=shape.common(probe)
            if (not common.isNull() and not common.isValid()) or not math.isfinite(float(common.Volume)) or float(common.Volume)>VOLUME_TOL:
                raise RuntimeError(expected_name+': actual terminal bore obstructed')
            # Added leaf extends 4mm outward and the revision-specific reach inward.
            # Leaf, connecting web, opening and material beyond its root are separate probes.
            for z in (lo+.1,zc,hi-.1):
                for off,y in ((0.,6.),(4.5,3.)):
                    if not shape.isInside(App.Vector(x+inward*off,y,z),1e-7,True):
                        raise RuntimeError(expected_name+': compact terminal cheek missing')
                if shape.isInside(App.Vector(x+inward*(reach+.1),3,z),1e-7,True):
                    raise RuntimeError(expected_name+': added cheek exceeds frozen inward reach')
            gap=(1.2+lo)/2 if lo>1.2 else hi/2
            if not shape.isInside(App.Vector(x+inward*((depth+reach)/2),3,gap),1e-7,True):
                raise RuntimeError(expected_name+': compact connecting web missing')
            if shape.isInside(App.Vector(x+inward*(depth-1.),3,gap),1e-7,True):
                raise RuntimeError(expected_name+': terminal fork opening obstructed')
        # A remains a single eye throughout a bounded end-region grid; all
        # non-main-leaf heights must be empty even though B has a raised leaf.
        zsamples=sorted(set([bounds[4]+.1,bounds[5]-.1,-.1,1.3]+[
            bounds[4]+(bounds[5]-bounds[4])*j/12 for j in range(13)]))
        for x in (-.5,1.,3.,5.,7.5):
            for y in (0.,1.,3.,5.,6.):
                for z in zsamples:
                    if z<-.001 or z>1.201:
                        if shape.isInside(App.Vector(x,y,z),1e-7,True):
                            raise RuntimeError(expected_name+': A end has extra fork material')
        for z in (.1,.6,1.1):
            for y,inside in ((.1,True),(5.9,True),(-.1,False),(6.1,False)):
                if bool(shape.isInside(App.Vector(3+length/2,y,z),1e-7,True))!=inside:
                    raise RuntimeError(expected_name+': organic6mm waist failed')
            for y in (-.8,6.8):
                if not shape.isInside(App.Vector(3,y,z),1e-7,True):
                    raise RuntimeError(expected_name+': rounded8mm A eye missing')
            if not shape.isInside(App.Vector(3+length/2,3,z),1e-7,True):
                raise RuntimeError(expected_name+': continuous main leaf missing')
        outline=_organic_outline(shape,length,expected_name)
        terminal_rows.append({'instance':n,'source':expected_name,'added_terminal_length_mm':reach+4.,
            'fork_end':'B','A_end_single_eye':True,'waist_width_mm':6.,'organic_main_outline':outline,
            'inward_reach_mm':reach,'opening_mm':depth,'web_interval_mm':[depth,reach]})
    if len(terminal_rows)!=4:raise RuntimeError('Expected four handed compact terminal sources')
    for n,total,shoulder in (('ThroughA1',82.4,54.),('ThroughA2',82.4,54.),
                              ('SyncB1',76.,60.),('SyncB2',76.,60.)):
        source=cur['instances'][n]['source'];box=base._bbox(_local(cur['sources'][source]))
        _near(box[5]-box[4],total,n+' actual shaft length')
        pads=[v for k,v in cur['native_features'].items() if k.startswith(source+'_') and v['type']=='PartDesign::Pad']
        if not pads:raise RuntimeError(n+': native shoulder Pad missing')
        _near(pads[-1]['numeric']['Length'],shoulder,n+' actual shoulder span')
    for n in prepared['bar_detail']['new_instances']:
        m=cur['motion'][n];box=base._bbox(cur['instances'][n]['shape'])
        _near((box[2]+box[3])/2,m['y'],n+' actual center')
        _near(box[3]-box[2],m['length'],n+' actual thickness')
    for n in prepared['bar_detail']['changed_existing']:
        if n.startswith(('B1_','B2_')) and '_Retainer' in n:
            m=cur['motion'][n];_near(abs(m['y']),37.5,n+' retainer center')
            box=base._bbox(cur['instances'][n]['shape']);_near(abs((box[2]+box[3])/2),37.5,n+' actual retainer center')
    return {'status':'PASS_BOUNDED_LOCAL_PROBES_ONLY','bars':rows,'frame_span_mm':78.8,
        'housing_span_mm':56.8,'compact_terminal_sources':terminal_rows,'fits_thrust_retention':'UNVERIFIED'}


def s9_screen(prepared):
    """Detached actual cylindrical surface axes; no sketch-only inference."""
    import Part
    from collections import Counter
    from kinematics import spine
    current=prepared['current'];state=spine(0,current['parameters']);rows=[]
    expected=[('O','G'),('G','B1'),('G','B2'),('A1','B1'),('A2','B2'),
        ('B1','C1'),('B2','C2'),('C1','D1'),('C2','D2'),('E1','D1'),('E2','D2')]
    observed={-1:[],1:[]}
    def check_axes(name,pivots,ys=None):
        axes=[]
        for face in current['instances'][name]['shape'].Faces:
            surface=face.Surface
            if not isinstance(surface,Part.Cylinder):continue
            axis=surface.Axis
            if axis.Length<1e-12 or abs(axis.y)/axis.Length<1-1e-8:continue
            center=surface.Center
            if ys is not None and not any(abs(float(face.CenterOfMass.y)-y)<1.1 for y in ys):continue
            axes.append((float(center.x),float(center.z),float(surface.Radius)))
        for pivot in pivots:
            error=min((math.dist(state[pivot],q[:2]) for q in axes),default=math.inf)
            if not math.isfinite(error) or error>1e-4:
                raise RuntimeError(name+': actual cylindrical axis missing/moved at '+pivot)
            rows.append({'instance':name,'pivot':pivot,'axis_error_mm':error})
    for n,m in current['motion'].items():
        if m.get('kind')=='segment' and n.startswith(('Link','DirectCrank')):
            edge=(m['a'],m['b']);observed[1 if m['y']>0 else -1].append(edge)
            check_axes(n,edge)
    for kind,i in (('hind',1),('fore',2)):
        name='Torso_'+kind
        # r12 deliberately retires lateral E journals. E bore is the center clevis.
        check_axes(name,('E'+str(i),),[-2.8,2.8])
        for side in (-1,1):check_axes(name,('D'+str(i),),[side*15.2])
        for side in (-1,1):observed[side].append(('E'+str(i),'D'+str(i)))
    for side in (-1,1):
        if Counter(observed[side])!=Counter(expected):raise RuntimeError('S9 graph differs on side '+str(side))
    check_axes('LumbarIntegrated1',('A1','A2','E1','E2'))
    return {'status':'PASS_ACTUAL_NEUTRAL_CYLINDRICAL_AXES_ONLY','axes':rows,
        'maximum_axis_error_mm':max(r['axis_error_mm'] for r in rows),
        'projected_edges_per_side':expected,'world_shape_transform_applied_twice':False,
        'limitation':'Neutral actual axes and projected graph; no complete spatial mobility proof'}


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
    report={'status':'RUNNING','assembly_revision':prepared['assembly_revision'],
            'configuration_path':prepared['configuration_path'],'identity':proof,'manifest_sha256':prepared['manifest_sha256'],
            'native_sha256':prepared['native_sha256'],'dependency_sha256':prepared['dependency_sha256'],
            'lead_frozen_sha256':prepared.get('lead_frozen_sha256'),
            'expected_sample_ids':[s['sample_id'] for s in prepared['states']],
            'changed_existing_count':len(proof['changed_existing']),'new_instance_count':proof['new_count'],
            'retired_instance_count':len(proof['retired']),'requested_sample_count':len(prepared['states']),'expected_pair_decisions':len(pairs)*len(prepared['states']),
            'pair_count':len(pairs),'pair_sha256':base._digest(pairs),'records':[],
            'adaptive_intersections':[],'collisions':[],'errors':[],'dynamic_sources_regenerated':0,'occ_checks':0,
            'cached_pair_checks':0,'exceptions':[],'continuous_clearance':False,'fabrication_release':False,
            'coverage_scope':prepared['coverage_scope'],
            'tolerances':{'intersection_volume_mm3':VOLUME_TOL,'bbox_reject_mm':BBOX_TOL,'axis_mm':1e-4,
                'source_identity_boolean_mm3':base.VOLUME_TOL,'source_identity_bbox_mm':base.BBOX_TOL,
                'source_identity_adaptive_relative':base.REL_VOLUME_TOL},
            'limitations':['Finite requested poses only; no continuous clearance proof',
                'Unchanged-versus-unchanged pair collisions are outside affected-pair coverage',
                'Bearing fits, preload, thrust, retention and strength remain UNVERIFIED',
                'Section and point probes bound local geometry only; no fabrication release']}
    source_cache={}; pair_cache={}
    def publish():
        report['samples_completed']=len(report['records'])
        report['completed_pair_decisions']=sum(sum(r['counts'].values()) for r in report['records'])
        report['all_requested_pair_decisions_complete']=(report['completed_pair_decisions']==report['expected_pair_decisions'])
        if progress_path is not None:base._write(Path(progress_path),report)
    try:
        report['section_screen']=section_screen(prepared)
        report['s9']=s9_screen(prepared)
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
                    if v > VOLUME_TOL:
                        from adaptive_volume_r07 import measure_shape
                        measured=measure_shape(common,ROOT,a+' / '+b)
                        v=measured['volume_mm3']
                        if not math.isfinite(v) or not math.isfinite(measured['estimated_numerical_margin_mm3']):
                            raise RuntimeError('Nonfinite adaptive intersection volume')
                        report['adaptive_intersections'].append(dict(measured,a=a,b=b,sample_id=state['sample_id']))
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
        ids=[r['sample_id'] for r in report['records']]
        complete=ids==[s['sample_id'] for s in prepared['states']]
        failed=report['collisions'] or any(r['guide_warnings'] for r in report['records'])
        frozen=prepared.get('lead_frozen_sha256') is not None
        report['status']='FAIL' if failed else ('PASS_AFFECTED_FINITE_ONLY' if complete and frozen else 'PASS_BOUNDED_ONLY')
    except Exception as error:
        report['status']='ERROR';report['errors'].append(repr(error))
    report['disk_inputs_unchanged']=all(base._sha(p)==h for p,h in prepared['native_sha256'].items())
    report['dependencies_unchanged']=all(base._sha(ROOT/p)==h for p,h in prepared['dependency_sha256'].items())
    if not report['disk_inputs_unchanged'] or not report['dependencies_unchanged']:
        report['status']='FAIL_INPUT_CHANGED'
    publish()
    return report
