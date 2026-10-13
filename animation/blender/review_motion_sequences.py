"""Decoded adjacent-frame review sheets around mechanical and camera events."""
from pathlib import Path
import subprocess,json,sys
from PIL import Image,ImageDraw
from encode_verify import discover_encoder
ROOT=Path(__file__).resolve().parents[2];ff,_,_=discover_encoder(None,None)
EVENTS={'active_spine_mechanism':[(2,'isolation boundary'),(3.2,'linkage posture'),(5,'cycle seam'),(12,'whole robot return')],
        'spine_leg_coordination':[(.25,'hip and prescribed knee extremum'),(2.75,'hind backswing onset'),(5,'cycle seam'),(15,'hind wheel and routing view')]}
folder=ROOT/'reports/animation/previews/adjacent_motion';folder.mkdir(parents=True,exist_ok=True)
for name,events in EVENTS.items():
 if len(sys.argv)>1 and name not in sys.argv[1:]:continue
 sheet=Image.new('RGB',(1440,1200),(225,229,232));draw=ImageDraw.Draw(sheet);records=[]
 for j,(t,label) in enumerate(events):
  for k,delta in enumerate([-1/60,0,1/60]):
   seconds=t+delta;p=folder/(name+'_'+str(j)+'_'+str(k)+'.png')
   subprocess.run([ff,'-v','error','-ss',str(seconds),'-i',str(ROOT/'animation/output'/(name+'.mp4')),'-frames:v','1','-y',str(p)],check=True)
   sheet.paste(Image.open(p).resize((480,270)),(k*480,j*300));draw.text((k*480+8,j*300+275),label+' '+str(round(seconds,5))+'s',fill=(0,0,0));records.append({'event':label,'seconds':seconds})
 dest=ROOT/'reports/animation'/(name+'_adjacent_frames.png');sheet.save(dest)
 (ROOT/'reports/animation'/(name+'_adjacent_frames.json')).write_text(json.dumps({'sheet':str(dest.relative_to(ROOT)),'decoded_samples':records,'visual_acceptance':'requires lead inspection'},indent=2)+'\n')
 print('ADJACENT_FRAMES_EXTRACTED',name,flush=True)
