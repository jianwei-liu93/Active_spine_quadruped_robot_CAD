"""Lead-only reproducible r07 complete candidate integration via installed MCP."""
from pathlib import Path
import json
import build_robot_r06,spine_frame_r07,cable_clamps_r07,fore_panel_relief_r07,controller_carrier_r07
ROOT=Path(__file__).resolve().parents[1]

def integrate(b):
    frame=spine_frame_r07.apply(b)
    clamps=cable_clamps_r07.apply(b)
    relief=fore_panel_relief_r07.apply(b)
    carrier=controller_carrier_r07.apply(b)
    return {'frame':frame,'clamps':clamps,'relief':relief,'carrier':carrier}

def finalize(b,save=True):
    d=b.doc;d.Label='FLEXOR r07 complete review candidate'
    d.DesignParameters.Revision='r07';d.DesignParameters.ParameterFile='parameters/assembly_r07.json; parameters/candidate_r02.json'
    d.PoseController.ParameterRevision='r07';d.PoseController.MotionMap=json.dumps(b.motion)
    d.PoseController.Scope='Seven motor articulated candidate; source-reconciled rectangular lumbar cradle; positive cable terminals; removable controller carrier; provisional supplier interfaces; release gate separate'
    for o in b.library.Group:o.Visibility=False
    b.library.Visibility=False;d.recompute()
    if save:d.saveAs(str(ROOT/'cad/flexor_r07_robot.FCStd'))
    return b

def build(save=True,doc_name='FlexorR07'):
    b=build_robot_r06.build(save=False,doc_name=doc_name)
    integrate(b)
    return finalize(b,save)
