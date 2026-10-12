"""Lead-only source-faithful central joints and plate/link profile revision."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def integrate(b):
    import spine_frame_r10,torso_attachment_r10,spine_bar_profile_r10,central_joint_hardware_r10
    results={}
    results['frame']=spine_frame_r10.apply(b)
    results['torso']=torso_attachment_r10.apply(b)
    results['bars']=spine_bar_profile_r10.apply(b)
    results['hardware']=central_joint_hardware_r10.apply(b)
    return results

def finalize(b,save=True):
    doc=b.doc
    doc.Label='FLEXOR r10 central attachment and reference-profile candidate'
    doc.DesignParameters.Revision='r10'
    doc.DesignParameters.ParameterFile='parameters/assembly_r10.json; parameters/candidate_r02.json'
    doc.PoseController.ParameterRevision='r10'
    doc.PoseController.MotionMap=json.dumps(b.motion)
    doc.PoseController.Scope=('Seven motors, six commands plus four prescribed knees; one integrated lumbar frame with '
        'central E1/E2 beams/lugs and torso clevises, existing S9 axes/coupling, distinct same-direction legs; '
        'supplier fits/strength/retention remain provisional')
    for obj in b.library.Group:obj.Visibility=False
    b.library.Visibility=False
    doc.recompute()
    if save:doc.saveAs(str(ROOT/'cad/flexor_r10_robot.FCStd'))
    return b

def build(save=True,doc_name='FlexorR10'):
    import build_robot_r09
    b=build_robot_r09.build(save=False,doc_name=doc_name)
    integrate(b)
    return finalize(b,save)
