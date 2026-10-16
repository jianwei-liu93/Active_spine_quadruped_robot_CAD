"""Changed source-only metre mesh from saved native BRep, isolated FreeCADCmd."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import FreeCAD as App,MeshPart
from animation_pose_export import shape_hash
native=ROOT/'cad/flexor_r15_robot.FCStd'
doc=App.openDocument(str(native))
try:
    source=doc.LumbarIntegrated1.LinkedObject
    if not source.Placement.isIdentity() or not source.Shape.Placement.isIdentity():
        raise RuntimeError('Unverified source-frame transform')
    shape=source.Shape.copy(copyGeom=True,copyMesh=False)
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.05,AngularDeflection=.15,Relative=False)
    vertices,triangles=mesh.Topology
    data={'source_object':source.Name,'mesh_id':'mesh:'+source.Name,'units':'m',
          'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
          'geometry_hash':shape_hash(shape),'linear_deflection_mm':.05,'angular_deflection_rad':.15,
          'vertices_m':[[v.x*.001,v.y*.001,v.z*.001] for v in vertices],
          'triangles':[list(t) for t in triangles]}
    path=ROOT/'animation/assets/r15/lumbar_source.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('R15_MESH_EXPORTED',len(vertices),len(triangles),flush=True)
finally:App.closeDocument(doc.Name)
