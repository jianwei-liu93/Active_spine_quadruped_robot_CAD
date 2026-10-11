"""Shared actual robot anchors and rigid transforms (mm/rad)."""
import math
from kinematics import spine,angle_diff
from leg_mechanics import leg_pose,tangent_route,spring_state,cable_state

def rotate(P,a):return (math.cos(a)*P[0]-math.sin(a)*P[1],math.sin(a)*P[0]+math.cos(a)*P[1])
def add(A,B):return tuple(a+b for a,b in zip(A,B))
def scale(A,k):return tuple(k*a for a in A)
def norm(A):return math.sqrt(sum(a*a for a in A))
def sub(A,B):return tuple(a-b for a,b in zip(A,B))
def unit(A):return scale(A,1/norm(A))
def dot(A,B):return sum(a*b for a,b in zip(A,B))

def leg_geometry(theta,chain,side,p,qh=None,qk=None,qa=None):
    s=spine(theta,p);n=spine(p['neutral_phase_rad'],p)
    torso=angle_diff(s[f'beta{chain}'],n[f'beta{chain}']);E=s[f'E{chain}'];direction=-1 if chain==1 else 1
    H=add(E,rotate((direction*18,0),torso))
    qh=p['leg_qh_rad'] if qh is None else qh;qk=p['leg_qk_rad'] if qk is None else qk
    if chain==2 and qa is None:qa=p['leg_qa_fore_rad']
    local=leg_pose(qh,qk,qa,p)
    world={k:add(H,rotate(local[k],torso)) for k in ['H','K','A','F','P0','P1','P2','P3']}
    world.update(torso_rad=torso,qh_rad=qh,qk_rad=qk,qa_rad=local['qa_rad'],chain=chain,side=side)
    # Actual spring anchor coordinates, carried by thigh and shank, not free points.
    HK=sub(local['K'],local['H']);KA=sub(local['A'],local['K'])
    anchors={'extension_A':scale(HK,0.65),'extension_B':add(local['K'],scale(KA,0.40)),
             'compression_A':scale(HK,0.80),'compression_B':add(local['K'],scale(KA,0.35)),
             'cable_anchor':add(local['K'],scale(KA,0.30))}
    for k,P in anchors.items():world[k]=add(H,rotate(P,torso))
    return world

def rounded_corner(A,P,B,r):
    incoming=unit(sub(P,A));outgoing=unit(sub(B,P))
    turn=math.acos(max(-1,min(1,dot(incoming,outgoing))))
    trim=r*math.tan(turn/2)
    if trim>=min(norm(sub(P,A)),norm(sub(B,P))):raise ValueError('Guide bend does not fit adjacent runs')
    T1=sub(P,scale(incoming,trim));T2=add(P,scale(outgoing,trim))
    C=add(P,scale(unit(sub(outgoing,incoming)),r/math.cos(turn/2)))
    M=add(C,scale(unit(sub(P,C)),r))
    return {'entry':T1,'exit':T2,'mid':M,'center':C,'arc_mm':r*turn,'trim_mm':trim,'turn_rad':turn}

def tendon_geometry(theta,side,p,qh=None,qk=None,wheel=0):
    g=leg_geometry(theta,1,side,p,qh,qk);s=spine(theta,p);n=spine(p['neutral_phase_rad'],p)
    q=g['torso_rad'];E=s['E1'];W=add(E,rotate((-37,0),q));H=g['H'];P=add(H,rotate((-10,12),q));Q=g['cable_anchor']
    # Pulley tangent calculations stay in the torso's plane and are rotated once.
    Hlocal=(-18,0);Plocal=(-28,12)
    qlocal=add(Hlocal,rotate(sub(Q,H),-q))
    route=tangent_route(Plocal,Hlocal,p['guide_radius_mm'],qlocal,-1)
    pts=[add(E,rotate(v,q)) for v in route['points']]
    yy=side*82.0
    W3=(W[0],side*2.5,W[1]+p['wheel_pitch_radius_mm'])
    P3=(pts[0][0],yy,pts[0][1]);T3=(pts[1][0],yy,pts[1][1])
    corner=rounded_corner(W3,P3,T3,p['guide_radius_mm'])
    length=norm(sub(corner['entry'],W3))+corner['arc_mm']+norm(sub(T3,corner['exit']))+route['arc_length_mm']+math.dist(pts[2],pts[3])
    return {'leg':g,'wheel_center':W,'wheel_contact':W3,'shell_guide':P3,'corner':corner,'hip_center':H,
            'hip_route':route,'hip_points':[(x,yy,z) for x,z in pts], 'length_mm':length,'cable_plane_y_mm':yy}


def elastic_geometry(theta,side,p,qh=None,qk=None,wheel=0):
    t=tendon_geometry(theta,side,p,qh,qk,wheel);neutral=tendon_geometry(p['neutral_phase_rad'],side,p)
    available=neutral['length_mm']+p['cable_slack_neutral_mm']-p['wheel_pitch_radius_mm']*wheel
    states={'cable':cable_state(t['length_mm'],available,p),'available_mm':available,'path_mm':t['length_mm']}
    for k in ['extension','compression']:
        states[k]=spring_state(math.dist(t['leg'][k+'_A'],t['leg'][k+'_B']),k,p)
    return states
