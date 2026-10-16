"""STEP exchange for all physical r15b instances, preserving caller geometry."""
import time
from pathlib import Path
from package_sculpted_r15 import _doc_fingerprint,_links,_sha

ROOT=Path(__file__).resolve().parents[1]


def export_step(doc):
    import FreeCAD as App
    import Part
    import Import
    from adaptive_volume_r07 import validate_solids
    path=Path(doc.FileName);assert path==ROOT/'cad/flexor_r15b_robot.FCStd'
    before=_doc_fingerprint(doc);digest=_sha(path);start=time.time()
    links=_links(doc);ordered=[links[n] for n in sorted(links)]
    target=ROOT/'exports/step/r15b/flexor_r15b_robot.step';target.parent.mkdir(parents=True,exist_ok=True)
    Part.setStaticValue('write.surfacecurve.mode',1)
    exchange=App.newDocument('R15bTransientExchange')
    try:
        objects=[]
        for link in ordered:
            obj=exchange.addObject('Part::Feature',link.Name)
            obj.Label=link.Label;obj.Shape=link.Shape.copy(copyGeom=True,copyMesh=False);objects.append(obj)
        exchange.recompute();Import.export(objects,str(target))
    finally:
        App.closeDocument(exchange.Name);App.setActiveDocument(doc.Name)
    shape=Part.read(str(target));assert shape.isValid() and len(shape.Solids)==455
    result=validate_solids(shape,[o.Shape for o in ordered],ROOT,[o.Name for o in ordered])
    assert before==_doc_fingerprint(doc) and digest==_sha(path)
    return {'status':'PASS','revision':'r15b','native_path':str(path.relative_to(ROOT)),
            'native_sha256':digest,'step_path':str(target.relative_to(ROOT)),'step_sha256':_sha(target),
            'physical_solids':455,'geometry_roundtrip':result,'elapsed_s':time.time()-start,
            'export_inputs':'Deep copies of455 already placed BReps; no additional instance transform',
            'source_to_world_convention':'world_mm = LinkPlacement.multVec(source_mm); source and shape placements identity; no double transform',
            'native_document_and_file_unchanged':True}
