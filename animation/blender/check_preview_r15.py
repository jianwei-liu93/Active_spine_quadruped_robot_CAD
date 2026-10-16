"""Reopen the standalone preview with Blender -b, then inspect actual data."""
import bpy,json,hashlib,math
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
scene=bpy.data.scenes['r15_geometry_interoperability_preview']
if bpy.context.window:bpy.context.window.scene=scene
instances={o['instance_id']:o for o in scene.objects if 'instance_id' in o}
assert len(instances)==455 and len({o['source_id'] for o in instances.values()})==108
target=instances['instance:LumbarIntegrated1']
assert target['part_number']=='FRM_LUMBAR_COMPACT_CAGE_r15'
assert target.data['units']=='m'
asset=json.loads((ROOT/'animation/assets/r15/lumbar_source.json').read_text())
assert len(target.data.vertices)==len(asset['vertices_m'])==6251
assert len(target.data.polygons)==len(asset['triangles'])==12598
error=max(abs(float(v.co[j])-a[j]) for v,a in zip(target.data.vertices,asset['vertices_m']) for j in range(3))
assert error<1e-8
native_sha=hashlib.sha256((ROOT/'cad/flexor_r15_robot.FCStd').read_bytes()).hexdigest()
assert scene['source_cad_sha256']==native_sha
pose=json.loads((ROOT/'animation/motion/ax01_r15.json').read_text())
index=pose['instance_order'].index('instance:LumbarIntegrated1')
scene.frame_set(1)
bpy.context.view_layer.update()
matrix=pose['frames'][0]['transforms_m'][index]
world_error=max(abs(float(target.matrix_world[i][j])-matrix[i][j]) for i in range(4) for j in range(4))
# Blender uses single-precision transforms; check their actual spatial effect
# as well as a float32 matrix bound, not double-precision CAD tolerances.
point_error_mm=0.
for vertex,exact in zip(target.data.vertices,asset['vertices_m']):
    actual=target.matrix_world @ vertex.co
    expected=[sum(matrix[i][j]*exact[j] for j in range(3))+matrix[i][3] for i in range(3)]
    point_error_mm=max(point_error_mm,1000*math.dist(actual,expected))
assert world_error<1e-6 and point_error_mm<.001
assert scene.frame_start==1 and scene.frame_end==300 and scene.render.fps==60
framing=[]
for frame in range(1,297,5):
    scene.frame_set(frame);bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    camera=scene.camera;inverse=camera.matrix_world.normalized().inverted()
    corners=camera.data.view_frame(scene=scene)
    x0,x1=min(v.x for v in corners),max(v.x for v in corners)
    y0,y1=min(v.y for v in corners),max(v.y for v in corners)
    xs=[];ys=[]
    for obj in instances.values():
        ev=obj.evaluated_get(deps)
        for corner in ev.bound_box:
            v=inverse @ (ev.matrix_world @ Vector(corner))
            xs.append((v.x-x0)/(x1-x0));ys.append((v.y-y0)/(y1-y0))
    margin=min(min(xs),min(ys),1-max(xs),1-max(ys))
    framing.append({'source_frame':frame,'minimum_normalized_image_margin':margin})
minimum_margin=min(r['minimum_normalized_image_margin'] for r in framing)
assert minimum_margin>.015,('cropping risk',minimum_margin)
report={'status':'PASS_SAVED_BLENDER_PREVIEW','native_sha256':native_sha,
        'scene_path':str(Path(bpy.data.filepath).relative_to(ROOT)),
        'scene_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
        'instances':455,'sources':108,'changed_source_vertices':6251,'changed_source_triangles':12598,
        'maximum_source_mesh_coordinate_error_m':error,'source_to_world_matrix_error':world_error,
        'maximum_source_to_world_vertex_error_mm':point_error_mm,
        'matrix_precision':'Blender float32; matrix bound1e-6, actual vertex reprojection bound0.001mm',
        'all_60_sample_framing':framing,'minimum_normalized_image_margin':minimum_margin,
        'units':'metres','transform_application':'one preserved source-to-world transform',
        'source_library_r14_sha256':scene['r15_r14_library_sha256'],
        'limits':'Small inherited prescribed-kinematics preview; no new dynamics or complete Blender export campaign.'}
(ROOT/'reports/animation/r15_saved_scene.json').write_text(json.dumps(report,indent=2)+'\n')
print('R15_SAVED_SCENE_PASS',error,world_error,flush=True)
