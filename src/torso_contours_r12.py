"""Compact r12 torso morphology, executed only by the lead in the r10 document.

Edits eight existing pan/panel sketches and four obsolete lateral E-ear
sketches. No bodies, features, links, instance transforms or motion data are
created/replaced. Dimensions are DESIGN_ASSUMPTION, not source measurements.
See reports/reviews/r12/source_part_ownership_and_shapes.md, priority 4.
"""
import math


def apply(b, cfg):
    """Revise existing native torso profiles, preserving all feature identities.

    ``cfg`` accepts the full assembly mapping or its ``attachment_frame``.
    Fixed r12 outlines override the legacy rectangular panel outlines; all
    placements, extrusion lengths and other owner features remain untouched.
    A transaction aborts the complete edit if any native feature loses its
    single connected solid or any edited sketch is not fully constrained.
    No save/export or live connection is performed here.
    """
    import FreeCAD as App
    import Part
    import Sketcher
    from refine_flexor import rect, disk
    from leg_geometry_r02 import leg_geometry

    frame = cfg.get('attachment_frame', cfg)
    doc = b.doc
    V = App.Vector
    outlines = {'fore': (12., -9., 24., 38.),
                'hind': (-49., -12., 38., 24.)}
    windows = {'fore': (17., 7., 14., 18.),
               'hind': (-46., 2., 32., 7.)}
    case_bounds = {'fore': (14., 34.), 'hind': (-47., -13.)}

    def rounded(x, y, w, h, r):
        points = [(x+r,y), (x+w-r,y), (x+w,y+r), (x+w,y+h-r),
                  (x+w-r,y+h), (x+r,y+h), (x,y+h-r), (x,y+r)]
        d = r / math.sqrt(2)
        mids = [(x+w-r+d,y+r-d), (x+w-r+d,y+h-r+d),
                (x+r-d,y+h-r+d), (x+r-d,y+r-d)]
        p = lambda a: V(a[0], a[1], 0)
        edges = []
        for j in range(4):
            i = 2*j
            edges.append(Part.makeLine(p(points[i]), p(points[(i+1) % 8])))
            edges.append(Part.Arc(p(points[(i+1) % 8]), p(mids[j]),
                                  p(points[(i+2) % 8])).toShape())
        return Part.Face(Part.Wire(edges))

    def section(shape):
        # Normalize planar booleans into one section; coplanar edge splitting
        # otherwise leaves internal wires that cannot form a native Pad.
        pieces = [f.extrude(V(0, 0, 1)) for f in shape.Faces]
        if not pieces:
            raise RuntimeError('Empty torso profile')
        solid = pieces[0]
        for piece in pieces[1:]:
            solid = solid.fuse(piece)
        solid = solid.removeSplitter()
        bottoms = [f for f in solid.Faces if f.BoundBox.ZLength < 1e-7
                   and abs(f.CenterOfMass.z) < 1e-7]
        if not solid.isValid() or len(solid.Solids) != 1 or len(bottoms) != 1:
            raise RuntimeError('Torso profile must have one connected section')
        return bottoms[0]

    def profile(feature):
        value = feature.Profile
        return value[0] if isinstance(value, tuple) else value

    def geometry(face):
        # Equivalent to refine_flexor.sketch_face, without a temporary sketch
        # or any changes to Body.Tip. Every edge receives a Block constraint.
        result = []
        for wire in face.Wires:
            for edge in wire.Edges:
                if isinstance(edge.Curve, Part.Circle) and edge.isClosed():
                    result.append(edge.Curve)
                elif isinstance(edge.Curve, Part.Line):
                    result.append(Part.LineSegment(edge.Vertexes[0].Point,
                                                   edge.Vertexes[-1].Point))
                else:
                    result.append(Part.ArcOfCircle(edge.Curve,
                                                  edge.FirstParameter,
                                                  edge.LastParameter))
        return result

    def valid(feature):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError(feature.Name + ': expected one valid solid')
        if hasattr(feature, 'getStatusString') and 'Error' in feature.getStatusString():
            raise RuntimeError(feature.Name + ': ' + feature.getStatusString())

    edits = []
    bodies = {}
    before = {}
    # Resolve all owner profiles before mutating either body. No inferred
    # face-index attachments or changed source-local frames are introduced.
    for kind in ('fore', 'hind'):
        link = doc.getObject('Torso_' + kind)
        if link is None or link.TypeId != 'App::Link':
            raise ValueError('Existing Torso_' + kind + ' AppLink required')
        body = link.LinkedObject
        if body is None or body.TypeId != 'PartDesign::Body':
            raise ValueError('Existing native torso Body required')
        if doc.getObject(body.Name + '_CentralClevisEar0_r10') is None:
            raise ValueError('r10 central clevis must own E before lateral ear retirement')
        valid(body)
        bodies[kind] = body
        before[kind] = (link.LinkedObject.Name, link.LinkPlacement.toMatrix().A,
                        body.Placement.toMatrix().A, body.Tip.Name,
                        tuple(o.Name for o in body.Group))
        H = leg_geometry(kind)['H']
        panel = section(rounded(*outlines[kind], 4.)
                        .cut(rounded(*windows[kind], 1.))
                        .fuse(disk(*H, 3.5)).cut(disk(*H, 2.025)))
        x0, x1 = case_bounds[kind]
        for side in (-1, 1):
            label = 'L' if side == 1 else 'R'
            y0, y1 = sorted((side*14.4, side*43.2))
            pan = section(rect(x0, y0, x1-x0, y1-y0)
                          .cut(rect(x0+2., y0+2., x1-x0-4., y1-y0-4.)))
            for name, face in (('OuterHPanel'+label, panel),
                               ('BottomPan'+label, pan)):
                feature = doc.getObject(body.Name + '_' + name)
                if feature is None or feature not in body.Group or feature.TypeId != 'PartDesign::Pad':
                    raise ValueError('Existing native Pad required: ' + body.Name + '_' + name)
                edits.append((kind, feature, profile(feature), geometry(face)))
        # Keep Pad/Profile nodes in their original history slots. Their new
        # stubs overlap the plate and extend only 0.4 mm inboard, leaving no
        # E-axis material at the obsolete ±15.2 mm lateral journal centers.
        px = frame['plate_inner_x_mm'][kind]
        sign = frame['plate_normal_x'][kind]
        thick = frame['plate_thickness_mm']
        xa, xb = sorted((px-sign*0.4, px+sign*thick))
        stub = section(rounded(xa, -3.5, xb-xa, 7., 0.4))
        for j in range(2):
            feature = doc.getObject(body.Name + '_EarE' + str(j))
            if feature is None or feature not in body.Group or feature.TypeId != 'PartDesign::Pad':
                raise ValueError('Existing lateral E-ear Pad required')
            edits.append((kind, feature, profile(feature), geometry(stub)))

    doc.openTransaction('r12 compact torso contours')
    try:
        changed = []
        for kind, feature, sk, edges in edits:
            placement = App.Placement(sk.Placement)
            for i in reversed(range(sk.ConstraintCount)):
                sk.delConstraint(i)
            for i in reversed(range(sk.GeometryCount)):
                sk.delGeometry(i)
            for edge in edges:
                index = sk.addGeometry(edge, False)
                sk.addConstraint(Sketcher.Constraint('Block', index))
            sk.Placement = placement
            doc.recompute()
            if not sk.FullyConstrained:
                raise RuntimeError(sk.Name + ': expected fully constrained profile')
            valid(feature)
            sk.Visibility = False
            changed.append({'body': bodies[kind].Name, 'pad': feature.Name,
                            'sketch': sk.Name, 'fully_constrained': True})
        doc.recompute()
        checks = {}
        for kind, body in bodies.items():
            for obj in body.Group:
                if obj.TypeId.startswith('PartDesign::') and hasattr(obj, 'Shape'):
                    valid(obj)
            valid(body)
            link = doc.getObject('Torso_' + kind)
            after = (link.LinkedObject.Name, link.LinkPlacement.toMatrix().A,
                     body.Placement.toMatrix().A, body.Tip.Name,
                     tuple(o.Name for o in body.Group))
            if after != before[kind]:
                raise RuntimeError(kind + ': source, placement, Tip or owner history changed')
            checks[kind] = {'body': body.Name, 'valid': True, 'solid_count': 1,
                            'volume_mm3': body.Shape.Volume,
                            'preserved_group': before[kind][-1]}
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise
    return {'revision': 'r12', 'bodies': checks, 'edited_profiles': changed,
            'ear_retirement': 'Existing EarE0/EarE1 profiles replaced by plate-attached stubs; no history deletion',
            'assumptions': ['Contours/window radii and 2 mm pan rails are DESIGN_ASSUMPTION',
                            'Hip disk OD 7 mm and bore diameter 4.05 mm; H datum unchanged',
                            'Stub depth 0.4 mm inboard, full plate thickness overlap, height 7 mm, corner radius 0.4 mm',
                            'Retire obsolete lateral E hardware separately; central r10 clevis owns E'],
            'scope': 'Existing sketch geometry only; D, H, knee/cable owner features, top straps/case captures and source/instance frames preserved',
            'clearance_and_load_status': 'NOT_RUN; lead must verify native recompute, motion clearances and support contacts'}
