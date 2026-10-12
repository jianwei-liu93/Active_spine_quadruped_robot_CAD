"""One-piece Movie S1 center frame; native features, lead-only integration.

Source geometry preserves r08 sagittal interfaces. The two former half-cages
become one continuous frame in the retained left instance's local coordinates.
No save, export, application launch, or live-session connection occurs here.
"""
import json
import math
from pathlib import Path

SOURCE_NAME = 'FRM_LUMBAR_MONOLITHIC_CAGE_r09'
RETAINED_INSTANCE = 'LumbarIntegrated1'
RETIRED_INSTANCE = 'LumbarIntegrated_1'
RIGHT_OFFSET = 55.2
FRAME_SPAN = 56.8
STACK_LOW = -12.6
STACK_HIGH = 69.4
STACK_DEPTH = 82.0
OBSOLETE_TIE_INSTANCES = tuple(
    ['FixedLumbarTie' + str(j) for j in range(4)] +
    ['FixedTieScrew' + str(j) + suffix for j in range(4) for suffix in ('__1', '_1')])


def frame_parameters():
    return json.loads((Path(__file__).resolve().parents[1] /
                       'parameters/assembly_r09.json').read_text())['lumbar_frame_r09']


def build(doc, p):
    """Build an unattached native source for isolated lead-run CAD validation.

    Local XY is the sagittal plane and local +Z maps to world -Y. The retained
    instance origin is worldY=28.4. No physical instance is created by build().
    Every feature recompute must retain one valid solid; every profile has zero
    remaining degrees of freedom. Exceptions are CAD failures, never PASS.
    """
    import FreeCAD as App, Part, Sketcher
    import cad_common as cc
    from refine_flexor import rect, disk, pill_face, sketch_face
    from kinematics import spine
    V = App.Vector
    s = spine(0, p)
    angle = p['spine_case_angle_rad']
    frame = frame_parameters()
    if abs(angle - math.pi / 6) > 1e-9:
        raise ValueError('Frozen case angle requires 30deg')
    if frame['midplane_seam_total_clearance_mm'] != 0:
        raise ValueError('Monolithic r09 frame requires zero midplane seam')
    if doc.getObject(SOURCE_NAME):
        raise ValueError(SOURCE_NAME + ' exists; use a fresh document')

    def rotate(face):
        face = face.copy()
        face.rotate(V(), V(0, 0, 1), math.degrees(angle))
        return face

    def section(face):
        # Resolve 2D boolean compounds, retaining all inner/outer section wires.
        pieces = [f.extrude(V(0, 0, 1)) for f in face.Faces]
        if not pieces:
            raise RuntimeError('Empty frame section')
        solid = pieces[0]
        for q in pieces[1:]:
            solid = solid.fuse(q)
        solid = solid.removeSplitter()
        if not solid.isValid() or len(solid.Solids) != 1:
            raise RuntimeError('Frame section must be connected')
        bottoms = [f for f in solid.Faces if f.BoundBox.ZLength < 1e-7
                   and abs(f.CenterOfMass.z) < 1e-7]
        if len(bottoms) != 1:
            raise RuntimeError('Frame section needs one complete bottom face')
        return bottoms[0]

    body = doc.addObject('PartDesign::Body', SOURCE_NAME)
    cc.metadata(body, SOURCE_NAME, 'PA12',
                'DESIGN_ASSUMPTION Movie S1 monolithic open-top cage; '
                'solid sagittal cheeks and continuous orthogonal windowed walls; '
                'mounting interfaces/fits/preload UNVERIFIED')
    body.Revision = 'r09'
    feature_names = []

    def finish(feature, sketch, previous):
        doc.recompute()
        sketch.Visibility = False
        if previous:
            previous.Visibility = False
        if sketch.FullyConstrained is not True:
            raise RuntimeError(sketch.Name + ' must be fully constrained')
        if feature.Shape.isNull() or not feature.Shape.isValid() or len(feature.Shape.Solids) != 1:
            raise RuntimeError(feature.Name + ' must preserve one valid connected solid')
        feature_names.append(feature.Name)
        return feature

    def pad(label, face, z, length, reverse=False):
        previous = body.Tip
        sk = sketch_face(doc, body, body.Name + '_' + label + 'Sketch', section(face), z)
        feature = body.newObject('PartDesign::Pad', body.Name + '_' + label)
        feature.Profile = sk
        feature.Length = length
        feature.Reversed = reverse
        return finish(feature, sk, previous)

    def pocket(label, holes, z, depth, reverse=False):
        previous = body.Tip
        sk = doc.addObject('Sketcher::SketchObject', body.Name + '_' + label + 'Sketch')
        body.addObject(sk)
        sk.Placement.Base.z = z
        for x, y, radius in holes:
            cc.circle(sk, x, y, radius)
        feature = body.newObject('PartDesign::Pocket', body.Name + '_' + label)
        feature.Profile = sk
        feature.Length = depth
        feature.Reversed = reverse
        return finish(feature, sk, previous)

    def face_pocket(label, face, placement, depth):
        previous = body.Tip
        sk = sketch_face(doc, body, body.Name + '_' + label + 'Sketch', face, 0)
        sk.Placement = placement
        feature = body.newObject('PartDesign::Pocket', body.Name + '_' + label)
        feature.Profile = sk
        feature.Length = depth
        return finish(feature, sk, previous)

    # Solid upper sagittal cheeks. Broad windows belong on orthogonal walls.
    # The front wall lies outside the case face; only the rear collar must
    # clear the entire manufacturer body envelope.
    x,z,w,h=frame['outer_rectangle_mm'];r=frame['outer_corner_radius_mm']
    # Rounded rectangle with an essentially square lower perimeter, unlike
    # the r06 external circular foot. Corners stay inside recorded extents.
    outer=rect(x+r,z,w-2*r,h).fuse(rect(x,z+r,w,h-2*r))
    for cx in (x+r,x+w-r):
        for cz in (z+r,z+h-r):outer=outer.fuse(disk(cx,cz,r))
    outer=outer.removeSplitter()
    annulus=rotate(outer.cut(disk(0,0,frame['lower_opening_radius_mm'])).removeSplitter())
    collar=rotate(outer.cut(rect(-10,-7,20,34)).removeSplitter())
    bands=[rotate(rect(-12,-7,24,1.5)),rotate(rect(-12,24,24,3))]
    guides=[];slot_report=[]
    for i,sign in ((1,1),(2,-1)):
        xs=[spine(j*math.tau/720,p)['C'+str(i)][0] for j in range(721)]
        xc=(min(xs)+max(xs))/2;zc=sign*p['guide_z_mm']
        ax,az=s['A2' if i==1 else 'A1'];r=p['guide_pivot_radius_mm']
        pts=[V(xc-6.5,zc,0),V(xc+6.5,zc,0),V(ax+r,az,0),V(ax-r,az,0)]
        web=Part.Face(Part.makePolygon(pts+[pts[0]]))
        face=pill_face((xc-6.5,zc),(xc+6.5,zc),8.2).fuse(web).fuse(disk(ax,az,r))
        face=face.cut(pill_face((xc-6.5,zc),(xc+6.5,zc),5.2)).cut(disk(ax,az,2.025)).removeSplitter()
        guides.append(face)
        slot_report.append({'slider':'C'+str(i),'pivot':'A2' if i==1 else 'A1','center_xz_mm':(xc,zc),'travel_bounds_x_mm':(min(xs),max(xs))})
    # Connected construction: near cheek, both full-span walls, far cheek.
    pad('LeftCaseCheek', annulus, 0, 1.6)
    for j, (lo, hi) in enumerate(frame['crosswall_case_x_intervals_mm']):
        za, zb = frame['crosswall_case_z_bounds_mm']
        pad('ContinuousCrosswall' + str(j), rotate(rect(lo, za, hi-lo, zb-za)), 0, FRAME_SPAN)
    pad('RightCaseCheek', annulus, RIGHT_OFFSET, 1.6)

    zlo, zhi = frame['crosswall_window_case_z_bounds_mm']
    ylo, yhi = frame['crosswall_window_y_bounds_mm']
    wlo, whi = sorted((28.4-ylo, 28.4-yhi))
    for j, (lo, hi) in enumerate(frame['crosswall_case_x_intervals_mm']):
        normal = 1 if j == 1 else -1
        xwall = hi if normal == 1 else lo
        U = V(0, 0, -normal)
        W = V(math.cos(angle)*normal, math.sin(angle)*normal, 0)
        Zcase = V(-math.sin(angle), math.cos(angle), 0)
        rotation = App.Rotation(U, Zcase, W, 'ZXY')
        ulo, uhi = sorted((-normal*wlo, -normal*whi))
        face_pocket('CrosswallWindow' + str(j), rect(ulo, zlo, uhi-ulo, zhi-zlo),
                    App.Placement(V(xwall*math.cos(angle), xwall*math.sin(angle), 0), rotation), hi-lo)

    # Two carrier clearances on positive case-X wall, in unchanged worldY bands.
    U = V(0, 0, -1)
    Zcase = V(-math.sin(angle), math.cos(angle), 0)
    W = V(math.cos(angle), math.sin(angle), 0)
    xwall = frame['crosswall_case_x_intervals_mm'][1][1]
    previous = body.Tip
    sk = doc.addObject('Sketcher::SketchObject', body.Name + '_CarrierAccessSketch')
    body.addObject(sk)
    sk.Placement = App.Placement(V(xwall*math.cos(angle), xwall*math.sin(angle), 0),
                                 App.Rotation(U, Zcase, W, 'ZXY'))
    ya0, yb0 = frame['carrier_access_pockets_y_abs_mm']
    za, zb = frame['carrier_access_pockets_case_z_mm']
    for ya, yb in ((ya0, yb0), (-yb0, -ya0)):
        ua, ub = sorted((ya-28.4, yb-28.4))
        for e in rect(ua, za, ub-ua, zb-za).Edges:
            k = sk.addGeometry(Part.LineSegment(e.Vertexes[0].Point, e.Vertexes[-1].Point), False)
            sk.addConstraint(Sketcher.Constraint('Block', k))
    cut = body.newObject('PartDesign::Pocket', body.Name + '_CarrierAccess')
    cut.Profile = sk
    cut.Length = 1.6
    finish(cut, sk, previous)

    for side in (1, -1):
        suffix = 'Left' if side == 1 else 'Right'
        offset = 0 if side == 1 else RIGHT_OFFSET
        for j, (lo, hi) in enumerate(((-35.5, -10), (10, 35.5))):
            pad(suffix + 'LocalEndPlatform' + str(j), rect(lo, -2.5, hi-lo, 5), offset, 1.6)
        for label, A, B in (('ShortEarE1A2', 'E1', 'A2'), ('ShortEarE2A1', 'E2', 'A1')):
            P = s[B]
            direction = 1 if P[1] > 0 else -1
            lo = max(-35.5, P[0]-frame['ear_base_width_mm']/2)
            hi = min(35.5, P[0]+frame['ear_base_width_mm']/2)
            pts = [V(lo, direction*2, 0), V(hi, direction*2, 0),
                   V(P[0]+3.5, P[1], 0), V(P[0]-3.5, P[1], 0)]
            pedestal = Part.Face(Part.makePolygon(pts+[pts[0]])).fuse(disk(*P, 3.5))
            pad(suffix + label, pedestal, offset, 1.6)
        for j, face in enumerate((rect(-35.5, -2.5, 19.5, 5), rect(16, -2.5, 19.5, 5))):
            pad(suffix + 'BroadShelf' + str(j), face, offset+(0 if side == 1 else 1.6), 11, side == 1)
        for j, face in enumerate(guides):
            pad(suffix + 'OuterGuide' + str(j), face, offset+(-11 if side == 1 else 12.6), 1.6, side == 1)
        pad(suffix + 'CaseEdgeCollar', collar, offset+(1.6 if side == 1 else 0), 1.4, side == -1)
        for j, band in enumerate(bands):
            pad(suffix + 'CaseFaceBand' + str(j), band, offset+(1.6 if side == 1 else 0), .4, side == -1)
        for key in ('A1', 'A2'):
            pad(suffix + 'InnerJournalBoss' + key, disk(*s[key], 3.5), offset, 1.6)
        for key in ('E1', 'E2'):
            pad(suffix + 'ShelfJournalBoss' + key, disk(*s[key], 3.5), offset+(1.6 if side == 1 else 0), 14.2, side == 1)

    pocket('WholeStackJournalClearances', [(0, 0, frame['lower_opening_radius_mm'])] +
           [(s[n][0], s[n][1], 2.025) for n in ('A1', 'A2', 'E1', 'E2')], STACK_HIGH, STACK_DEPTH)
    travel_records = []
    for i in (1, 2):
        points = [spine(j*math.tau/3600, p)['C'+str(i)] for j in range(3601)]
        lo = min(q[0] for q in points)-.01
        hi = max(q[0] for q in points)+.01
        z = points[0][1]
        radius = frame['travel_relief_radius_mm']
        feature = face_pocket('C'+str(i)+'TravelRelief', pill_face((lo, z), (hi, z), 2*radius),
                              App.Placement(V(0, 0, STACK_HIGH), App.Rotation()), STACK_DEPTH)
        travel_records.append({'shaft': 'C'+str(i), 'center_x_bounds_mm': [lo, hi],
                               'center_z_mm': z, 'radius_mm': radius, 'feature': feature.Name})
    doc.recompute()
    return body, {'features': tuple(feature_names), 'guide_slots': slot_report,
                  'travel_reliefs': travel_records, 'execution_native_validity': True,
                  'solid_count': len(body.Shape.Solids),
                  'pad_count': sum(o.TypeId == 'PartDesign::Pad' for o in body.Group),
                  'pocket_count': sum(o.TypeId == 'PartDesign::Pocket' for o in body.Group),
                  'sketch_count': sum(o.TypeId == 'Sketcher::SketchObject' for o in body.Group),
                  'source_local_stack_bounds_mm': [STACK_LOW, STACK_HIGH]}


def apply(b, remove_old=True):
    """Install on the retained physical ID; explicitly retire only the other ID.

    Both expected AppLinks must exist. Build/validate before swapping sources.
    No autosave. Retire only the 12 explicitly identified separation-tie parts.
    Motor shims, shafts, motors and mechanism datums remain untouched.
    """
    doc = b.doc
    retained = doc.getObject(RETAINED_INSTANCE)
    retired = doc.getObject(RETIRED_INSTANCE)
    if any(o is None or o.TypeId != 'App::Link' for o in (retained, retired)):
        raise ValueError('Both exact existing LumbarIntegrated AppLinks are required')
    obsolete_links = [doc.getObject(name) for name in OBSOLETE_TIE_INSTANCES]
    if any(o is None or o.TypeId != 'App::Link' for o in obsolete_links):
        raise ValueError('All 12 exact obsolete separation-tie AppLinks are required')
    links_before = sum(o.TypeId == 'App::Link' for o in doc.Objects)
    old_sources = {o.LinkedObject.Name: o.LinkedObject for o in [retained, retired] + obsolete_links}
    placement = retained.LinkPlacement
    body, result = build(doc, b.p)
    b.library.addObject(body)
    b.sources[body.Name] = body
    retained.setLink(body)
    retained.LinkPlacement = placement
    retired_names = (RETIRED_INSTANCE,) + OBSOLETE_TIE_INSTANCES
    for name in retired_names:
        doc.removeObject(name)
        if hasattr(b, 'motion'):
            b.motion.pop(name, None)
    controller = doc.getObject('PoseController')
    if controller is not None and 'MotionMap' in controller.PropertiesList:
        motion = json.loads(controller.MotionMap)
        for name in retired_names:
            motion.pop(name, None)
        controller.MotionMap = json.dumps(motion)
    removed, preserved = [], []
    doc.recompute()
    for source in old_sources.values():
        owned_objects = [source] + list(getattr(source, 'Group', []))
        owned = {o.Name for o in owned_objects}
        external = [q for o in owned_objects for q in o.InList
                    if q.Name not in owned and q != b.library]
        used = any(o.TypeId == 'App::Link' and o.LinkedObject == source for o in doc.Objects)
        if not remove_old or external or used:
            preserved.append(source.Name)
            continue
        name = source.Name
        for key, val in list(b.sources.items()):
            if val.Name == name:
                del b.sources[key]
        children = [o.Name for o in getattr(source, 'Group', [])]
        b.library.removeObject(source)
        doc.removeObject(name)
        for child in reversed(children):
            if doc.getObject(child) is not None:
                doc.removeObject(child)
        removed.append(name)
    doc.recompute()
    result.update({'instances': (RETAINED_INSTANCE,), 'sources': (body.Name,),
                   'identity_merge': {RETIRED_INSTANCE: RETAINED_INSTANCE},
                   'removed_unused_sources': tuple(removed), 'retained_used_sources': tuple(preserved),
                   'physical_frame_instance_count': 1,
                   'removed_obsolete_tie_instances': OBSOLETE_TIE_INSTANCES,
                   'retired_physical_instances': retired_names,
                   'physical_link_count_before': links_before,
                   'physical_link_count_after': sum(o.TypeId == 'App::Link' for o in doc.Objects),
                   'limitations': ('Whole-spine collision/motion require lead validation',
                                   'Metric reconstruction, fits/preload and fabrication remain assumptions',
                                   'Motor center shims preserved; native motor retention remains provisional')})
    return result
