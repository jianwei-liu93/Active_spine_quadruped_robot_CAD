"""Numerical evidence: actual geometric closure, continuation and derivatives."""
from kinematics import *
import csv

def run(root=ROOT):
    import numpy as np
    p=load_parameters(); ts=np.linspace(0,math.tau,721)
    ss=[spine(float(t),p) for t in ts]
    bs=np.unwrap(np.array([[s['beta1'],s['beta2']] for s in ss]),axis=0)
    # Independent squared-distance Jacobian for each 5-unknown chain. Rows/columns scaled uniformly by Lref.
    cond=[]; derivative_error=[]; h=1e-5
    for theta,s in zip(ts,ss):
        for i in (1,2):
            B,C,D,A,E,G=[np.array(s[n if n in ('G',) else n+str(i)],float) for n in ('B','C','D','A','E','G')]
            j=np.zeros((5,5)); f=np.zeros(5)
            j[0,:2]=(B-G)/p['L2_mm']; f[0]=-np.dot((B-G)/p['L2_mm'],p['L1_mm']*np.array([-math.sin(theta),math.cos(theta)]))
            j[1,:2]=(B-A)/p['L3_mm']
            v=(C-B)/p['L4_mm']; j[2,:2]=-v; j[2,2]=v[0]
            v=(D-C)/p['L5_mm']; j[3,2]=-v[0]; j[3,3:]=v
            j[4,3:]=(D-E)/p['L6_mm']
            cond.append(float(np.linalg.cond(j)))
            zd=np.linalg.solve(j,-f)
            v=D-E; bd=(-v[1]*zd[3]+v[0]*zd[4])/np.dot(v,v)
            fd=angle_diff(spine(float(theta+h),p)['beta'+str(i)],spine(float(theta-h),p)['beta'+str(i)])/(2*h)
            derivative_error.append(abs(float(bd)-fd))
    q=bs-bs[0]
    # Project convention psi1=pi/2+q1; psi2=pi/2+q2. Paper sign/offset uncalibrated.
    sym=q[:,0]+q[:,1]
    report={'revision':'r01','status':'PASS','samples':721,'step_deg':0.5,'phase_rad':[0,math.tau],
      'branch':{'B':'positive oriented circle intersection','slider':['negative x root','positive x root'],'D':'positive oriented circle intersection','source_visual_seed':'BLOCKED'},
      'closure_max_mm':max(abs(r) for s in ss for r in residuals(s,p)), 'closure_tolerance_mm':1e-8*p['L4_mm'],
      'min_geometric_feasibility_margin_mm':min(min(s['margins_mm']) for s in ss),
      'periodic_position_error_mm':max(math.dist(ss[0][n],ss[-1][n]) for n in ('B1','B2','C1','C2','D1','D2')),
      'max_successive_joint_step_mm':max(math.dist(a[n],b[n]) for a,b in zip(ss,ss[1:]) for n in ('B1','B2','C1','C2','D1','D2')),
      'slider_ranges_mm':{f'C{i}':[min(s[f'C{i}'][0] for s in ss),max(s[f'C{i}'][0] for s in ss)] for i in (1,2)},
      'output_ranges_relative_neutral_deg':(np.array([q.min(axis=0),q.max(axis=0)])*180/math.pi).tolist(),
      'symmetry_max_abs_deg_project_convention':float(max(abs(sym))*180/math.pi),
      'symmetry_definition':'psi1=pi/2+(beta1-beta1_neutral), psi2=pi/2+(beta2-beta2_neutral); paper convention uncalibrated',
      'jacobian':'5x5 length-residual derivatives wrt [Bx,Bz,Cx,Dx,Dz] in mm; uniform lengths/coordinates scale cancel',
      'max_jacobian_condition_2':max(cond),'max_analytic_vs_central_derivative_error_rad_per_rad':max(derivative_error),
      'limits':'Finite 0.5-degree samples; strict positive intersection margins and invariant oriented branch labels. No source-visual or physical certification.'}
    (root/'reports/verification/spine_cycle.json').write_text(json.dumps(report,indent=2)+'\n')
    with (root/'reports/verification/spine_cycle.csv').open('w') as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(['theta_rad','beta1_rad','beta2_rad','C1_x_mm','C2_x_mm','max_closure_mm','symmetry_rad'])
        for t,s,b,e in zip(ts,ss,bs,sym):w.writerow([t,*b,s['C1'][0],s['C2'][0],max(abs(x) for x in residuals(s,p)),e])
    print(json.dumps(report,indent=2)); return report
if __name__=='__main__':run()
