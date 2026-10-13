"""Turn an isolated MCP-written Blender library into a directly opening project.

Run in a fresh Blender process; never saves the live authoring GUI's file.
"""
import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
name=sys.argv[sys.argv.index('--')+1];scene=bpy.data.scenes[name]
bpy.context.window.scene=scene
for other in list(bpy.data.scenes):
 if other!=scene:bpy.data.scenes.remove(other)
assert len([o for o in scene.objects if 'instance_id' in o])==scene['physical_instances']
scene.frame_set(1);scene['standalone_project']=True
path=ROOT/'animation/scenes'/(name+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
print('STANDALONE_SCENE_SAVED',name,hashlib.sha256(path.read_bytes()).hexdigest())
