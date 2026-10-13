"""Exact native checks of observed rigid clip/cap clashes at every video phase."""
import json,time
from pathlib import Path
from animation_coordination_v2 import trajectory,paper_descriptor_context,PROFILE
from animation_pose_export import ROOT,digest,snapshot
PAIRS=(('A2_1_CaptureCap','hindL_K_Clip0'),('A2_1_CaptureCap','hindL_O1_Clip0'),
       ('A2__1_CaptureCap','hindR_K_Clip1'),('A2__1_CaptureCap','hindR_O1_Clip1'))
PAIRS=PAIRS+tuple((f'fore{side}_{a}',f'hind{side}_{b}') for side in ('L','R') for a in ('Foot','FootPad') for b in ('Foot','FootPad'))
def run(native):
    import FreeCAD as App
    import leg_motion_r07 as motion
    from sweep_robot_r03 import _bounds,_overlap,_world_copy
    start=time.monotonic();native=Path(native);doc=App.openDocument(str(native));before=snapshot(doc)
    config=json.loads((ROOT/'parameters/assembly_r10.json').read_text());neutral=json.loads((ROOT/'animation/motion/ax01_r10.json').read_text())['frames'][0]['leg_angles_rad']
    report={'status':'RUNNING','pairs':PAIRS,'profile':PROFILE,'profile_sha256':digest((ROOT/'animation/coordination_paper_profile_v2.json').read_bytes()),'native_sha256':digest(native.read_bytes()),'samples':0,'overlaps':[],'scope':'Observed rigid clip/cap and fore/hind foot pairs at all 300 integer render phases; other pairs bounded separately','continuous_clearance':False}
    out=ROOT/'reports/animation/coordination_v2_observed_pairs_300.json';worst=0.
    for i in range(300):
        theta,angles,wheel=trajectory('coordinated_spine_legs',i/60,neutral)
        with paper_descriptor_context():plan=motion.descriptor(doc,theta,angles,wheel,config)
        shapes={n:_world_copy(doc.getObject(n).Shape,doc.getObject(n).LinkPlacement,plan['placements'][n]) for n in {n for pair in PAIRS for n in pair}}
        for a,b in PAIRS:
            if _overlap(_bounds(shapes[a]),_bounds(shapes[b])):
                volume=float(shapes[a].common(shapes[b]).Volume);worst=max(worst,volume)
                if volume>1e-5:report['overlaps'].append({'sample':i,'phase_deg':i*1.2,'a':a,'b':b,'intersection_mm3':volume})
        report['samples']=i+1
        if i%30==0:out.write_text(json.dumps(report,indent=2)+'\n');print('OBSERVED_PAIRS',i,len(report['overlaps']),flush=True)
    report.update(status='PASS' if not report['overlaps'] else 'FAIL',max_intersection_mm3=worst,document_unchanged=before==snapshot(doc),native_file_unchanged=report['native_sha256']==digest(native.read_bytes()),elapsed_seconds=time.monotonic()-start)
    out.write_text(json.dumps(report,indent=2)+'\n');App.closeDocument(doc.Name);return report
