"""Assemble final artifact hashes from executed revision-specific reports."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads((ROOT/p).read_text())
native=ROOT/'cad/flexor_r15_robot.FCStd';native_sha=sha(native)
reports={k:read(p) for k,p in {
    'native':'reports/verification/r15_native_checks.json','step':'reports/verification/r15_assembly_export.json',
    'identity':'reports/verification/r15_identity.json','motion':'reports/verification/r15_motion.json',
    'numeric':'reports/verification/r15_numeric_cycle.json','ax':'reports/animation/ax01_r15.json',
    'preview':'reports/animation/r15_preview_qa.json','saved_scene':'reports/animation/r15_saved_scene.json',
    'bom':'reports/verification/r15_bom.json'}.items()}
for key in ('native','step','motion','numeric','ax','saved_scene','bom'):
    assert reports[key]['native_sha256']==native_sha,key
assert reports['identity']['native_files_sha256']['r15']==native_sha
assert reports['native']['status']==reports['step']['status']=='PASS'
assert reports['motion']['status']=='PASS_BOUNDED_ADDITIVE_DELTA_R15'
assert reports['numeric']['status']=='PASS_NUMERICAL_FULL_CYCLE'
assert reports['ax']['AX0']==reports['ax']['AX1']=='PASS'
assert reports['preview']['status']=='PASS_SMALL_PREVIEW_QA'
preserved=read('reports/verification/r14_checkpoint_summary.json')['artifacts']
assert all(sha(ROOT/name)==meta['sha256'] for name,meta in preserved.items())
paths=set()
for pattern in ('src/*r15.py','src/*r15.FCMacro','animation/blender/*r15.py','parameters/assembly_r15.json',
                'cad/flexor_r15_robot.FCStd','cad/prototypes/r15*.FCStd','exports/step/r15/*',
                'animation/motion/*r15.json','animation/schema/*r15.json','animation/assets/r15/*',
                'animation/previews/r15*','bom/*r15.csv','reports/animation/*r15*.json',
                'reports/verification/r15*.json','reports/views/r15*','reports/views/r14*matched*.png',
                'reports/reviews/r15*.md','docs/25_sculpted_geometry_refinement_r15.md'):
    paths.update(p for p in ROOT.glob(pattern) if p.is_file())
paths.discard(ROOT/'reports/verification/r15_checkpoint_summary.json')
report={'date':'2026-10-16','revision':'r15','status':'RESEARCH_CAD_CANDIDATE_VERIFIED_WITH_FINITE_SCOPE',
        'branch':'feat/flexor-r15-sculpted','baseline_commit':'1a7781349a336020e235e80e17b9336a545842a8',
        'geometry_checkpoint_commit':'fc5bdf4','native_sha256':native_sha,
        'physical_instances':455,'source_definitions':108,'changed_sources':1,'unchanged_sources':107,
        'geometry':'Four continuous shelf-to-case shoulder pads and twelve additive R1 root blends; no baseline material removed',
        'frame_volume_mm3':reports['motion']['frame_volume_mm3'],
        'gates':{'native_reopen_recompute_edit_restore':'PASS','STEP_455_solids':'PASS','BOM_identity':'PASS',
                 'AX0':'PASS','AX1':'PASS','numeric_cycle_361_poses':'PASS',
                 'finite_delta_cycle_91_poses':'PASS','finite_full_frame_coordination_9_poses':'PASS',
                 'small_Blender_preview':'PASS','continuous_clearance':'NOT_VERIFIED','fabrication_release':'BLOCKED'},
        'source_to_world':{'native_AX_maximum_reprojection_error_mm':max(r['local_to_world_max_error_mm'] for r in reports['ax']['frame_checks']),
                           'Blender_maximum_vertex_error_mm':reports['saved_scene']['maximum_source_to_world_vertex_error_mm'],
                           'verified_convention':'+X forward,+Y left,+Z up; CAD mm to Blender metres once; one source-to-world transform'},
        'r14_preservation':{'all_checkpoint_artifact_hashes_match':True,'immutable_artifact_count':len(preserved),
                            'full_r14_videos_unchanged':True},
        'application_workflow':'Installed FreeCAD MCP constructed and inspected native geometry. Read-only isolated installed FreeCAD processes completed native/exchange/pose checks and offscreen matched views. Installed Blender MCP constructed the preview; isolated Blender packaged/rendered/reopened it.',
        'live_session_limit':'Live FreeCAD GUI dispatcher stopped starting requests after the detached sweep; session preserved, no restart or unsaved-session overwrite. Saved r15 candidate independently verified.',
        'limits':['Source-informed morphology; new radius and shoulder dimensions are design assumptions.',
                  'Finite sampling does not prove continuous or all-gait clearance.',
                  'Knees and whole motion remain prescribed; loaded passive response unsolved.',
                  'Supplier mounting/output datums, fits, shaft/bearing retention, structural/fatigue capacity and fabrication process remain unqualified.',
                  'Historical complete source rebuild remains unqualified; r14 native checkpoint is the accepted reconstruction base.',
                  'Full r15 polished animation videos and drawings were not produced.'],
        'artifacts':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(paths)}}
(ROOT/'reports/verification/r15_checkpoint_summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'],len(paths),'hashed artifacts')
