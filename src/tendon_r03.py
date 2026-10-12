"""r03 finite 3D secured-branch tendon routing, mm/rad/N.

Geometry is a DESIGN_ASSUMPTION informed by S19, not measured fabrication data.
Torso-local origin E1; no global parameter loader or live CAD access. Supplied
transform maps planar (x,z) to world (x,z); Y is preserved and applied once.
Wheel axis is local X, W=(-27,0,0), OD13 source, cable groove radius5.5 assumed.
Two axial groove planes have x=Wx+side*.6. Cable plane is Y=side*53.2.

The wheel angle u is an UNWRAPPED commanded state. At neutral each hole is at
its outgoing clockwise tangent to shell P=(grooveX,side*53.2,8). Positive u
adds clockwise wound path; negative u first uses a disk-clear moving-hole
chord. Beyond the second tangent the continuous reverse CCW branch is used.
Only u in [0,pi/2] is an assembled operating state: negative-u chord
routing remains diagnostic because its shell guide center changes.
Both branches are separately secured; available length remains neutral path
+0.5mm slack. Wound arcs are already counted in path, never subtracted again.
Cable stiffness2N/mm is provisional. No loaded passive equilibrium is solved.

Defaults retain r03; r04 datums plane57/wheelX-37 are packaging assumptions.
Cable/ankle attachment A defaults to compression-seat plane53.2: physical eye
and seat coexistence remains a CAD integration clearance/attachment question.
"""
import math
from leg_geometry_r02 import leg_geometry
from leg_mechanics import tangent_route, cable_state
from robot_geometry import rounded_corner


def _sub(a,b): return tuple(x-y for x,y in zip(a,b))
def _dot(a,b): return sum(x*y for x,y in zip(a,b))
def _norm(a): return math.sqrt(_dot(a,a))
def _unit(a):
    n=_norm(a)
    if n==0: raise ValueError('Degenerate routing vector')
    return tuple(x/n for x in a)
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _mid_radius(A,B,C,r):
    u=_unit(tuple(x+y for x,y in zip(_sub(A,C),_sub(B,C))))
    return tuple(c+r*x for c,x in zip(C,u))
def _line(name,A,B):
    return {'type':'line','name':name,'start':A,'end':B,'length_mm':math.dist(A,B)}
def _arc(name,A,B,M,C,axis,r,sweep):
    return {'type':'arc','name':name,'start':A,'end':B,'mid':M,'center':C,
            'axis':axis,'radius_mm':r,'sweep_rad':sweep,'length_mm':r*sweep}


def _min_segment_radius(A,B,C):
    d=_sub(B,A);denom=_dot(d,d)
    if denom==0: return math.dist(A,C)
    t=max(0,min(1,-_dot(_sub(A,C),d)/denom))
    return math.dist(tuple(a+t*x for a,x in zip(A,d)),C)


def _transformers(transform):
    if transform is None:
        return (lambda p:tuple(p)),(lambda v:tuple(v))
    origin=tuple(transform((0,0)));X=tuple(transform((1,0)));Z=tuple(transform((0,1)))
    ux=(X[0]-origin[0],X[1]-origin[1]);uz=(Z[0]-origin[0],Z[1]-origin[1])
    errors=(_norm(ux)-1,_norm(uz)-1,_dot(ux,uz),ux[0]*uz[1]-ux[1]*uz[0]-1)
    if not all(math.isfinite(x) for x in (*origin,*ux,*uz)) or max(abs(x) for x in errors)>1e-9:
        raise ValueError('transform must be finite proper rigid planar motion')
    def point(p):
        x,z=transform((p[0],p[2]))
        return (x,p[1],z)
    def vector(v): return (ux[0]*v[0]+uz[0]*v[2],v[1],ux[1]*v[0]+uz[1]*v[2])
    return point,vector


def tendon_route(side,u=0,thigh_angle=None,passive_knee=None,transform=None,wrap_sign=-1,cable_plane_mm=53.2,wheel_x_mm=-27,ankle_eye_radius_mm=0):
    """Ordered centerline primitives, finite guide frames, diagnostics and length.

    Arc axes follow the right-hand rule; sweep_rad is positive and may exceed
    2pi for multi-turn wheel motion. CAD must split such arcs before creating
    three-point circular edges. Wheel tangency is not asserted for a clear
    chord: its physical departure from an anchored moving hole is oblique.
    """
    if side not in (-1,1) or not math.isfinite(u):
        raise ValueError('side must be +/-1 and u must be finite')
    if not math.isfinite(cable_plane_mm) or cable_plane_mm<=0 or not math.isfinite(wheel_x_mm):
        raise ValueError('Cable plane must be positive finite and wheel X finite')
    if not math.isfinite(ankle_eye_radius_mm) or ankle_eye_radius_mm<0:
        raise ValueError('Ankle eye radius must be nonnegative finite')
    tf,tv=_transformers(transform)
    g=leg_geometry('hind',thigh_angle,passive_knee)
    r=5.5;gx=wheel_x_mm+side*.6;y=side*cable_plane_mm
    C=(gx,0.0,0.0);P=(gx,y,8.0)
    dy,dz=P[1]-C[1],P[2]-C[2];d=math.hypot(dy,dz)
    beta=math.atan2(dz,dy);a=math.acos(r/d)
    theta=beta+a  # outgoing CW tangent has positive dot with T->P
    reverse_limit=-2*a
    def wheel_point(t): return (gx,r*math.cos(t),r*math.sin(t))
    hole=wheel_point(theta+u)
    chord_min=_min_segment_radius(hole,P,C)
    primitives=[]
    if u>0:
        regime='CW_wrap';T=wheel_point(theta);sweep=u;axis=(-1.0,0.0,0.0)
        primitives.append(_arc('wheel_wrap',hole,T,wheel_point(theta+u/2),C,axis,r,sweep))
    elif u==0:
        regime='neutral_tangent';T=hole
    elif u>=reverse_limit and chord_min>=r-1e-9:
        regime='clear_chord';T=hole
    else:
        regime='reverse_CCW_wrap';endtheta=theta+reverse_limit;T=wheel_point(endtheta)
        sweep=reverse_limit-u
        primitives.append(_arc('wheel_wrap',hole,T,wheel_point((theta+u+endtheta)/2),C,(1.0,0.0,0.0),r,sweep))
    # Derive the fixed guide from the same primary hind hip frame as the bones.
    hip_center=leg_geometry('hind')['H']
    hip=tangent_route((gx,8),hip_center,2.5,g['A'],wrap_sign)
    Tin,Tout=tuple((x,y,z) for x,z in hip['contacts'])
    H=(hip_center[0],y,hip_center[1])
    corner=rounded_corner(T,P,Tin,2.5)
    entry,exit=corner['entry'],corner['exit']
    axis=_unit(_cross(_sub(P,T),_sub(Tin,P)))
    primitives.extend((
        _line('wheel_to_shell',T,entry),
        _arc('shell_redirect',entry,exit,corner['mid'],corner['center'],axis,2.5,corner['turn_rad']),
        _line('shell_to_hip',exit,Tin)))
    hm=hip['arc_start_rad']+wrap_sign*hip['wrap_angle_rad']/2
    hipmid=(hip_center[0]+2.5*math.cos(hm),y,hip_center[1]+2.5*math.sin(hm))
    hipaxis=(0.0,-float(wrap_sign),0.0)
    primitives.append(_arc('hip_redirect',Tin,Tout,hipmid,H,hipaxis,2.5,hip['wrap_angle_rad']))
    virtual_A=(g['A'][0],y,g['A'][1])
    if ankle_eye_radius_mm>=math.dist(Tout,virtual_A):raise ValueError('Ankle eye must lie on final incoming span')
    approach=_unit(_sub(Tout,virtual_A))
    A=tuple(c+ankle_eye_radius_mm*v for c,v in zip(virtual_A,approach))
    primitives.append(_line('hip_to_ankle',Tout,A))
    # Dot products carry mm²; radius residuals carry mm. The set is deliberately
    # explicit about which segment is checked against which finite guide.
    errors={
        'shell_entry_tangent_mm2':abs(_dot(_sub(entry,T),_sub(entry,corner['center']))),
        'shell_exit_tangent_mm2':abs(_dot(_sub(Tin,exit),_sub(exit,corner['center']))),
        'hip_entry_tangent_mm2':abs(_dot(_sub(Tin,exit),_sub(Tin,H))),
        'hip_exit_tangent_mm2':abs(_dot(_sub(A,Tout),_sub(Tout,H))),
        'wheel_radius_mm':abs(math.dist(hole,C)-r),
        'shell_entry_radius_mm':abs(math.dist(entry,corner['center'])-2.5),
        'shell_exit_radius_mm':abs(math.dist(exit,corner['center'])-2.5),
        'hip_entry_radius_mm':abs(math.dist(Tin,H)-2.5),
        'hip_exit_radius_mm':abs(math.dist(Tout,H)-2.5)}
    if regime!='clear_chord':
        errors['wheel_outgoing_tangent_mm2']=abs(_dot(_sub(entry,T),_sub(T,C)))
    transformed=[]
    for primitive in primitives:
        q=dict(primitive)
        for key in ('start','end','mid','center'):
            if key in q:q[key]=tf(q[key])
        if 'axis' in q:q['axis']=tv(q['axis'])
        transformed.append(q)
    cw=(math.sin(theta),-math.cos(theta))
    cw_dot=cw[0]*(P[1]-wheel_point(theta)[1])+cw[1]*(P[2]-wheel_point(theta)[2])
    return {'side':side,'wheel_angle_rad':u,'wheel_regime':regime,
        'assembled_operating_interval_rad':(0,math.pi/2),'assembly_compatible':0<=u<=math.pi/2,
        'primitives':transformed,'length_mm':sum(q['length_mm'] for q in primitives),
        'tangency_errors':errors,
        'wheel':{'center':tf(C),'axle_center':tf((wheel_x_mm,0,0)),'axis':tv((1,0,0)),
                 'hole':tf(hole),'contact':tf(T),'pitch_radius_mm':r,'outer_diameter_mm':13,
                 'neutral_hole_angle_rad':theta,'hole_angle_rad':theta+u,
                 'reverse_chord_limit_rad':reverse_limit,'chord_min_radius_mm':chord_min,
                 'chosen_CW_tangent_dot_mm':cw_dot},
        'shell_guide':{'corner':tf(P),'center':tf(corner['center']),'entry':tf(entry),'exit':tf(exit),
                       'mid':tf(corner['mid']),'axis':tv(axis),'pitch_radius_mm':2.5},
        'hip_guide':{'center':tf(H),'entry':tf(Tin),'exit':tf(Tout),'axis':tv(hipaxis),'pitch_radius_mm':2.5},
        'ankle_anchor':tf(A),'virtual_ankle_axis':tf(virtual_A),'ankle_eye_radius_mm':ankle_eye_radius_mm,'geometry':g,
        'limitations':('Wheel grooves/hole/radii/terminations are provisional engineering choices',
                      'Shell circular guide center/axis moves in chord regime; see mounting note',
                      'Cable ankle anchor coincides with spring seat plane; attachment collision pending',
                      'No loaded equilibrium or wear/strength certification')}


def bilateral_states(u=0,left_knee=None,right_knee=None,left_thigh=None,right_thigh=None,transform=None,stiffness=2.0,cable_plane_mm=53.2,wheel_x_mm=-27,ankle_eye_radius_mm=0):
    """Two secured branches with neutral+0.5mm fixed available length per branch.

    Available lengths are installed at the declared neutral knees/thighs, not
    recomputed for the queried asymmetric pose. Wheel arcs are already in path.
    """
    if not math.isfinite(u) or not 0<=u<=math.pi/2:
        raise ValueError('Assembled fixed-guide wheel interval is [0, pi/2]; use tendon_route for diagnostics')
    result={}
    for side,knee,thigh in ((1,left_knee,left_thigh),(-1,right_knee,right_thigh)):
        neutral=tendon_route(side,0,cable_plane_mm=cable_plane_mm,wheel_x_mm=wheel_x_mm,ankle_eye_radius_mm=ankle_eye_radius_mm)
        route=tendon_route(side,u,thigh,knee,transform,cable_plane_mm=cable_plane_mm,wheel_x_mm=wheel_x_mm,ankle_eye_radius_mm=ankle_eye_radius_mm)
        available=neutral['length_mm']+.5
        state=cable_state(route['length_mm'],available,{'cable_stiffness_N_per_mm':stiffness})
        result[side]={'route':route,'path_mm':route['length_mm'],'available_mm':available,'state':state}
    return {'branches':result,'topology':'Two separately secured branches on one commanded wheel',
            'available_policy':'Constant neutral geometric length +0.5mm per branch; wrap already in path',
            'stiffness_N_per_mm':stiffness,'provenance':'DESIGN_ASSUMPTION','loaded_equilibrium':False}
