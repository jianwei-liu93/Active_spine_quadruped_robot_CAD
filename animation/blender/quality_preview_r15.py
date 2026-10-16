"""Encode and verify the bounded 60-frame preview; ordinary host Python."""
import argparse,hashlib,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageSequence
from encode_verify import discover_encoder
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--encode',action='store_true');args=parser.parse_args()
ffmpeg,ffprobe,version=discover_encoder(None,None)
folder=ROOT/'animation/previews';folder.mkdir(parents=True,exist_ok=True)
mp4=folder/'r15_spine_leg_coordination.mp4';gif=folder/'r15_spine_leg_coordination.gif'
frames=ROOT/'reports/tmp/r15/blender_frames'
if args.encode:
    base=[ffmpeg,'-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(frames/'r15_preview_%04d.png')]
    subprocess.run(base+['-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(mp4)],check=True)
    subprocess.run(base+['-filter_complex','[0:v]split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0',str(gif)],check=True)
probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(mp4)]))
stream=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (stream['width'],stream['height'],int(stream['nb_read_frames']),stream['r_frame_rate'])==(640,360,60,'12/1')
assert abs(float(probe['format']['duration'])-5.)<.01
subprocess.run([ffmpeg,'-v','error','-i',str(mp4),'-f','null','-'],check=True)
images=[Image.open(frames/('r15_preview_%04d.png'%i)).convert('RGB') for i in range(1,61)]
assert all(im.size==(640,360) for im in images)
manifest=json.loads((frames/'render_manifest.json').read_text())
assert manifest['resolution']==[640,360] and manifest['frames']==60
differences=[sum(ImageStat.Stat(ImageChops.difference(images[0],images[i])).mean)/3 for i in (15,30,45)]
assert min(differences)>.1
im=Image.open(gif);duration=sum(f.info.get('duration',0) for f in ImageSequence.Iterator(im))
assert im.size==(640,360) and im.n_frames==60 and abs(duration-5000)<50
motion=json.loads((ROOT/'reports/animation/r15_preview_motion_probe.json').read_text())
matrix_delta=lambda n:max(abs(a-b) for r,s in zip(motion['1'][n]['matrix'],motion['151'][n]['matrix']) for a,b in zip(r,s))
assert matrix_delta('instance:LumbarIntegrated1')==0
assert matrix_delta('instance:foreL_thigh')>.001 and matrix_delta('instance:hindL_thigh')>.001
spring='instance:foreL_extension_Spring'
spring_delta=max(abs(a-b) for r,s in zip(motion['1'][spring]['local_first_vertices'],motion['151'][spring]['local_first_vertices']) for a,b in zip(r,s))
assert spring_delta>1e-8 and motion['1'][spring]['shape_keys']
saved=json.loads((ROOT/'reports/animation/r15_saved_scene.json').read_text())
assert saved['status']=='PASS_SAVED_BLENDER_PREVIEW' and saved['scene_sha256']==sha(ROOT/saved['scene_path'])
assert saved['minimum_normalized_image_margin']>.015
sheet=Image.new('RGB',(1280,720),'white')
for j,i in enumerate((0,15,30,45)):sheet.paste(images[i],((j%2)*640,(j//2)*360))
sheet_path=ROOT/'reports/views/r15_preview_contact_sheet.png';sheet.save(sheet_path)
records=[mp4,gif,sheet_path,ROOT/'animation/assets/r15/lumbar_source.json',ROOT/'animation/motion/geometry_preview_r15.json',ROOT/'reports/animation/r15_saved_scene.json']
report={'status':'PASS_SMALL_PREVIEW_QA','frames':60,'fps':12,'duration_s':5,'resolution':[640,360],
        'full_mp4_decode':'PASS','gif_frames':im.n_frames,'gif_duration_ms':duration,'sample_image_difference_mean_rgb':differences,
        'foreleg_matrix_change':matrix_delta('instance:foreL_thigh'),'hindleg_matrix_change':matrix_delta('instance:hindL_thigh'),
        'spring_local_vertex_change_m':spring_delta,'lumbar_transform_unchanged':True,
        'saved_blender_scene':'PASS','ffmpeg':version,'artifacts':{str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in records},
        'all_sample_framing_minimum_margin':saved['minimum_normalized_image_margin'],
        'limits':'Five-second geometry interoperability preview using inherited prescribed r14 kinematics; full videos unchanged; no loaded dynamics or full future animation release.'}
(ROOT/'reports/animation/r15_preview_qa.json').write_text(json.dumps(report,indent=2)+'\n')
print('R15_PREVIEW_QA_PASS',json.dumps({k:report[k] for k in ('frames','fps','duration_s','resolution','spring_local_vertex_change_m')}))
