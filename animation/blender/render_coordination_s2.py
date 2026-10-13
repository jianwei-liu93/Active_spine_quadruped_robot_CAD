"""Render/encode an immutable S2 scene after fresh readback and preview approval."""
from pathlib import Path
import subprocess,sys,json,hashlib,time
ROOT=Path(__file__).resolve().parents[2];BLENDER='/snap/blender/current/blender';name='spine_leg_coordination_s2'
scene=ROOT/'animation/scenes'/(name+'.blend');digest=hashlib.sha256(scene.read_bytes()).hexdigest();start=time.monotonic()
qa=json.loads((ROOT/'reports/animation'/f'{name}_readback.json').read_text())
assert qa['status']=='PASS' and qa['blend_sha256']==digest
with (ROOT/'reports/tmp/s2_render.log').open('w') as log:
 subprocess.run([BLENDER,'-b',str(scene),'--python',str(ROOT/'animation/blender/render_frames.py'),'--','--scene',name],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
assert hashlib.sha256(scene.read_bytes()).hexdigest()==digest
with (ROOT/'reports/animation'/f'{name}_video.json').open('w') as log:
 subprocess.run([sys.executable,str(ROOT/'animation/blender/encode_verify.py'),'--input-pattern',str(ROOT/'animation/output/frames'/name/'frame_%06d.png'),'--output',str(ROOT/'animation/output'/f'{name}.mp4'),'--frame-count','1500','--fps','60','--overwrite'],cwd=ROOT,stdout=log,check=True)
report={'status':'ENCODE_AND_FULL_DECODE_PASS','scene':name,'blend_sha256':digest,'elapsed_seconds':time.monotonic()-start,'frames':1500,'fps':60,'duration_s':25}
(ROOT/'reports/animation'/f'{name}_production.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
