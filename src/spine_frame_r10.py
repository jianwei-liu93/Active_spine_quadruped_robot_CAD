"""Append native central E crossmembers/lugs to the monolithic r09 frame.

Lead-only integration. This module never saves, exports, launches a GUI or
creates a physical instance. Dimensions are reconstructed design assumptions;
central clevis/pin/bearing hardware is a separate lead-owned implementation.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTANCE_NAME = 'LumbarIntegrated1'
SOURCE_NAME = 'FRM_LUMBAR_MONOLITHIC_CAGE_r09'
PART_NUMBER = 'FRM_LUMBAR_MONOLITHIC_CAGE_r10'


def attachment_parameters():
    return json.loads((ROOT/'parameters/assembly_r10.json').read_text())['central_attachment_r10']


def apply(b):
    """Append12 constrained native features; preserve original40 and all IDs.

    Source-local(X,Y,Z)=(worldX,worldZ,28.4-worldY). The transverse beam is
    grounded; its central lug bore is the existing transverse-Y E revolute axis.
    No new mechanism datum, DOF, physical part or motion descriptor is added.
    """
    import FreeCAD as App, Part
    import cad_common as cc
    from refine_flexor import rect, disk, sketch_face
    from kinematics import spine
    V = App.Vector
    cfg = attachment_parameters()
    doc = b.doc
    link = doc.getObject(INSTANCE_NAME)
    if link is None or link.TypeId != 'App::Link':
        raise ValueError('Retained monolithic frame AppLink is required')
    body = link.LinkedObject
    if body.Name != SOURCE_NAME or body.TypeId != 'PartDesign::Body':
        raise ValueError('Expected stable r09 monolithic source Body')
    if body.PartNumber != SOURCE_NAME or body.Revision != 'r09':
        raise ValueError('Append requires the unmodified r09 frame revision')
    original_features = tuple(o.Name for o in body.Group if o.TypeId in ('PartDesign::Pad','PartDesign::Pocket'))
    if len(original_features) != 40:
        raise ValueError('Expected original40 native r09 frame features')
    if not body.Shape.isValid() or len(body.Shape.Solids) != 1:
        raise ValueError('Input frame must be one valid connected solid')
    placement = link.LinkPlacement
    origin_y = cfg['frame_origin_world_y_mm']
    expected_base = V(0, origin_y, 0)
    axes = ((V(1,0,0),V(1,0,0)),(V(0,1,0),V(0,0,1)),(V(0,0,1),V(0,-1,0)))
    if (placement.Base-expected_base).Length > 1e-9 or any(
            (placement.Rotation.multVec(local)-world).Length > 1e-9 for local,world in axes):
        raise ValueError('Frame placement differs from the frozen source-local contract')
    stations = spine(0, b.p)
    instance_names = sorted(o.Name for o in doc.Objects if o.TypeId == 'App::Link')
    initial_map = getattr(doc.getObject('PoseController'),'MotionMap',None)
    feature_names = []
    records = []

    def finish(feature, profile, previous):
        doc.recompute()
        profile.Visibility = False
        if previous:
            previous.Visibility = False
        if not profile.FullyConstrained:
            raise RuntimeError(profile.Name+': fully constrained profile required')
        if feature.Shape.isNull() or not feature.Shape.isValid() or len(feature.Shape.Solids) != 1:
            raise RuntimeError(feature.Name+': must preserve one valid connected frame solid')
        feature_names.append(feature.Name)
        return feature

    def profile(label, face, z):
        name = body.Name+'_'+label+'Sketch'
        if doc.getObject(name):
            raise ValueError('r10 feature already exists: '+name)
        return sketch_face(doc, body, name, face, z)

    def pad(label, face, z, depth):
        previous = body.Tip
        sk = profile(label, face, z)
        feature = body.newObject('PartDesign::Pad', body.Name+'_'+label)
        feature.Profile = sk
        feature.Length = depth
        return finish(feature, sk, previous)

    def circle_pocket(label, center, diameter, z, depth, reverse=False):
        previous = body.Tip
        name = body.Name+'_'+label+'Sketch'
        if doc.getObject(name):
            raise ValueError('r10 feature already exists: '+name)
        sk = doc.addObject('Sketcher::SketchObject', name)
        body.addObject(sk)
        sk.Placement.Base.z = z
        cc.circle(sk, center[0], center[1], diameter/2)
        feature = body.newObject('PartDesign::Pocket', body.Name+'_'+label)
        feature.Profile = sk
        feature.Length = depth
        feature.Reversed = reverse
        return finish(feature, sk, previous)

    def complete_section(face):
        # Temporary geometry only: extract a single connected planar sketch face.
        pieces = [f.extrude(V(0,0,1)) for f in face.Faces]
        if not pieces:
            raise RuntimeError('Empty lug section')
        solid = pieces[0]
        for piece in pieces[1:]:
            solid = solid.fuse(piece)
        solid = solid.removeSplitter()
        bottoms = [f for f in solid.Faces if f.BoundBox.ZLength < 1e-7 and abs(f.CenterOfMass.z) < 1e-7]
        if not solid.isValid() or len(solid.Solids) != 1 or len(bottoms) != 1:
            raise RuntimeError('Lug profile must have one complete connected section')
        return bottoms[0]

    ya,yb = cfg['beam_y_bounds_mm']
    beam_start,beam_end = sorted((origin_y-ya,origin_y-yb))
    za,zb = cfg['beam_z_bounds_mm']
    inset_a,inset_b = cfg['beam_inward_x_bounds_from_E_mm']
    lug_radius = cfg['lug_radius_mm']
    lug_half = cfg['lug_half_width_y_mm']
    lug_start,lug_end = origin_y-lug_half,origin_y+lug_half
    for key in ('E1','E2'):
        E = stations[key]
        inward = 1 if E[0] < 0 else -1
        xlo,xhi = sorted((E[0]+inward*inset_a,E[0]+inward*inset_b))
        # This full-span pad positively overlaps both original shelf ends.
        pad('CentralBeam'+key, rect(xlo,za,xhi-xlo,zb-za), beam_start,beam_end-beam_start)
        stem_tip = E[0]+inward*cfg['lug_stem_inward_length_mm']
        stem_lo,stem_hi = sorted((E[0],stem_tip))
        lug = disk(E[0],E[1],lug_radius).fuse(
            rect(stem_lo,za,stem_hi-stem_lo,zb-za)).removeSplitter()
        pad('CentralLug'+key, complete_section(lug), lug_start,lug_end-lug_start)
        # Sketch U maps to world+Y and V to world+Z; normal maps to world+X.
        # One native pocket contains both separately bounded rectangular windows.
        windows = []
        wz0,wz1 = cfg['window_z_bounds_mm']
        for wy0,wy1 in cfg['window_y_intervals_mm']:
            windows.append(rect(wy0-origin_y,wz0,wy1-wy0,wz1-wz0))
        previous = body.Tip
        sk = profile('CentralBeamWindows'+key, Part.makeCompound(windows), 0)
        sk.Placement = App.Placement(V(xhi,0,0),
                                    App.Rotation(V(0,0,-1),V(0,1,0),V(1,0,0),'ZXY'))
        feature = body.newObject('PartDesign::Pocket', body.Name+'_CentralBeamWindows'+key)
        feature.Profile = sk
        feature.Length = xhi-xlo
        finish(feature, sk, previous)
        circle_pocket('CentralLugThroughBore'+key, E, cfg['lug_through_bore_mm'],lug_end,lug_end-lug_start)
        circle_pocket('CentralLugBearingSeatPositiveY'+key, E,cfg['bearing_seat_diameter_mm'],
                      lug_start,cfg['bearing_seat_depth_mm'],True)
        circle_pocket('CentralLugBearingSeatNegativeY'+key, E,cfg['bearing_seat_diameter_mm'],
                      lug_end,cfg['bearing_seat_depth_mm'])
        records.append({'joint': key, 'center_world_xz_mm': list(E), 'axis_world': [0,1,0],
                        'beam_world_x_bounds_mm': [xlo,xhi], 'beam_world_y_bounds_mm': [ya,yb],
                        'beam_world_z_bounds_mm': [za,zb], 'lug_world_y_bounds_mm': [-lug_half,lug_half],
                        'bearing_y_centers_mm': cfg['bearing_y_centers_mm'],
                        'through_bore_diameter_mm': cfg['lug_through_bore_mm'],
                        'bearing_seat_diameter_mm': cfg['bearing_seat_diameter_mm'],
                        'bearing_seat_depth_mm': cfg['bearing_seat_depth_mm']})
    body.PartNumber = PART_NUMBER
    body.Revision = 'r10'
    body.Process = str(body.Process)+'; r10 integral E open-box crossmembers and central bearing lugs; dimensions/fits/strength UNVERIFIED'
    if hasattr(b,'sources'):
        b.sources[body.Name] = body
    doc.recompute()
    if tuple(o.Name for o in body.Group if o.TypeId in ('PartDesign::Pad','PartDesign::Pocket'))[:40] != original_features:
        raise RuntimeError('Original r09 feature identity/order changed')
    if sorted(o.Name for o in doc.Objects if o.TypeId=='App::Link') != instance_names:
        raise RuntimeError('Physical instance identities changed')
    if tuple(link.LinkPlacement.toMatrix().A) != tuple(placement.toMatrix().A):
        raise RuntimeError('Retained frame placement changed')
    if initial_map != getattr(doc.getObject('PoseController'),'MotionMap',None):
        raise RuntimeError('MotionMap changed')
    sketches = [o for o in body.Group if o.TypeId=='Sketcher::SketchObject']
    return {'source': body.Name, 'part_number': body.PartNumber, 'revision': body.Revision,
            'instance': link.Name, 'original_features_preserved': original_features,
            'appended_features': tuple(feature_names), 'appended_feature_count': len(feature_names),
            'pad_count': sum(o.TypeId=='PartDesign::Pad' for o in body.Group),
            'pocket_count': sum(o.TypeId=='PartDesign::Pocket' for o in body.Group),
            'sketch_count': len(sketches), 'all_frame_sketches_fully_constrained': all(o.FullyConstrained for o in sketches),
            'solid_count': len(body.Shape.Solids), 'native_validity': body.Shape.isValid(),
            'physical_instance_count': len(instance_names), 'central_joints': records,
            'limitations': ('Reconstructed metric assumptions; source does not identify exact hidden bearing stack',
                            'Moving central clevis/pin/bearings are separate lead-owned parts',
                            'Actual motion/collision, insertion access and manufacturing fits require lead verification')}
