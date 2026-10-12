"""Fresh-source rebuild comparison; never saves the canonical file.

The lead also executed the complete builder in the installed MCP application.
The lead passes the freshly built live document; this compares every placed physical solid.
"""
from pathlib import Path
import hashlib,json,time
ROOT=Path(__file__).resolve().parents[1]

def run(rebuilt, canonical, revision='r07'):
    import FreeCAD as App,Part
    import robot_pose_r03 as pose,leg_motion_r07
    from adaptive_volume_r07 import validate_solids
    native=ROOT/('cad/flexor_'+revision+'_robot.FCStd')
    before=hashlib.sha256(native.read_bytes()).hexdigest();start=time.monotonic()
    # Use actual descriptor lengths at the final neutral placements. This is
    # the same explicit source regeneration recorded for the canonical model.
    springs=pose._plan(rebuilt,0.,None)[3]
    for name,m,source,length,free,mismatch in pose._spring_lengths(rebuilt,springs):
        source.Shape=leg_motion_r07._spring_source({'kind':m['spring'],'length_mm':length,'free_length_mm':free})
        if 'InstalledCoilLength_mm' not in source.PropertiesList:source.addProperty('App::PropertyLength','InstalledCoilLength_mm','MotionR07')
        source.InstalledCoilLength_mm=length
    rebuilt.recompute()
    a={o.Name:o for o in canonical.Objects if o.TypeId=='App::Link'}
    b={o.Name:o for o in rebuilt.Objects if o.TypeId=='App::Link'}
    assert set(a)==set(b) and len(a)==486
    assert all(a[n].LinkedObject.PartNumber==b[n].LinkedObject.PartNumber for n in a)
    assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in b.values())
    print('REBUILT',len(b),'seconds',time.monotonic()-start,flush=True)
    names=sorted(a)
    comparison=validate_solids(Part.makeCompound([b[n].Shape for n in names]),[a[n].Shape for n in names],ROOT,names)
    record={'status':'PASS','native_sha256':before,'native_file_unchanged':before==hashlib.sha256(native.read_bytes()).hexdigest(),
            'instances':len(a),'part_numbers_match':True,'source_partdesign_bodies':len([o for o in rebuilt.Objects if o.TypeId=='PartDesign::Body']),
            'scope':'Clean frozen-source rebuild and all486placedsolid comparison; no byte-equality claim; installed MCP source build also executed',
            'comparison':comparison,'seconds':time.monotonic()-start}
    assert record['native_file_unchanged']
    (ROOT/('reports/verification/'+revision+'_source_reproduction.json')).write_text(json.dumps(record,indent=2)+'\n')
    print('SOURCE_REPRODUCTION_PASS',record['seconds'],flush=True)
    return record
