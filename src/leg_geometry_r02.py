"""Source-corrected primary direct-drive leg geometry, mm/rad.

Fore22/24/34 and hind29/30/31 center distances, H offsets+24/-27,
and fixed bent horn offsets+60 degrees are explicit reconstruction assumptions.
User Figure E / MovieS2 establish both thigh/toe chains forward/down.
Prior opposing-direction interpretation is superseded.
S19 establishes O1=K-6e(thigh), A1=A-6e(thigh), O3=K-6e(shank).
O2 lies on a fixed bent proximal lever; shaft and thigh are directly coupled.
Four passive knees/elbows remain; no extra proximal elastic coordinate.
"""
import math


_LENGTHS = {'hind': (29.0,30.0,31.0), 'fore': (22.0,24.0,34.0)}
_NEUTRAL_DEG = {'hind': (-40.0,-100.0), 'fore': (-50.0,-90.0)}


def _offset(origin,length,angle):
    return (origin[0]+length*math.cos(angle),origin[1]+length*math.sin(angle))


def _difference(a,b):
    return (a[0]-b[0],a[1]-b[1])


def leg_geometry(leg_type, thigh_angle=None, passive_knee=None,
                 motor_proximal_angle=None):
    """Return named joints/attachments, parent frames, lengths and loop errors.

    Coordinates and frame origins are immutable tuples. Returned dictionaries
    are independent per call, suitable for CAD placement and serialization.
    Independent prescribed inputs are thigh_angle and passive_knee; the motor
    shaft follows thigh_angle directly;
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
    if abs(math.atan2(math.sin(motor-qh),math.cos(motor-qh)))>1e-9:
        raise ValueError('Primary direct-drive leg requires motor shaft angle equal to thigh angle')
    delta=math.radians(60)
    horn_angle=motor+delta
    a1,a2,a3 = _LENGTHS[leg_type]
    H = (-27.0 if leg_type=='hind' else 24.0,0.0)
    K = _offset(H,a1,qh)
    A = _offset(K,a2,qh+qk)
    F = _offset(A,a3,qh)
    O1 = _offset(K,-6.0,qh)
    A1 = _offset(A,-6.0,qh)
    O2 = _offset(H,9.0,horn_angle)
    O3 = _offset(K,-6.0,qh+qk)
    points = dict(H=H,K=K,A=A,F=F,O1=O1,A1=A1,O2=O2,O3=O3)
    offset_error = math.dist(_difference(O1,K),_difference(A1,A))
    rail_error = math.dist(_difference(A,K),_difference(A1,O1))
    frames = {
        'torso': {'origin': (0.0,0.0), 'angle_rad': 0.0},
        'thigh': {'origin': H, 'angle_rad': qh},
        'shank': {'origin': K, 'angle_rad': qh+qk},
        'foot': {'origin': A, 'angle_rad': qh},
        'motor_horn': {'origin': H, 'angle_rad': horn_angle},
        'return_rail': {'origin': O1, 'angle_rad': qh+qk},
    }
    owners = {'H':'torso','K':'thigh','A':'foot','F':'foot',
              'O1':'thigh','A1':'foot','O2':'motor_horn','O3':'shank',
              'cable_anchor':'foot'}
    local_offsets = {'H':H,'K':(a1,0.0),'A':(0.0,0.0),'F':(a3,0.0),
                     'O1':(a1-6.0,0.0),'A1':(-6.0,0.0),'O2':(9.0,0.0),
                     'O3':(-6.0,0.0),'cable_anchor':(0.0,0.0)}
    return dict(points, leg_type=leg_type, cable_anchor=A,
                thigh_angle_rad=qh,passive_knee_rad=qk,
                motor_proximal_angle_rad=motor,motor_horn_angle_rad=horn_angle,horn_fixed_offset_rad=delta,qa_rad=-qk,
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
