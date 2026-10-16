"""Hash and reconcile the executed r15b revision gates, preserving r15 evidence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads((ROOT/p).read_text())


def run():
    native=ROOT/'cad/flexor_r15b_robot.FCStd';digest=sha(native)
    paths={'identity':'reports/verification/r15b_identity.json',
           'native':'reports/verification/r15b_native.json',
           'motion':'reports/verification/r15b_motion.json',
           'step':'reports/verification/r15b_step.json',
           'ax':'reports/animation/ax01_r15b.json',
           'bom':'reports/verification/r15b_bom.json'}
    reports={k:read(p) for k,p in paths.items()}
    assert all(r['native_sha256']==digest for r in reports.values())
    assert all(reports[k]['status']=='PASS' for k in ('identity','native','step'))
    assert reports['motion']['status']=='PASS_FINITE_CHANGED_PAIRS'
    assert reports['ax']['AX0']==reports['ax']['AX1']=='PASS'
    assert reports['bom']['status']=='PASS_SOURCE_INVENTORY_BOM'
    prior=read('reports/verification/r15_checkpoint_summary.json')['artifacts']
    assert all(sha(ROOT/name)==row['sha256'] for name,row in prior.items())
    manifest=read('reports/views/r15b_capture_manifest.json')
    assert manifest['native_sha256']==digest
    assert all(sha(ROOT/r['path'])==r['sha256'] for r in manifest['captures'])
    old=read('animation/motion/ax01_r15.json');new=read('animation/motion/ax01_r15b.json')
    old_instances={r['instance_id']:r for r in old['instances']}
    new_instances={r['instance_id']:r for r in new['instances']}
    assert set(old_instances)==set(new_instances)
    assert all(old_instances[n]['source_object_name']==r['source_object_name'] for n,r in new_instances.items())
    part_number_changes=[n for n,r in new_instances.items() if old_instances[n]['part_number']!=r['part_number']]
    assert len(part_number_changes)==12
    cycle=reports['motion']['cycle'];paper=reports['motion']['paper_profile']
    assert len(cycle)==91 and len(paper)==9
    assert sum(len(r['forbidden_overlaps']) for r in cycle+paper)==0
    artifacts=set()
    for pattern in ('src/*r15b.py','parameters/assembly_r15b.json','cad/flexor_r15b_robot.FCStd',
                    'exports/step/r15b/*','animation/schema/*r15b.json','animation/motion/*r15b.json',
                    'bom/*r15b.csv','reports/animation/*r15b.json','reports/verification/r15b*.json',
                    'reports/reviews/r15b*.md','reports/views/r15b*','reports/views/r15_before_AB*',
                    'docs/26_symmetric_rocker_r15b.md','README.md'):
        artifacts.update(p for p in ROOT.glob(pattern) if p.is_file())
    output=ROOT/'reports/verification/r15b_checkpoint_summary.json';artifacts.discard(output)
    report={'status':'RESEARCH_CAD_CANDIDATE_VERIFIED_WITH_FINITE_SCOPE','date':'2026-10-16',
            'revision':'r15b','branch':'feat/flexor-r15-sculpted','native_sha256':digest,
            'baseline_native_sha256':sha(ROOT/'cad/flexor_r15_robot.FCStd'),
            'physical_instances':455,'source_definitions':108,'changed_source_count':8,'strict_unchanged_sources':100,
            'part_number_changed_instances':part_number_changes,
            'geometry':'Four centred-depth, tangent-arc AB rockers, single A eye and rounded B-only fork;four nominal A-spacer sources resized',
            'gates':{'native_reopen_forced_recompute_edit_restore':'PASS','depth_symmetry_four_rockers':'PASS',
                     'STEP_455_solids':'PASS','AX0':'PASS','AX1':'PASS','BOM':'PASS',
                     'numeric_closure_361':'PASS','changed_pair_cycle_91':'PASS','changed_pair_coordination_9':'PASS',
                     'continuous_clearance':'NOT_VERIFIED','loaded_equilibrium':'NOT_SOLVED',
                     'fabrication_release':'NOT_QUALIFIED','r15b_Blender_video':'NOT_PRODUCED'},
            'clearance':{'pairs_per_pose':7144,'pose_count':100,
                         'pair_decisions':sum(r['pair_count'] for r in cycle+paper),
                         'occ_checks':sum(r['occ_checks'] for r in cycle+paper),
                         'bbox_exclusions':sum(r['bbox_excluded'] for r in cycle+paper),
                         'cached_rigid_pairs':sum(r['cached_rigid_pairs'] for r in cycle+paper),
                         'positive_volume_intersections':0},
            'source_to_world_verified':True,
            'maximum_AX_vertex_reprojection_error_mm':max(r['local_to_world_max_error_mm'] for r in reports['ax']['frame_checks']),
            'stable_instance_and_source_mapping':True,'rocker_local_frames_and_instance_matrices_unchanged':True,
            'MotionMap_unchanged':True,'six_commands_and_separate_knees_preserved':True,
            'prior_r15_artifacts_preserved':len(prior),
            'application_workflow':'Lead installed FreeCAD MCP construction/inspection; independent installed FreeCADCmd checks on saved/private copies',
            'limits':['Morphology is source-informed; exact section dimensions are assumptions.',
                      'Finite changed-pair samples do not prove continuous or all-gait clearance.',
                      'Strength, fatigue, bearing fits/race capture/thrust, supplier datums, process and access remain unqualified.',
                      'Historical complete rebuild is unqualified; migration uses preserved native r15.',
                      'Earlier r15/r14 videos retain previous geometry; no new video is claimed.'],
            'artifacts':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(artifacts)}}
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    result=run();print(result['status'],len(result['artifacts']),'hashed artifacts')
