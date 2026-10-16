"""Matched actual FreeCAD BRep views; no mesh synthesis or canonical saves."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def prototype(old_shape, new_shape, placement):
    import FreeCAD as App, FreeCADGui as Gui
    from pivy import coin
    active = App.ActiveDocument
    doc = App.newDocument('R15_MatchedGeometryViews')
    view = Gui.activeDocument().activeView()
    objects = []
    for label, shape in [('r14', old_shape), ('r15', new_shape)]:
        obj = doc.addObject('Part::Feature', label+'_ActualNativeSourceSnapshot')
        obj.Shape = shape.copy(copyGeom=True, copyMesh=False)
        obj.Placement = placement
        obj.ViewObject.ShapeColor = (0.32, 0.34, 0.36)
        obj.ViewObject.LineColor = (0.08, 0.08, 0.08)
        obj.ViewObject.DisplayMode = 'Flat Lines'
        obj.Visibility = False
        objects.append((label, obj))
    doc.recompute()
    folder = ROOT/'reports/views'; folder.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        for name, normal_tuple, center, height in [
                ('lumbar_matched',(.35,1,.35),None,None),
                ('root_matched_close',(.2,1,.6),(29.5,32.5,4.5),19.),
                ('shoulder_matched_close',(.1,1,.55),(15.,32.,0.),27.),
                ('lumbar_under_matched',(.35,1,-.6),None,None)]:
            normal = App.Vector(*normal_tuple); normal.normalize()
            right = App.Vector(0,0,1).cross(normal); right.normalize()
            up = normal.cross(right)
            rotation = App.Rotation(right,up,normal,'ZXY')
            box = objects[0][1].Shape.BoundBox
            origin = App.Vector(*center) if center else box.Center
            node = view.getCameraNode()
            node.orientation.setValue(coin.SbRotation(*rotation.Q))
            node.position.setValue(*tuple(origin+normal*300))
            node.nearDistance.setValue(1);node.farDistance.setValue(1000)
            node.focalDistance.setValue(300)
            corners = [App.Vector(x,y,z)-box.Center for x in (box.XMin,box.XMax)
                       for y in (box.YMin,box.YMax) for z in (box.ZMin,box.ZMax)]
            w = max(p.dot(right) for p in corners)-min(p.dot(right) for p in corners)
            h = max(p.dot(up) for p in corners)-min(p.dot(up) for p in corners)
            node.height.setValue(height or max(h,w/1.5)*1.12)
            for label, obj in objects:
                for _, other in objects: other.Visibility = other is obj
                Gui.updateGui()
                path = folder/(label+'_'+name+'.png')
                view.saveImage(str(path),1500,1000,'White')
                records.append({'path':str(path.relative_to(ROOT)),
                                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                'revision':label,'view':name,'normal_xyz':normal_tuple,
                                'center_mm':list(origin),'camera_height_mm':node.height.getValue()})
    finally:
        App.closeDocument(doc.Name)
        if active: App.setActiveDocument(active.Name)
    (folder/'r15_prototype_capture_manifest.json').write_text(json.dumps({
        'scope':'Matched camera actual native source BRep snapshots with one preserved assembly placement',
        'captures':records,'geometry_edited_for_visualization':False},indent=2)+'\n')
    return records
