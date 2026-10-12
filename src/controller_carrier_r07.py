"""Provisional, removable OpenRB-150 carrier, isolated r07 source module.

The board outline is the manufacturer-published 25 x 66 mm envelope. PCB
thickness (1.6 mm), population allowance (5 mm), edge-contact zones, carrier,
clamp, and M1.4 fastener details are DESIGN_ASSUMPTION. No PCB mounting holes
are modeled. The top population-clearance volume is nonphysical and excluded
from BOM/collision checks. No save, live session, shared parameter, or source
frame edit occurs here.

Call apply(builder) only after the lead's r07 candidate build. The generated
fixed-placement descriptors identify the lumbar tie as their anchor and use
the lead-owned fixed-kind placement mapping.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Published board outline; all other carrier dimensions below are provisional.
BOARD_X = (-22.5, 2.5)
BOARD_Y = (-33.0, 33.0)
BOARD_BOTTOM_Z = 39.6
BOARD_THICKNESS_ASSUMED = 1.6
BOARD_TOP_Z = BOARD_BOTTOM_Z + BOARD_THICKNESS_ASSUMED
POPULATION_CLEARANCE_ASSUMED = 5.0
TRAY_X = (-24.0, 4.0)
TRAY_Y = (-35.0, 35.0)
TRAY_BOTTOM_Z = 37.2
TRAY_THICKNESS = 1.2
TRAY_TOP_Z = TRAY_BOTTOM_Z + TRAY_THICKNESS

CASE_ANGLE_RAD = math.pi / 6.0
TIE_LOCAL_XZ = (11.4, 28.4)
TIE_X = math.cos(CASE_ANGLE_RAD) * TIE_LOCAL_XZ[0] - math.sin(CASE_ANGLE_RAD) * TIE_LOCAL_XZ[1]
TIE_Z = math.sin(CASE_ANGLE_RAD) * TIE_LOCAL_XZ[0] + math.cos(CASE_ANGLE_RAD) * TIE_LOCAL_XZ[1]
TIE_OD = 2.4
TIE_HALF_SPAN_Y = 26.8
CLAMP_Y = (-20.0, 20.0)
CLAMP_WIDTH = 4.0
CLAMP_BORE_ASSUMED = 2.5
CLAMP_OD_ASSUMED = 3.6
CLAMP_TAB_X_ASSUMED = 4.0
CLAMP_BOLT_DIA_ASSUMED = 1.6
CLAMP_BOLT_NOMINAL_ASSUMED = 1.4
CLAMP_BOLT_CORE_ASSUMED = 1.3
FASTENER_SOCKET_AF_ASSUMED = 0.9
CLAMP_BOLT_Y_OFFSETS = (-1.4, 1.4)
CLAMP_BOLT_Z_OFFSET = 2.0
TRAY_RETAINER_BOLT_X = (-23.2, 3.2)
TRAY_RETAINER_BOLT_Y = (-29.0, 29.0)
TRAY_RETAINER_BOLT_DIA_ASSUMED = 1.6


def _cc():
    import FreeCAD as App, Part, Sketcher
    import cad_common as cc
    return App, Part, Sketcher, cc


def _rectangle_face(Part, x, y, length, width):
    import FreeCAD as App
    V = App.Vector
    wire = Part.Wire([Part.makeLine(V(x, y, 0), V(x + length, y, 0)),
                      Part.makeLine(V(x + length, y, 0), V(x + length, y + width, 0)),
                      Part.makeLine(V(x + length, y + width, 0), V(x, y + width, 0)),
                      Part.makeLine(V(x, y + width, 0), V(x, y, 0))])
    return Part.Face(wire)


def _circle_face(Part, x, y, radius):
    import FreeCAD as App
    return Part.Face(Part.Wire([Part.makeCircle(radius, App.Vector(x, y, 0))]))


def _face_sketch(doc, body, name, face, placement, App, Part, Sketcher):
    """Create a stable, fully constrained sketch from planar line/arc loops."""
    sk = doc.addObject('Sketcher::SketchObject', name)
    body.addObject(sk)
    sk.Placement = placement
    for wire in face.Wires:
        for edge in wire.Edges:
            curve = edge.Curve
            if isinstance(curve, Part.Circle) and edge.isClosed():
                geom = curve
            elif isinstance(curve, Part.Line):
                geom = Part.LineSegment(edge.Vertexes[0].Point, edge.Vertexes[-1].Point)
            else:
                geom = Part.ArcOfCircle(curve, edge.FirstParameter, edge.LastParameter)
            index = sk.addGeometry(geom, False)
            sk.addConstraint(Sketcher.Constraint('Block', index))
    return sk


def _pad(doc, body, name, face, placement, length, reverse, App, Part, Sketcher):
    old = body.Tip
    sk = _face_sketch(doc, body, name + '_Sketch', face, placement, App, Part, Sketcher)
    feature = body.newObject('PartDesign::Pad', name)
    feature.Profile = sk
    feature.Length = length
    feature.Reversed = reverse
    doc.recompute()
    sk.Visibility = False
    if old:
        old.Visibility = False
    return feature


def _rectangle_pad(doc, body, name, x, y, length, width, z, height, App, Part, Sketcher):
    face = _rectangle_face(Part, x, y, length, width)
    place = App.Placement(App.Vector(0, 0, z), App.Rotation())
    return _pad(doc, body, name, face, place, height, False, App, Part, Sketcher)


def _circle_pocket(doc, body, name, centers, radius, sketch_place, length,
                   reverse, cc, App, Part, Sketcher):
    sk = doc.addObject('Sketcher::SketchObject', name + '_Sketch')
    body.addObject(sk)
    sk.Placement = sketch_place
    for x, y in centers:
        cc.circle(sk, x, y, radius)
    old = body.Tip
    pocket = body.newObject('PartDesign::Pocket', name)
    pocket.Profile = sk
    pocket.Length = length
    pocket.Reversed = reverse
    doc.recompute()
    sk.Visibility = False
    if old:
        old.Visibility = False
    return pocket


def _new_body(doc, name, material, process, cc):
    body = doc.addObject('PartDesign::Body', name)
    cc.metadata(body, name, material, process)
    body.Revision = 'r07'
    return body


def _add_source(builder, body):
    builder.library.addObject(body)
    builder.sources[body.Name] = body
    return body


def _assert_native_body(body, App):
    App.ActiveDocument.recompute()
    if not body.Shape.isValid() or len(body.Shape.Solids) != 1 or body.Shape.Volume <= 0:
        raise RuntimeError(body.Name + ' must be one valid connected positive-volume solid')
    sketches = [obj for obj in body.Group if obj.TypeId == 'Sketcher::SketchObject']
    if any(not obj.FullyConstrained for obj in sketches):
        raise RuntimeError(body.Name + ' contains an under-constrained sketch')


def _support_profile(Part):
    """Right semicollar, assumed bolt ears, elevated post, and offset tray arm."""
    half = _circle_face(Part, 0, 0, CLAMP_OD_ASSUMED / 2.0).cut(
        _circle_face(Part, 0, 0, CLAMP_BORE_ASSUMED / 2.0))
    half = half.common(_rectangle_face(Part, 0, -CLAMP_OD_ASSUMED / 2.0,
                                       CLAMP_OD_ASSUMED / 2.0,
                                       CLAMP_OD_ASSUMED))
    faces = [half]
    # Paired fastening holes occupy one upper lug, at separated stations along
    # the tie axis. This keeps the lower side clear of the adjacent motor case.
    faces.append(_rectangle_face(Part, 1.4, CLAMP_BOLT_Z_OFFSET - 0.9,
                                 CLAMP_TAB_X_ASSUMED - 1.4, 1.8))
    # The 1.2 mm post web begins outside the assumed bore and overlaps the
    # narrow right collar wall. It rises to tray-bottom height.
    # A 1.2 mm post web overlaps the collar and rises to the tray underside.
    faces.append(_rectangle_face(Part, 1.25, 0.0, 1.2, 6.905))
    # The 1.2 mm arm overlaps the tray underside by 0.6 mm for a positive
    # native union. Its outer X endpoint is exactly the tray endpoint X=4.
    faces.append(_rectangle_face(Part, 1.9, 6.3, 4.0 - TIE_X - 1.9, 1.2))
    shape = faces[0]
    for face in faces[1:]:
        shape = shape.fuse(face)
    shape = shape.removeSplitter()
    if len(shape.Faces) == 0:
        raise RuntimeError('empty carrier support section')
    # Shapes are 2D faces here; sketches retain their native edges/arcs.
    return shape


def _cap_profile(Part):
    half = _circle_face(Part, 0, 0, CLAMP_OD_ASSUMED / 2.0).cut(
        _circle_face(Part, 0, 0, CLAMP_BORE_ASSUMED / 2.0))
    half = half.common(_rectangle_face(Part, -CLAMP_OD_ASSUMED / 2.0,
                                       -CLAMP_OD_ASSUMED / 2.0,
                                       CLAMP_OD_ASSUMED / 2.0,
                                       CLAMP_OD_ASSUMED))
    tab = _rectangle_face(Part, -CLAMP_TAB_X_ASSUMED,
                          CLAMP_BOLT_Z_OFFSET - 0.9,
                          CLAMP_TAB_X_ASSUMED - 1.4, 1.8)
    # A 1.2 mm web joins the upper cap lug to the annular wall without
    # protruding into the 2.5 mm bore.
    web = _rectangle_face(Part, -2.45, 0.0, 1.2, 2.2)
    half = half.fuse(tab).fuse(web)
    return half.removeSplitter()


def _plane_for_yz(App, V, at_x, positive_x_normal=True):
    """Plane local x=Y, local y=Z, normal=+/-X."""
    if positive_x_normal:
        rot = App.Rotation(V(0, 1, 0), V(0, 0, 1), V(1, 0, 0), 'ZXY')
    else:
        rot = App.Rotation(V(0, 1, 0), V(0, 0, -1), V(-1, 0, 0), 'ZXY')
    return App.Placement(V(at_x, 0, 0), rot)


def _hex_face(Part, across_flats, x=0, y=0):
    import FreeCAD as App
    radius = across_flats / math.sqrt(3.0)
    vertices = [App.Vector(x + radius * math.cos(i * math.pi / 3.0),
                           y + radius * math.sin(i * math.pi / 3.0), 0)
                for i in range(6)]
    return Part.Face(Part.Wire([Part.makePolygon(vertices + [vertices[0]])]))


def apply(builder, revision="r07"):
    """Add the r07 carrier, clamps, retainers, fasteners, and nonphysical envelopes.

    This only constructs source bodies and placed links in the caller's builder;
    it never saves the native document. The body/fastener dimensions are
    adaptation assumptions until verified against the real board and tied
    lumbar source.
    """
    if revision not in ("r07", "r08"):
        raise ValueError("Carrier revision must be r07 or r08")
    App, Part, Sketcher, cc = _cc()
    doc = builder.doc
    V = App.Vector
    prefix = 'OpenRB150_Carrier_r07'
    if doc.getObject(prefix + '_Tray'):
        raise ValueError('r07 controller carrier already exists; rebuild in a fresh document')
    if not doc.getObject('LumbarIntegrated1'):
        raise ValueError('r06 fixed lumbar links must exist before carrier generation')

    process = ('DESIGN_ASSUMPTION adjustable positive split-tie carrier; board holes not modeled; '
               'edge population, fits, fastener engagement, print strength and clearance UNVERIFIED')
    carrier = _new_body(doc, prefix + '_Tray', 'PA12', process, cc)
    _rectangle_pad(doc, carrier, 'TrayPlatePad', TRAY_X[0], TRAY_Y[0],
                   TRAY_X[1] - TRAY_X[0], TRAY_Y[1] - TRAY_Y[0],
                   TRAY_BOTTOM_Z, TRAY_THICKNESS, App, Part, Sketcher)

    # Two raised support strips under the assumed clear long PCB edges.
    _rectangle_pad(doc, carrier, 'BoardEdgeSupportLeft', BOARD_X[0], BOARD_Y[0],
                   1.0, BOARD_Y[1] - BOARD_Y[0], TRAY_TOP_Z, 1.2,
                   App, Part, Sketcher)
    _rectangle_pad(doc, carrier, 'BoardEdgeSupportRight', BOARD_X[1] - 1.0, BOARD_Y[0],
                   1.0, BOARD_Y[1] - BOARD_Y[0], TRAY_TOP_Z, 1.2,
                   App, Part, Sketcher)

    # The two 4 mm-wide XZ supports wrap a fixed r06 tie and connect it to the
    # tray by a post and a +X offset arm ending at the tray endpoint X=4 mm.
    xz_rot = App.Rotation(V(1, 0, 0), V(0, 0, 1), V(0, -1, 0), 'ZXY')
    support = _support_profile(Part)
    for j, yc in enumerate(CLAMP_Y):
        start_y = yc + CLAMP_WIDTH / 2.0
        placement = App.Placement(V(TIE_X, start_y, TIE_Z), xz_rot)
        _pad(doc, carrier, 'TieSupportArmPost' + str(j), support, placement,
             CLAMP_WIDTH, False, App, Part, Sketcher)

    # Through-clearance pockets in each upper carrier lug, separated axially.
    bolt_centers = [(yc + dy, TIE_Z + CLAMP_BOLT_Z_OFFSET)
                    for yc in CLAMP_Y for dy in CLAMP_BOLT_Y_OFFSETS]
    _circle_pocket(doc, carrier, 'SplitClampBoltClearance', bolt_centers,
                   CLAMP_BOLT_DIA_ASSUMED / 2.0,
                   _plane_for_yz(App, V, TIE_X + CLAMP_TAB_X_ASSUMED, True),
                   CLAMP_TAB_X_ASSUMED + 0.1, False, cc, App, Part, Sketcher)

    # Retainer screws sit outside the board outline. Their holes pass only
    # through the carrier/tray and its removable top edge strips.
    tray_fasteners = [(x, y) for x in TRAY_RETAINER_BOLT_X for y in TRAY_RETAINER_BOLT_Y]
    _circle_pocket(doc, carrier, 'RetainerThroughHoles', tray_fasteners,
                   TRAY_RETAINER_BOLT_DIA_ASSUMED / 2.0,
                   App.Placement(V(0, 0, TRAY_TOP_Z), App.Rotation()),
                   TRAY_THICKNESS, False, cc, App, Part, Sketcher)
    carrier.addProperty('App::PropertyString', 'InterfaceStatus', 'Evidence')
    carrier.InterfaceStatus = 'DESIGN_ASSUMPTION; fixed r06 tie clamp and free-edge retention; not vendor geometry'
    carrier.addProperty('App::PropertyString', 'AnchorDatum', 'Evidence')
    carrier.AnchorDatum = 'upper fixed tie axis (world XZ from rotated local 11.4,28.4); Y stations +/-20'
    _assert_native_body(carrier, App)
    _add_source(builder, carrier)

    # Removable left halves of the two split clamps, sharing one editable body.
    caps = _new_body(doc, prefix + '_SplitClampCaps', 'steel',
                     'DESIGN_ASSUMPTION machined split-clamp caps; cap material and fits unverified', cc)
    cap = _cap_profile(Part)
    # Local cap sketch is in XZ, pad direction is +local Z (axial Y after link placement).
    _pad(doc, caps, 'SplitClampCapPad', cap,
         App.Placement(V(0, 0, 0), App.Rotation()), CLAMP_WIDTH, False,
         App, Part, Sketcher)
    # Two horizontal X-axis bores run through the cap lug at the same axial
    # offsets and cross-section height as the matching carrier lug.
    caprot = App.Rotation(V(0, 0, 1), V(0, 1, 0), V(-1, 0, 0), 'ZXY')
    cap_bores = [(2.0 - dy, CLAMP_BOLT_Z_OFFSET) for dy in CLAMP_BOLT_Y_OFFSETS]
    _circle_pocket(doc, caps, 'CapBoltClearance', cap_bores,
                   CLAMP_BOLT_DIA_ASSUMED / 2.0,
                   App.Placement(V(-CLAMP_TAB_X_ASSUMED, 0, 0), caprot),
                   CLAMP_TAB_X_ASSUMED + 0.1, False, cc, App, Part, Sketcher)
    caps.addProperty('App::PropertyString', 'InterfaceStatus', 'Evidence')
    caps.InterfaceStatus = 'DESIGN_ASSUMPTION split cap for nominal OD2.4 tie; bore 2.5 mm; fit/load unverified'
    _assert_native_body(caps, App)
    _add_source(builder, caps)

    # Two removable rail retainers clamp only the assumed component-free PCB edges.
    retainer_sources = {}
    for label, x0 in (('Left', -24.0), ('Right', 2.0)):
        name = prefix + '_EdgeRetainer' + label
        ret = _new_body(doc, name, 'PA12', process + '; assumed 0.5 mm edge overlap', cc)
        _rectangle_pad(doc, ret, 'RetainerStripPad', x0, BOARD_Y[0],
                       2.0, BOARD_Y[1] - BOARD_Y[0], BOARD_TOP_Z,
                       0.8, App, Part, Sketcher)
        xcenter = TRAY_RETAINER_BOLT_X[0] if label == 'Left' else TRAY_RETAINER_BOLT_X[1]
        centers = [(xcenter, y) for y in TRAY_RETAINER_BOLT_Y]
        _circle_pocket(doc, ret, 'RetainerBoltClearance', centers,
                       TRAY_RETAINER_BOLT_DIA_ASSUMED / 2.0,
                       App.Placement(V(0, 0, BOARD_TOP_Z + 0.8), App.Rotation()),
                       0.8, False, cc, App, Part, Sketcher)
        ret.addProperty('App::PropertyString', 'ContactProvenance', 'Evidence')
        ret.ContactProvenance = 'DESIGN_ASSUMPTION; 0.5 mm overlap on board edges presumed component-free'
        _assert_native_body(ret, App)
        retainer_sources[label] = _add_source(builder, ret)

    # Native editable M1.4 fastener bodies. Core diameter/head form/thread are
    # candidate dimensions, not a selected supplier part specification.
    xbolt = _new_body(doc, prefix + '_M1p4SplitClampBolt', 'steel',
                      'DESIGN_ASSUMPTION M1.4 bolt envelope; thread/strength unverified', cc)
    xpad = doc.addObject('Sketcher::SketchObject', prefix + '_XboltCoreSketch')
    xbolt.addObject(xpad)
    cc.circle(xpad, 0, 0, CLAMP_BOLT_CORE_ASSUMED / 2.0)
    core = xbolt.newObject('PartDesign::Pad', 'XboltCorePad'); core.Profile = xpad; core.Length = 8.8
    doc.recompute(); xpad.Visibility = False
    head_sk = doc.addObject('Sketcher::SketchObject', prefix + '_XboltHeadSketch'); xbolt.addObject(head_sk)
    head_sk.Placement.Base.z = 0
    cc.circle(head_sk, 0, 0, 1.25)
    head = xbolt.newObject('PartDesign::Pad', 'XboltHeadPad'); head.Profile = head_sk; head.Length = 0.7
    doc.recompute(); head_sk.Visibility = False; core.Visibility = False
    # Hex driver pocket from head outer end; all dimensions remain assumed.
    hs = doc.addObject('Sketcher::SketchObject', prefix + '_XboltSocketSketch'); xbolt.addObject(hs)
    hs.Placement.Base.z = 0.7
    hf = _hex_face(Part, FASTENER_SOCKET_AF_ASSUMED)
    hsk = _face_sketch(doc, xbolt, prefix + '_XboltSocketProfile', hf,
                       hs.Placement, App, Part, Sketcher)
    doc.removeObject(hs.Name)
    pocket = xbolt.newObject('PartDesign::Pocket', 'XboltHexSocket'); pocket.Profile = hsk; pocket.Length = 0.35
    doc.recompute(); hsk.Visibility = False; head.Visibility = False
    xbolt.addProperty('App::PropertyFloat', 'NominalThread_mm', 'Assumption'); xbolt.NominalThread_mm = CLAMP_BOLT_NOMINAL_ASSUMED
    _assert_native_body(xbolt, App); _add_source(builder, xbolt)

    zbolt = _new_body(doc, prefix + '_M1p4RetainerBolt', 'steel',
                      'DESIGN_ASSUMPTION M1.4 bolt envelope; thread/strength unverified', cc)
    zpad_sk = doc.addObject('Sketcher::SketchObject', prefix + '_ZboltCoreSketch'); zbolt.addObject(zpad_sk)
    cc.circle(zpad_sk, 0, 0, CLAMP_BOLT_CORE_ASSUMED / 2.0)
    # The retainer top is Z=42.0; a 4.8 mm shaft from tray underside reaches
    # that face and the 0.7 mm head sits above the strip.
    zcore = zbolt.newObject('PartDesign::Pad', 'ZboltCorePad'); zcore.Profile = zpad_sk; zcore.Length = 4.8
    doc.recompute(); zpad_sk.Visibility = False
    zhead_sk = doc.addObject('Sketcher::SketchObject', prefix + '_ZboltHeadSketch'); zbolt.addObject(zhead_sk)
    zhead_sk.Placement.Base.z = 4.8
    cc.circle(zhead_sk, 0, 0, 1.25)
    zhead = zbolt.newObject('PartDesign::Pad', 'ZboltHeadPad'); zhead.Profile = zhead_sk; zhead.Length = 0.7
    doc.recompute(); zhead_sk.Visibility = False; zcore.Visibility = False
    zhex = doc.addObject('Sketcher::SketchObject', prefix + '_ZboltSocketSketch'); zbolt.addObject(zhex)
    zhex.Placement.Base.z = 5.5
    zhf = _hex_face(Part, FASTENER_SOCKET_AF_ASSUMED)
    zprof = _face_sketch(doc, zbolt, prefix + '_ZboltSocketProfile', zhf,
                         zhex.Placement, App, Part, Sketcher)
    doc.removeObject(zhex.Name)
    zpocket = zbolt.newObject('PartDesign::Pocket', 'ZboltHexSocket'); zpocket.Profile = zprof; zpocket.Length = 0.35
    doc.recompute(); zprof.Visibility = False; zhead.Visibility = False
    zbolt.addProperty('App::PropertyFloat', 'NominalThread_mm', 'Assumption'); zbolt.NominalThread_mm = CLAMP_BOLT_NOMINAL_ASSUMED
    _assert_native_body(zbolt, App); _add_source(builder, zbolt)

    # Separate component envelope and nonphysical population clearance.
    board = cc.simple_shape(doc, prefix + '_BoardEnvelope',
                            Part.makeBox(BOARD_X[1] - BOARD_X[0], BOARD_Y[1] - BOARD_Y[0],
                                         BOARD_THICKNESS_ASSUMED,
                                         V(BOARD_X[0], BOARD_Y[0], BOARD_BOTTOM_Z)),
                            'electronics', 'manufacturer 25 x 66 mm PCB envelope; assumed 1.6 mm thickness',
                            pn='OPENRB150_PCB_ENVELOPE_r07', role='PURCHASED')
    board.addProperty('App::PropertyString', 'OutlineEvidence', 'Evidence')
    board.OutlineEvidence = 'MANUFACTURER_VERIFIED published OpenRB-150 board dimensions 25 x 66 mm'
    board.addProperty('App::PropertyString', 'ThicknessEvidence', 'Evidence')
    board.ThicknessEvidence = 'DESIGN_ASSUMPTION 1.6 mm; not verified against drawing/model'
    _add_source(builder, board)

    # This is an engineering reference only, never an App::Link/physical part.
    clearance = cc.simple_shape(doc, prefix + '_PopulationClearance_UNKNOWN',
                                Part.makeBox(BOARD_X[1] - BOARD_X[0], BOARD_Y[1] - BOARD_Y[0],
                                             POPULATION_CLEARANCE_ASSUMED,
                                             V(BOARD_X[0], BOARD_Y[0], BOARD_TOP_Z)),
                                'electronics', 'NONPHYSICAL reference clearance only; population height UNKNOWN',
                                pn='OPENRB150_POPULATION_CLEARANCE_UNKNOWN_r07', role='NONPHYSICAL_CLEARANCE')
    for prop, value in (('NonphysicalClearance', True), ('ExcludeFromBOM', True),
                        ('ExcludeFromCollision', True)):
        clearance.addProperty('App::PropertyBool', prop, 'Envelope handling')
        setattr(clearance, prop, value)
    clearance.addProperty('App::PropertyString', 'PopulationEvidence', 'Evidence')
    clearance.PopulationEvidence = 'UNKNOWN; 5 mm is a placeholder reservation, not a verified populated assembly height'
    clearance.Visibility = False
    reference_group = doc.getObject('ReferenceClearances')
    if reference_group is None:
        reference_group = doc.addObject('App::DocumentObjectGroup', 'ReferenceClearances')
    reference_group.addObject(clearance)

    # For now instances are placed in world coordinates and carry an explicit
    # fixed-to-lumbar descriptor. The pose engine needs the lead-owned adapter.
    attach = {'kind': 'fixed', 'attach': 'lumbar_crossbrace',
              'anchor_xz_mm': (TIE_X, TIE_Z), 'anchor_y_stations_mm': CLAMP_Y}
    links = []
    def add(src, name, placement, group, extra=None):
        motion = dict(attach)
        if extra:
            motion.update(extra)
        obj = builder.add(src, name, placement, group, motion)
        links.append(obj.Name)
        return obj

    add(carrier, prefix + '_Instance', App.Placement(), 'Electronics')
    clamp_rotation = App.Rotation(V(1, 0, 0), V(0, 0, 1), V(0, -1, 0), 'ZXY')
    for j, yc in enumerate(CLAMP_Y):
        add(caps, prefix + '_ClampCap_' + str(j),
            App.Placement(V(TIE_X, yc + CLAMP_WIDTH / 2.0, TIE_Z), clamp_rotation),
            'Electronics', {'clamp_station_y_mm': yc})
        for zi, dy in enumerate(CLAMP_BOLT_Y_OFFSETS):
            rot = App.Rotation(V(0, 0, 1), V(1, 0, 0))
            # Head sits outside the cap; its inner face meets the cap at
            # X=TIE_X-4 while the shaft crosses both clamp lugs.
            bolt_placement = App.Placement(V(TIE_X - 4.7, yc + dy,
                                             TIE_Z + CLAMP_BOLT_Z_OFFSET), rot)
            add(xbolt, prefix + '_ClampBolt_' + str(j) + '_' + str(zi), bolt_placement,
                'SpineHardware', {'clamp_station_y_mm': yc})

    for label, ret in retainer_sources.items():
        add(ret, prefix + '_EdgeRetainer' + label, App.Placement(), 'Electronics')
    for x in TRAY_RETAINER_BOLT_X:
        for y in TRAY_RETAINER_BOLT_Y:
            # Retainer bolts are modeled from tray underside up through the
            # outside edge strip; PCB clearance at these x values is assumed.
            place = App.Placement(V(x, y, TRAY_BOTTOM_Z), App.Rotation())
            add(zbolt, prefix + '_RetainerBolt_' + str(x).replace('-', 'm') + '_' + str(y).replace('-', 'm'),
                place, 'SpineHardware')

    add(board, prefix + '_BoardEnvelope_Instance', App.Placement(), 'Electronics',
        {'role': 'PURCHASED'})

    if revision == "r08":
        repair_existing(builder)
    return {
        'revision': revision,
        'carrier_source': carrier.Name,
        'carrier_instances': tuple(links),
        'board_envelope_role': 'PURCHASED',
        'board_dimensions_mm': (25.0, 66.0, BOARD_THICKNESS_ASSUMED),
        'board_thickness_status': 'DESIGN_ASSUMPTION',
        'population_clearance_mm': POPULATION_CLEARANCE_ASSUMED,
        'population_clearance_status': 'UNKNOWN; nonphysical reservation, excluded from BOM/collision',
        'anchor': {'type': 'fixed lumbar upper crossbrace/tie', 'world_xz_mm': (TIE_X, TIE_Z),
                   'y_stations_mm': CLAMP_Y, 'tube_od_mm': TIE_OD,
                   'carrier_bore_mm': CLAMP_BORE_ASSUMED, 'fit_status': 'DESIGN_ASSUMPTION'},
        'board_holes_modeled': False,
        'native_features': {body.Name: tuple(o.Name for o in body.Group
                                              if o.TypeId in ('PartDesign::Pad', 'PartDesign::Pocket'))
                            for body in (carrier, caps, *retainer_sources.values(), xbolt, zbolt)},
        'board_material': 'electronics',
        'board_part_number': 'OPENRB150_PCB_ENVELOPE_r07',
        'board_mass': 'UNKNOWN; lead may add a separate assumed load-screen value',
        'pose_integration': 'fixed motion kind returned; mapped by lead-owned pose handler',
        'worker_geometry_validation': 'not executed by apply(); see controller_carrier_r07.md for isolated FreeCADCmd validation',
        'limitations': ('All carrier/retainer/clamp dimensions are adaptation assumptions',
                        'No live/canonical assembly was changed',
                        'r06 actual-shape interference and motion validation remain lead gates')
    }



def repair_existing(builder):
    """Rebuild three native pad sketches with 0.8 mm outer hole walls.

    Intended for the lead's r08 integration. Preserves bodies, feature history,
    part numbers, links, hole geometry, board datum and clamp/tie attachments.
    Repeated calls are idempotent; never saves the caller's document.
    """
    App, Part, Sketcher, cc = _cc()
    doc = builder.doc
    edits = (
        ('OpenRB150_Carrier_r07_Tray', 'TrayPlatePad', -24.8, -35.0, 29.6, 70.0),
        ('OpenRB150_Carrier_r07_EdgeRetainerLeft', 'RetainerStripPad', -24.8, -33.0, 2.8, 66.0),
        ('OpenRB150_Carrier_r07_EdgeRetainerRight', 'RetainerStripPad', 2.0, -33.0, 2.8, 66.0),
    )
    sketches = []
    for body_name, pad_prefix, x, y, length, width in edits:
        body = doc.getObject(body_name)
        if body is None:
            raise ValueError('Missing existing carrier body: ' + body_name)
        pads = [o for o in body.Group if o.TypeId == 'PartDesign::Pad' and o.Name.startswith(pad_prefix)]
        if len(pads) != 1:
            raise ValueError('Expected one native base pad in ' + body_name)
        sk = pads[0].Profile[0] if isinstance(pads[0].Profile, tuple) else pads[0].Profile
        sketches.append((body, sk, x, y, length, width))
    for body, sk, x, y, length, width in sketches:
        for i in range(sk.ConstraintCount - 1, -1, -1):
            sk.delConstraint(i)
        for i in range(sk.GeometryCount - 1, -1, -1):
            sk.delGeometry(i)
        pts = [App.Vector(x,y,0), App.Vector(x+length,y,0),
               App.Vector(x+length,y+width,0), App.Vector(x,y+width,0)]
        for i in range(4):
            index = sk.addGeometry(Part.LineSegment(pts[i], pts[(i+1)%4]), False)
            sk.addConstraint(Sketcher.Constraint('Block', index))
        body.Revision = 'r08'
    doc.recompute()
    for body, sk, *_ in sketches:
        if not sk.FullyConstrained:
            raise ValueError('Repaired carrier sketch is not fully constrained: ' + sk.Name)
        if not body.Shape.isValid() or len(body.Shape.Solids) != 1:
            raise ValueError('Repaired carrier body is not one valid solid: ' + body.Name)
    return {'revision': 'r08', 'outer_wall_mm': 0.8, 'tray_x_mm': [-24.8, 4.8],
            'modified_bodies': [body.Name for body, *_ in sketches],
            'modified_sketches': [sk.Name for _, sk, *_ in sketches],
            'datums_and_holes_unchanged': True}
