"""Serial resumable production from frozen scene snapshots, then atomic encoding."""
import subprocess,sys,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BLENDER='/snap/blender/current/blender'
JOBS=[('exploded_assembly',720,30),('active_spine_mechanism',900,60),('spine_leg_coordination',1200,60)]
if len(sys.argv)>1:JOBS=[j for j in JOBS if j[0] in sys.argv[1:]]
start=time.monotonic();results=[]
for name,count,fps in JOBS:
 scene=ROOT/'animation/scenes'/(name+'.blend');sha=hashlib.sha256(scene.read_bytes()).hexdigest()
 print('PRODUCTION_START',name,sha,flush=True)
 for stage,args in [('readback',[BLENDER,'-b',str(scene),'--python',str(ROOT/'animation/blender/verify_saved_scene.py'),'--',name]),
                    ('render',[BLENDER,'-b',str(scene),'--python',str(ROOT/'animation/blender/render_frames.py'),'--','--scene',name])]:
  with (ROOT/'reports/tmp'/(name+'_'+stage+'_production.log')).open('w') as log:
   subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
  assert hashlib.sha256(scene.read_bytes()).hexdigest()==sha
  print('PRODUCTION_STAGE_PASS',name,stage,flush=True)
 args=[sys.executable,str(ROOT/'animation/blender/encode_verify.py'),'--input-pattern',str(ROOT/'animation/output/frames'/name/'frame_%06d.png'),'--output',str(ROOT/'animation/output'/(name+'.mp4')),'--frame-count',str(count),'--fps',str(fps),'--overwrite']
 with (ROOT/'reports/animation'/(name+'_video.json')).open('w') as log:subprocess.run(args,cwd=ROOT,stdout=log,check=True)
 results.append({'scene':name,'blend_sha256':sha,'frames':count,'fps':fps,'duration_s':count/fps,'status':'ENCODE_AND_FULL_DECODE_PASS'})
 (ROOT/'reports/animation/production_render_completion.json').write_text(json.dumps({'results':results,'elapsed_s':time.monotonic()-start},indent=2)+'\n')
 print('PRODUCTION_VIDEO_PASS',name,flush=True)
print('PRODUCTION_COMPLETE',round(time.monotonic()-start,2),flush=True)
