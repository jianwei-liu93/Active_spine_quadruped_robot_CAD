"""Lead-only source-faithful orthogonal center cage candidate."""
from pathlib import Path
import json
import build_robot_r07,spine_frame_r08,controller_carrier_r07
ROOT=Path(__file__).resolve().parents[1]
def integrate(b):
    frame=spine_frame_r08.apply(b)
    carrier=controller_carrier_r07.repair_existing(b)
    return {'frame':frame,'carrier':carrier}
def finalize(b,save=True):
    d=b.doc;d.Label='FLEXOR r08 orthogonal windowed center cage candidate'
    d.DesignParameters.Revision='r08';d.DesignParameters.ParameterFile='parameters/assembly_r08.json; parameters/candidate_r02.json'
    d.PoseController.ParameterRevision='r08';d.PoseController.MotionMap=json.dumps(b.motion)
    d.PoseController.Scope='Seven motor scripted kinematic candidate; orthogonal S1 lumbar windows, solid horn cheeks, open top; manufacturing split with nonstructural seam; supplier interfaces provisional'
    for o in b.library.Group:o.Visibility=False
    b.library.Visibility=False;d.recompute()
    if save:d.saveAs(str(ROOT/'cad/flexor_r08_robot.FCStd'))
    return b
def build(save=True,doc_name='FlexorR08'):
    b=build_robot_r07.build(save=False,doc_name=doc_name)
    integrate(b)
    return finalize(b,save)
