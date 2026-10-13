"""Private native rigid-pair screening of CAD datum/phase assumptions."""
import json, time
from animation_coordination_v2 import PROFILE,trajectory,paper_descriptor_context
from animation_coordination_clearance_v2 import PAIRS
from animation_pose_export import ROOT,snapshot

def run(native):
    import FreeCAD as App
    import leg_motion_r07 as motion
    from sweep_robot_r03 import _bounds,_overlap,_world_copy
    doc=App.openDocument(str(native));before=snapshot(doc);start=time.monotonic()
    config=json.loads((ROOT/'parameters/assembly_r10.json').read_text())
    neutral=json.loads((ROOT/'animation/motion/ax01_r10.json').read_text())['frames'][0]['leg_angles_rad']
    pairs=list(PAIRS)
    for side in ('L','R'):
        pairs.extend([(f'fore{side}_Foot',f'hind{side}_Foot'),(f'fore{side}_FootPad',f'hind{side}_Foot'),(f'fore{side}_Foot',f'hind{side}_FootPad'),(f'fore{side}_FootPad',f'hind{side}_FootPad')])
    names={n for pair in pairs for n in pair};results=[]
    for fore,hind in ((-60,-75),(-60,-90),(-75,-75),(-75,-90),(-90,-90)):
        PROFILE['hip_cad_midpoints_deg']={'fore':fore,'hind':hind};PROFILE['fore_phase_offset_rad']=0.
        worst=0.;hits=[];minimum=1e9
        for degree in range(0,360,6):
            theta,angles,wheel=trajectory('coordinated_spine_legs',degree/72,neutral)
            with paper_descriptor_context():plan=motion.descriptor(doc,theta,angles,wheel,config)
            shapes={n:_world_copy(doc.getObject(n).Shape,doc.getObject(n).LinkPlacement,plan['placements'][n]) for n in names}
            for a,b in pairs:
                if _overlap(_bounds(shapes[a]),_bounds(shapes[b])):
                    v=float(shapes[a].common(shapes[b]).Volume);worst=max(worst,v)
                    if v>1e-5:hits.append({'phase_deg':degree,'a':a,'b':b,'intersection_mm3':v})
                minimum=min(minimum,float(shapes[a].distToShape(shapes[b])[0]))
        row={'fore_mean_deg':fore,'hind_mean_deg':hind,'fore_phase_rad':0,'samples':60,'max_intersection_mm3':worst,'minimum_distance_mm':minimum,'overlaps':hits,'status':'FAIL' if hits else 'PASS_OBSERVED_PAIRS_ONLY'}
        results.append(row);print('CANDIDATE',fore,hind,row['status'],minimum,len(hits),flush=True)
        (ROOT/'reports/animation/coordination_v2_datum_candidates.json').write_text(json.dumps({'results':results,'elapsed_seconds':time.monotonic()-start,'document_unchanged':before==snapshot(doc),'scope':'Observed rigid interference pairs only, 6 degree spacing; no spring or whole assembly claim'},indent=2)+'\n')
        if not hits:break
    App.closeDocument(doc.Name);return results
