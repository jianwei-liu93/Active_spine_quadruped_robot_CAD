"""Supplementary isolated FreeCADCmd checks; canonical build is via installed MCP."""
import json
import os
import shutil
import traceback
from pathlib import Path
import FreeCAD as App

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'src'))
import verify_symmetric_r15b as verify

mode=os.environ.get('R15B_CHECK_MODE','native')
out=ROOT/'reports/verification'/('r15b_'+mode+'.json')
try:
    doc=App.openDocument(str(ROOT/'cad/flexor_r15b_robot.FCStd'))
    if mode=='native':
        old=App.openDocument(str(ROOT/'cad/flexor_r15_robot.FCStd'))
        report=verify.identity(old,doc)
        copy=ROOT/'reports/tmp/r15b/native_probe.FCStd';shutil.copyfile(doc.FileName,copy)
        probe=App.openDocument(str(copy))
        for o in probe.Objects: o.touch()
        probe.recompute(None,True,True)
        report['forced_recompute_identity']=verify.identity(old,probe)
        report['edit_probe']=verify.native_probe(probe)
        report['probe_saved_after_edits']=False
    elif mode=='motion': report=verify.motion(doc,out)
    elif mode=='ax':
        import animation_pose_export as ax
        absent=sorted(o.Name for o in doc.Objects if o.TypeId=='App::Link' and o.Name not in json.loads(doc.PoseController.MotionMap))
        grounding={'cad_sha256':verify.sha(doc.FileName),'grounded_names':absent,
                   'provenance':'Same explicit fixed A/C/lumbar hardware as r15;12 A hardware placements intentionally repacked in r15b'}
        (ROOT/'animation/schema/grounded_instances_r15b.json').write_text(json.dumps(grounding,indent=2)+'\n')
        report=ax.run(doc)
    elif mode=='step':
        import package_sculpted_r15 as package
        package.STEP_REPORT=out
        import package_symmetric_r15b
        report=package_symmetric_r15b.export_step(doc)
    else: raise ValueError(mode)
    if mode!='ax':out.write_text(json.dumps(report,indent=2)+'\n')
    passed=(report.get('AX0')==report.get('AX1')=='PASS') if mode=='ax' else report.get('status','').startswith('PASS')
    if not passed:raise RuntimeError('Verification gate failed: '+mode)
    print('R15B_CHECK_COMPLETE',mode,'PASS',flush=True)
except Exception:
    out.with_suffix('.error.txt').write_text(traceback.format_exc());raise
finally:
    for name in list(App.listDocuments()):App.closeDocument(name)
