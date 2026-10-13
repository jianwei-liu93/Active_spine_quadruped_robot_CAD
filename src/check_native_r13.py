"""Lead-only saved-file load and reversible edit probes on a disposable copy."""
import json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(doc):
    import FreeCAD as App
    from verify_changed_revision_r10 import _native_state_guard
    from verify_frame_revision_r09 import _strict_shape_identity
    import animation_pose_export as ax
    path=Path(doc.FileName);sha=hashlib.sha256(path.read_bytes()).hexdigest()
    before=ax.snapshot(doc);temp=ROOT/'reports/tmp/r13/native_edit_probe.FCStd'
    temp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,temp)
    probe=App.openDocument(str(temp))
    report={'status':'RUNNING','native_sha256':sha,'probe_is_disposable_copy':True,'edit_tests':[]}
    try:
        original={o.Name:o for o in doc.Objects if o.TypeId=='App::Link'}
        loaded={o.Name:o for o in probe.Objects if o.TypeId=='App::Link'}
        assert set(original)==set(loaded) and len(loaded)==455
        probe.recompute(None,True,True)
        report['native_guard']=_native_state_guard(probe)
        assert all(s.FullyConstrained for s in probe.Objects if s.TypeId=='Sketcher::SketchObject')
        for n in sorted(loaded):
            _strict_shape_identity(original[n].Shape,loaded[n].Shape,n+' saved/recompute')
        report['saved_recompute_instances']=len(loaded)
        targets=[('SPN_AB_TERMINAL_r12_B1_POS_BTerminalLeaf',.1),
                 ('SPN_r02_L4_BlindReliefR12',.05),
                 ('FRM_LUMBAR_COMPACT_CAGE_r12_ContinuousCrosswall0',.1)]
        for name,delta in targets:
            feature=probe.getObject(name);assert feature is not None,name
            body=feature.getParentGeoFeatureGroup();old=body.Shape.copy();length=float(feature.Length)
            feature.Length=length+delta;probe.recompute(None,True,True)
            assert body.Shape.isValid() and len(body.Shape.Solids)==1
            change=abs(float(body.Shape.Volume)-float(old.Volume));assert change>1e-5
            feature.Length=length;probe.recompute(None,True,True)
            proof=_strict_shape_identity(old,body.Shape,name+' restore')
            report['edit_tests'].append({'feature':name,'parameter':'Length','original_mm':length,
                'temporary_delta_mm':delta,'volume_change_mm3':change,'restored_geometry':proof})
        report['status']='PASS'
    except Exception as error:
        report['status']='FAIL';report['error']=repr(error)
    finally:
        App.closeDocument(probe.Name);App.setActiveDocument(doc.Name)
    report['canonical_file_unchanged']=sha==hashlib.sha256(path.read_bytes()).hexdigest()
    report['canonical_document_unchanged']=before==ax.snapshot(doc)
    assert report['canonical_file_unchanged'] and report['canonical_document_unchanged']
    report['limits']='Native load/edit/restore only; no supplier fit, structural or fabrication qualification'
    (ROOT/'reports/verification/r13_native_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
