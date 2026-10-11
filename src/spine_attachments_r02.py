"""Lead-only r02 drive/frame attachment candidate; no GUI calls or automatic run.

Call apply(builder) after slider_plate_flexor.apply. It returns the hard-coded
provisional parameter/screening dictionary. Nothing here verifies ROBOTIS
horn/output geometry. The lead must integrate the horn_screw motion descriptor
with pose AND copied-shape sweep using motion_placement().
"""
import json
import math


def provisional_parameters():
    return {
        'revision': 'r02', 'provenance': 'DESIGN_ASSUMPTION',
        'horn_pattern_status': 'UNVERIFIED_NOT_ROBOTIS_DRAWING',
        'crank_thickness_mm': 1.2, 'crank_layer_abs_mm': 29.1,
        'crank_hub_radius_mm': 4.5, 'crank_O_bore_mm': 2.05,
        'crank_G_fixed_bore_mm': 1.9, 'horn_layer_abs_mm': 27.6,
        'horn_od_mm': 8.0, 'horn_thickness_mm': 1.2,
        'horn_tap_minor_mm': 1.7, 'horn_screw_offset_mm': 2.5,
        'screw_clearance_mm': 2.2, 'screw_major_mm': 2.0,
        'screw_core_mm': 1.65, 'screw_head_od_mm': 3.5,
        'screw_head_height_mm': 0.8, 'horn_screw_underhead_mm': 1.9,
        'horn_screw_tip_abs_y_mm': 27.0, 'horn_engagement_mm': 1.2,
        'crank_counterbore_depth_mm': 0.8, 'crank_remaining_floor_mm': 0.4,
        'gap_washer_thickness_mm': 0.3, 'gap_washer_layer_abs_mm': 28.35,
        'tie_corners_case_local_mm': [[x, z] for x in [-11.4, 11.4] for z in [-8.4, 28.4]],
        'tie_od_mm': 2.4, 'tie_tap_minor_mm': 1.7, 'tie_length_mm': 53.6,
        'tie_boss_radius_mm': 2.5, 'tie_collar_recess_mm': 2.6,
        'tie_screw_underhead_mm': 2.8, 'tie_screw_tip_abs_y_mm': 25.6,
        'frame_inner_abs_y_mm': 26.8, 'frame_outer_abs_y_mm': 28.4,
        'frame_thickness_mm': 1.6, 'restraint_collar_projection_mm': 1.4,
        'face_pad_projection_mm': 0.4, 'center_shim_thickness_mm': 0.8,
        'restraint_fit': 'NOMINAL_TANGENT_CASE_CONTACT_PRELOAD_AND_TOLERANCES_UNVERIFIED',
        'output_reservation': 'Preserve L6/L11; future torso interface owned by lead at outer plane 42.6 mm',
    }


def rotate_plane(point, angle):
    c, s = math.cos(angle), math.sin(angle)
    return (c * point[0] - s * point[1], s * point[0] + c * point[1])


def horn_screw_pose_data(theta, motion, origin=(0.0, 0.0)):
    """Pure numeric placement contract: screw source tip at local z=0, head +z.

    theta is the same planar phase as O->G, radians. Positive plane rotation
    is about -Y. offset_perp_mm is the signed local +z offset from O. A screw
    axis points outward (+Y on side +1, -Y on side -1). This must be used for
    negative-side screws too; cc.hardware_place alone always points -Y.
    """
    if motion['kind'] != 'horn_screw':
        raise ValueError('Expected horn_screw motion descriptor')
    side = motion['axis_side']
    if side not in (-1, 1):
        raise ValueError('axis_side must be -1 or +1')
    offset = motion['offset_perp_mm']
    return {
        'tip_xyz_mm': (origin[0] - offset * math.sin(theta),
                       side * motion['tip_abs_y_mm'],
                       origin[1] + offset * math.cos(theta)),
        'axis_xyz': (0, side, 0),
    }


def motion_placement(motion, theta, points=None):
    """FreeCAD placement adapter for the lead's pose/sweep; no document access."""
    import FreeCAD as App
    origin = (points or {}).get(motion.get('point', 'O'), (0.0, 0.0))
    data = horn_screw_pose_data(theta, motion, origin)
    return App.Placement(App.Vector(*data['tip_xyz_mm']),
                         App.Rotation(App.Vector(0, 0, 1), App.Vector(*data['axis_xyz'])))


def screen_fixed_attachments(p, samples=721):
    """Pure sampled planar screening, not a CAD Boolean or continuous guarantee.

    Braces/collars sit inside the moving-link layers. B synchronization shafts
    cross those layers, so they are screened explicitly in the X/Z plane.
    """
    from kinematics import spine
    cfg = provisional_parameters()
    angle = p['spine_case_angle_rad']
    corners = [rotate_plane(q, angle) for q in cfg['tie_corners_case_local_mm']]
    best_tie = (float('inf'), None)
    best_boss = (float('inf'), None)
    best_collar = (float('inf'), None)
    for j in range(samples):
        theta = math.tau * j / (samples - 1)
        state = spine(theta, p)
        for key in ['B1', 'B2']:
            B = state[key]
            for k, P in enumerate(corners):
                center_distance = math.dist(B, P)
                tie = center_distance - 0.95 - cfg['tie_od_mm'] / 2
                boss = center_distance - 0.95 - cfg['tie_boss_radius_mm']
                pose = {'theta_rad': theta, 'joint': key, 'corner': k}
                if tie < best_tie[0]: best_tie = (tie, pose)
                if boss < best_boss[0]: best_boss = (boss, pose)
            x, z = rotate_plane(B, -angle)
            # Distance to the whole outer rectangle is conservative for its rim.
            distance = math.hypot(max(-12 - x, 0, x - 12), max(-9 - z, 0, z - 29)) - 0.95
            if distance < best_collar[0]: best_collar = (distance, {'theta_rad': theta, 'joint': key})
    motor_corner_distance = math.hypot(1.4, 1.4) - cfg['tie_od_mm'] / 2
    return {'status': 'SAMPLED_PLANAR_SCREEN_ONLY', 'samples': samples,
            'tie_centers_xz_mm': corners, 'min_Bshaft_to_tie_mm': best_tie,
            'min_Bshaft_to_boss_mm': best_boss, 'min_Bshaft_to_collar_bound_mm': best_collar,
            'tie_to_motor_case_nominal_mm': motor_corner_distance,
            'limits': 'Finite samples; excludes connectors, supplier variations, loads, and final CAD surfaces.'}


def _register(b, body):
    b.library.addObject(body)
    b.sources[body.Name] = body
    return body


def _body(b, name, face, thickness, material, process):
    from refine_flexor import sketch_face
    import cad_common as cc
    body = b.doc.addObject('PartDesign::Body', name)
    cc.metadata(body, name, material, process)
    body.Revision = 'r02'
    sk = sketch_face(b.doc, body, name + '_Profile', face)
    pad = body.newObject('PartDesign::Pad', name + '_Pad')
    pad.Profile = sk; pad.Length = thickness
    b.doc.recompute(); sk.Visibility = False
    return _register(b, body)


def _pad(b, body, name, face, z, length, reversed_=False):
    from refine_flexor import sketch_face
    old = body.Tip
    sk = sketch_face(b.doc, body, name + '_Profile', face, z)
    pad = body.newObject('PartDesign::Pad', name)
    pad.Profile = sk; pad.Length = length; pad.Reversed = reversed_
    b.doc.recompute(); sk.Visibility = False; old.Visibility = False
    return pad


def _pocket(b, body, name, bores, z, depth, reversed_=False):
    import cad_common as cc
    sk = b.doc.addObject('Sketcher::SketchObject', name + '_Profile')
    body.addObject(sk); sk.Placement.Base.z = z
    for x, y, diameter in bores: cc.circle(sk, x, y, diameter / 2)
    old = body.Tip
    cut = body.newObject('PartDesign::Pocket', name)
    cut.Profile = sk; cut.Length = depth; cut.Reversed = reversed_
    b.doc.recompute(); sk.Visibility = False; old.Visibility = False
    return cut


def _screw(b, name, underhead, cfg, purpose):
    from refine_flexor import disk
    body = _body(b, name, disk(0, 0, cfg['screw_core_mm'] / 2), underhead,
                 'steel', purpose + '; minor-core envelope, no helical threads; supplier UNVERIFIED')
    _pad(b, body, name + '_Head', disk(0, 0, cfg['screw_head_od_mm'] / 2),
         underhead, cfg['screw_head_height_mm'])
    for key, value in [('ThreadMajorDiameter_mm', cfg['screw_major_mm']),
                       ('CoreDiameter_mm', cfg['screw_core_mm']),
                       ('UnderHeadLength_mm', underhead),
                       ('CandidateEngagement_mm', cfg['horn_engagement_mm'])]:
        body.addProperty('App::PropertyFloat', key, 'CandidateFastener'); setattr(body, key, value)
    return body


def _fixed_screw_placement(P, side, tip_abs_y):
    import FreeCAD as App
    return App.Placement(App.Vector(P[0], side * tip_abs_y, P[1]),
                         App.Rotation(App.Vector(0, 0, 1), App.Vector(0, side, 0)))


def _rotated_face(face, angle):
    import FreeCAD as App
    out = face.copy(); out.rotate(App.Vector(), App.Vector(0, 0, 1), math.degrees(angle))
    return out


def _frame_restraints(b, cfg, screening):
    import cad_common as cc
    from refine_flexor import disk, rect
    angle = b.p['spine_case_angle_rad']
    corners = screening['tie_centers_xz_mm']
    bosses = disk(*corners[0], cfg['tie_boss_radius_mm'])
    for P in corners[1:]: bosses = bosses.fuse(disk(*P, cfg['tie_boss_radius_mm']))
    collar = _rotated_face(rect(-12, -9, 24, 38).cut(rect(-10, -7, 20, 34)), angle)
    bands = rect(-12, -7, 24, 1.5).fuse(rect(-12, 24, 24, 3))
    bands = _rotated_face(bands, angle)
    for side, name in [(-1, 'LumbarIntegrated_1'), (1, 'LumbarIntegrated1')]:
        body = b.doc.getObject(name).LinkedObject
        _pad(b, body, 'BraceMountBosses' + ('L' if side == 1 else 'R'), bosses, 0, 1.6)
        if side == 1:
            _pad(b, body, 'CaseEdgeCollarL', collar, 1.6, 1.4)
            _pad(b, body, 'CaseFaceCaptureL', bands, 1.6, .4)
        else:
            _pad(b, body, 'CaseEdgeCollarR', collar, 0, 1.4, True)
            _pad(b, body, 'CaseFaceCaptureR', bands, 0, .4, True)
        holes = [(P[0], P[1], cfg['screw_clearance_mm']) for P in corners]
        _pocket(b, body, 'BraceMountClearances' + str(side).replace('-', '_'), holes, 1.6, 1.6)
        recess = [(P[0], P[1], cfg['tie_collar_recess_mm']) for P in corners]
        _pocket(b, body, 'BraceTubeRecess' + str(side).replace('-', '_'), recess,
                3.0 if side == 1 else -1.4, 1.4, side == -1)
        body.Process += '; nominal case-edge collar and face capture bands; shim/preload/tolerances UNVERIFIED'
    tie = b.ring('FIXED_TIE_OD2p4_TAPMINOR1p7_L53p6', 2.4, 1.7, 53.6)
    tie.Revision = 'r02'; tie.Process = 'metal threaded spacer tube, candidate M2 tapped ends; supplier UNVERIFIED'
    screw = _screw(b, 'FIXED_TIE_M2_CORE_L2p8', cfg['tie_screw_underhead_mm'], cfg,
                   'candidate short M2 tie screw; 1.2 mm nominal end engagement')
    for j, P in enumerate(corners):
        b.add(tie, 'FixedLumbarTie' + str(j), cc.hardware_place(P, 0, 53.6), 'Chassis')
        for side in [-1, 1]:
            b.add(screw, 'FixedTieScrew' + str(j) + '_' + str(side).replace('-', '_'),
                  _fixed_screw_placement(P, side, 25.6), 'SpineHardware')
    # Insulating center shim makes both cases part of the nominal captive pack.
    shim = b.plate('MOTOR_CENTER_INSULATING_SHIM_T0p8', 20, 34, .8)
    shim.Revision = 'r02'; shim.Process = 'insulating prototype shim; nominal tangent case pack; compression allowance UNVERIFIED'
    b.add(shim, 'MotorCenterShim', cc.plane_placement(rotate_plane((-10, -7), angle), .4, angle), 'Chassis')


def apply(b):
    """Mutate the lead's builder only when explicitly called; return audit data.

    Neither saves nor changes views. Recompute/validate/export remains lead work.
    """
    import cad_common as cc
    from refine_flexor import disk, pill_face
    from kinematics import spine
    doc = b.doc
    if 'SpineAttachmentCandidate' in doc.PoseController.PropertiesList:
        return json.loads(doc.PoseController.SpineAttachmentCandidate)
    cfg = provisional_parameters()
    screening = screen_fixed_attachments(b.p)
    if min(screening['min_Bshaft_to_tie_mm'][0], screening['min_Bshaft_to_boss_mm'][0],
           screening['min_Bshaft_to_collar_bound_mm'][0]) <= 0:
        raise RuntimeError('Fixed attachment candidate fails planar B-shaft screen; no modeling attempted')
    phase = doc.PoseController.SpinePhaseRad; state = spine(phase, b.p)
    b.motion = json.loads(doc.PoseController.MotionMap)
    old_sources = set()
    # Crank O=(2.5,2.5), G=(7.5,2.5) retain the existing line_place origin.
    outline = pill_face((2.5, 2.5), (7.5, 2.5), 5).fuse(disk(2.5, 2.5, 4.5)).removeSplitter()
    crank_bores = [(2.5, 2.5, 2.05), (7.5, 2.5, 1.9), (2.5, 0, 2.2), (2.5, 5, 2.2)]
    horn = _body(b, 'HORN_PATTERN_ASSUMED_OD8_T1p2', disk(0, 0, 4), 1.2, 'steel',
                 'candidate horn adapter; pattern/spline/output datum NOT ROBOTIS VERIFIED')
    _pocket(b, horn, 'HornCandidateBores', [(0, 0, 2.05), (0, -2.5, 1.7), (0, 2.5, 1.7)], 1.2, 1.2)
    washer = _body(b, 'HORN_GAP_WASHER_OD8_T0p3', disk(0, 0, 4), .3, 'steel', 'machined gap washer; candidate horn pattern')
    _pocket(b, washer, 'GapWasherBores', [(0, 0, 2.05), (0, -2.5, 2.2), (0, 2.5, 2.2)], .3, .3)
    screw = _screw(b, 'HORN_M2_TRIMMED_CORE_L1p9', 1.9, cfg,
                   'nonstandard trimmed M2 screw candidate; flush head in 0.8 mm counterbore')
    for side, crank_name, horn_name in [(-1, 'DirectCrank_1', 'HornAdapter_1'), (1, 'DirectCrank1', 'HornAdapter1')]:
        suffix = 'L' if side == 1 else 'R'
        crank = _body(b, 'DIRECT_CRANK_FLUSH_M2_' + suffix, outline, 1.2, 'steel',
                      'metal crank; 1.9 mm fixed G bore; flush counterbores leave 0.4 mm floor; strength UNVERIFIED')
        _pocket(b, crank, 'CrankThroughBores' + suffix, crank_bores, 1.2, 1.2)
        _pocket(b, crank, 'CrankFlushCounterbores' + suffix, [(2.5, 0, 3.5), (2.5, 5, 3.5)],
                .8 if side == 1 else 1.2, .8)
        link = doc.getObject(crank_name); old_sources.add(link.LinkedObject.Name); link.setLink(crank)
        link.LinkPlacement = cc.line_place(state['O'], state['G'], side * 29.1, 5, 1.2)
        link = doc.getObject(horn_name); old_sources.add(link.LinkedObject.Name); link.setLink(horn)
        link.LinkPlacement = cc.plane_placement(state['O'], side * 27.6 + .6, phase)
        b.motion[horn_name] = {'kind': 'axialrot', 'point': 'O', 'y': side * 27.6, 'length': 1.2}
        b.add(washer, 'HornGapWasher_' + suffix, cc.plane_placement(state['O'], side * 28.35 + .15, phase),
              'Actuators', {'kind': 'axialrot', 'point': 'O', 'y': side * 28.35, 'length': .3})
        for k, offset in enumerate([-2.5, 2.5]):
            motion = {'kind': 'horn_screw', 'point': 'O', 'offset_perp_mm': offset,
                      'axis_side': side, 'tip_abs_y_mm': 27.0,
                      'underhead_mm': 1.9, 'head_height_mm': .8}
            b.add(screw, 'HornClampScrew_' + suffix + '_' + str(k), motion_placement(motion, phase, state),
                  'SpineHardware', motion)
    _frame_restraints(b, cfg, screening)
    doc.PoseController.MotionMap = json.dumps(b.motion)
    used = {o.LinkedObject.Name for o in doc.Objects if o.TypeId == 'App::Link'}
    b.sources = {k: v for k, v in b.sources.items() if v.Name in used}
    for name in old_sources - used:
        body = doc.getObject(name)
        if body is not None:
            for child in reversed(list(body.Group)): doc.removeObject(child.Name)
            doc.removeObject(name)
    b.library.Visibility = False
    for source in b.sources.values(): source.Visibility = False
    doc.recompute()
    result = {'parameters': cfg, 'fixed_attachment_screen': screening,
              'status': 'BUILT_CANDIDATE_REQUIRES_NATIVE_AND_MOTION_CHECKS',
              'new_motion_kind': 'horn_screw',
              'contact_notes': ['Nominal G press fit', 'M2 minor-core envelopes omit thread-major contact',
                                'Head/counterbore and case/shim surfaces have nominal intended contact'],
              'limits': 'Supplier horn/spline, strengths, fits, connector keepouts, and clamp preload UNVERIFIED'}
    doc.PoseController.addProperty('App::PropertyString', 'SpineAttachmentCandidate')
    doc.PoseController.SpineAttachmentCandidate = json.dumps(result)
    return result
