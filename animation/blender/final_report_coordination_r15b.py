"""Fail-closed release summary for the freshly exported r15b studio cut."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NAME='spine_leg_coordination_s2_r15b'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(rel):return json.loads((ROOT/rel).read_text())


def run():
    prefix='reports/animation/'+NAME
    rb=read(prefix+'_readback.json');production=read(prefix+'_production.json')
    video_report=read(prefix+'_video.json');visual=read(prefix+'_visual_review.json')
    adjacent=read(prefix+'_adjacent_review.json');decoded=read(prefix+'_decoded_review.json')
    source=read('animation/motion/production_coordination_r15b.json')
    presentation=read('animation/motion/presentation_coordination_s2_r15b.json')
    native=ROOT/source['source']['cad_path'];native_hash=sha(native)
    blend=ROOT/'animation/scenes'/(NAME+'.blend');blend_hash=sha(blend)
    video=ROOT/'animation/output'/(NAME+'.mp4');video_hash=sha(video)
    assert source['source']['cad_revision']=='r15b' and source['source']['cad_sha256']==native_hash
    assert source['production']['source_geometry_identity']['status']=='PASS'
    assert source['production']['source_geometry_identity']['sources_compared']==108
    assert source['production']['source_geometry_identity']['canonical_cad_sha256']==native_hash
    assert source['production']['document_unchanged'] and source['production']['native_file_unchanged']
    assert rb['status']=='PASS' and rb['blend_sha256']==blend_hash and rb['reopened_in_fresh_process']
    assert rb['physical_instances']==455 and rb['distinct_rigid_meshes']==98 and rb['procedural_instances']==10
    assert rb['frames_checked']==1500 and rb['distinct_source_samples_checked']==100
    assert rb['procedural_shape_samples_checked']==3000 and rb['camera_framing']['status']=='PASS'
    assert rb['leg_articulation']['distinct_source_samples_checked']==100
    assert min(rb['leg_articulation']['maximum_rotation_excursion_deg'].values())>1
    assert rb['maximum_root_relative_position_error_mm']<=.02
    assert rb['maximum_evaluated_procedural_local_vertex_error_m']<=1e-7
    assert rb['source_manifest_sha256']==sha(ROOT/'animation/motion/production_coordination_r15b.json')
    assert rb['presentation_manifest_sha256']==sha(ROOT/'animation/motion/presentation_coordination_s2_r15b.json')
    timeline=source['production']['timelines']['coordinated_spine_legs']
    assert rb['source_timeline_sha256']==timeline['sha256']==sha(ROOT/timeline['path'])
    for p,h in source['production']['source_files_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in presentation['helper_files_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in (('source_scene_path','source_scene_sha256'),('style_config_path','style_config_sha256'),('builder_path','builder_sha256')):
        assert sha(ROOT/presentation[p])==presentation[h],p
    assert presentation['frame_count']==1500 and presentation['fps']==60 and presentation['sample_stride']==3
    assert presentation['source_cad_sha256']==native_hash
    assert production['status']=='ENCODE_AND_FULL_DECODE_PASS'
    assert production['blend_sha256']==blend_hash and production['native_sha256']==native_hash
    assert production['frames']==1500 and production['fps']==60 and production['duration_s']==25
    assert video_report['decode_check']=='passed'
    assert video_report['frames']==1500 and video_report['fps']==60 and video_report['duration_seconds']==25
    assert video_report['width']==1920 and video_report['height']==1080
    assert video_report['codec']=='h264' and video_report['pixel_format']=='yuv420p'
    assert Path(video_report['output']).name==video.name
    assert visual['status']=='PASS_LEAD_VISUAL_REVIEW' and visual['video_sha256']==video_hash
    assert adjacent['status']=='PASS_LEAD_ADJACENT_REVIEW' and adjacent['video_sha256']==video_hash
    decoded_row=next(r for r in decoded['results'] if r['shot']==NAME)
    assert decoded_row['video_sha256']==video_hash and not decoded_row['default_metadata_mismatches']
    assert all(not r['black_check']['basic_black_candidate'] for r in decoded_row['extracted_frames'])
    assert decoded_row['video_metadata']['frame_count']==1500
    clearance=read('reports/verification/r15b_motion.json')
    assert clearance['native_sha256']==native_hash and clearance['status']=='PASS_FINITE_CHANGED_PAIRS'
    assert len(clearance['cycle'])==91 and len(clearance['paper_profile'])==9
    assert not any(r['forbidden_overlaps'] for r in clearance['cycle']+clearance['paper_profile'])
    folder=ROOT/'animation/output/frames'/NAME
    signature=read(str((folder/'render_signature.json').relative_to(ROOT)))
    assert signature['blend_sha256']==blend_hash and signature['resolution']==[1920,1080,100]
    pngs=[folder/('frame_%06d.png'%i) for i in range(1,1501)]
    assert all(p.is_file() for p in pngs)
    assert len(list(folder.glob('frame_*.png')))==1500
    png_digest=hashlib.sha256(''.join(p.name+sha(p) for p in pngs).encode()).hexdigest()
    evidence={
        'source_manifest':'animation/motion/production_coordination_r15b.json',
        'presentation_manifest':'animation/motion/presentation_coordination_s2_r15b.json',
        'source_timeline':timeline['path'],'builder':'animation/blender/build_coordination_s2_r15b.py',
        'style_config':'animation/coordination_s2_style_r15b.json',
        'readback':prefix+'_readback.json','video_report':prefix+'_video.json',
        'production_report':prefix+'_production.json','decoded_review':prefix+'_decoded_review.json',
        'visual_review':prefix+'_visual_review.json','adjacent_frame_review':prefix+'_adjacent_review.json',
        'finite_clearance_evidence':'reports/verification/r15b_motion.json'}
    report={'status':'PASS_WITH_DOCUMENTED_LIMITATIONS','scene':NAME,
            'source_hashes':{'source_cad':native_hash,'packaged_scene':blend_hash,'video':video_hash,
                             **{k:sha(ROOT/p) for k,p in evidence.items()}},
            'evidence_paths':evidence,
            'native_path':str(native.relative_to(ROOT)),'video_path':str(video.relative_to(ROOT)),
            'source_inventory':{'physical_instances':455,'source_definitions':108,'strict_saved_native_sources':108},
            'render_and_video':{'frames':1500,'fps':60,'duration_s':25,'resolution':[1920,1080],
                                'codec':'h264','pixel_format':'yuv420p','full_decode':'PASS',
                                'png_ordered_name_sha256_digest':png_digest},
            'scene_readback':rb,'decoded_review':{'status':'PASS','samples':len(decoded_row['extracted_frames'])},
            'leg_articulation':rb['leg_articulation'],
            'finite_mechanical_evidence':{'cycle_poses':91,'coordinated_poses':9,'changed_instances':16,
                                          'positive_intersections':0,'continuous_clearance':'NOT_VERIFIED'},
            'limits':['Prescribed kinematics and illustrative body pitch/translation; no dynamics or validated ground contact.',
                      'Knees are separately prescribed; springs/cables retain anchor/routing regeneration, no loaded equilibrium.',
                      'Finite changed-pair checks do not certify full all-pairs, continuous or all-gait clearance.',
                      'Detail shots intentionally crop unrelated modules and toes; full assembly is framed in overview.',
                      'Manufacturing/strength/fit blockers remain unchanged.']}
    (ROOT/(prefix+'_qa.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],video_hash)
    return report


if __name__=='__main__':run()
