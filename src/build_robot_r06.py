"""Lead-only installed-MCP build: Movie S1 transverse torso frames / cradle.

Native r06 morphology supersedes r05 frame sources; joint, case, leg and tendon
coordinates remain unchanged. The GUI document is never wrapped in a single
transaction spanning source deletion. Staged saves belong to the lead caller.
"""
from pathlib import Path
import build_robot_r05,build_torso_r03,hind_tendon_mounts_r05
import spine_frame_r06,torso_frame_r06
ROOT=Path(__file__).resolve().parents[1]


def integrate(b):
    lumbar=spine_frame_r06.apply(b)
    torso=torso_frame_r06.apply(b)
    hind_tendon_mounts_r05.apply(b,build_robot_r05.routes(),
        transform=build_torso_r03.Transform((-33,0),0),
        body_override=b.doc.getObject(torso['bodies']['hind']))
    b.doc.recompute()
    for o in b.sources.values():o.Visibility=False
    b.library.Visibility=False
    return {'lumbar':lumbar,'torso':torso}


def finalize(b,save=True):
    d=b.doc;d.Label='FLEXOR r06 Movie S1 frame refinement candidate'
    d.DesignParameters.Revision='r06'
    d.DesignParameters.ParameterFile='parameters/assembly_r06.json; parameters/candidate_r02.json'
    d.PoseController.ParameterRevision='r06'
    d.PoseController.Scope='Seven motor candidate; Movie S1 frame morphology; unchanged S9 spine datums; hind tendon geometry fixed at neutral leg angles and wheelu0; manufacturer interfaces provisional'
    d.recompute()
    if save:d.saveAs(str(ROOT/'cad/flexor_r06_robot.FCStd'))
    return b


def build(save=True,doc_name='FlexorR06'):
    b=build_robot_r05.build(save=False,doc_name=doc_name)
    integrate(b)
    return finalize(b,save)
