"""Actual FreeCAD BRep screenshots; one fixed camera per before/after pair."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def capture(old,new):
    import FreeCAD as App
    import FreeCADGui as Gui
    from pivy import coin
    folder=ROOT/'reports/views';records=[]
    original=App.ActiveDocument
    temp=App.newDocument('R15bMatchedPartViews')
    view=Gui.activeDocument().activeView();items=[]
    for label,doc in [('r15_before',old),('r15b',new)]:
        obj=temp.addObject('Part::Feature',label+'_AB')
        obj.Shape=doc.SPN_AB_TERMINAL_r12_B1_POS.Shape.copy(copyGeom=True,copyMesh=False)
        obj.ViewObject.ShapeColor=(.82,.83,.82);obj.ViewObject.LineColor=(.12,.13,.14)
        obj.ViewObject.DisplayMode='Flat Lines';obj.Visibility=False;items.append((label,obj))
    temp.recompute()
    def camera(active_view,normal_tuple,box,margin=1.18):
        normal=App.Vector(*normal_tuple);normal.normalize()
        right=App.Vector(0,0,1).cross(normal);right.normalize();up=normal.cross(right)
        rotation=App.Rotation(right,up,normal,'ZXY');origin=box.Center
        points=[App.Vector(x,y,z)-origin for x in (box.XMin,box.XMax)
                for y in (box.YMin,box.YMax) for z in (box.ZMin,box.ZMax)]
        width=max(p.dot(right) for p in points)-min(p.dot(right) for p in points)
        height=max(p.dot(up) for p in points)-min(p.dot(up) for p in points)
        node=active_view.getCameraNode();node.orientation.setValue(coin.SbRotation(*rotation.Q))
        node.position.setValue(*tuple(origin+normal*500));node.focalDistance.setValue(500)
        node.nearDistance.setValue(1);node.farDistance.setValue(2000)
        node.height.setValue(max(height,width/1.5)*margin)
        return {'normal':normal_tuple,'centre_mm':list(origin),'height_mm':node.height.getValue()}
    def save(active_view,name,cam):
        Gui.updateGui();path=folder/(name+'.png');active_view.saveImage(str(path),1500,1000,'White')
        records.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera':cam})
    try:
        for suffix,normal in [('AB_isolated',(.65,-1,.9)),('AB_depth',(0,-1,0)),('AB_plan',(.001,.001,1))]:
            cam=camera(view,normal,items[1][1].Shape.BoundBox)
            for label,obj in items:
                for _,other in items:other.Visibility=other is obj
                save(view,label+'_'+suffix,cam)
        App.setActiveDocument(new.Name);view=Gui.activeDocument().activeView()
        links=[o for o in new.Objects if o.TypeId=='App::Link'];visibility={o.Name:o.Visibility for o in links}
        try:
            for mode in ('robot_isometric','spine_close'):
                selected=links if mode=='robot_isometric' else [o for o in links if not o.Name.startswith(('fore','hind','HindTendon','OpenRB','Controller'))]
                for obj in links:obj.Visibility=obj in selected
                bb=App.BoundBox()
                for obj in selected:bb.add(obj.Shape.BoundBox)
                cam=camera(view,(.8,1,.65),bb,1.12)
                save(view,'r15b_'+mode,cam)
        finally:
            for obj in links:obj.Visibility=visibility[obj.Name]
    finally:
        App.closeDocument(temp.Name)
        if original:App.setActiveDocument(original.Name)
    path=folder/'r15b_capture_manifest.json'
    path.write_text(json.dumps({'native_path':'cad/flexor_r15b_robot.FCStd',
                               'native_sha256':hashlib.sha256((ROOT/'cad/flexor_r15b_robot.FCStd').read_bytes()).hexdigest(),
                               'actual_FreeCAD_native_geometry':True,'captures':records},indent=2)+'\n')
    return records
