"""Execute through installed MCP inside FreeCAD; isolated G0 diagnostic."""
import FreeCAD as App
import FreeCADGui as Gui
import json, math, os, sys

def run(root):
    name='FlexorDiagnosticR01'
    if name in App.listDocuments():
        raise RuntimeError('Diagnostic exists; refusing to overwrite live document')
    d=App.newDocument(name)
    b=d.addObject('Part::Box','DiagnosticBox'); b.Length=10; b.Width=20; b.Height=30
    c=d.addObject('Part::Cylinder','DiagnosticCylinder'); c.Radius=5; c.Height=20
    c.Placement.Base=App.Vector(30,0,0)
    b.ViewObject.ShapeColor=(0.3,0.6,0.9); c.ViewObject.ShapeColor=(0.9,0.65,0.25)
    d.recompute()
    rows=[]
    for o in (b,c):
        rows.append(dict(name=o.Name,volume_mm3=o.Shape.Volume,valid=o.Shape.isValid(),solids=len(o.Shape.Solids),bounds_mm=[o.Shape.BoundBox.XLength,o.Shape.BoundBox.YLength,o.Shape.BoundBox.ZLength]))
    assert abs(b.Shape.Volume-6000)<1e-8
    assert abs(c.Shape.Volume-math.pi*25*20)<1e-8
    path=os.path.join(root,'cad/diagnostics/mcp_sanity.FCStd')
    d.saveAs(path)
    Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
    Gui.activeDocument().activeView().saveImage(os.path.join(root,'reports/views/mcp_sanity.png'),1200,850,'White')
    App.closeDocument(d.Name)
    reopened=App.openDocument(path); reopened.recompute()
    assert len(reopened.Objects)==2 and all(o.Shape.isValid() for o in reopened.Objects)
    env=dict(status='PASS',FreeCAD=App.Version(),Python=sys.version,workbenches=list(Gui.listWorkbenches()),MCP_addon='0.1.26',protocol=1,preexisting_documents=[],objects=rows,native_reopen='PASS',diagnostic=path,view='reports/views/mcp_sanity.png',reference_PDFs='ABSENT; source visual checks BLOCKED')
    project=App.newDocument('ActiveSpineQuadruped')
    marker=project.addObject('App::FeaturePython','ProjectIdentity')
    marker.addProperty('App::PropertyString','Revision'); marker.Revision='r01: initial MCP checkpoint'
    project.recompute(); project.saveAs(os.path.join(root,'cad/checkpoints/initial_project.FCStd'))
    with open(os.path.join(root,'reports/verification/environment.json'),'w') as f: json.dump(env,f,indent=2)
    print(json.dumps(env))
