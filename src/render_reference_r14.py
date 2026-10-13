"""Lead-only actual CAD reference views; restore pose/UI, never save native."""
from pathlib import Path
import hashlib,json,math

ROOT=Path(__file__).resolve().parents[1]

def render(doc):
    import FreeCAD as App,FreeCADGui as Gui
    from pivy import coin
    import robot_pose_r03 as pose
    import animation_pose_export as ax
    import render_robot_r07
    vis=[(o,o.Visibility) for o in doc.Objects if hasattr(o,'Visibility')]
    if doc.getObject('ReferenceClearances'):doc.ReferenceClearances.Visibility=False
    report=render_robot_r07.render(doc,ROOT,revision='r14')
    App.setActiveDocument(doc.Name);view=Gui.activeDocument().activeView()
    camera=view.getCamera();before=ax.snapshot(doc)
    native_sha=hashlib.sha256(Path(doc.FileName).read_bytes()).hexdigest()
    phase=float(doc.PoseController.SpinePhaseRad)
    links=[o for o in doc.Objects if o.TypeId=='App::Link']
    placements={o.Name:o.LinkPlacement for o in links}
    records=[]
    def capture(name,names,normal_xyz,center=None,height=None):
        box=App.BoundBox();selected=[]
        for o in links:
            o.Visibility=o.Name in names
            if o.Visibility:box.add(o.Shape.BoundBox);selected.append(o.Name)
        if not selected:raise ValueError('Empty actual capture')
        normal=App.Vector(*normal_xyz);normal.normalize()
        right=App.Vector(0,0,1).cross(normal);right.normalize();up=normal.cross(right)
        rot=App.Rotation(right,up,normal,'ZXY');node=view.getCameraNode()
        node.orientation.setValue(coin.SbRotation(*rot.Q))
        origin=App.Vector(*center) if center else box.Center
        node.position.setValue(*tuple(origin+normal*300));node.nearDistance.setValue(1)
        node.farDistance.setValue(1000);node.focalDistance.setValue(300)
        corners=[App.Vector(x,y,z)-box.Center for x in (box.XMin,box.XMax) for y in (box.YMin,box.YMax) for z in (box.ZMin,box.ZMax)]
        w=max(p.dot(right) for p in corners)-min(p.dot(right) for p in corners)
        h=max(p.dot(up) for p in corners)-min(p.dot(up) for p in corners)
        node.height.setValue(height or max(h,w/1.5,1)*1.15);Gui.updateGui()
        path=ROOT/'reports/views'/('r14_'+name+'.png');view.saveImage(str(path),1500,1000,'White')
        records.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'instances':selected,'normal_xyz':normal_xyz,'spine_phase_rad':float(doc.PoseController.SpinePhaseRad),'crop_center_mm':center,'camera_height_mm':height})
    try:
        for o in doc.PartsLibrary.Group:o.Visibility=False
        doc.PartsLibrary.Visibility=False
        if doc.getObject('ReferenceClearances'):doc.ReferenceClearances.Visibility=False
        core={o.Name for o in links if o.Name.startswith(('LumbarIntegrated','Torso_','CentralE'))}
        capture('central_attachment_bare',core,(.35,-1,.35))
        mechanism={o.Name for o in links if o.Name.startswith(('LumbarIntegrated','Link','Through','Sync','A1_','A2_','B1_','B2_','C1_','C2_','CentralE','DirectCrank','Horn'))}
        capture('spine_mechanism',mechanism,(.35,-1,.45))
        capture('AB_terminal_close',{'Link1_L3__1','A1__1_Bearing0','A1__1_Bearing1','A1__1_ForkInnerBearing','B1__1_ForkOuterBearing','B1__1_Bearing0','B1__1_Bearing1','B1__1_Bearing2'},(.7,-1,.45))
        capture('bare_lumbar',{'LumbarIntegrated1'},(.35,-1,.35))
        capture('lumbar_transverse_span',{'LumbarIntegrated1'},(1,0,0),height=92)
        capture('AB_isolated',{'Link1_L3__1'},(.7,-1,.45))
        capture('central_E1_close',core,(.25,-1,.45),(-33,0,0),24)
        capture('central_E2_close',core,(-.25,-1,.45),(33,0,0),24)
        for torso in ('hind','fore'):
            capture(torso+'_plate_profile',{'Torso_'+torso},(-1 if torso=='hind' else 1,0,0))
        capture('long_bar_profile',{'Link1_L4__1'},(0,-1,0))
        for deg in (60,240):
            pose.apply_pose(doc,math.radians(deg))
            capture('central_attachment_%03ddeg'%deg,core,(.35,-1,.35))
        pose.apply_pose(doc,phase)
    finally:
        if float(doc.PoseController.SpinePhaseRad)!=phase:pose.apply_pose(doc,phase)
        # The analytical restore can differ by a final floating-point bit.
        # Restore the actual saved link placements exactly for UI-only work.
        for o in links:o.LinkPlacement=placements[o.Name]
        for o,value in vis:o.Visibility=value
        view.setCamera(camera);Gui.updateGui()
    report.update(focused_captures=records,native_sha256=native_sha,
                  native_file_unchanged=native_sha==hashlib.sha256(Path(doc.FileName).read_bytes()).hexdigest(),
                  document_pose_geometry_unchanged=before==ax.snapshot(doc),
                  scope='Actual r14 geometry, central E joints, distinct torso plates and long B-C bar; fixed legs and wheel in two prescribed spine poses',
                  visual_review='PENDING_LEAD_INSPECTION')
    (ROOT/'reports/views/r14_reference_capture_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['native_file_unchanged'] and report['document_pose_geometry_unchanged']
    return {k:v for k,v in report.items() if k not in ('captures','focused_captures')}
