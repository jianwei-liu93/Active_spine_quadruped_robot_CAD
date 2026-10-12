"""r03 prescribed poses and read-only copied-source placements (mm/radians).

apply_pose(doc, theta, leg_angles={tag: (qh, qk)}) moves actual links and,
only when needed after a permitted leg-angle change, creates private spring definitions.
Installed tendon geometry permits fixed wheel u=0 and captured hind leg angles
only; spine motion rigidly transforms its torso-local source geometry once.
placements(doc, theta) returns all App::Link placements without mutations or
spring rebuilding, holding the document's recorded leg angles fixed. Assign
these placements to COPIES OF LINKED SOURCE shapes, not already placed shapes.
Neither API saves, opens a GUI, or solves cable/elastic equilibrium. Unknown
motion kinds fail rather than silently leaving an assembly member behind.
"""
import json
import math
from pathlib import Path
import sys

from kinematics import load_parameters, spine
from leg_geometry_r02 import leg_geometry

ROOT = Path(__file__).resolve().parents[1]
LEG_KINDS = frozenset(('leg_r02_segment', 'leg_r02_point', 'leg_r02_body',
    'leg_r02_body_axial', 'leg_r02_headed_pin', 'leg_r02_spring',
    'leg_r02_compression_seat', 'leg_r02_spring_guide'))
KINDS = LEG_KINDS | {'segment', 'point', 'axialrot', 'horn_screw',
                     'torso_r03', 'torso_offset_r03', 'torso_r03_offset',
                     'tendon_r03_wheel', 'tendon_r03_guide', 'tendon_r03_cable',
                     'torso_r04_rigid'}


def _number(value):
    return float(value.Value if hasattr(value, 'Value') else value)


def _parameters(doc):
    p = load_parameters(ROOT / 'parameters/candidate_r02.json')
    native = doc.getObject('DesignParameters')
    if native is not None:
        for key in p:
            if key in native.PropertiesList:
                value = _number(getattr(native, key))
                if isinstance(p[key], int):
                    if not value.is_integer():
                        raise ValueError('Nonintegral native branch/integer parameter: ' + key)
                    value = int(value)
                p[key] = value
    return p


def torso_angle(theta, kind, p):
    """Same contract as build_torso_r03.torso_angle, without its GUI imports.

    If the build module is already loaded, use its authoritative function.
    Its import chain otherwise reaches build_flexor/FreeCADGui, so CLI calls
    evaluate the identical beta(theta)-beta(0) formula directly.
    """
    if kind not in ('hind', 'fore'):
        raise ValueError('Unknown torso: ' + str(kind))
    module = sys.modules.get('build_torso_r03')
    if module is not None:
        return module.torso_angle(theta, kind, p)
    i = 1 if kind == 'hind' else 2
    a = spine(theta, p)['beta' + str(i)] - spine(0, p)['beta' + str(i)]
    return math.atan2(math.sin(a), math.cos(a))


def _transform(E, angle, point):
    c, s = math.cos(angle), math.sin(angle)
    return (E[0] + c * point[0] - s * point[1],
            E[1] + s * point[0] + c * point[1])


def _angle(A, B):
    if math.dist(A, B) <= 1e-12:
        raise ValueError('Coincident motion endpoints')
    return math.atan2(B[1] - A[1], B[0] - A[0])


def _offset(A, B, distance):
    length = math.dist(A, B)
    if length <= 1e-12:
        raise ValueError('Coincident spring/guide endpoints')
    return (A[0] + (B[0] - A[0]) * distance / length,
            A[1] + (B[1] - A[1]) * distance / length)


def _angles(motion, controller, requested=None):
    tags = {}
    for m in motion.values():
        if m['kind'] in LEG_KINDS:
            identity = (m['leg_type'], m['side'])
            if m['tag'] in tags and tags[m['tag']] != identity:
                raise ValueError('Conflicting leg identity: ' + m['tag'])
            tags[m['tag']] = identity
    saved = json.loads(controller.LegAnglesR03) if 'LegAnglesR03' in controller.PropertiesList else {}
    if set(saved) - set(tags):
        raise ValueError('Recorded leg state has unknown tags')
    current = {}
    for tag, (kind, side) in tags.items():
        if side not in (-1, 1):
            raise ValueError('Invalid leg side for ' + tag)
        g = leg_geometry(kind)
        current[tag] = tuple(saved.get(tag, (g['thigh_angle_rad'], g['passive_knee_rad'])))
    target = dict(current)
    if requested is not None:
        if not isinstance(requested, dict) or set(requested) - set(tags):
            raise ValueError('leg_angles must map existing leg tags to (qh,qk) radians')
        for tag, pair in requested.items():
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise ValueError(tag + ': expected (qh,qk)')
            target[tag] = tuple(float(q) for q in pair)
    for tag, pair in target.items():
        if len(pair) != 2 or not all(math.isfinite(q) for q in pair):
            raise ValueError('Invalid recorded/requested angles for ' + tag)
    changed = {tag for tag in tags if any(abs(a - b) > 1e-12
               for a, b in zip(current[tag], target[tag]))}
    return tags, target, changed


def _world_tendon_point(E, angle, point):
    """Torso-local XYZ to world XYZ, preserving axial Y exactly once."""
    x,z=_transform(E,angle,(point[0],point[2]))
    return (x,point[1],z)


def _guard_installed_tendons(motion,tags,angles):
    """Refuse stale cable geometry before any document mutation/regeneration."""
    cables=[m for m in motion.values() if m['kind']=='tendon_r03_cable']
    if not cables:return
    for m in cables:
        route=m.get('route_local')
        if not route or 'geometry' not in route:
            raise ValueError('Installed tendon lacks captured local route/leg state; regenerate routing')
        if abs(route['wheel_angle_rad'])>1e-12 or abs(m.get('wheel_angle_rad',0))>1e-12:
            raise ValueError('Installed tendon pose supports fixed wheel u=0 only; regenerate routing')
        g=route['geometry'];fixed=(g['thigh_angle_rad'],g['passive_knee_rad'])
        for tag,(kind,side) in tags.items():
            if kind=='hind' and side==m['side'] and any(abs(x-y)>1e-12 for x,y in zip(angles[tag],fixed)):
                raise ValueError('Installed tendon requires fixed hind leg angles for '+tag+'; regenerate cable route before changing leg/wheel state')
    for m in motion.values():
        if m['kind'] in ('tendon_r03_wheel','torso_r04_rigid'):
            u=m.get('angle_rad',m.get('wheel_angle_rad',0))
            if abs(u)>1e-12:
                raise ValueError('Installed tendon wheel/coupling state differs from fixed u=0; regenerate routing')


def _tendon_placement(App,m,E,a):
    """Rigid parent motion for source-local geometry; no route rebuilding."""
    V=lambda p:App.Vector(*p)
    parent=App.Rotation(App.Vector(0,-1,0),math.degrees(a))
    k=m['kind']
    if k=='torso_r04_rigid':
        data=json.loads(m['local_placement_json'])
        base=tuple(data['base_xyz_mm']);q=tuple(data['rotation_xyzw'])
        if len(base)!=3 or len(q)!=4 or not all(math.isfinite(x) for x in (*base,*q)):
            raise ValueError('Invalid captured rigid placement')
        rotation=App.Rotation(*q)
    elif k=='tendon_r03_wheel':
        W=m['center'];base=(m['source_start_x'],W[1],W[2])
        rotation=App.Rotation(V((0,1,0)),V((0,0,1)),V((1,0,0)),'ZXY')
        rotation=App.Rotation(V((1,0,0)),math.degrees(m['angle_rad'])).multiply(rotation)
    elif k=='tendon_r03_guide':
        C=m['center'];axis=m['axis'];component=m.get('component')
        length=3.6 if component=='journal' else .2 if component=='washer' else .6 if component=='outer_clip' else 1.2
        offset=m.get('axial_offset_mm',0)
        base=tuple(c+(offset-length/2)*v for c,v in zip(C,axis))
        rotation=App.Rotation(V((0,0,1)),V(axis))
    elif k=='tendon_r03_cable':
        base=(0,0,0);rotation=App.Rotation()
    elif k=='torso_r03_offset':
        base=m['point']
        rotation=App.Rotation(V(m['rotation_local_axis']),m['rotation_deg'])
    else:raise ValueError('Unsupported tendon parent frame: '+str(k))
    return App.Placement(V(_world_tendon_point(E,a,base)),parent.multiply(rotation))


def _plan(doc, theta, leg_angles=None):
    import FreeCAD as App
    import cad_common as cc
    from build_leg_r02 import _axis_placement, _outer_axial_placement
    from spine_attachments_r02 import motion_placement
    theta = float(theta)
    if not math.isfinite(theta):
        raise ValueError('theta must be finite radians')
    controller = doc.getObject('PoseController')
    if controller is None:
        raise ValueError('PoseController is missing')
    motion = json.loads(controller.MotionMap)
    unknown = {m.get('kind') for m in motion.values()} - KINDS
    if unknown:
        raise ValueError('Unsupported motion kinds: ' + repr(sorted(unknown, key=str)))
    for name in motion:
        obj = doc.getObject(name)
        if obj is None or obj.TypeId != 'App::Link':
            raise ValueError('MotionMap target is not an existing App::Link: ' + name)
    p = _parameters(doc); state = spine(theta, p)
    torsos = {kind: (state['E1' if kind == 'hind' else 'E2'], torso_angle(theta, kind, p))
              for kind in ('hind', 'fore')}
    tags, angles, changed = _angles(motion, controller, leg_angles)
    _guard_installed_tendons(motion,tags,angles)
    legs = {}
    for tag, (kind, side) in tags.items():
        g = leg_geometry(kind, thigh_angle=angles[tag][0], passive_knee=angles[tag][1])
        E, a = torsos[kind]
        P = {n: _transform(E, a, g[n]) for n in ('H','K','A','F','O1','A1','O2','O3')}
        legs[tag] = (g, P, a)
    result = {o.Name: App.Placement(o.LinkPlacement) for o in doc.Objects if o.TypeId == 'App::Link'}
    springs, guides = [], []
    for name, m in motion.items():
        k = m['kind']
        if k == 'segment':
            place = cc.line_place(state[m['a']], state[m['b']], m['y'], m['width'], m['thickness'])
        elif k == 'point':
            place = cc.hardware_place(state[m['point']], m['y'], m['length'])
        elif k == 'axialrot':
            place = cc.plane_placement(state[m['point']], m['y'] + m['length']/2, theta)
        elif k == 'horn_screw':
            place = motion_placement(m, theta, state)
        elif k in ('tendon_r03_wheel','tendon_r03_guide','tendon_r03_cable','torso_r03_offset','torso_r04_rigid'):
            E,a=torsos[m.get('torso','hind')]
            place=_tendon_placement(App,m,E,a)
        elif k in ('torso_r03', 'torso_offset_r03'):
            E, a = torsos[m['torso']]
            if k == 'torso_r03':
                place = cc.plane_placement(E, m['local_y'], a)
            else:
                P = _transform(E, a, m['point']); a += m.get('angle', 0)
                place = (cc.plane_placement(P, m['y'], a) if m.get('plane') else
                         App.Placement(App.Vector(P[0], m['y'], P[1]),
                                       App.Rotation(App.Vector(0,-1,0), math.degrees(a))))
        else:
            g, P, a = legs[m['tag']]
            if k == 'leg_r02_segment':
                A, B = P[m['a']], P[m['b']]
                rule = m['placement_rule']
                if rule == 'capsule_pivot_offset':
                    place = cc.line_place(A, B, m['y'], m['width'], m['thickness'])
                elif rule == 'origin_centered_profile':
                    place = cc.plane_placement(A, m['y'] + m['thickness']/2, _angle(A,B))
                else:
                    raise ValueError('Unsupported leg placement rule: ' + rule)
            elif k == 'leg_r02_point':
                place = cc.hardware_place(P[m['point']], m['y'], m['length'])
            elif k == 'leg_r02_body':
                angle = a + g['body_frames'][m['body']]['angle_rad']
                place = cc.plane_placement(P[m['point']], m['y'] + m['thickness']/2, angle)
            elif k == 'leg_r02_body_axial':
                if m['body'] != 'motor_shaft' or m['axial_direction'] != -m['side']:
                    raise ValueError('Unsupported keyed-shaft frame: ' + name)
                place = _outer_axial_placement(P[m['point']], m['start_y'],
                                               a + g['thigh_angle_rad'], m['side'])
            elif k == 'leg_r02_headed_pin':
                if m['axial_direction'] != -m['side']:
                    raise ValueError('Unsupported headed-pin direction: ' + name)
                place = _outer_axial_placement(P[m['point']], m['outer_y'], a, m['side'])
            elif k == 'leg_r02_compression_seat':
                A, B = P[m['a']], P[m['b']]
                place = cc.plane_placement(A, m['y'] + m['thickness']/2, _angle(A,B))
            elif k in ('leg_r02_spring', 'leg_r02_spring_guide'):
                A, B = P[m['a']], P[m['b']]
                inset = m['seat_offset_mm'] if k == 'leg_r02_spring' else m['offset_mm']
                place = _axis_placement(_offset(A, B, inset), B, m['y'])
                if k == 'leg_r02_spring':
                    if not m.get('rebuild_length_dependent_source'):
                        raise ValueError('Spring lacks length-dependent contract: ' + name)
                    springs.append((name, m, math.dist(A,B) - 2*inset))
                else:
                    guides.append((name, m, math.dist(A,B) - 2*inset))
            else:
                raise ValueError('Unhandled motion kind: ' + str(k))
        result[name] = place
    return result, angles, changed, springs, guides, motion


def _spring_lengths(doc, entries):
    """Read installed/free lengths from source metadata; never infer from BBox."""
    rows = []
    for name, m, length in entries:
        src = doc.getObject(name).LinkedObject
        required = ('FreeLength_mm', 'InstalledCoilLength_mm', 'SeatInset_mm',
                    'WireDiameter_mm', 'OuterDiameter_mm')
        if any(key not in src.PropertiesList for key in required):
            raise ValueError('Spring source metadata incomplete: ' + name)
        inset, free, installed = (_number(getattr(src, k)) for k in
                                 ('SeatInset_mm','FreeLength_mm','InstalledCoilLength_mm'))
        if abs(inset - m['seat_offset_mm']) > 1e-8:
            raise ValueError('Spring source/descriptor seat offsets disagree: ' + name)
        if abs(_number(src.WireDiameter_mm)-.5)>1e-8 or abs(_number(src.OuterDiameter_mm)-4)>1e-8:
            raise ValueError('Spring generator only supports frozen OD4/wire0.5: ' + name)
        if length <= 0 or free <= 0:
            raise ValueError('Nonpositive spring coil length: ' + name)
        rows.append((name, m, src, length, free, abs(installed-length)>1e-7))
    return rows


def placements(doc, theta):
    """All source-local→world link placements; NO document or shape mutations.

    The saved LegAnglesR03 (otherwise frozen leg defaults) remain fixed while
    torso groups rotate. Existing spring-source lengths must match those angles.
    Unknown/missing descriptors or mismatched spring sources raise explicitly.
    """
    result, angles, changed, entries, guides, motion = _plan(doc, theta)
    mismatches = [row[0] for row in _spring_lengths(doc, entries) if row[-1]]
    if mismatches:
        raise ValueError('Copied sweep requires matching fixed leg/spring state: ' + repr(mismatches))
    return result


def apply_pose(doc, theta, leg_angles=None):
    """Apply a prescribed state transactionally; no save or GUI operations.

    Partial per-tag overrides keep other recorded angles. Each pair is (qh,qk)
    radians; qh is directly driven, ankle angle is dependent. Spring regeneration
    is private per link and only permitted after an actual leg-angle change.
    Fixed-length compression guides are placed but never scaled.
    """
    import cad_common as cc
    from build_leg_r02 import spring_shape
    result, angles, changed, entries, guides, motion = _plan(doc, theta, leg_angles)
    rows = _spring_lengths(doc, entries)
    prepared = []
    for name, m, source, length, free, mismatch in rows:
        if mismatch:
            if m['tag'] not in changed:
                raise ValueError('Unrecorded leg/spring state mismatch: ' + name)
            shape = spring_shape(length, m['spring'], free)
            if not shape.isValid() or len(shape.Solids) != 1:
                raise ValueError('Regenerated spring is not one valid solid: ' + name)
            prepared.append((name,m,source,length,free,shape))
    warnings, guide_overlap = [], {}
    for name, m, gap in guides:
        if gap < m['length']:
            warnings.append(name + ': guide projects beyond opposite seat (coil gap < guide length)')
        # Both source guides have the same frozen length; report the engagement.
        partners = [d for n, d, v in guides if d['tag']==m['tag'] and n!=name]
        if len(partners) != 1:
            raise ValueError('Compression guide needs one opposing partner: ' + name)
        overlap = m['length'] + partners[0]['length'] - gap
        guide_overlap[name] = overlap
        if overlap <= 0:
            warnings.append(name + ': compression guide overlap is nonpositive')
    doc.openTransaction('r03 prescribed robot pose')
    try:
        library = doc.getObject('PartsLibrary')
        for name, m, old, length, free, shape in prepared:
            users = [o for o in doc.Objects if o.TypeId == 'App::Link'
                     and o.LinkedObject.Name == old.Name]
            if getattr(old, 'PoseSpringInstance', None) == name and len(users) == 1:
                # Only this link owns the source: safe to regenerate in place.
                old.Shape = shape
                old.InstalledCoilLength_mm = length
                continue
            root = getattr(old, 'PoseSpringRootName', old.Name)
            src = doc.addObject('PartDesign::Feature', root + '_Pose')
            src.Shape = shape
            cc.metadata(src, old.PartNumber, old.MaterialName, old.Process, role='SPRING')
            src.Revision = old.Revision
            for key in ('FreeLength_mm','AnchorFreeLength_mm','SeatInset_mm','WireDiameter_mm','OuterDiameter_mm'):
                if key in old.PropertiesList:
                    src.addProperty('App::PropertyLength',key,'SpringAssumptions')
                    setattr(src,key,_number(getattr(old,key)))
            src.addProperty('App::PropertyLength','InstalledCoilLength_mm','SpringAssumptions')
            src.InstalledCoilLength_mm = length
            for key,value in (('Provenance',getattr(old,'Provenance','DESIGN_ASSUMPTION')),
                              ('PoseSpringRootName',root), ('PoseSpringInstance',name)):
                src.addProperty('App::PropertyString',key,'SpringAssumptions');setattr(src,key,value)
            if library is not None: library.addObject(src)
            src.Visibility = False
            doc.getObject(name).setLink(src)
        for name, place in result.items():
            doc.getObject(name).LinkPlacement = place
        controller = doc.PoseController
        if 'LegAnglesR03' not in controller.PropertiesList:
            controller.addProperty('App::PropertyString','LegAnglesR03','Pose')
        controller.LegAnglesR03 = json.dumps(angles)
        controller.SpinePhaseRad = float(theta)
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    return {'spine_phase_rad':float(theta), 'placements':len(result),
            'leg_angles_rad':angles, 'changed_leg_tags':sorted(changed),
            'regenerated_spring_instances':[row[0] for row in prepared],
            'guide_warnings':warnings,
            'compression_guide_overlap_mm':guide_overlap,
            'unmapped_fixed_links':len(result)-len(motion),
            'limits':'Prescribed geometry only; cable/wheel motion, loads, fit and swept clearance are not solved. Unmapped links stay fixed.'}
