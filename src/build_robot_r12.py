"""Lead-owned compact reference-fidelity candidate. No Blender geometry changes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def integrate(doc, save=True, write_report=True, config=None):
    from spine_link_sections_r11 import resume
    import compact_spine_stack_r12, spine_bars_r12, torso_contours_r12
    b=resume(doc)
    cfg=config or json.loads((ROOT/'parameters/assembly_r12.json').read_text())
    report={}
    report['stack']=compact_spine_stack_r12.apply(b,cfg)
    report['bars']=spine_bars_r12.apply(b,cfg)
    report['torsos']=torso_contours_r12.apply(b,cfg)
    for kind in ('fore','hind'):
        body=doc.getObject('Torso_'+kind).LinkedObject
        body.PartNumber='TORSO_'+kind.upper()+'_COMPACT_FRAME_r12';body.Revision='r12'
    doc.Label='FLEXOR r12 compact center frame and terminal-fork candidate'
    doc.DesignParameters.Revision='r12';doc.DesignParameters.ParameterFile='parameters/assembly_r12.json; parameters/candidate_r02.json'
    doc.PoseController.ParameterRevision='r12';doc.PoseController.MotionMap=json.dumps(b.motion)
    doc.PoseController.PrescribedMotionConfigR07=json.dumps(cfg)
    doc.PoseController.Scope='Seven physical motors/six commands; compact terminal-fork bars, compact monolithic frame, single central E support; fits and loads provisional'
    for obj in b.library.Group:obj.Visibility=False
    b.library.Visibility=False;doc.recompute()
    if save:doc.saveAs(str(ROOT/'cad/flexor_r12_robot.FCStd'))
    b.integration_report=report
    if write_report:(ROOT/'reports/verification/r12_integration.json').write_text(json.dumps(report,indent=2)+'\n')
    return b

def build(save=True, doc_name='FlexorR12'):
    import build_robot_r10
    return integrate(build_robot_r10.build(save=False,doc_name=doc_name).doc,save)
