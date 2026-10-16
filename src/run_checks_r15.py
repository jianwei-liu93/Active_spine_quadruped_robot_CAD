"""Supplemental isolated installed-FreeCADCmd verification of saved r15.

R15_CHECK_MODE=native|ax|step|motion|all /snap/bin/freecad.cmd src/run_checks_r15.py
Construction and canonical inspection use the installed live FreeCAD MCP.
"""
import os,sys,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import FreeCAD as App
import package_sculpted_r15
mode=os.environ.get('R15_CHECK_MODE','all')
if mode not in ('native','ax','step','motion','motion-reuse','all'):raise ValueError('Unknown check mode')
doc=App.openDocument(str(ROOT/'cad/flexor_r15_robot.FCStd'))
try:
    if mode in ('native','all'):
        report=package_sculpted_r15.native_checks(doc)
        print('R15_NATIVE_RESULT',report['status'],report.get('error'),flush=True)
        if report['status']!='PASS':raise RuntimeError('Native check failed')
    if mode in ('ax','all'):
        import animation_pose_export
        report=animation_pose_export.run(doc)
        print('R15_AX_RESULT',report.get('status'),flush=True)
    if mode in ('step','all'):
        report=package_sculpted_r15.export_step(doc)
        print('R15_STEP_RESULT',report['status'],flush=True)
    if mode in ('motion','motion-reuse'):
        import verify_sculpted_delta_r15
        old=App.openDocument(str(ROOT/'cad/flexor_r14_robot.FCStd'))
        try:
            cfg=json.loads((ROOT/'parameters/assembly_r15.json').read_text())
            report=verify_sculpted_delta_r15.run(doc,old.LumbarIntegrated1.LinkedObject,
                                               doc.LumbarIntegrated1.LinkedObject,cfg,
                                               paper_evidence_path=(ROOT/'reports/verification/r15_motion_initial.json') if mode=='motion-reuse' else None)
            (ROOT/'reports/verification/r15_motion.json').write_text(json.dumps(report,indent=2)+'\n')
            print('R15_MOTION_RESULT',report['status'],flush=True)
        finally:App.closeDocument(old.Name)
except Exception:
    (ROOT/'reports/verification'/('r15_cli_'+mode+'_error.txt')).write_text(traceback.format_exc())
    raise
finally:
    App.closeDocument(doc.Name)
