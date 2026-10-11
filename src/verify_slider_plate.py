"""Read actual slider supports, bearing axes and axial capture from native CAD."""
import FreeCAD as App,json,math
from pathlib import Path
from kinematics import load_parameters,spine
ROOT=Path(__file__).resolve().parents[1]

def run(doc):
    p=load_parameters(ROOT/'parameters/candidate_r02.json');s=spine(0,p)
    frames=[o for o in doc.Objects if o.TypeId=='App::Link' and o.Name.startswith('LumbarIntegrated')]
    mm=json.loads(doc.PoseController.MotionMap);errors=[];distances=[]
    for frame in frames:
        side=1 if frame.LinkPlacement.Base.y>0 else -1
        sk=next(o for o in frame.LinkedObject.Group if o.Name.startswith('GuideBossProfiles'))
        circles=[g for g in sk.Geometry if hasattr(g,'Radius') and abs(g.Radius-2.025)<1e-7]
        for i in [1,2]:
            expected=s[f'A{i}']
            g=min(circles,key=lambda g:math.dist((g.Center.x,g.Center.y),expected))
            P=frame.LinkPlacement.multVec(sk.Placement.multVec(g.Center))
            errors.append(math.dist((P.x,P.z),expected))
            pref=f'A{i}_'+str(side).replace('-','_')
            bearing=doc.getObject(pref+'_OuterBearing');pin=doc.getObject(pref+'_Pin')
            errors.append(math.dist((bearing.LinkPlacement.Base.x,bearing.LinkPlacement.Base.z),expected))
            distances.append({'parts':[frame.Name,bearing.Name],'gap_mm':frame.Shape.distToShape(bearing.Shape)[0]})
        for i in [1,2]:
            pref=f'C{i}_'+str(side).replace('-','_')
            washer=doc.getObject(pref+'_CaptureWasher');roller=doc.getObject(pref+'_Bearing2')
            distances.append({'parts':[frame.Name,washer.Name],'gap_mm':frame.Shape.distToShape(washer.Shape)[0]})
            # Liner names use the signed original builder convention.
            liners=[o for o in doc.Objects if o.TypeId=='App::Link' and o.Name.startswith(f'GuideLiner{i}_'+str(side).replace('-','_')+'_')]
            for liner in liners:
                distances.append({'parts':[liner.Name,roller.Name],'gap_mm':liner.Shape.distToShape(roller.Shape)[0]})
    samples=[spine(j*math.tau/14400,p) for j in range(14401)]
    ranges={f'C{i}':[min(q[f'C{i}'][0] for q in samples),max(q[f'C{i}'][0] for q in samples)] for i in [1,2]}
    reserves={k:(p['guide_slot_travel_mm']-(hi-lo))/2 for k,(lo,hi) in ranges.items()}
    r={'scope':'r02 corrected fixed slider plates; actual native neutral interfaces and 0.025deg mathematical track sampling',
       'status':'PASS' if max(errors)<1e-4 and all(v>0 for v in reserves.values()) and all(d['gap_mm']>0 for d in distances) and not any(f.Name in mm for f in frames) else 'FAIL',
       'fixed_A_axis_error_mm':max(errors),'fixed_frame_motion_entries':sum(f.Name in mm for f in frames),
       'native_neutral_distances':distances,'C_ranges_mm':ranges,'minimum_center_travel_end_reserve_mm':reserves,
       'washer_radial_overlap_mm':(p['guide_capture_washer_od_mm']-p['guide_slot_width_mm'])/2,
       'limits':'Distances apply to neutral only. End reserves use sampled extrema, not a continuous proof. Supplier fits, liner retention method, stiffness and wear are unresolved.'}
    (ROOT/'reports/verification/r02_slider_plate_interfaces.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r));return r
