"""Frozen r02 planar reconstruction assumptions, not measured source geometry.

All coordinates are immutable (x,z) tuples in a hind/fore torso-local frame
whose origin E is the spine-to-torso pivot. Lengths are mm, angles radians;
positive rotation maps +X toward +Z. No global parameter file is loaded.

Selected center distances: hind (29,30,31), fore (24,24,30). Hip/shoulder H
is (-13,0) hind or (+13,0) fore. Both types have an ideal uncrossed lower
parallelogram and distal absolute angle equal to the actual thigh angle.
Neutral actual thigh/knee angles are (-40,-100) deg hind, (-130,+90) deg fore.

Named body attachments are explicit design assumptions:
  O1 = K + 6 e(thigh), carried by the thigh (return-rail proximal pivot).
  A1 = A + 6 e(thigh), carried by the foot (return-rail distal pivot).
  O2 = H + 9 e(motor), carried by a separate motor horn.
  O3 = K - 6 e(thigh+knee), carried by the shank's beyond-knee lever.
The rigid return rail joins O1 to A1. Extension spring joins O2 to O3;
compression spring joins O1 to A, NOT A1. Cable termination is A, carried
by the ankle/foot carrier. The ankle pivot A is also a point on the shank.

The motor proximal angle defaults numerically to the actual thigh angle,
but no rigid equality constraint is imposed. Prescribing these angles is a
geometry evaluation, not a loaded equilibrium solution or mobility proof.
Frames describe parent rigid bodies; the lead applies torso-to-world and
lateral instance transforms once at integration.
"""
import math


_LENGTHS = {'hind': (29.0,30.0,31.0), 'fore': (24.0,24.0,30.0)}
_NEUTRAL_DEG = {'hind': (-40.0,-100.0), 'fore': (-130.0,90.0)}


def _offset(origin,length,angle):
    return (origin[0]+length*math.cos(angle),origin[1]+length*math.sin(angle))


def _difference(a,b):
    return (a[0]-b[0],a[1]-b[1])


def leg_geometry(leg_type, thigh_angle=None, passive_knee=None,
                 motor_proximal_angle=None):
    """Return named joints/attachments, parent frames, lengths and loop errors.

    Coordinates and frame origins are immutable tuples. Returned dictionaries
    are independent per call, suitable for CAD placement and serialization.
    Independent prescribed inputs are thigh_angle, passive_knee and motor angle;
    qa=-passive_knee is dependent. Positive spring lengths are geometric only.
    """
    if leg_type not in _LENGTHS:
        raise ValueError('leg_type must be hind or fore')
    neutral = _NEUTRAL_DEG[leg_type]
    qh = math.radians(neutral[0]) if thigh_angle is None else thigh_angle
    qk = math.radians(neutral[1]) if passive_knee is None else passive_knee
    motor = qh if motor_proximal_angle is None else motor_proximal_angle
    if not all(math.isfinite(q) for q in (qh,qk,motor)):
        raise ValueError('Leg angles must be finite')
    a1,a2,a3 = _LENGTHS[leg_type]
    H = (-13.0 if leg_type=='hind' else 13.0,0.0)
    K = _offset(H,a1,qh)
    A = _offset(K,a2,qh+qk)
    F = _offset(A,a3,qh)
    O1 = _offset(K,6.0,qh)
    A1 = _offset(A,6.0,qh)
    O2 = _offset(H,9.0,motor)
    O3 = _offset(K,-6.0,qh+qk)
    points = dict(H=H,K=K,A=A,F=F,O1=O1,A1=A1,O2=O2,O3=O3)
    offset_error = math.dist(_difference(O1,K),_difference(A1,A))
    rail_error = math.dist(_difference(A,K),_difference(A1,O1))
    frames = {
        'torso': {'origin': (0.0,0.0), 'angle_rad': 0.0},
        'thigh': {'origin': H, 'angle_rad': qh},
        'shank': {'origin': K, 'angle_rad': qh+qk},
        'foot': {'origin': A, 'angle_rad': qh},
        'motor_horn': {'origin': H, 'angle_rad': motor},
        'return_rail': {'origin': O1, 'angle_rad': qh+qk},
    }
    owners = {'H':'torso','K':'thigh','A':'foot','F':'foot',
              'O1':'thigh','A1':'foot','O2':'motor_horn','O3':'shank',
              'cable_anchor':'foot'}
    local_offsets = {'H':H,'K':(a1,0.0),'A':(0.0,0.0),'F':(a3,0.0),
                     'O1':(a1+6.0,0.0),'A1':(6.0,0.0),'O2':(9.0,0.0),
                     'O3':(-6.0,0.0),'cable_anchor':(0.0,0.0)}
    return dict(points, leg_type=leg_type, cable_anchor=A,
                thigh_angle_rad=qh,passive_knee_rad=qk,
                motor_proximal_angle_rad=motor,qa_rad=-qk,
                distal_angle_rad=qh,distal_angle_dependent=True,
                body_frames=frames,owning_body=owners,
                body_local_offsets_mm=local_offsets,
                lengths_mm={'a1':a1,'a2':a2,'a3':a3,'return_rail':a2,
                            'coupler_offset':6.0,'horn_offset':9.0,
                            'beyond_knee_lever':6.0},
                spring_attachments={'extension':('O2','O3'),
                                    'compression':('O1','A')},
                spring_lengths_mm={'extension':math.dist(O2,O3),
                                   'compression':math.dist(O1,A)},
                loop_residuals_mm={'opposite_offset':offset_error,
                                   'opposite_rail':rail_error,
                                   'return_rail_length':abs(math.dist(O1,A1)-a2)})
