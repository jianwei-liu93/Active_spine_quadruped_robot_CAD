"""Lead-only live FreeCAD views; visibility/camera changes never save geometry."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def render(doc):
    import FreeCAD as App,FreeCADGui as Gui
    from pivy import coin
    App.setActiveDocument(doc.Name)
    v=Gui.activeDocument().activeView()
    instances=[o for o in doc.Objects if o.TypeId=='App::Link']
    saved={o.Name:o.Visibility for o in instances}
    out=ROOT/'reports/views';out.mkdir(exist_ok=True)
    def capture(name,predicate,front=False):
        box=App.BoundBox()
        for o in instances:
            o.Visibility=bool(predicate(o))
            if o.Visibility:box.add(o.Shape.BoundBox)
        v.viewFront() if front else v.viewAxonometric()
        Gui.updateGui()
        target=box.Center;position=target+v.getCameraOrientation().multVec(App.Vector(0,0,300))
        height=max(box.ZLength,box.XLength/1.45)*1.2 if front else box.DiagonalLength*.9
        node=v.getCameraNode()
        node.position.setValue(position.x,position.y,position.z)
        node.nearDistance.setValue(1);node.farDistance.setValue(1000)
        node.focalDistance.setValue(300);node.height.setValue(height)
        v.saveImage(str(out/name),1600,1100,'White')
    try:
        capture('r06_bare_lumbar.png',lambda o:o.Name.startswith('LumbarIntegrated'))
        capture('r06_bare_fore_attachment.png',lambda o:o.Name=='Torso_fore')
        capture('r06_bare_hind_attachment.png',lambda o:o.Name=='Torso_hind')
        capture('r06_spine_torso_frames.png',lambda o:o.Name.startswith(('LumbarIntegrated','Torso_','Link','SyncB','Through')) or o.LinkedObject.MaterialName=='copper' or 'Capture' in o.Name)
        capture('r06_robot_side.png',lambda o:True,front=True)
        capture('r06_robot_assembled.png',lambda o:True)
    finally:
        for o in instances:o.Visibility=saved[o.Name]
        v.viewAxonometric();v.fitAll();Gui.updateGui()
