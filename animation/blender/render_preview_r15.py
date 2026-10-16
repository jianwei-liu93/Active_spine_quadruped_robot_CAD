"""Render only the small MCP-constructed r15 interoperability scene."""
import sys
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'animation/blender'))
from preview_geometry_r15 import render,SCENE_NAME,FRAMING_ORTHO_SCALE_M,stamp_source_metadata,_load_manifest
scene=bpy.data.scenes[SCENE_NAME]
if not bpy.app.background:raise RuntimeError('Package in an isolated background process, preserving the live user session')
needs_packaging=bpy.context.scene.name!=SCENE_NAME or len(bpy.data.scenes)!=1
if abs(scene.camera.data.ortho_scale-FRAMING_ORTHO_SCALE_M)>1e-7:needs_packaging=True
scene.camera.data.ortho_scale=FRAMING_ORTHO_SCALE_M
scene['preview_camera_ortho_scale_m']=FRAMING_ORTHO_SCALE_M
data,_=_load_manifest(ROOT)
target=next(o for o in scene.objects if o.get('instance_id')=='instance:LumbarIntegrated1')
stamp_source_metadata(scene,target,data,ROOT)
if bpy.context.window:bpy.context.window.scene=scene
# A scene-only library can load alongside a synthetic empty default scene.
# Package a true standalone main file whose active scene is the CAD preview.
for other in list(bpy.data.scenes):
    if other is not scene and len(other.objects)==0:bpy.data.scenes.remove(other)
scene.frame_set(1)
if needs_packaging:bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'animation/scenes/r15_geometry_interoperability_preview.blend'),compress=True)
if '--package-only' not in sys.argv:render(ROOT/'reports/tmp/r15/blender_frames')
