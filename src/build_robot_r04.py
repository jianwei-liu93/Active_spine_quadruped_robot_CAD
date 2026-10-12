"""Movie-S1 native source-fidelity refinement; lead-only installed MCP build."""
from pathlib import Path
import build_robot_r03,spine_frame_r04,spine_shafts_r04
ROOT=Path(__file__).resolve().parents[1]

def appearance(b):
    from build_flexor import col
    for o in b.doc.Objects:
        if o.TypeId!='App::Link':continue
        material=o.LinkedObject.MaterialName
        c=(.9,.9,.87) if o.Name.startswith('Link') else ({'PA12':(.13,.15,.17),'steel':(.70,.72,.74),'spring':(.73,.75,.78),'motor':(.18,.19,.21),'copper':(.72,.45,.20),'rubber':(.06,.06,.07),'cable':(.05,.05,.05)}.get(material,(.5,.5,.5)))
        col(o,c)

def finalize(b,save=True):
    build_robot_r03.finalize(b,save=False)
    appearance(b)
    b.doc.Label='FLEXOR r04 Movie S1 refinement candidate'
    b.doc.DesignParameters.Revision='r04'
    b.doc.DesignParameters.ParameterFile='parameters/assembly_r04.json; parameters/candidate_r02.json'
    if save:b.doc.saveAs(str(ROOT/'cad/flexor_r04_robot.FCStd'))
    return b

def build(save=True):
    b=build_robot_r03.build(save=False)
    spine_frame_r04.apply(b);spine_shafts_r04.apply(b)
    return finalize(b,save)
