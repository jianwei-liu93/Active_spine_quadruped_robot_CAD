"""Lead-owned separate candidate; earlier saved native models stay untouched."""
import json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def finalize(b,save=True,construction='fresh_full_source'):
    doc=b.doc;cfg=json.loads((ROOT/'parameters/assembly_r13.json').read_text())
    doc.Label='FLEXOR r13 compact frame and single-ended organic A-B rocker'
    doc.DesignParameters.Revision='r13';doc.DesignParameters.ParameterFile='parameters/assembly_r13.json; parameters/candidate_r02.json'
    doc.PoseController.ParameterRevision='r13';doc.PoseController.PrescribedMotionConfigR07=json.dumps(cfg)
    doc.PoseController.Scope='Seven motors/six commands; organic A-B rockers forked only at B, compact monolithic frame, central E support; fits and loads provisional'
    doc.recompute()
    if save:doc.saveAs(str(ROOT/'cad/flexor_r13_robot.FCStd'))
    report=b.integration_report
    report.update(assembly_revision='r13',actual_final_instance_count=sum(o.TypeId=='App::Link' for o in doc.Objects),
                  construction=construction,supersedes='r12 two-ended trial rejected by latest user close-up correction')
    if save:report['native_sha256']=hashlib.sha256(Path(doc.FileName).read_bytes()).hexdigest()
    (ROOT/'reports/verification/r13_integration.json').write_text(json.dumps(report,indent=2)+'\n')
    return b


def build(save=True,doc_name='FlexorR13'):
    import build_robot_r10,build_robot_r12
    b=build_robot_r10.build(save=False,doc_name=doc_name)
    b=build_robot_r12.integrate(b.doc,save=False,write_report=False,config=json.loads((ROOT/'parameters/assembly_r13.json').read_text()))
    return finalize(b,save)


def from_checkpoint():
    """Build in a new disposable r10 copy; never mutate a prior live document.

    Used after the full historical source builder stalled at r04 in this
    runtime. All changed component factories still execute through MCP.
    """
    import FreeCAD as App
    import build_robot_r12
    target=ROOT/'cad/flexor_r13_robot.FCStd'
    if target.exists():raise ValueError('r13 already exists; inspect before replacing any progress')
    seed=ROOT/'reports/tmp/r13/r13_build_seed.FCStd';seed.parent.mkdir(parents=True,exist_ok=True)
    if seed.exists():raise ValueError('r13 seed already exists; preserve before retry')
    baseline=ROOT/'cad/flexor_r10_robot.FCStd'
    expected='d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9'
    if hashlib.sha256(baseline.read_bytes()).hexdigest()!=expected:raise ValueError('r10 baseline differs from preserved checkpoint')
    shutil.copy2(baseline,seed);doc=App.openDocument(str(seed))
    b=build_robot_r12.integrate(doc,save=False,write_report=False,config=json.loads((ROOT/'parameters/assembly_r13.json').read_text()))
    return finalize(b,True,'preserved_r10_checkpoint_plus_executed_changed_native_factories')
