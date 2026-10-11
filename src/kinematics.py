"""Exact planar linkage closure. mm and rad; +angle rotates +X towards +Z."""
import json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_parameters(path=None):
    data=json.loads(Path(path or ROOT/'parameters/candidate_r01.json').read_text())
    return {k:v['value'] for k,v in data['parameters'].items()}
def circles(P,Q,r,s):
    d=math.dist(P,Q)
    if min(r,s)<=0 or d==0: raise ValueError('Degenerate circles')
    a=(r*r-s*s+d*d)/(2*d); h2=r*r-a*a
    tol=64*sys.float_info.epsilon*max(r*r,s*s,d*d,1)
    if h2 < -tol or d>r+s+tol or d<abs(r-s)-tol: raise ValueError('Infeasible circle closure')
    h=math.sqrt(max(h2,0)); ux=(Q[0]-P[0])/d; uz=(Q[1]-P[1])/d
    return [(P[0]+a*ux-j*h*uz,P[1]+a*uz+j*h*ux) for j in (1,-1)]
def line_circle(B,z,r,sign):
    h2=r*r-(z-B[1])**2
    tol=64*sys.float_info.epsilon*max(r*r,(z-B[1])**2,1)
    if h2 < -tol: raise ValueError('Infeasible slider')
    return (B[0]+sign*math.sqrt(max(h2,0)),z)
def spine(theta,p):
    G=(p['L1_mm']*math.cos(theta),p['L1_mm']*math.sin(theta))
    s={'O':(0,0),'G':G,'margins_mm':[]}
    for i,sign in ((1,1),(2,-1)):
        A=(sign*p['Hx_mm'],sign*p['Hz_mm']); E=(-sign*p['HE_mm'],0)
        B=circles(G,A,p['L2_mm'],p['L3_mm'])[p['B_branch']]
        C=line_circle(B,sign*p['guide_z_mm'],p['L4_mm'],-sign)
        D=circles(C,E,p['L5_mm'],p['L6_mm'])[p['D_branch']]
        s.update({f'A{i}':A,f'B{i}':B,f'C{i}':C,f'D{i}':D,f'E{i}':E})
        s[f'beta{i}']=math.atan2(D[1]-E[1],D[0]-E[0])
        for P,Q,r,t in ((G,A,p['L2_mm'],p['L3_mm']),(C,E,p['L5_mm'],p['L6_mm'])):
            d=math.dist(P,Q); s['margins_mm'] += [r+t-d,d-abs(r-t)]
        s['margins_mm'].append(p['L4_mm']-abs(B[1]-C[1]))
    return s

def residuals(s,p):
    result=[math.dist(s['O'],s['G'])-p['L1_mm']]
    for i in (1,2):
        for a,b,n in (('G',f'B{i}',2),(f'A{i}',f'B{i}',3),(f'B{i}',f'C{i}',4),(f'C{i}',f'D{i}',5),(f'E{i}',f'D{i}',6)):
            result.append(math.dist(s[a],s[b])-p[f'L{n}_mm'])
    return result

def angle_diff(a,b): return math.atan2(math.sin(a-b),math.cos(a-b))
