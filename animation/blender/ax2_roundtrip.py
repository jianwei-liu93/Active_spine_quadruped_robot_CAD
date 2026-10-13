import bpy, json, sys, hashlib
from pathlib import Path
from mathutils import Matrix, Vector
ROOT=Path('/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD')
sys.path.insert(0,str(ROOT/'animation/blender'))
import build_scenes
manifest=build_scenes.load_manifest(); mats=build_scenes.materials()
scene=bpy.data.scenes.new('AX2 source-local roundtrip');bpy.context.window.scene=scene;build_scenes.stage(scene)
cam=build_scenes.camera(scene);build_scenes.point_camera(cam,(.1,-.18,.09),(0,0,0),.18)
items=[r for r in manifest['instances'] if r['source_object_name']=='SPN_r02_L4'][:2]
row=next(r for r in manifest['meshes'] if r['mesh_id']==items[0]['mesh_id']);raw=json.loads((ROOT/row['path']).read_text())
mesh=build_scenes.add_mesh('AX2 shared actual source',raw['vertices_m'],raw['triangles']);mesh.materials.append(mats['link'])
objects=[];max_error=0
for item in items:
    o=bpy.data.objects.new(item['instance_id'],mesh);scene.collection.objects.link(o);objects.append(o)
    index=manifest['instance_order'].index(item['instance_id'])
    for f,sample in enumerate(manifest['frames'],1):
        o.matrix_world=Matrix(sample['transforms_m'][index]);o.keyframe_insert('location',frame=f);o.rotation_mode='QUATERNION';o.keyframe_insert('rotation_quaternion',frame=f)
        for point in raw['vertices_m'][::max(1,len(raw['vertices_m'])//40)]:
            world=o.matrix_world@Vector(point);M=sample['transforms_mm'][index]
            expected=[sum(M[r][c]*point[c]*1000 for c in range(3))+M[r][3] for r in range(3)]
            max_error=max(max_error,(world*1000-Vector(expected)).length)
    build_scenes.linear_keys(o)
scene.frame_end=3;scene.frame_set(1)
path=ROOT/'animation/scenes/ax2_roundtrip.blend';path.parent.mkdir(exist_ok=True);bpy.data.libraries.write(str(path),{scene},compress=True)
report={'AX2':'PASS','blender':bpy.app.version_string,'physical_instances':2,'shared_mesh':objects[0].data==objects[1].data,'source':'SPN_r02_L4','poses':3,'selected_mesh_vertex_max_error_mm':max_error,'tolerance_mm':.02,'units':'native mm -> local mesh m and supplied transforms_m once','scene':str(path.relative_to(ROOT)),'original_scene_preserved':'Scene' in bpy.data.scenes}
assert max_error<.02
(ROOT/'reports/animation/ax2_roundtrip.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
