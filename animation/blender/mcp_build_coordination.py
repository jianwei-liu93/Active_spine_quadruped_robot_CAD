import sys, importlib
sys.path.insert(0,'/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD/animation/blender')
import build_scenes,presentation_shots
importlib.reload(build_scenes);importlib.reload(presentation_shots)
_coordination_scene=build_scenes.build('spine_leg_coordination','animation/motion/production_coordination_v2_r10.json')
print('BUILT',_coordination_scene.name)
