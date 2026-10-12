"""Read-only r08 native motion package verification and exact coverage ledger.

Revision-isolated FreeCADCmd partitions are launched by a generated local wrapper.
No GUI, document mutation, native save, fit exemptions or world-shape writes.
Coarse success is a screening gate, not full finite-sample acceptance.
"""
import hashlib
import json
import math
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/verification/r08_motion_partitions'
TMP=ROOT/'reports/tmp/motion_package_r08'
VOLUME_TOL=1e-5
FREEZE=OUT/'freeze.json'
DEPENDENCIES=('verify_motion_package_r08.py','leg_motion_r07.py','robot_pose_r03.py',
              'leg_geometry_r02.py','build_leg_r02.py','spring_wire_r03.py',
              'build_tendon_r03.py','tendon_r03.py','cable_clamps_r07.py',
              'kinematics.py','cad_common.py','spine_attachments_r02.py',
              'leg_mechanics.py','robot_geometry.py',
              'compression_spring_r07.py','spring_normalization_r07.py',
              'spine_frame_r08.py','build_robot_r08.py','controller_carrier_r07.py',
              'sweep_robot_r03.py')


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()

def _write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def capture_freeze(expected_native_sha256):
    """Called only after lead explicitly freezes canonical native SHA."""
    native=ROOT/'cad/flexor_r08_robot.FCStd'
    actual=_sha(native)
    if actual!=expected_native_sha256:raise RuntimeError('Lead-frozen native SHA does not match disk')
    record={'revision':'r08','native_sha256':actual,
            'config_sha256':_sha(ROOT/'parameters/assembly_r08.json'),
            'dependency_sha256':{n:_sha(ROOT/'src'/n) for n in DEPENDENCIES}}
    _write(FREEZE,record)
    return record


def validate_freeze(native=None):
    if not FREEZE.exists():raise RuntimeError('Explicit lead SHA freeze required before CAD checks')
    record=json.loads(FREEZE.read_text());native=Path(native or ROOT/'cad/flexor_r08_robot.FCStd')
    if _sha(native)!=record['native_sha256']:raise RuntimeError('Native changed after lead SHA freeze')
    if _sha(ROOT/'parameters/assembly_r08.json')!=record['config_sha256']:raise RuntimeError('Config changed after freeze')
    if {n:_sha(ROOT/'src'/n) for n in DEPENDENCIES}!=record['dependency_sha256']:
        raise RuntimeError('Motion dependency changed after freeze')
    return record


def manifest(stage='coarse'):
    from leg_motion_r07 import sample_states,pose_states
    if stage not in ('coarse','full'):raise ValueError('stage must be coarse/full')
    config=json.loads((ROOT/'parameters/assembly_r08.json').read_text())
    step=5. if stage=='coarse' else 1.
    samples=[]
    for sample in sample_states(step,10):
        if stage=='full' and sample['label'].startswith(('coordinated_','asymmetric_')):continue
        samples.append(dict(sample,theta=0.,trajectory=sample['label'].rsplit('_',1)[0]))
    if stage=='full':
        # Native sample_states(1,10) changes wheel4.5deg in these paths.
        # Subdivide instead, so EVERY commanded/passive coordinate <=1deg.
        for sample in sample_states(2/9,10):
            if sample['label'].startswith(('coordinated_','asymmetric_')):
                samples.append(dict(sample,theta=0.,trajectory=sample['label'].rsplit('_',1)[0]))
    spine_step=15 if stage=='coarse' else 1
    neutral=pose_states(config=config)['legs']
    for degree in range(0,361,spine_step):
        theta=math.radians(degree)
        angles={tag:(row['angles_rad'][0]+math.radians(5)*math.sin(theta),
                     row['angles_rad'][1]+math.radians(5)*math.sin(theta+(math.pi if row['kind']=='hind' else 0)))
                for tag,row in neutral.items()}
        samples.append({'label':'combined_spine_'+str(degree),'trajectory':'combined_spine_gait',
                        'theta':theta,'leg_angles':angles,
                        'wheel_angle':math.radians(45+45*math.sin(theta))})
    max_step={};previous={}
    for index,sample in enumerate(samples):
        sample['sample_id']=stage+'_'+str(index).zfill(4)
        sample['input_sha256']=_digest({k:sample[k] for k in ('theta','leg_angles','wheel_angle')})
        pose_states(sample['leg_angles'],sample['wheel_angle'],config,positive_terminals=True)
        key=sample['trajectory']
        if key in previous:
            old=previous[key]
            changes=[abs(sample['theta']-old['theta']),abs(sample['wheel_angle']-old['wheel_angle'])]
            changes.extend(abs(a-b) for tag in sample['leg_angles'] for a,b in zip(sample['leg_angles'][tag],old['leg_angles'][tag]))
            max_step[key]=max(max_step.get(key,0),math.degrees(max(changes)))
        previous[key]=sample
    if stage=='full' and max(max_step.values())>1+1e-9:raise AssertionError('Full coordinate steps exceed1deg')
    return {'stage':stage,'states':samples,'count':len(samples),'sha256':_digest(samples),
            'config_sha256':_sha(ROOT/'parameters/assembly_r08.json'),
            'max_coordinate_increment_deg_by_trajectory':max_step,
            'scope':'One-coordinate ±10deg leg ranges; wheel0..90; both coordinated/asymmetric paths; adverse fore/hind combined full spine gait',
            'continuous_clearance':False,'loaded_equilibrium':False,'fabrication_release':False}


def _native_fingerprint(doc):
    """Exact source BRep plus instance placement hash, independent of drawings."""
    sources={};links=[]
    for obj in sorted((o for o in doc.Objects if o.TypeId=='App::Link'),key=lambda o:o.Name):
        src=obj.LinkedObject
        if src.Name not in sources:
            data=src.Shape.exportBrepToString()
            if isinstance(data,str):data=data.encode()
            sources[src.Name]=hashlib.sha256(data).hexdigest()
        links.append({'name':obj.Name,'source':src.Name,'placement':tuple(obj.LinkPlacement.toMatrix().A)})
    data={'sources':sources,'links':links,'motion_map':doc.PoseController.MotionMap,
          'leg_angles':getattr(doc.PoseController,'LegAnglesR03',''),
          'wheel_angle':float(getattr(doc.PoseController,'WheelAngleR07',0))}
    return _digest(data)


def _lower_distance(A,B):
    return math.sqrt(sum(max(0,A[i]-B[i+1],B[i]-A[i+1])**2 for i in (0,2,4)))


def _safety_pairs(names):
    names=set(names)
    frames=[n for n in ('LumbarIntegrated_1','LumbarIntegrated1','Torso_fore','Torso_hind') if n in names]
    shafts=[n for n in ('SyncB1','SyncB2') if n in names]
    controllers=[n for n in ('OpenRB150_Carrier_r07_Instance','OpenRB150_Carrier_r07_BoardEnvelope_Instance') if n in names]
    cables=[n for n in ('HindTendon_L_Cable','HindTendon_R_Cable') if n in names]
    pairs={(min(a,b),max(a,b)) for a in frames for b in shafts+controllers+cables}
    pairs|={(min(a,b),max(a,b)) for a in controllers for b in shafts+cables}
    return sorted(pairs)


def run_partition(stage='coarse',partition=0,partitions=6,native=None):
    import FreeCAD as App
    from leg_motion_r07 import copied_shapes
    from sweep_robot_r03 import _bounds,_overlap
    start=time.monotonic();native=Path(native or ROOT/'cad/flexor_r08_robot.FCStd')
    freeze=validate_freeze(native)
    config=json.loads((ROOT/'parameters/assembly_r08.json').read_text())
    plan=manifest(stage);states=plan['states'][partition::partitions]
    output=OUT/(stage+'_part_'+str(partition)+'.json')
    report={'status':'RUNNING','stage':stage,'partition':partition,'partitions':partitions,
            'freeze_sha256':_sha(FREEZE),'native_path':str(native),'native_sha256':_sha(native),'config_sha256':_sha(ROOT/'parameters/assembly_r08.json'),
            'dependency_sha256':{n:_sha(ROOT/'src'/n) for n in DEPENDENCIES},
            'manifest_sha256':plan['sha256'],'expected_sample_ids':[s['sample_id'] for s in states],
            'samples_total':len(states),'samples_completed':0,'records':[],'baseline_overlaps':[],
            'overlaps':[],'errors':[],'minimum_observed_distances':[],'occ_checks':0,
            'distance_checks':0,'cached_pair_checks':0,'continuous_clearance':False,
            'loaded_equilibrium':False,'fabrication_release':False,'volume_tolerance_mm3':VOLUME_TOL}
    shape_cache={};pair_cache={};distance_min={};worst={};doc=None
    def publish():
        report['elapsed_seconds']=time.monotonic()-start
        report['overlaps']=sorted(worst.values(),key=lambda r:-r['intersection_mm3'])
        report['minimum_observed_distances']=list(distance_min.values())
        _write(output,report)
    def inspect(shapes,placement_plan,sample,baseline=False):
        names=sorted(shapes);bounds={n:_bounds(shapes[n]) for n in names}
        request_keys={n:_digest(r) for n,r in placement_plan['shape_requests'].items()}
        placements=placement_plan['placements'];rows=[]
        signatures={n:(request_keys.get(n,'native:'+doc.getObject(n).LinkedObject.Name),
                       tuple(placements[n].toMatrix().A),bounds[n]) for n in names}
        for i,A in enumerate(names):
            for B in names[i+1:]:
                if not _overlap(bounds[A],bounds[B]):continue
                key=(A,B,signatures[A],signatures[B])
                if key in pair_cache:
                    volume=pair_cache[key];report['cached_pair_checks']+=1
                else:
                    volume=float(shapes[A].common(shapes[B]).Volume)
                    report['occ_checks']+=1;pair_cache[key]=volume
                if volume>VOLUME_TOL:
                    row={'a':A,'b':B,'intersection_mm3':volume,'sample_id':sample['sample_id'],'input':sample}
                    rows.append(row)
                    if not baseline and volume>worst.get((A,B),{}).get('intersection_mm3',0):worst[(A,B)]=row
        for A,B in _safety_pairs(names):
            key=A+'::'+B
            if key in distance_min and _lower_distance(bounds[A],bounds[B])>=distance_min[key]['distance_mm']:continue
            distance=float(shapes[A].distToShape(shapes[B])[0]);report['distance_checks']+=1
            if distance<distance_min.get(key,{}).get('distance_mm',math.inf):
                distance_min[key]={'a':A,'b':B,'distance_mm':distance,'sample_id':sample['sample_id'],
                                   'input':sample,'scope':'Minimum over declared finite samples; AABB lower bounds prune only impossible improvements'}
        return rows
    try:
        doc=App.openDocument(str(native));report['instances']=len([o for o in doc.Objects if o.TypeId=='App::Link'])
        if report['instances']!=486:raise ValueError('Expected486 actual r08 instances')
        report['geometry_sha256_before']=_native_fingerprint(doc)
        baseline={'sample_id':'neutral_baseline','theta':0.,'wheel_angle':0.,'leg_angles':{},'label':'neutral_baseline'}
        shapes,pp=copied_shapes(doc,config=config,cache=shape_cache)
        report['baseline_overlaps']=inspect(shapes,pp,baseline,True)
        if report['baseline_overlaps']:
            report['status']='FAIL_BASELINE';publish();return report
        report['baseline_status']='PASS';publish()
        for sample in states:
            record={'sample_id':sample['sample_id'],'input_sha256':sample['input_sha256'],'input':sample,'status':'RUNNING'}
            try:
                shapes,pp=copied_shapes(doc,sample['theta'],sample['leg_angles'],sample['wheel_angle'],config,cache=shape_cache)
                overlaps=inspect(shapes,pp,sample)
                record['status']='FAIL_COLLISION' if overlaps else 'PASS'
                record['overlap_pairs']=len(overlaps);record['valid_single_solids']=len(shapes)
                record['guide_warnings']=pp['guide_warnings']
                if pp['guide_warnings']:record['status']='FAIL_GUIDE_TRAVEL'
            except Exception as error:
                record['status']='ERROR';record['error']=repr(error);report['errors'].append(record.copy())
            report['records'].append(record);report['samples_completed']+=1;publish()
            if stage=='coarse' and record['status']!='PASS':break
        report['status']='PASS' if len(report['records'])==len(states) and all(r['status']=='PASS' for r in report['records']) else 'FAIL'
    except Exception as error:
        report['status']='ERROR';report['errors'].append({'error':repr(error)})
    finally:
        if doc is not None:
            report['geometry_sha256_after']=_native_fingerprint(doc)
            report['document_unchanged']=report['geometry_sha256_before']==report['geometry_sha256_after']
            if not report['document_unchanged']:report['status']='FAIL_MUTATION'
        report['native_sha256_after']=_sha(native)
        report['native_file_unchanged']=report['native_sha256']==report['native_sha256_after']
        if not report['native_file_unchanged']:report['status']='FAIL_NATIVE_CHANGED_DURING_RUN'
        try:validate_freeze(native)
        except Exception as error:
            report['status']='FAIL_FREEZE_CHANGED';report['errors'].append({'error':repr(error)})
        publish()
    print('MOTION_PARTITION',stage,partition,report['status'],report['samples_completed'],report['samples_total'],flush=True)
    return report


def collect(stage='coarse',partitions=6):
    plan=manifest(stage);paths=[OUT/(stage+'_part_'+str(i)+'.json') for i in range(partitions)]
    reports=[json.loads(p.read_text()) for p in paths if p.exists()]
    expected=[s['sample_id'] for s in plan['states']];completed=[r['sample_id'] for p in reports for r in p['records']]
    coherent_keys=('native_sha256','geometry_sha256_before','config_sha256','manifest_sha256','freeze_sha256')
    coherent={k:len({p.get(k) for p in reports})==1 for k in coherent_keys}
    coherent['dependencies']=len({_digest(p.get('dependency_sha256',{})) for p in reports})==1
    coherent['current_freeze']=all(p.get('freeze_sha256')==_sha(FREEZE) for p in reports) if FREEZE.exists() else False
    out={'stage':stage,'status':'NOT_RUN' if not reports else 'INCOMPLETE','partitions_expected':partitions,
         'partitions_found':len(reports),'samples_expected':len(expected),'records_found':len(completed),
         'missing_sample_ids':sorted(set(expected)-set(completed)),
         'duplicate_sample_ids':sorted(n for n in set(completed) if completed.count(n)>1),
         'failed_records':[r for p in reports for r in p['records'] if r['status']!='PASS'],
         'partition_statuses':{str(p['partition']):p['status'] for p in reports},
         'hash_coherence':coherent,'baseline_overlaps':[r for p in reports for r in p['baseline_overlaps']],
         'manifest':plan,'continuous_clearance':False,'loaded_equilibrium':False,'fabrication_release':False}
    if reports:out.update({k:reports[0].get(k) for k in coherent_keys})
    if len(reports)==partitions and all(p['status'] in ('PASS','FAIL','ERROR','FAIL_BASELINE','FAIL_MUTATION','FAIL_NATIVE_CHANGED_DURING_RUN','FAIL_FREEZE_CHANGED') for p in reports):
        out['status']='PASS' if not out['missing_sample_ids'] and not out['duplicate_sample_ids'] and not out['failed_records'] and not out['baseline_overlaps'] and all(coherent.values()) and all(p['status']=='PASS' for p in reports) else 'FAIL'
    _write(OUT/(stage+'_summary.json'),out);return out


def prepare_launch(stage='coarse',partitions=6):
    """Write isolated CLI wrappers and a bounded partition-count launcher."""
    TMP.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    if stage not in ('coarse','full') or not isinstance(partitions,int) or not 1<=partitions<=24:
        raise ValueError('Expected coarse/full and1..24 partitions')
    wrappers=[]
    for i in range(partitions):
        p=TMP/(stage+'_part_'+str(i)+'.py')
        p.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT/'src'))+')\nfrom verify_motion_package_r08 import run_partition\nrun_partition('+repr(stage)+','+str(i)+','+str(partitions)+')\n')
        wrappers.append(str(p))
    launcher=TMP/('launch_'+stage+'.py')
    gate=('import sys\nsys.path.insert(0,'+repr(str(ROOT/'src'))+')\nfrom verify_motion_package_r08 import validate_freeze,collect\nvalidate_freeze()\nassert collect("coarse",6)["status"]=="PASS","Full verification requires coherent coarse PASS"\n' if stage=='full' else '')
    launcher.write_text(gate+'import subprocess\nfrom pathlib import Path\nwrappers='+repr(wrappers)+'\nchildren=[]\nfor wrapper in wrappers:\n log=open(str(Path(wrapper).with_suffix(".log")),"w")\n children.append(subprocess.Popen(["/snap/bin/freecad.cmd",wrapper],stdout=log,stderr=subprocess.STDOUT))\nfor child in children:child.wait()\n')
    _write(OUT/(stage+'_manifest.json'),manifest(stage))
    return launcher


def run_cage_spine(native=None):
    """361 integer spine phases, actual cage copies against all other solids.

    Neutral leg coordinates and wheel are held fixed. No pair exemptions;
    AABB disjointness is the only geometric broadphase. Both cage halves are
    checked against each other as well as all 484 other physical instances.
    """
    import FreeCAD as App
    from leg_motion_r07 import copied_shapes
    from sweep_robot_r03 import _bounds,_overlap
    start=time.monotonic();native=Path(native or ROOT/'cad/flexor_r08_robot.FCStd')
    freeze=validate_freeze(native);output=OUT/'cage_spine_361.json'
    config=json.loads((ROOT/'parameters/assembly_r08.json').read_text())
    report={'status':'RUNNING','revision':'r08','native_sha256':_sha(native),
            'config_sha256':freeze['config_sha256'],'dependency_sha256':freeze['dependency_sha256'],
            'freeze_sha256':_sha(FREEZE),'samples_expected':361,'samples_completed':0,
            'scope':'Both actual half-cages vs every other physical instance including each other; integer spine phases0..360; legs/wheel neutral',
            'exceptions':[],'volume_tolerance_mm3':VOLUME_TOL,'occ_checks':0,'cached_pair_checks':0,
            'records':[],'worst_pair':None,'overlaps':[],'errors':[],
            'continuous_clearance':False,'loaded_equilibrium':False,'fabrication_release':False}
    doc=None;shape_cache={};pair_cache={};worst={}
    def publish():
        report['elapsed_seconds']=time.monotonic()-start
        report['overlaps']=sorted(worst.values(),key=lambda r:-r['intersection_mm3'])
        _write(output,report)
    try:
        doc=App.openDocument(str(native));report['geometry_sha256_before']=_native_fingerprint(doc)
        cage_names=('LumbarIntegrated1','LumbarIntegrated_1')
        for degree in range(361):
            shapes,pp=copied_shapes(doc,math.radians(degree),wheel_angle=0.,config=config,cache=shape_cache)
            if len(shapes)!=486:raise ValueError('Expected486 actual native physical instances')
            if not set(cage_names)<=set(shapes):raise ValueError('Two half-cage instances absent')
            report['instances']=len(shapes)
            pairs=sorted({tuple(sorted((c,n))) for c in cage_names for n in shapes if n!=c})
            report['pairs_per_angle']=len(pairs)
            bounds={n:_bounds(shapes[n]) for n in shapes};collisions=0
            signatures={n:(tuple(pp['placements'][n].toMatrix().A),bounds[n],
                           _digest(pp['shape_requests'].get(n,{'native_source':doc.getObject(n).LinkedObject.Name}))) for n in shapes}
            for A,B in pairs:
                if not _overlap(bounds[A],bounds[B]):continue
                key=(A,B,signatures[A],signatures[B])
                if key in pair_cache:
                    volume=pair_cache[key];report['cached_pair_checks']+=1
                else:
                    volume=float(shapes[A].common(shapes[B]).Volume)
                    pair_cache[key]=volume;report['occ_checks']+=1
                row={'a':A,'b':B,'intersection_mm3':volume,'spine_angle_deg':degree}
                if report['worst_pair'] is None or volume>report['worst_pair']['intersection_mm3']:
                    report['worst_pair']=row
                if volume>VOLUME_TOL:
                    collisions+=1
                    if volume>worst.get((A,B),{}).get('intersection_mm3',0):worst[(A,B)]=row
            report['records'].append({'spine_angle_deg':degree,'status':'FAIL_COLLISION' if collisions else 'PASS',
                                      'overlap_pairs':collisions,'valid_single_solids':len(shapes)})
            report['samples_completed']+=1;publish()
        report['status']='FAIL_COLLISION' if worst else 'PASS'
    except Exception as error:
        report['status']='ERROR';report['errors'].append({'error':repr(error)})
    finally:
        if doc is not None:
            report['geometry_sha256_after']=_native_fingerprint(doc)
            report['document_unchanged']=report['geometry_sha256_before']==report['geometry_sha256_after']
            if not report['document_unchanged']:report['status']='FAIL_MUTATION'
        report['native_file_unchanged']=report['native_sha256']==_sha(native)
        try:validate_freeze(native)
        except Exception as error:
            report['status']='FAIL_FREEZE_CHANGED';report['errors'].append({'error':repr(error)})
        publish()
    return report


def prepare_cage_launch():
    TMP.mkdir(parents=True,exist_ok=True)
    wrapper=TMP/'cage_spine_361.py'
    wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT/'src'))+')\nfrom verify_motion_package_r08 import run_cage_spine\nrun_cage_spine()\n')
    return wrapper
