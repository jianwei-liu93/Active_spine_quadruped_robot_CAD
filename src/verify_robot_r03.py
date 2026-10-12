"""Actual native r03 checks; run in supplemental isolated FreeCADCmd."""
import json,math,time
from pathlib import Path
import FreeCAD as App
ROOT=Path(__file__).resolve().parents[1]

def neutral(doc,output=None,revision='r03'):
    start=time.time();objs=[o for o in doc.Objects if o.TypeId=='App::Link']
    rows=[{'instance':o.Name,'source':o.LinkedObject.Name,'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'volume_mm3':o.Shape.Volume} for o in objs]
    shapes={o.Name:o.Shape.copy() for o in objs};bounds={n:s.BoundBox for n,s in shapes.items()};hits=[];checks=0
    for i,a in enumerate(objs):
        for b in objs[i+1:]:
            ba,bb=bounds[a.Name],bounds[b.Name]
            if min(min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bb,k+'Min')) for k in ('X','Y','Z'))<=1e-6:continue
            checks+=1;vol=shapes[a.Name].common(shapes[b.Name]).Volume
            if vol>1e-5:hits.append({'a':a.Name,'b':b.Name,'intersection_mm3':vol})
    r={'revision':revision,'scope':'actual native assembly at saved prescribed pose; raw intersections without exceptions','status':'PASS' if not hits and all(x['valid'] and x['solids']==1 and x['volume_mm3']>0 for x in rows) else 'FAIL','instances':len(rows),'parts':rows,'editable_bodies':sum(o.TypeId=='PartDesign::Body' for o in doc.Objects),'fully_constrained_sketches':all(o.FullyConstrained for o in doc.Objects if o.TypeId=='Sketcher::SketchObject'),'narrowphase_tests':checks,'raw_overlaps':sorted(hits,key=lambda x:-x['intersection_mm3']),'volume_tolerance_mm3':1e-5,'elapsed_seconds':time.time()-start,'limits':'Prescribed pose only. No continuous clearance, loaded equilibrium or fabrication claim.'}
    path=Path(output) if output else ROOT/'reports/verification/r03_robot_neutral.json';path.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('parts','raw_overlaps')}),flush=True);print(json.dumps(r['raw_overlaps'],indent=2),flush=True)
    return r

if __name__=='__main__':
    d=App.openDocument(str(ROOT/'cad/flexor_r03_robot.FCStd'));d.recompute();neutral(d)
