import sys, importlib
sys.path.insert(0,'/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/animation/blender')
import build_scenes
importlib.reload(build_scenes)
_coordination_scene=build_scenes.build('spine_leg_coordination')
print('BUILT',_coordination_scene.name)
