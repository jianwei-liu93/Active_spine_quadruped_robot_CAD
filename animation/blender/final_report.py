"""Aggregate executed checks and hashes after all three video reviews exist."""
from pathlib import Path
import json,hashlib,statistics
ROOT=Path(__file__).resolve().parents[2]
def load(rel):return json.loads((ROOT/rel).read_text())
def sha(rel):return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
m=load('animation/motion/production_r10.json');snapshot=load('reports/animation/frozen_scenes.json')
assert sha(m['source']['cad_path'])==m['source']['cad_sha256']==snapshot['canonical_cad_sha256']
for rel,digest in m['production']['source_files_sha256'].items():assert sha(rel)==digest,rel
results=[]
for frozen in snapshot['scenes']:
 name=Path(frozen['path']).stem
 assert sha(frozen['path'])==frozen['sha256']
 readback=load('reports/animation/'+name+'_readback.json');assert readback['status']=='PASS' and readback['blend_sha256']==frozen['sha256']
 signature=load('animation/output/frames/'+name+'/render_signature.json');assert signature['blend_sha256']==frozen['sha256']
 video=load('reports/animation/'+name+'_video.json');assert video['decode_check']=='passed' and video['width']==1920 and video['height']==1080
 review=load('reports/animation/'+name+'_decoded_review.json');item=next(x for x in review['results'] if x['shot']==name)
 assert not item['basic_black_candidates'] and not item['default_metadata_mismatches']
 path='animation/output/'+name+'.mp4';assert sha(path)==item['video_sha256']
 visual=load('reports/animation/'+name+'_visual_review.json');assert visual['status'].startswith('PASS') and visual['video_sha256']==sha(path)
 rows=[json.loads(line) for line in (ROOT/'animation/output/frames'/name/'render_progress.jsonl').read_text().splitlines()]
 assert len({x['frame'] for x in rows})==video['frames']
 seconds=[x['seconds'] for x in rows]
 results.append({'scene':name,'blend_path':frozen['path'],'blend_sha256':frozen['sha256'],'video_path':path,'video_sha256':sha(path),'video_bytes':(ROOT/path).stat().st_size,'frames':video['frames'],'fps':video['fps'],'duration_s':video['duration_seconds'],'resolution':[video['width'],video['height']],'decode':'PASS','saved_scene_readback':'PASS','visual_review':visual['status'],'representative_decoded_frames':len(item['extracted_frames']),'review_clip_count':len(item['review_clips']),'black_candidates':0,'render_seconds_sum':sum(seconds),'median_seconds_per_frame':statistics.median(seconds),'mean_seconds_per_frame_excluding_startup':statistics.mean(seconds[1:]),'png_cache_bytes':sum(x['bytes'] for x in rows),'physical_instances':readback['physical_instances'],'max_sampled_world_vertex_error_mm':readback['max_imported_world_vertex_error_mm']})
report={'date':'2026-10-13','AX2':'PASS','AX3':'PASS','AX4':'PASS_WITH_DOCUMENTED_LIMITATIONS','cad_revision':'r10','mechanical_source_commit':load('animation/source_snapshot_r10.json')['source_git_commit'],'source_cad_sha256':m['source']['cad_sha256'],'canonical_cad_and_parameter_and_motion_source_hashes_unchanged':True,'source_to_world_transform_verified':True,'runtime':load('reports/animation/blender_render_runtime.json'),'videos':results,'timeline_validation':'reports/animation/production_offline_validation.json','native_procedural_comparison':'reports/animation/procedural_surface_comparison.json','limitations':['Prescribed kinematics, with separate prescribed knees and independently prescribed winding wheel; no passive loads or dynamic locomotion simulated.','Cables are dashed routing guides; physical slack geometry remains unresolved.','Baked motion is verified at rendered integer frame times; subframe retiming or motion blur requires resampling/validation.','Exploded sequence is a presentation overview with intentional isolation cuts, not a verified assembly/service instruction. Peripheral geometry can cross the graphics area briefly during detail-camera transitions.','Finite spring surface probes and source mesh tolerance support rendered approximation, not BRep equivalence.','Existing manufacturing blockers and finite r10 clearance scopes are unchanged.','Large editable Blender projects and native comparison/frame caches are local ignored artifacts; tracked sources reproduce them.']}
(ROOT/'reports/animation/final_video_qa.json').write_text(json.dumps(report,indent=2)+'\n')
snapshot['render_status']='COMPLETE_ENCODE_DECODE_AND_REVIEW';(ROOT/'reports/animation/frozen_scenes.json').write_text(json.dumps(snapshot,indent=2)+'\n')
for result in results:
 p=ROOT/'reports/animation'/(result['scene']+'_scene.json');data=json.loads(p.read_text());data['render_status']='COMPLETE_ENCODE_DECODE_AND_REVIEW';data['packaged_blend_sha256']=result['blend_sha256'];data['video_sha256']=result['video_sha256'];p.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'AX4':report['AX4'],'videos':len(results),'frames':sum(x['frames'] for x in results),'render_seconds':sum(x['render_seconds_sum'] for x in results)},indent=2))
