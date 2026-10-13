import bpy,sys,importlib
from pathlib import Path
ROOT=Path('/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD')
sys.path.insert(0,str(ROOT/'animation/blender'))
import build_scenes,presentation_shots
importlib.reload(build_scenes);importlib.reload(presentation_shots)
mats=build_scenes.materials()
for name in ('exploded_assembly','active_spine_mechanism','spine_leg_coordination'):
 scene=bpy.data.scenes[name];bpy.context.window.scene=scene
 objects={o['instance_id']:o for o in scene.objects if 'instance_id' in o}
 presentation_shots.apply(scene,objects,mats);build_scenes.save_scene(scene);print('SHOT_REFINEMENT_SAVED',name)
