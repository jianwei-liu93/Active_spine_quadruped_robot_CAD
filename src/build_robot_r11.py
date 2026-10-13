"""Reproducible lead-only r11 native linkage-section candidate."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def finalize(b,save=True):
    d=b.doc;d.Label='FLEXOR r11 local-clevis and recessed-link candidate'
    d.DesignParameters.Revision='r11';d.DesignParameters.ParameterFile='parameters/assembly_r11.json; parameters/candidate_r02.json'
    d.PoseController.ParameterRevision='r11';d.PoseController.MotionMap=json.dumps(b.motion)
    for o in b.library.Group:o.Visibility=False
    b.library.Visibility=False;d.recompute()
    if save:d.saveAs(str(ROOT/'cad/flexor_r11_robot.FCStd'))
    return b

def integrate(doc,save=True):
    import spine_link_sections_r11 as sections
    b=sections.resume(doc);report=sections.apply(b)
    finalize(b,save)
    (ROOT/'reports/verification/r11_integration.json').write_text(json.dumps(report,indent=2)+'\n')
    return b

def build(save=True,doc_name='FlexorR11'):
    import build_robot_r10,spine_link_sections_r11
    b=build_robot_r10.build(save=False,doc_name=doc_name)
    report=spine_link_sections_r11.apply(b);finalize(b,save)
    return b
