"""361-point numerical cycle, using saved native parameters and motion API."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import FreeCAD as App
import robot_pose_r03 as pose,leg_motion_r07 as motion
from kinematics import spine,residuals,angle_diff
native=ROOT/'cad/flexor_r15_robot.FCStd';doc=App.openDocument(str(native))
try:
    p=pose._parameters(doc);cfg=json.loads(doc.PoseController.PrescribedMotionConfigR07)
    rows=[];previous=None;first=None;angular_step=0.
    for degree in range(361):
        theta=math.radians(degree);state=spine(theta,p)
        if first is None:first=state
        if previous:
            angular_step=max(angular_step,*(abs(angle_diff(state[k],previous[k])) for k in ('beta1','beta2')))
        rows.append({'phase_deg':degree,'maximum_closure_residual_mm':max(abs(v) for v in residuals(state,p)),
                     'minimum_branch_margin_mm':min(state['margins_mm'])})
        previous=state
    names=[k for k,v in first.items() if isinstance(v,tuple) and len(v)==2]
    endpoint=max(math.dist(first[k],state[k]) for k in names)
    plan0=motion.descriptor(doc,0.,config=cfg)
    plan1=motion.descriptor(doc,math.tau,config=cfg)
    matrix_error=max(abs(a-b) for n in plan0['placements'] for a,b in
                     zip(plan0['placements'][n].toMatrix().A,plan1['placements'][n].toMatrix().A))
    passed=(max(r['maximum_closure_residual_mm'] for r in rows)<1e-6 and
            min(r['minimum_branch_margin_mm'] for r in rows)>0 and endpoint<1e-6
            and matrix_error<1e-9 and angular_step<math.pi/4)
    report={'status':'PASS_NUMERICAL_FULL_CYCLE' if passed else 'FAIL','native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
            'samples':361,'phase_step_deg':1,'records':rows,'endpoint_joint_error_mm':endpoint,
            'endpoint_all_455_transform_max_error':matrix_error,'maximum_adjacent_output_angle_step_rad':angular_step,
            'source_parameters':p,'limits':'Numerical kinematic continuity and closure only. Geometric collision coverage is separately finite at four-degree baseline samples.'}
    (ROOT/'reports/verification/r15_numeric_cycle.json').write_text(json.dumps(report,indent=2)+'\n')
    print('R15_NUMERIC_CYCLE',report['status'],endpoint,matrix_error,angular_step,flush=True)
finally:App.closeDocument(doc.Name)
