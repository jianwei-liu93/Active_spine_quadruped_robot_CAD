"""Lead GUI captures of actual articulated CAD; visual evidence, not a solver.

Fixed saved leg coordinates and wheel state. No native save, source regeneration,
hidden part substitution or interpolation of rendered geometry.
"""
from pathlib import Path
import hashlib,json,math


def render(doc, root, step_deg=15):
    import FreeCAD as App, FreeCADGui as Gui
    from pivy import coin
    import robot_pose_r03 as pose
    root=Path(root);out=root/'reports/motion/r07';out.mkdir(parents=True,exist_ok=True)
    filename=Path(doc.FileName);before=hashlib.sha256(filename.read_bytes()).hexdigest()
    original=float(doc.PoseController.SpinePhaseRad)
    App.setActiveDocument(doc.Name);view=Gui.activeDocument().activeView()
    links=[o for o in doc.Objects if o.TypeId=='App::Link']
    visibility={o.Name:o.Visibility for o in links}
    for o in doc.PartsLibrary.Group:o.Visibility=False
    doc.PartsLibrary.Visibility=False
    for o in doc.Objects:
        if getattr(o,'NonphysicalClearance',False):o.Visibility=False
    normal=App.Vector(-.3,1,.22);normal.normalize()
    right=App.Vector(0,0,1).cross(normal);right.normalize();up=normal.cross(right)
    rotation=App.Rotation(right,up,normal,'ZXY')
    records=[]
    try:
        for index,degree in enumerate(range(0,360,step_deg)):
            pose.apply_pose(doc,math.radians(degree))
            for o in links:o.Visibility=True
            node=view.getCameraNode();node.orientation.setValue(coin.SbRotation(*rotation.Q))
            position=App.Vector(0,0,-7)+rotation.multVec(App.Vector(0,0,300))
            node.position.setValue(*tuple(position));node.nearDistance.setValue(1)
            node.farDistance.setValue(1000);node.focalDistance.setValue(300);node.height.setValue(190)
            Gui.updateGui()
            path=out/('frame_%03d.png'%index);view.saveImage(str(path),1200,800,'White')
            records.append({'frame':index,'spine_phase_deg':degree,'path':str(path.relative_to(root)),
                            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            (out/'capture_progress.json').write_text(json.dumps({'status':'RUNNING','frames_completed':len(records),'frames':records},indent=2)+'\n')
    finally:
        pose.apply_pose(doc,original)
        for o in links:o.Visibility=visibility[o.Name]
        view.viewAxonometric();view.fitAll();Gui.updateGui()
    unchanged=before==hashlib.sha256(filename.read_bytes()).hexdigest()
    report={'status':'PASS_CAPTURED_RESTORED' if unchanged else 'FAIL_NATIVE_CHANGED',
            'native_sha256':before,'native_file_unchanged':unchanged,'frames':records,
            'scope':'Actual CAD spine articulation at fixed saved leg/wheel state; visual evidence only',
            'limits':'Finite visual frames; no continuous clearance, loaded equilibrium or physical performance claim.'}
    (out/'capture_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
