"""Larger explicit leg articulation using the existing CAD motion/export APIs.

The v1 mechanical APIs and their pinned source files stay unchanged. Only the
prescribed presentation trajectory differs. All outputs extend the AX01 schema.
"""
from pathlib import Path
import json,math,gzip,time,hashlib
import animation_production_export as base
from animation_pose_export import ROOT,serial,digest,snapshot
from animation_production_validate import validate_frame,validate

PROFILE_PATH=ROOT/'animation/coordination_paper_profile_v2.json'
PROFILE=json.loads(PROFILE_PATH.read_text())
AMPLITUDE_DEG=math.degrees(PROFILE['hip_half_excursion_rad'])

def trajectory(name,t,neutral):
    if name=='active_spine_mechanism':return base.trajectory(name,t,neutral)
    cycle=math.tau*PROFILE['presentation_frequency_hz']*t
    phase=cycle+PROFILE['spine_phase_origin_rad'];lag=PROFILE['hind_backswing_lag_rad']
    angles={}
    for tag,q in neutral.items():
        offset=PROFILE['fore_phase_offset_rad'] if tag.startswith('fore') else 0.
        signal=math.cos(cycle-lag+offset)
        kind='fore' if tag.startswith('fore') else 'hind'
        angles[tag]=[math.radians(PROFILE['hip_cad_midpoints_deg'][kind])-PROFILE['hip_half_excursion_rad']*signal,
                     q[1]+math.radians(PROFILE['knee_half_excursion_deg'])*signal]
    wheel=math.radians(45+45*math.cos(cycle-lag))
    return phase,angles,wheel


def paper_descriptor_context():
    """Scoped override of demonstration bounds, not mechanical joint geometry.

    Existing +/-15deg candidate limits were numerical screening intervals, not
    manufacturer hard stops. User now requests larger source-informed motion.
    Native screening and numeric checks replace any assumption of prior range
    clearance. Source motion code and canonical controller remain unchanged.
    """
    import contextlib,leg_motion_r07 as motion
    @contextlib.contextmanager
    def context():
        original=motion.pose_states
        def expanded(*args,**kwargs):
            kwargs['enforce_candidates']=False
            return original(*args,**kwargs)
        motion.pose_states=expanded
        try:yield
        finally:motion.pose_states=original
    return context()


def run(doc):
    start=time.monotonic();before=snapshot(doc)
    baseline=json.loads((ROOT/'animation/motion/production_r10.json').read_text())
    assert digest((ROOT/baseline['source']['cad_path']).read_bytes())==baseline['source']['cad_sha256']
    config=json.loads((ROOT/'parameters/assembly_r10.json').read_text())
    effective={n:row['motion'] for n,row in baseline['production']['component_metadata'].items()}
    instances={x['instance_id']:x for x in baseline['instances']}
    neutral=baseline['frames'][0]['leg_angles_rad'];path=ROOT/'animation/motion/coordinated_spine_legs_v2_r10.jsonl.gz'
    original_trajectory=base.trajectory;previous=first=None;worst_anchor=0.
    # The serializer's only trajectory input is its module callback. Replace
    # it privately for this exclusive read-only sampling job and restore it in
    # finally. No document/source-code/solver state is modified.
    base.trajectory=trajectory
    context=paper_descriptor_context();context.__enter__()
    try:
        with path.open('wb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as stream:
                for i in range(1201):
                    frame=base._frame(doc,'coordinated_spine_legs',i,60,neutral,effective,baseline['instance_order'],previous,config)
                    worst_anchor=max(worst_anchor,validate_frame(frame,instances,previous));stream.write(serial(frame)+b'\n')
                    if first is None:first=frame
                    previous=frame
                    if i%120==0:print('COORDINATION_V2_SAMPLE',i,round(time.monotonic()-start,1),flush=True)
    finally:
        context.__exit__(None,None,None);base.trajectory=original_trajectory
    assert before==snapshot(doc)
    data=json.loads(json.dumps(baseline));production=data['production'];production['extension_version']='AX2-2-coordination'
    production['source_files_sha256']['src/animation_coordination_v2.py']=digest(Path(__file__).read_bytes())
    production['source_files_sha256'][str(PROFILE_PATH.relative_to(ROOT))]=digest(PROFILE_PATH.read_bytes())
    production['paper_motion_profile']=PROFILE
    loop=max(abs(a-b) for M,N in zip(first['transforms_mm'],previous['transforms_mm']) for r,s in zip(M,N) for a,b in zip(r,s))
    production['timelines']['coordinated_spine_legs'].update(path=str(path.relative_to(ROOT)),sha256=digest(path.read_bytes()),
        leg_motion='S27 plot-informed hip +/-0.6rad; separately prescribed knees +/-10deg; paired fore/hind hip signals share phase in existing same-direction coordinates; hind backswing event lag pi/10',
        amplitude_deg=AMPLITUDE_DEG,loop_matrix_max_error=loop,anchor_max_error_mm=worst_anchor,
        clearance_evidence='reports/animation/coordination_v2_clearance.json; bounded native screening only, not the prior full campaign')
    production['trajectory_regression']={'status':'NEW_PRESCRIBED_TRAJECTORY','change':'paper-informed hip excursion and event-calibrated spine/hind phase; passive knees remain prescribed','prior_full_campaign_reused_for_new_combined_path':False}
    production['procedural_native_examples']='v1 examples validate native/render generator structure; v2 example comparison recorded separately'
    production['limitations'].append('New source-informed trajectory exceeds historical candidate motion intervals; only bounded native screening supports this visualization.')
    out=ROOT/'animation/motion/production_coordination_v2_r10.json';out.write_bytes(serial(data));report=validate(out)
    report.update(elapsed_seconds=time.monotonic()-start,amplitude_deg=AMPLITUDE_DEG,document_unchanged=True,native_file_unchanged=True)
    (ROOT/'reports/animation/production_coordination_v2.json').write_text(json.dumps(report,indent=2)+'\n');return report


def screen_clearance(native,phases=(0,18,90,135,180,198,240,270,330)):
    """Bounded exact native leg/tendon vs all-member intersections, no GUI/save."""
    import FreeCAD as App
    import leg_motion_r07 as motion
    from sweep_robot_r03 import _bounds,_overlap
    start=time.monotonic();native=Path(native);doc=App.openDocument(str(native));before=snapshot(doc)
    cadsha=digest(native.read_bytes());config=json.loads((ROOT/'parameters/assembly_r10.json').read_text())
    neutral=json.loads((ROOT/'animation/motion/ax01_r10.json').read_text())['frames'][0]['leg_angles_rad']
    out=ROOT/'reports/animation/coordination_v2_clearance.json';cache={};records=[];occ=0
    report={'status':'RUNNING','native_sha256':cadsha,'profile_sha256':digest(PROFILE_PATH.read_bytes()),'profile':PROFILE,'amplitude_deg':AMPLITUDE_DEG,'phase_samples_deg':list(phases),
        'scope':'Every unordered pair with a leg/tendon member; exact native regenerated solids at listed phases only',
        'continuous_clearance':False,'full_campaign':False,'loaded_equilibrium':False,'records':records}
    for degree in phases:
        theta,angles,wheel=trajectory('coordinated_spine_legs',degree/(360*.2),neutral)
        with paper_descriptor_context():
            shapes,plan=motion.copied_shapes(doc,theta,angles,wheel,config,cache)
        names=sorted(shapes);bounds={n:_bounds(shapes[n]) for n in names};moving={n for n in names if n.startswith(('foreL_','foreR_','hindL_','hindR_','HindTendon'))}
        overlaps=[]
        for i,a in enumerate(names):
            for b in names[i+1:]:
                if a not in moving and b not in moving:continue
                if not _overlap(bounds[a],bounds[b]):continue
                volume=float(shapes[a].common(shapes[b]).Volume);occ+=1
                if volume>1e-5:overlaps.append({'a':a,'b':b,'intersection_mm3':volume})
        records.append({'phase_deg':degree,'status':'FAIL' if overlaps or plan['guide_warnings'] else 'PASS','overlaps':overlaps,'guide_warnings':plan['guide_warnings'],'physical_instances':len(shapes)})
        report.update(elapsed_seconds=time.monotonic()-start,occ_checks=occ);out.write_text(json.dumps(report,indent=2)+'\n');print('V2_CLEARANCE',degree,records[-1]['status'],len(overlaps),flush=True)
        if overlaps or plan['guide_warnings']:break
    report.update(status='PASS_BOUNDED_NATIVE_SAMPLES' if len(records)==len(phases) and all(x['status']=='PASS' for x in records) else 'FAIL',
        document_unchanged=before==snapshot(doc),native_file_unchanged=cadsha==digest(native.read_bytes()),elapsed_seconds=time.monotonic()-start,occ_checks=occ)
    assert report['document_unchanged'] and report['native_file_unchanged'];out.write_text(json.dumps(report,indent=2)+'\n');App.closeDocument(doc.Name);return report
