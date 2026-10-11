"""Planar leg mechanics in mm, rad, N and N mm.

Angles rotate +X toward +Z. Inputs p are the flat values returned by
kinematics.load_parameters(). Geometric poses are prescribed, not equilibria.
All r01 elastic properties remain provisional design assumptions.
"""
import math


def _nonnegative(value, name):
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{name} must be finite and nonnegative')
    return value


def _positive(value, name):
    _nonnegative(value, name)
    if value == 0:
        raise ValueError(f'{name} must be positive')
    return value


def leg_pose(qh, qk, qa, p):
    """Return H/K/A/F and coupler P0..P3 in the local (x,z) frame.

    qa=None selects hind coupling qa=-qk (uncrossed, kappa=0).
    A numeric qa preserves all three independent foreleg joint angles.
    P0=K, P3=A and the offset members point along the proximal segment;
    they represent the ideal hind parallelogram only when qa=-qk.
    """
    if qa is None:
        qa = -qk
    if not all(math.isfinite(q) for q in (qh, qk, qa)):
        raise ValueError('Joint angles must be finite')
    lengths = [_positive(p[f'leg_a{i}_mm'], f'a{i}') for i in (1,2,3)]
    offset = _positive(p['coupler_offset_mm'], 'coupler offset')
    angles = (qh, qh+qk, qh+qk+qa)
    points = [(0.0, 0.0)]
    for length, angle in zip(lengths, angles):
        last = points[-1]
        points.append((last[0]+length*math.cos(angle), last[1]+length*math.sin(angle)))
    H,K,A,F = points
    shift = (offset*math.cos(qh), offset*math.sin(qh))
    return dict(H=H,K=K,A=A,F=F,P0=K,
                P1=(K[0]+shift[0], K[1]+shift[1]),
                P2=(A[0]+shift[0], A[1]+shift[1]),P3=A,
                qh_rad=qh,qk_rad=qk,qa_rad=qa,alpha3_rad=angles[2])


def tangent_route(P, C, r, Q, wrap_sign):
    """Directed P->circle->Q route with tangent entry and exit, no straight cut.

    wrap_sign=+1 is CCW and -1 CW in (x,z). Radius is cable centerline
    radius. External anchors must satisfy d>r; boundary degeneracy is rejected.
    The directed arc is in (0,2*pi], with its end angle unwrapped relative
    to its start. Contact selection remains on the same tangent branch;
    a full-wrap branch is used at coincident contacts. Length is continuous
    away from this wrap-zero transition. Multi-turn routing requires an
    external winding counter; a stateless function cannot track revolutions.
    """
    _positive(r,'pulley radius')
    if wrap_sign not in (-1,1):
        raise ValueError('wrap_sign must be +1 or -1')
    P,C,Q = tuple(P),tuple(C),tuple(Q)
    if any(len(point)!=2 for point in (P,C,Q)) or not all(math.isfinite(x) for point in (P,C,Q) for x in point):
        raise ValueError('Points must contain two finite coordinates')
    dP,dQ = math.dist(P,C),math.dist(Q,C)
    if min(dP,dQ) <= r:
        raise ValueError('Anchor inside or on pulley; tangent is degenerate')
    betaP = math.atan2(P[1]-C[1],P[0]-C[0])
    betaQ = math.atan2(Q[1]-C[1],Q[0]-C[0])
    start = betaP + wrap_sign*math.acos(r/dP)
    exit_angle = betaQ - wrap_sign*math.acos(r/dQ)
    wrap = (wrap_sign*(exit_angle-start)) % math.tau
    if wrap == 0:
        wrap = math.tau
    end = start+wrap_sign*wrap
    contacts = [(C[0]+r*math.cos(a),C[1]+r*math.sin(a)) for a in (start,end)]
    straight = math.sqrt(dP*dP-r*r)+math.sqrt(dQ*dQ-r*r)
    return dict(points=[P,*contacts,Q],contacts=contacts,center=C,radius_mm=r,
                wrap_sign=wrap_sign,arc_start_rad=start,arc_end_rad=end,
                wrap_angle_rad=wrap,arc_length_mm=r*wrap,
                straight_length_mm=straight,length_mm=straight+r*wrap)


def spring_state(length, kind, p):
    """Unilateral spring magnitude and potential, with separate travel flags.

    Extension pulls anchors together; compression pushes seats apart.
    Thus Q=-F*dL/dq for extension and Q=+F*dL/dq for compression.
    Out-of-travel values are flagged, never silently clipped into safety.
    Initial tension defaults to explicitly assumed zero unless supplied as
    extension_initial_tension_N. No manufacturer/load certification implied.
    """
    _nonnegative(length,'spring length')
    if kind not in ('extension','compression'):
        raise ValueError('kind must be extension or compression')
    free = _positive(p[f'{kind}_free_mm'],'spring free length')
    rate = _positive(p[f'{kind}_rate_N_per_mm'],'spring rate')
    if kind == 'extension':
        initial = _nonnegative(p.get('extension_initial_tension_N',0),'initial tension')
        x = max(length-free,0)
        maximum = _nonnegative(p['extension_max_mm'],'maximum extension')
        return dict(force_N=initial+rate*x if x>0 else 0.0,
                    energy_Nmm=initial*x+0.5*rate*x*x,
                    state='extended' if x>0 else 'closed_or_slack',
                    travel_ok=x<=maximum,deflection_mm=x,
                    initial_tension_N=initial,
                    initial_tension_provenance='PARAMETER' if 'extension_initial_tension_N' in p else 'DESIGN_ASSUMPTION_ZERO')
    solid = _nonnegative(p['compression_solid_mm'],'solid length')
    margin = _positive(p['compression_bind_margin_mm'],'coil-bind margin')
    if solid+margin>free:
        raise ValueError('Solid length plus margin exceeds free length')
    x = max(free-length,0)
    return dict(force_N=rate*x,energy_Nmm=0.5*rate*x*x,
                state='compressed' if x>0 else 'unloaded',
                travel_ok=length>=solid+margin,deflection_mm=x,
                bind_clearance_mm=length-solid)


def cable_state(path_length, available, p):
    """One secured elastic cable branch: T=k*[path-available]+.

    slack_mm is nonnegative free slack, extension_mm is elastic stretch.
    Call per separately secured branch, or once on the total length of a
    freely redistributing loop. Two calls do not model that loop topology.
    """
    _nonnegative(path_length,'path length')
    _nonnegative(available,'available cable length')
    stiffness = _positive(p['cable_stiffness_N_per_mm'],'cable stiffness')
    delta = path_length-available
    stretch = max(delta,0)
    return dict(slack_mm=max(-delta,0),extension_mm=stretch,
                tension_N=stiffness*stretch,energy_Nmm=0.5*stiffness*stretch*stretch,
                state='stretched' if delta>0 else ('slack' if delta<0 else 'taut_unloaded'))
