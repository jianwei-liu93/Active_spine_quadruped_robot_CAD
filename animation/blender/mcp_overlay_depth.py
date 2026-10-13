import bpy,sys,importlib
from pathlib import Path
ROOT=Path('/home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD');sys.path.insert(0,str(ROOT/'animation/blender'))
import build_scenes;importlib.reload(build_scenes)
for name in ('exploded_assembly','active_spine_mechanism','spine_leg_coordination'):
 scene=bpy.data.scenes[name];bpy.context.window.scene=scene
 for obj in scene.objects:
  if obj.parent!=scene.camera:continue
  if obj.type=='FONT':
   obj.location.z=-.003
   if obj.animation_data and obj.animation_data.action:
    for layer in obj.animation_data.action.layers:
     for strip in layer.strips:
      for bag in strip.channelbags:
       for curve in bag.fcurves:
        if curve.data_path=='location' and curve.array_index==2:
         for k in curve.keyframe_points:k.co[1]=-.003
  if obj.type=='MESH' and obj.data.shape_keys:
   for k in obj.data.shape_keys.key_blocks:
    for v in k.data:v.co.z=-.004
  if obj.type=='CURVE':
   for sp in obj.data.splines:
    for p in sp.points:p.co.z=-.003
 build_scenes.save_scene(scene);print('OVERLAY_DEPTH_SAVED',name)
