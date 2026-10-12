"""Lead-only installed-MCP build: seven motor, fixed-neutral tendon candidate."""
from pathlib import Path
import build_robot_r04,build_torso_r03,build_tendon_r03,tendon_r03
import tendon_drive_coupling_r04,hind_tendon_mounts_r05,ankle_tendon_eye_r05
ROOT=Path(__file__).resolve().parents[1]

def routes():
    return {s:tendon_r03.tendon_route(s,cable_plane_mm=57,wheel_x_mm=-50,ankle_eye_radius_mm=1.5) for s in (-1,1)}

def integrate(b):
    r=routes();transform=build_torso_r03.Transform((-33,0),0)
    build_tendon_r03.build(b,transform=transform,routes=r,u=0)
    tendon_drive_coupling_r04.apply(b,W=(-50,0,0),transform=transform)
    hind_tendon_mounts_r05.apply(b,r,transform=transform)
    ankle_tendon_eye_r05.apply(b,r,transform=transform)
    return b

def finalize(b,save=True):
    build_robot_r04.finalize(b,save=False)
    b.doc.Label='FLEXOR r05 seven-motor tendon integration candidate'
    b.doc.DesignParameters.Revision='r05'
    b.doc.DesignParameters.ParameterFile='parameters/assembly_r05.json; parameters/candidate_r02.json'
    b.doc.PoseController.ParameterRevision='r05'
    b.doc.PoseController.Scope='Seven motor candidate; exact S9 spine parent motion; hind tendons fixed at captured neutral leg angles and wheelu0; manufacturer interfaces provisional'
    if save:b.doc.saveAs(str(ROOT/'cad/flexor_r05_robot.FCStd'))
    return b

def build(save=True,doc_name='FlexorR02'):
    b=build_robot_r04.build(save=False,doc_name=doc_name)
    integrate(b)
    return finalize(b,save)
