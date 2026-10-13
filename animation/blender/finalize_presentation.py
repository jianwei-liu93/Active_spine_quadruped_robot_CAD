import bpy,sys,importlib,json
from pathlib import Path
ROOT=Path('/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD')
sys.path.insert(0,str(ROOT/'animation/blender'))
import build_scenes
importlib.reload(build_scenes)
data=build_scenes.load_manifest();mats=build_scenes.materials();items={i['instance_id']:i for i in data['instances']}
for name in ('exploded_assembly','active_spine_mechanism','spine_leg_coordination'):
 scene=bpy.data.scenes[name];bpy.context.window.scene=scene
 for obj in scene.objects:
  if 'instance_id' in obj:
   item=items[obj['instance_id']];meta=data['production']['component_metadata'][item['freecad_object_name']]
   obj.material_slots[0].material=build_scenes.choose_mat(item,meta,mats)
 scene['manifest_sha256']=__import__('hashlib').sha256((ROOT/'animation/motion/production_r10.json').read_bytes()).hexdigest()
 build_scenes.save_scene(scene)
 print('FINAL_PRESENTATION_SAVED',name)
