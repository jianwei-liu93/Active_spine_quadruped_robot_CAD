"""Lead-only monolithic lumbar revision; preserves the authoritative mechanism."""
from pathlib import Path
from types import SimpleNamespace
import json

ROOT = Path(__file__).resolve().parents[1]


def existing_builder(doc):
    """Facade for a disposable copy of an existing saved robot, never autosaves."""
    import robot_pose_r03
    library = doc.getObject('PartsLibrary')
    if library is None:
        raise ValueError('PartsLibrary missing')
    return SimpleNamespace(doc=doc, p=robot_pose_r03._parameters(doc), library=library,
                           sources={o.Name:o for o in library.Group},
                           motion=json.loads(doc.PoseController.MotionMap))


def integrate(b):
    import spine_frame_r09
    return spine_frame_r09.apply(b)


def finalize(b, save=True):
    doc=b.doc
    doc.Label='FLEXOR r09 one-piece lumbar cage candidate'
    doc.DesignParameters.Revision='r09'
    doc.DesignParameters.ParameterFile='parameters/assembly_r09.json; parameters/candidate_r02.json'
    doc.PoseController.ParameterRevision='r09'
    doc.PoseController.MotionMap=json.dumps(b.motion)
    doc.PoseController.Scope=('Seven motors, six commands; one integrated open-top lumbar frame; '
        'S9 closure and distinct same-direction legs preserved; supplier interfaces/retention remain provisional')
    for obj in b.library.Group:
        obj.Visibility=False
    b.library.Visibility=False
    doc.recompute()
    if save:
        doc.saveAs(str(ROOT/'cad/flexor_r09_robot.FCStd'))
    return b


def build(save=True, doc_name='FlexorR09'):
    import build_robot_r07
    import controller_carrier_r07
    b=build_robot_r07.build(save=False,doc_name=doc_name)
    integrate(b)
    controller_carrier_r07.repair_existing(b)
    return finalize(b,save)
