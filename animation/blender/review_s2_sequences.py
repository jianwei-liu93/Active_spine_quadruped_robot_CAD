"""Decoded adjacent-frame sheets around the S2 motion cycle and camera cuts."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw
from encode_verify import discover_encoder
ROOT=Path(__file__).resolve().parents[2];name='spine_leg_coordination_s2';ff,_,_=discover_encoder(None,None)
folder=ROOT/'reports/animation/previews/s2_adjacent';folder.mkdir(parents=True,exist_ok=True)
events=[(1.666666667,'body/joint cycle seam'),(6.,'spine shot cut'),(12.,'hind shot cut'),(18.,'fore shot cut'),(22.,'overview return')]
sheet=Image.new('RGB',(1440,1500),(230,230,230));draw=ImageDraw.Draw(sheet);records=[]
for j,(t,label) in enumerate(events):
 for k,dt in enumerate((-1/60,0,1/60)):
  p=folder/f'{j}_{k}.png';seconds=t+dt
  subprocess.run([ff,'-v','error','-ss',str(seconds),'-i',str(ROOT/'animation/output'/f'{name}.mp4'),'-frames:v','1','-y',str(p)],check=True)
  with Image.open(p) as im:sheet.paste(im.resize((480,270)),(k*480,j*300))
  draw.text((k*480+8,j*300+277),f'{label} {seconds:.5f}s',fill=(0,0,0));records.append({'event':label,'seconds':seconds})
sheet.save(ROOT/'reports/animation'/f'{name}_adjacent_frames.png')
(ROOT/'reports/animation'/f'{name}_adjacent_frames.json').write_text(json.dumps({'decoded_samples':records,'visual_acceptance':'PENDING_LEAD_INSPECTION'},indent=2)+'\n')
print('S2_ADJACENT_EXTRACTED')
