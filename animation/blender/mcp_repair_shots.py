import bpy,sys,importlib
from pathlib import Path
ROOT=Path('/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD');sys.path.insert(0,str(ROOT/'animation/blender'))
import build_scenes,presentation_shots
importlib.reload(build_scenes);importlib.reload(presentation_shots)
mats=build_scenes.materials()
for name in ('exploded_assembly','active_spine_mechanism','spine_leg_coordination'):
 scene=bpy.data.scenes[name];bpy.context.window.scene=scene;scene.frame_set(1)
 # Remove previous presentation callouts only; preserve all physical objects.
 for obj in list(scene.objects):
  if any(obj.name.startswith(p) for p in ('COMMON CRANK','UPPER SLIDER','LOWER SLIDER','HIND WINDING WHEEL','FORELEG MODULE','HIND MODULE')):
   bpy.data.objects.remove(obj,do_unlink=True)
 if name=='exploded_assembly':
  scene.camera.animation_data_clear();scene.camera.data.animation_data_clear()
  for obj in scene.objects:
   if obj.parent==scene.camera:obj.animation_data_clear();obj.scale=(1,1,1)
 objects={o['instance_id']:o for o in scene.objects if 'instance_id' in o}
 presentation_shots.apply(scene,objects,mats);build_scenes.save_scene(scene);print('PRESENTATION_REPAIR_SAVED',name)
