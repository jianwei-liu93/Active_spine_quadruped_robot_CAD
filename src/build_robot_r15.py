"""Lead-only additive r15 integration from the preserved native r14 checkpoint."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def integrate(doc):
    import sculpted_frame_r15,shelf_shoulders_r15
    baseline=ROOT/'cad/flexor_r14_robot.FCStd'
    cfg=json.loads((ROOT/'parameters/assembly_r15.json').read_text())
    if hashlib.sha256(baseline.read_bytes()).hexdigest()!=cfg['sculpted_geometry_r15']['baseline_cad_sha256']:
        raise RuntimeError('Protected r14 checkpoint changed')
    target=ROOT/'cad/flexor_r15_robot.FCStd'
    if target.exists():raise RuntimeError('Preserve existing r15 progress before another integration')
    body=doc.LumbarIntegrated1.LinkedObject
    roots=sculpted_frame_r15.apply(body,cfg)
    shoulders=shelf_shoulders_r15.apply(body,cfg)
    doc.Label='FLEXOR r15 continuous lumbar shelf shoulders and blended support roots'
    doc.DesignParameters.Revision='r15'
    doc.DesignParameters.ParameterFile='parameters/assembly_r15.json; parameters/candidate_r02.json'
    doc.PoseController.ParameterRevision='r15'
    doc.PoseController.PrescribedMotionConfigR07=json.dumps(cfg)
    body.RefinementR15='Four additive shelf-to-case shoulders and twelve root blends; source-informed, dimensions and structural capacity provisional'
    doc.recompute();doc.saveAs(str(target))
    report={'status':'INTEGRATED_PENDING_REVISION_GATES','baseline_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),
            'native_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'config_sha256':hashlib.sha256((ROOT/'parameters/assembly_r15.json').read_bytes()).hexdigest(),
            'helper_sha256':{n:hashlib.sha256((ROOT/'src'/n).read_bytes()).hexdigest() for n in
                ('build_robot_r15.py','sculpted_frame_r15.py','shelf_shoulders_r15.py')},
            'roots':roots,'shoulders':shoulders,'native_path':str(target.relative_to(ROOT)),
            'changed_sources':[body.Name],'changed_instances':['LumbarIntegrated1']}
    (ROOT/'reports/verification/r15_integration.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
