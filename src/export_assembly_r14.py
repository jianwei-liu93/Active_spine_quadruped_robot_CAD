"""Candidate assembly STEP and round trip; no drawing or print release."""
import json,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(doc):
    import Import,Part
    import animation_pose_export as ax
    from adaptive_volume_r07 import validate_solids
    native=Path(doc.FileName);sha=hashlib.sha256(native.read_bytes()).hexdigest();before=ax.snapshot(doc)
    links=sorted((o for o in doc.Objects if o.TypeId=='App::Link'),key=lambda o:o.Name)
    assert len(links)==455
    folder=ROOT/'exports/step/r14';folder.mkdir(parents=True,exist_ok=True)
    path=folder/'flexor_r14_robot.step';start=time.monotonic()
    Import.export(links,str(path));shape=Part.read(str(path))
    assert len(shape.Solids)==455 and shape.isValid()
    result=validate_solids(shape,[o.Shape for o in links],ROOT,[o.Name for o in links])
    report={'status':'PASS','native_sha256':sha,'step_path':str(path.relative_to(ROOT)),
            'step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'physical_solids':455,
            'geometry_roundtrip':result,'seconds':time.monotonic()-start,
            'native_file_unchanged':sha==hashlib.sha256(native.read_bytes()).hexdigest(),
            'native_document_unchanged':before==ax.snapshot(doc),
            'scope':'Editable CAD candidate assembly exchange only; drawings, STLs and fabrication release deferred'}
    assert report['native_file_unchanged'] and report['native_document_unchanged']
    (ROOT/'reports/verification/r14_assembly_export.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
