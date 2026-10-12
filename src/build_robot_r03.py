"""Lead-only reproducible native robot integration through installed FreeCAD MCP.
Run build() in FreeCAD after closing the previous FlexorR02 document.
"""
import json
from pathlib import Path
import FreeCAD as App
import build_flexor,build_torso_r03,build_leg_r02,spine_attachments_r02
ROOT=Path(__file__).resolve().parents[1]

def finalize(b,save=True):
    d=b.doc;d.Label='FLEXOR r03 source-reconciled quadruped candidate'
    d.DesignParameters.Revision='r03';d.DesignParameters.ParameterFile='parameters/assembly_r03.json; parameters/candidate_r02.json'
    d.PoseController.MotionMap=json.dumps(b.motion)
    used={o.LinkedObject.Name for o in d.Objects if o.TypeId=='App::Link'}
    unused=[o for o in b.library.Group if o.Name not in used]
    for o in unused:
        if o.TypeId=='PartDesign::Body':
            for child in reversed(o.Group):d.removeObject(child.Name)
        d.removeObject(o.Name)
    b.sources={k:v for k,v in b.sources.items() if k in used}
    for o in b.library.Group:o.Visibility=False
    d.recompute()
    if save:d.saveAs(str(ROOT/'cad/flexor_r03_robot.FCStd'))
    return b

def build(save=True,doc_name='FlexorR02'):
    b=build_flexor.build(ROOT,save=False,doc_name=doc_name)
    spine_attachments_r02.apply(b)
    for kind in ('hind','fore'):
        transform=build_torso_r03.build_torso(b,kind)
        for side in (-1,1):
            tag=kind+('L' if side==1 else 'R')
            build_leg_r02.build_leg(b,tag,kind,side,transform,include_support=False)
    return finalize(b,save)
