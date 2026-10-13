"""Resume frozen Blender frame renders; invoked with installed Blender -b."""
from pathlib import Path
import bpy, sys, json, hashlib, time, argparse, struct, zlib
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scene',required=True);p.add_argument('--frames',nargs='*',type=int);p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int);p.add_argument('--preview',action='store_true');p.add_argument('--percent',type=int,default=100)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);scene=bpy.data.scenes[args.scene];bpy.context.window.scene=scene
assert scene.render.engine=='BLENDER_EEVEE'
folder=ROOT/('reports/animation/previews/'+args.scene if args.preview else 'animation/output/frames/'+args.scene);
if args.preview:folder=folder/hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()[:8]
folder.mkdir(parents=True,exist_ok=True)
scene.render.resolution_percentage=args.percent
signature={'blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y,args.percent],'fps':scene.render.fps,'frame_end':scene.frame_end}
try:
 import gpu
 signature['gpu']={'vendor':gpu.platform.vendor_get(),'renderer':gpu.platform.renderer_get(),'version':gpu.platform.version_get()}
except Exception as e:signature['gpu']={'query':str(e)}
signature_path=folder/'render_signature.json'
if signature_path.exists():assert json.loads(signature_path.read_text())==signature,'Scene/config changed; use a fresh output directory'
else:signature_path.write_text(json.dumps(signature,indent=2)+'\n')
def valid_png(path):
    try:
        raw=path.read_bytes()
        if raw[:8]!=b'\x89PNG\r\n\x1a\n':return False
        offset=8;compressed=[];size=None
        while offset<len(raw):
            length=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8];chunk=raw[offset+8:offset+8+length]
            if zlib.crc32(kind+chunk)&0xffffffff!=struct.unpack('>I',raw[offset+8+length:offset+12+length])[0]:return False
            if kind==b'IHDR':
                w,h,depth,color,compression,filtration,interlace=struct.unpack('>IIBBBBB',chunk)
                if depth!=8 or color!=2 or interlace!=0:return False
                size=h*(w*3+1)
            if kind==b'IDAT':compressed.append(chunk)
            offset+=length+12
            if kind==b'IEND':return offset==len(raw) and len(zlib.decompress(b''.join(compressed)))==size
        return False
    except (OSError,ValueError,struct.error,zlib.error):return False

selected=args.frames or range(args.start,(args.end or scene.frame_end)+1)
records=[];start=time.monotonic()
for f in selected:
 assert scene.frame_start<=f<=scene.frame_end
 path=folder/('frame_%06d.png'%f)
 # CRC and deflate checks reject corrupt caches before resuming.
 if path.exists() and valid_png(path):continue
 scene.frame_set(f);scene.render.filepath=str(path);tick=time.monotonic()
 bpy.ops.render.render(write_still=True,scene=scene.name)
 record={'frame':f,'seconds':time.monotonic()-tick,'bytes':path.stat().st_size};records.append(record)
 with (folder/'render_progress.jsonl').open('a') as out:out.write(json.dumps(record)+'\n')
 print('FLEXOR_RENDER',json.dumps(record),flush=True)
print('FLEXOR_RENDER_COMPLETE',len(records),'elapsed',time.monotonic()-start,flush=True)
