"""Fail-closed final artifact inventory; hashes files, never mutates CAD."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def require(value,message):
    if not value:raise RuntimeError(message)

def run():
    native=ROOT/'cad/flexor_r07_robot.FCStd';sha=digest(native)
    native_check=read('reports/verification/r07_native_checks.json')
    require(native_check['status']=='PASS' and native_check['native_sha256']==sha,'Native check stale or failed')
    motion=read('reports/verification/r07_motion_partitions/full_summary.json')
    require(motion['status']=='PASS' and motion['records_found']==985 and motion['native_sha256']==sha,'Full sampled motion incomplete/stale')
    exports=read('reports/package_manifest_r07.json')
    require(exports['status']=='EXPORTS_AND_STEP_ROUNDTRIP_VALIDATED_NO_FABRICATION_RELEASE','Export package not accepted')
    require(exports['native_document']['sha256']==sha and exports['native_file_unchanged'],'Export source stale')
    drawings=read('drawings/r07/drawing_manifest_r07.json')
    require(drawings['canonical_robot_sha256']==sha and drawings['sheet_count']==67 and drawings['dimension_count']==311,'Drawing source/count mismatch')
    require(drawings['visual_review']=='PASS' and drawings['pdf_exports']=='COMPLETE','Drawing visual/export acceptance incomplete')
    require(drawings['native_companion_sha256']==digest(ROOT/'cad/flexor_r07_drawings.FCStd'),'Companion digest stale')
    profiles=read('exports/profiles/r07/profile_manifest_r07.json')
    require(profiles['status']=='PASS_EXACT_PROFILE_READBACK' and profiles['source_sha256']==sha and profiles['profile_count']==3,'Profile validation stale/incomplete')
    reproduction=read('reports/verification/r07_source_reproduction.json')
    require(reproduction['status']=='PASS' and reproduction['native_sha256']==sha,'Source reproduction not accepted')
    review=read('reports/reviews/r07_final_review.json')
    require(review['status']=='PASS_CANDIDATE_WITH_RELEASE_BLOCKERS' and review['native_sha256']==sha,'Final independent review incomplete/stale')
    paths={native,ROOT/'cad/flexor_r07_drawings.FCStd',ROOT/'drawings/flexor_r07_drawing_book.pdf',ROOT/'docs/flexor_r07_assembly_calibration.pdf'}
    for pattern in ('src/*.py','src/*.cpp','tests/*.py','macros/*.FCMacro','parameters/*.json','docs/*.md','bom/*r07.csv',
                    'exports/step/r07/**/*','exports/print/r07/**/*','exports/profiles/r07/**/*','drawings/r07/**/*',
                    'reports/motion/r07/*','reports/views/r07*.png','reports/views/drawings_r07/*','reports/views/manual_r07/*',
                    'reports/verification/r07_*.json','reports/verification/r07_motion_partitions/*.json','reports/reviews/*r07*.md'):
        paths.update(p for p in ROOT.glob(pattern) if p.is_file())
    paths.add(ROOT/'reports/package_manifest_r07.json');paths.add(ROOT/'reports/reviews/r07_final_review.json')
    paths.update(ROOT/p for p in ('README.md','AGENTS.md','.gitattributes','reports/sources/supplier_completion_r07.md'))
    records=[]
    for p in sorted(paths):
        require(p.exists() and p.stat().st_size>0,'Missing/empty artifact: '+str(p))
        records.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':digest(p)})
    output={'status':'CAD_PACKAGE_VERIFIED','revision':'r07','native_sha256':sha,'physical_instances':486,
            'native_custom_bodies':95,'bom_part_numbers':105,'drawing_sheets':67,'native_dimensions':311,
            'full_motion_samples':985,'scope':'Reviewable editable CAD candidate; exact finite trajectories in motion manifest',
            'fabrication_release':'BLOCKED','physical_validation':'NOT_RUN','continuous_clearance':'NOT_RUN',
            'release_blockers_document':'docs/16_candidate_package_r07.md','file_count':len(records),'files':records,
            'inventory_limit':'Historical diagnostics may record failed attempts; acceptance uses only the named final gates. No self hash.'}
    (ROOT/'reports/delivery_manifest_r07.json').write_text(json.dumps(output,indent=2)+'\n')
    print('CAD_PACKAGE_VERIFIED',len(records),'files',sha)
    return output

if __name__=='__main__':run()
