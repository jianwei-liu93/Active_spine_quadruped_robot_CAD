"""Compact single-piece Movie S1 center frame; native features, lead-only integration.

Source geometry preserves S9 datums and the retained instance local frame.
The compact coherent body uses only the selected central E support system.
No save, export, application launch, or live-session connection occurs here.
Metric reconstruction, supplier interfaces, structural capacity and retention
remain assumptions; no dimensions are claimed to have been measured from film.
"""
import json
import math
from pathlib import Path

SOURCE_NAME = 'FRM_LUMBAR_COMPACT_CAGE_r12'
RETAINED_INSTANCE = 'LumbarIntegrated1'
RETIRED_INSTANCE = 'LumbarIntegrated_1'
RIGHT_OFFSET = 55.2
FRAME_SPAN = 56.8
STACK_LOW = -11.0
STACK_HIGH = 67.8
STACK_DEPTH = 78.8
OBSOLETE_TIE_INSTANCES = tuple(
    ['FixedLumbarTie' + str(j) for j in range(4)] +
    ['FixedTieScrew' + str(j) + suffix for j in range(4) for suffix in ('__1', '_1')])


def frame_parameters(config=None):
    cfg = config or json.loads((Path(__file__).resolve().parents[1] / 'parameters/assembly_r12.json').read_text())
    f = dict(cfg['lumbar_frame_r09'])
    lo,hi=cfg['center_frame_r12']['housing_case_x_bounds_mm']
    f['outer_rectangle_mm'] = [lo, -11, hi-lo, 44]
    f['outer_corner_radius_mm'] = 2.5
    f['crosswall_case_x_intervals_mm'] = [[lo,lo+1.6],[hi-1.6,hi]]
    return f


def build(doc, p, config=None):
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
    frame = frame_parameters(config)
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
    body.Revision = (config or {}).get('center_frame_r12',{}).get('component_revision','r12')
    if body.Revision!='r12':body.PartNumber=SOURCE_NAME.replace('_r12','_'+body.Revision)
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
            pad(suffix + 'BroadShelf' + str(j), face, offset+(0 if side == 1 else 1.6), 9.4, side == 1)
        for j, face in enumerate(guides):
            pad(suffix + 'OuterGuide' + str(j), face, offset+(-9.4 if side == 1 else 11.0), 1.6, side == 1)
        pad(suffix + 'CaseEdgeCollar', collar, offset+(1.6 if side == 1 else 0), 1.4, side == -1)
        for j, band in enumerate(bands):
            pad(suffix + 'CaseFaceBand' + str(j), band, offset+(1.6 if side == 1 else 0), .4, side == -1)
        for key in ('A1', 'A2'):
            pad(suffix + 'InnerJournalBoss' + key, disk(*s[key], 3.5), offset, 1.6)

    pocket('WholeStackJournalClearances', [(0, 0, frame['lower_opening_radius_mm'])] +
           [(s[n][0], s[n][1], 2.025) for n in ('A1', 'A2')], STACK_HIGH, STACK_DEPTH)
    # Single selected E load path: full-span windowed crossmember and central
    # bearing lug. Outer E tubes from earlier revisions are deliberately absent.
    cfg = (config or json.loads((Path(__file__).resolve().parents[1]/'parameters/assembly_r12.json').read_text()))['central_attachment_r10']
    origin_y=28.4
    for key in ('E1','E2'):
        E=s[key]; inward=1 if E[0]<0 else -1
        xlo,xhi=sorted((E[0]+inward*4,E[0]+inward*8))
        pad('CentralBeam'+key,rect(xlo,-2.5,xhi-xlo,5),0,FRAME_SPAN)
        stemlo,stemhi=sorted((E[0],E[0]+inward*8))
        lug=disk(*E,3.5).fuse(rect(stemlo,-2.5,stemhi-stemlo,5)).removeSplitter()
        pad('CentralLug'+key,lug,origin_y-1.6,3.2)
        windows=Part.makeCompound([rect(a-origin_y,-1.2,b-a,2.4) for a,b in cfg['window_y_intervals_mm']])
        face_pocket('CentralBeamWindows'+key,windows,
                    App.Placement(V(xhi,0,0),App.Rotation(V(0,0,-1),V(0,1,0),V(1,0,0),'ZXY')),xhi-xlo)
        pocket('CentralLugThroughBore'+key,[(E[0],E[1],1.1)],origin_y+1.6,3.2)
        pocket('CentralLugBearingSeatPositiveY'+key,[(E[0],E[1],2.025)],origin_y-1.6,1.2,True)
        pocket('CentralLugBearingSeatNegativeY'+key,[(E[0],E[1],2.025)],origin_y+1.6,1.2)
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

