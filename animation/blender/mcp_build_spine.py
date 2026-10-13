import sys, importlib
sys.path.insert(0,'/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/animation/blender')
import build_scenes
importlib.reload(build_scenes)
_spine_scene=build_scenes.build('active_spine_mechanism')
print('BUILT',_spine_scene.name)
