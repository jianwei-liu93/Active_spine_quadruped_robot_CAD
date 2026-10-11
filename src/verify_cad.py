"""Actual FreeCAD artifact checks, invoked by lead through installed MCP."""
import json,math,time
from pathlib import Path
import FreeCAD as App,Part
from kinematics import load_parameters,spine
ROOT=Path(__file__).resolve().parents[1]

def physical(doc):return [o for o in doc.Objects if o.TypeId=='App::Link']
def collision_scan(doc,path=ROOT/'reports/verification/neutral_interference.json'):
    objs=physical(doc);shapes={o.Name:o.Shape.copy() for o in objs};bounds={n:s.BoundBox for n,s in shapes.items()}
    found=[];candidates=0;start=time.time()
    for i,a in enumerate(objs):
        for b in objs[i+1:]:
            ba,bb=bounds[a.Name],bounds[b.Name]
            if not ba.intersect(bb):continue
            # Strict bbox interior overlap; touching solids need distance/contact rather than a volume boolean.
            dims=[min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bb,k+'Min')) for k in ['X','Y','Z']]
            if min(dims)<1e-6:continue
            candidates+=1
            v=shapes[a.Name].common(shapes[b.Name]).Volume
            if v>1e-5:found.append({'a':a.Name,'b':b.Name,'intersection_mm3':v})
    report={'revision':'r01','pose':'theta=0, all legs neutral prescribed','status':'FAIL' if found else 'PASS','instances':len(objs),'broadphase_candidate_pairs':candidates,'volume_tolerance_mm3':1e-5,'raw_overlaps':sorted(found,key=lambda x:-x['intersection_mm3']),'exceptions':'None applied in this raw diagnostic','elapsed_s':time.time()-start}
    Path(path).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='raw_overlaps'}));print(json.dumps(report['raw_overlaps'][:30],indent=2));return report

def inventory(doc):
    p=load_parameters();objs=physical(doc);rows=[];total=0;weighted=App.Vector();box=App.BoundBox()
    for o in objs:
        s=o.Shape;src=o.LinkedObject;valid=s.isValid();role=src.Role
        density=p['steel_density_kg_m3'] if src.MaterialName=='steel' else (8500 if src.MaterialName=='brass' else p['PA12_density_kg_m3'])
        mass=(src.PurchasedMass_g if 'PurchasedMass_g' in src.PropertiesList else s.Volume*density*1e-6)
        if o.Name=='ControllerCandidate':mass=p['controller_mass_g']
        if role=='SPRING':mass=0.5 # explicit assumed spring mass, envelope volume is not wire mass
        if role=='CABLE':mass=0.15
        center=s.Solids[0].CenterOfMass
        total+=mass;weighted+=center*mass;box.add(s.BoundBox)
        rows.append({'instance':o.Name,'part':src.PartNumber,'role':role,'valid':valid,'solids':len(s.Solids),'volume_mm3':s.Volume,'mass_g':mass,'center_mm':[center.x,center.y,center.z]})
    total+=p['wiring_mass_g'];weighted+=App.Vector(0,0,10)*p['wiring_mass_g'];com=weighted/total
    report={'revision':'r01','status':'PASS' if all(r['valid'] and r['solids']==1 and r['volume_mm3']>0 for r in rows) else 'FAIL','instances':len(rows),'editable_definitions':len([o for o in doc.Objects if o.TypeId=='PartDesign::Body']),'fully_constrained_sketches':all(o.FullyConstrained for o in doc.Objects if o.TypeId=='Sketcher::SketchObject'),'envelope_mm':[box.XLength,box.YLength,box.ZLength],'bounds_mm':[box.XMin,box.XMax,box.YMin,box.YMax,box.ZMin,box.ZMax],'mass_estimate_g':total,'CoM_estimate_mm':[com.x,com.y,com.z],'mass_limits':'Envelope motor masses overridden; PA12 1010/steel7850/brass8500 kg/m3 assumptions; spring0.5g each/cable0.15g each; wiring8g added at(0,0,10). Simplified hardware/guide solids; unmodeled tie screws remain mass gap. Not measured mass.','parts':rows}
    (ROOT/'reports/verification/cad_inventory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='parts'}));return report
