"""Lead-only reopen/recompute, actual fork-axis stack and native edit probes."""
from pathlib import Path
import json,hashlib,math,shutil
ROOT=Path(__file__).resolve().parents[1]

def run(doc):
    import FreeCAD as App,Part
    from verify_frame_revision_r09 import _strict_shape_identity
    from verify_link_sections_r11 import _native
    import animation_pose_export as ax
    native=Path(doc.FileName);sha=hashlib.sha256(native.read_bytes()).hexdigest()
    before=ax.snapshot(doc)
    doc.recompute(None,True,True)
    assert before==ax.snapshot(doc),'Forced native recompute changed cached physical geometry/pose'
    record={'status':'RUNNING','native_sha256':sha,'native':_native(doc),'reopened_from_saved_file':True,
            'forced_recompute_geometry_unchanged':True,'fork_axes':[],'edit_tests':[]}
    cfg=json.loads(doc.PoseController.LinkSectionsR11);mm=json.loads(doc.PoseController.MotionMap)
    for row in cfg['fork_sections']:
        obj=doc.getObject(row['instance']);m=mm[obj.Name];side=1 if m['y']>0 else -1
        for end,key,added in (('A',m['a'],25.8),('B',m['b'],36.0)):
            from kinematics import spine
            import robot_pose_r03
            point=spine(0,robot_pose_r03._parameters(doc))[key]
            faces=[]
            for face in obj.Shape.Faces:
                s=face.Surface
                if not isinstance(s,Part.Cylinder) or abs(s.Radius-2.025)>1e-7:continue
                if abs(s.Axis.y)/s.Axis.Length<1-1e-10:continue
                if math.dist((s.Center.x,s.Center.z),point)>1e-6:continue
                faces.append((face.BoundBox.YMin,face.BoundBox.YMax))
            expected=sorted([(m['y']-.6,m['y']+.6),(side*added-.6,side*added+.6)])
            actual=sorted(faces)
            assert len(actual)==2,(obj.Name,key,actual)
            assert max(abs(a-b) for x,y in zip(actual,expected) for a,b in zip(x,y))<1e-6
            record['fork_axes'].append({'instance':obj.Name,'joint':key,'actual_bore_world_y_bounds_mm':actual,'expected_leaf_y_bounds_mm':expected,'axis_xz_mm':point})
    temp=ROOT/'reports/tmp/r11/native_edit_probe.FCStd';shutil.copy2(native,temp)
    probe=App.openDocument(str(temp))
    try:
        targets=[(probe.getObject('SPN_AB_LOCAL_FORK_r11_B1_NEG_ABridge'),.1),
                 (probe.getObject('SPN_r02_L4_BlindRelief'),.05)]
        for feature,delta in targets:
            body=feature.getParentGeoFeatureGroup();old=body.Shape.copy();value=float(feature.Length)
            feature.Length=value+delta;probe.recompute()
            assert body.Shape.isValid() and len(body.Shape.Solids)==1
            difference=abs(body.Shape.Volume-old.Volume);assert difference>1e-5
            feature.Length=value;probe.recompute()
            proof=_strict_shape_identity(old,body.Shape,feature.Name+' edit restore')
            record['edit_tests'].append({'feature':feature.Name,'parameter':'Length','original_mm':value,
                'temporary_delta_mm':delta,'volume_change_mm3':difference,'restore_geometry':proof})
        assert not any('Invalid' in str(s) or 'Error' in str(s) for o in probe.Objects for s in o.State)
    finally:
        App.closeDocument(probe.Name);App.setActiveDocument(doc.Name)
    record.update(status='PASS',native_file_unchanged=sha==hashlib.sha256(native.read_bytes()).hexdigest(),
                  document_geometry_unchanged=before==ax.snapshot(doc),
                  limits='Actual leaf bores and native history/edit restore only; fits, thrust, loads and race retention remain UNVERIFIED')
    assert record['native_file_unchanged'] and record['document_geometry_unchanged']
    (ROOT/'reports/verification/r11_native_checks.json').write_text(json.dumps(record,indent=2)+'\n')
    return record
