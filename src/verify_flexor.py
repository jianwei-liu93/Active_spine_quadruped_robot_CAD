"""Revision-specific evidence from actual r02 FreeCAD objects; lead-only snapshots."""
import FreeCAD as App, Part
import math,json,time
from pathlib import Path
import build_flexor as bf
from kinematics import load_parameters,spine
ROOT=Path(__file__).resolve().parents[1]

def native_checks(doc):
    p=load_parameters(ROOT/'parameters/candidate_r02.json');s=spine(doc.PoseController.SpinePhaseRad,p)
    rows=[];err=[]
    for o in doc.Objects:
        if o.TypeId=='App::Link':
            sh=o.Shape
            rows.append({'instance':o.Name,'part':o.LinkedObject.Name,'valid':sh.isValid(),'solid_count':len(sh.Solids),'volume_mm3':sh.Volume})
    for name,m in json.loads(doc.PoseController.MotionMap).items():
        if m['kind']!='segment':continue
        o=doc.getObject(name);w=m['width'];T=m['thickness'];L=math.dist(s[m['a']],s[m['b']])
        P=o.LinkPlacement.multVec(App.Vector(w/2,w/2,T/2));Q=o.LinkPlacement.multVec(App.Vector(L+w/2,w/2,T/2))
        for X,key in [(P,m['a']),(Q,m['b'])]:err.append(math.dist((X.x,X.z),s[key]))
    box=App.BoundBox()
    for o in doc.Objects:
        if o.TypeId=='App::Link':box.add(o.Shape.BoundBox)
    r={'revision':'r02','scope':'spine only','status':'PASS' if all(x['valid'] and x['solid_count']==1 and x['volume_mm3']>0 for x in rows) and max(err)<1e-4 else 'FAIL','parts':rows,'editable_bodies':len([o for o in doc.Objects if o.TypeId=='PartDesign::Body']),'fully_constrained_sketches':all(o.FullyConstrained for o in doc.Objects if o.TypeId=='Sketcher::SketchObject'),'actual_native_joint_max_error_mm':max(err),'joint_tolerance_mm':1e-4,'envelope_mm':[box.XLength,box.YLength,box.ZLength],'limits':'Source morphology, physical clearance and supplier interface verification are separate gates.'}
    (ROOT/'reports/verification/r02_native.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='parts'}));return r

def view_evidence(doc):
    import FreeCADGui as Gui
    p=load_parameters(ROOT/'parameters/candidate_r02.json');ss=[spine(i*math.tau/1440,p) for i in range(1440)]
    imin=min(range(1440),key=lambda j:ss[j]['beta1']-ss[j]['beta2']);imax=max(range(1440),key=lambda j:ss[j]['beta1']-ss[j]['beta2'])
    # Save mathematical extrema without claiming anatomical flexion/extension calibration.
    extrema={}
    for key,fun in [('output1_min',lambda s:s['beta1']),('output1_max',lambda s:-s['beta1']),('neutral',lambda s:abs(s['G'][1]))]:
        j=min(range(1440),key=lambda x:fun(ss[x]));theta=0 if key=='neutral' else j*math.tau/1440
        bf.pose(doc,theta,p);v=Gui.activeDocument().activeView();v.viewFront();v.fitAll();v.setCamera(__import__('re').sub(r'height [0-9.eE+-]+','height 80',v.getCamera()))
        path=ROOT/f'reports/views/r02_{key}_side.png';v.saveImage(str(path),1500,1000,'White');extrema[key]={'theta_rad':theta,'file':str(path.relative_to(ROOT))}
    bf.pose(doc,0,p)
    for key,method in [('top','viewTop'),('front','viewRight'),('isometric','viewAxonometric'),('opposite_side','viewRear')]:
        v=Gui.activeDocument().activeView();getattr(v,method)();v.fitAll();v.setCamera(__import__('re').sub(r'height [0-9.eE+-]+','height 100',v.getCamera()));v.saveImage(str(ROOT/f'reports/views/r02_spine_{key}.png'),1500,1000,'White')
    (ROOT/'reports/verification/r02_view_poses.json').write_text(json.dumps(extrema,indent=2)+'\n');doc.save();return extrema

def snapshot(doc):
    """Read once on GUI thread. Returned independent shapes are background-safe."""
    return {o.Name:(o.Shape.copy(),o.LinkedObject.Name) for o in doc.Objects if o.TypeId=='App::Link'}

def scan_shapes(shapes,path):
    start=time.time();pairs=[];names=list(shapes);narrow=0
    for i,a in enumerate(names):
        sa=shapes[a][0];ba=sa.BoundBox
        for z in names[i+1:]:
            sz=shapes[z][0];bz=sz.BoundBox
            dims=[min(getattr(ba,k+'Max'),getattr(bz,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bz,k+'Min')) for k in ['X','Y','Z']]
            if min(dims)<=1e-6:continue
            narrow+=1;v=sa.common(sz).Volume
            if v>1e-5:pairs.append({'a':a,'b':z,'intersection_mm3':v})
    r={'revision':'r02','scope':'actual native neutral spine','status':'FAIL' if pairs else 'PASS','raw_overlaps':sorted(pairs,key=lambda x:-x['intersection_mm3']),'instances':len(names),'narrowphase':narrow,'volume_tolerance_mm3':1e-5,'exceptions':'None applied','elapsed_seconds':time.time()-start}
    Path(path).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='raw_overlaps'}));print(json.dumps(r['raw_overlaps'][:35],indent=2));return r

def sweep_snapshot(doc):
    data=snapshot(doc)
    placements={o.Name:o.LinkPlacement for o in doc.Objects if o.TypeId=='App::Link'}
    return data,placements,json.loads(doc.PoseController.MotionMap)

def sweep(data,placements,motion,step_deg=1):
    """Independent shape copies only. No document/GUI mutation; safe async."""
    from cad_common import line_place,hardware_place,plane_placement
    p=load_parameters(ROOT/'parameters/candidate_r02.json');names=list(data);start=time.time();hits={};worst=0;poses=round(360/step_deg)+1;pairtests=0
    # Different instances sharing a source still have independent placements.
    for j in range(poses):
        theta=j*math.tau/(poses-1);s=spine(theta,p);shapes={}
        for n,(sh,source) in data.items():
            new=placements[n]
            if n in motion:
                m=motion[n];k=m['kind']
                if k=='segment':new=line_place(s[m['a']],s[m['b']],m['y'],m['width'],m['thickness'])
                elif k=='point':new=hardware_place(s[m['point']],m['y'],m['length'])
                elif k=='axialrot':new=plane_placement(s[m['point']],m['y']+m['length']/2,theta)
            delta=new.multiply(placements[n].inverse());cop=sh.copy();cop.Placement=delta.multiply(sh.Placement);shapes[n]=cop
        bounds={n:sh.BoundBox for n,sh in shapes.items()}
        for k,a in enumerate(names):
            ba=bounds[a]
            for z in names[k+1:]:
                if a not in motion and z not in motion:continue # fixed/fixed passed raw neutral scan
                bz=bounds[z];ds=[min(getattr(ba,q+'Max'),getattr(bz,q+'Max'))-max(getattr(ba,q+'Min'),getattr(bz,q+'Min')) for q in ['X','Y','Z']]
                if min(ds)<=1e-6:continue
                pairtests+=1;v=shapes[a].common(shapes[z]).Volume
                if v>1e-5:
                    key=a+'|'+z;old=hits.get(key)
                    if old is None or v>old['intersection_mm3']:hits[key]={'a':a,'b':z,'theta_deg':theta*180/math.pi,'intersection_mm3':v}
                    worst=max(worst,v)
        if j%30==0:
            (ROOT/'reports/verification/r02_sweep_progress.json').write_text(json.dumps({'poses_done':j+1,'poses_planned':poses,'pair_violations_so_far':len(hits),'elapsed_seconds':time.time()-start})+'\n')
    r={'revision':'r02','scope':'spine only; shape transforms from actual native neutral solids','status':'FAIL' if hits else 'PASS','samples':poses,'step_deg':step_deg,'narrowphase_tests':pairtests,'volume_tolerance_mm3':1e-5,'pair_violations':sorted(hits.values(),key=lambda x:-x['intersection_mm3']),'elapsed_seconds':time.time()-start,'limits':'Finite pose sampling. Raw overlaps, no exceptions. Positive clearance requirement and continuous sweep bound not established.'}
    (ROOT/'reports/verification/r02_spine_sweep.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='pair_violations'}));return r
