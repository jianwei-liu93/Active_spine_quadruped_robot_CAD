"""Append the r10 central output clevis to existing r09 torso sources.

Lead-owned apply; no saving, source replacement, instance transform, or motion
edit. Native web pad and pattern pocket preserve every legacy feature unchanged.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply(b):
    import FreeCAD as App, Part
    from refine_flexor import rect, disk, pill_face, sketch_face
    cfg = json.loads((ROOT / 'parameters/assembly_r10.json').read_text())
    frame = cfg['attachment_frame']
    joint = cfg['central_attachment_r10']
    pattern = cfg['plate_profile_r10']
    doc = b.doc
    V = App.Vector
    xyz = lambda p: V(p[0], p[2], 16-p[1])
    vec = lambda p: V(p[0], p[2], -p[1])

    def section(shape):
        """Return a single clean planar face after 2D booleans."""
        pieces = [f.extrude(V(0, 0, 1)) for f in shape.Faces]
        if not pieces:
            raise RuntimeError('Empty planar profile')
        solid = pieces[0]
        for piece in pieces[1:]:
            solid = solid.fuse(piece)
        solid = solid.removeSplitter()
        bottoms = [f for f in solid.Faces if f.BoundBox.ZLength < 1e-7
                   and abs(f.CenterOfMass.z) < 1e-7]
        if not solid.isValid() or len(solid.Solids) != 1 or len(bottoms) != 1:
            raise RuntimeError('Profile must have one connected planar section')
        return bottoms[0]

    def rounded(x, y, w, h, r):
        pts = [(x+r,y), (x+w-r,y), (x+w,y+r), (x+w,y+h-r),
               (x+w-r,y+h), (x+r,y+h), (x,y+h-r), (x,y+r)]
        d = r/math.sqrt(2)
        mids = [(x+w-r+d,y+r-d), (x+w-r+d,y+h-r+d),
                (x+r-d,y+h-r+d), (x+r-d,y+r-d)]
        p = lambda q: V(q[0],q[1],0)
        edges = []
        for j in range(4):
            i = 2*j
            edges.append(Part.makeLine(p(pts[i]),p(pts[(i+1)%8])))
            edges.append(Part.Arc(p(pts[(i+1)%8]),p(mids[j]),p(pts[(i+2)%8])).toShape())
        return Part.Face(Part.Wire(edges))

    def arc_slot(z, sign):
        # Angles measured from +torsoY toward +torsoZ. Reflection is applied
        # pointwise to the complete sketch, including the adjacent circle.
        radius = pattern['end_slot_radius_mm']
        half = pattern['slot_width_mm']/2
        a, c = [math.radians(t) for t in pattern['end_slot_sweep_deg']]
        m = (a+c)/2
        def point(r, t):
            return V(sign*r*math.cos(t), z+r*math.sin(t), 0)
        def cap(t, sense):
            # Tangential midpoint closes a semicircle of radius half.
            return V(sign*(radius*math.cos(t)-sense*half*math.sin(t)),
                     z+radius*math.sin(t)+sense*half*math.cos(t), 0)
        edges = [Part.Arc(point(radius+half, a), point(radius+half, m), point(radius+half, c)).toShape(),
                 Part.Arc(point(radius+half, c), cap(c, 1), point(radius-half, c)).toShape(),
                 Part.Arc(point(radius-half, c), point(radius-half, m), point(radius-half, a)).toShape(),
                 Part.Arc(point(radius-half, a), cap(a, -1), point(radius+half, a)).toShape()]
        return Part.Face(Part.Wire(edges))

    def plate_face(sign):
        ymin, ymax = frame['plate_y_bounds_mm']
        zmin, zmax = frame['plate_z_bounds_mm']
        face = rounded(ymin, zmin, ymax-ymin, zmax-zmin,
                       frame['plate_corner_radius_mm'])
        width = pattern['slot_width_mm']
        # Bounds describe total capsule extents, including round caps.
        z0, z1 = pattern['side_slot_z_bounds_mm']
        for y in pattern['side_slot_y_mm']:
            face = face.cut(pill_face((sign*y, z0+width/2),
                                      (sign*y, z1-width/2), width))
        z0, z1 = pattern['center_slot_z_bounds_mm']
        face = face.cut(pill_face((0, z0+width/2), (0, z1-width/2), width))
        for z in pattern['end_slot_z_centers_mm']:
            face = face.cut(arc_slot(z, sign))
            face = face.cut(disk(sign*pattern['end_round_hole_offset_y_mm'], z,
                                 pattern['end_round_hole_diameter_mm']/2))
        return section(face)

    def valid(feature):
        shape = feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise RuntimeError(feature.Name + ': expected one valid solid')
        if hasattr(feature, 'getStatusString') and 'Error' in feature.getStatusString():
            raise RuntimeError(feature.Name + ': ' + feature.getStatusString())

    bodies = {}
    # Validate all prerequisites before the first mutation.
    for kind in ('fore', 'hind'):
        link = doc.getObject('Torso_'+kind)
        if link is None or link.TypeId != 'App::Link':
            raise ValueError('Existing Torso_'+kind+' AppLink required')
        body = link.LinkedObject
        if body.TypeId != 'PartDesign::Body':
            raise ValueError('Existing native torso body required')
        plate = doc.getObject(body.Name+'_TransverseSlottedPlate')
        if plate is None or plate not in body.Group:
            raise ValueError('Existing named transverse plate required')
        if doc.getObject(body.Name+'_PlateWebFill_r10'):
            raise ValueError('r10 clevis already applied; repeated application rejected')
        bodies[kind] = (body, plate)
    result = {}
    for kind, (body, plate) in bodies.items():
        sign = frame['plate_normal_x'][kind]
        sketch = plate.Profile[0] if isinstance(plate.Profile, tuple) else plate.Profile
        preserved = [o.Name for o in body.Group]
        existing_feature_checks = [
            {'name': obj.Name, 'valid': not obj.Shape.isNull() and obj.Shape.isValid(), 'solid_count': len(obj.Shape.Solids)}
            for obj in list(body.Group)
            if obj.TypeId.startswith('PartDesign::') and hasattr(obj, 'Shape')]
        valid(body.Tip)
        def native(label, face, placement, type_id, length):
            previous = body.Tip
            sk = sketch_face(doc, body, body.Name+'_'+label+'Profile', face)
            sk.Placement = placement
            feature = body.newObject(type_id, body.Name+'_'+label)
            feature.Profile = sk
            feature.Length = length
            doc.recompute()
            sk.Visibility = False
            previous.Visibility = False
            if not sk.FullyConstrained:
                raise RuntimeError(sk.Name+': profile must be fully constrained')
            valid(feature)
            return feature, sk
        ymin, ymax = frame['plate_y_bounds_mm']
        zmin, zmax = frame['plate_z_bounds_mm']
        outer = rounded(ymin, zmin, ymax-ymin, zmax-zmin, frame['plate_corner_radius_mm'])
        fill, fill_sketch = native('PlateWebFill_r10', outer, sketch.Placement,
                                  'PartDesign::Pad', plate.Length)
        pocket_placement = App.Placement(sketch.Placement)
        pocket_placement.Base = pocket_placement.Base + vec((sign*plate.Length, 0, 0))
        holes = outer.cut(plate_face(sign))
        pocket, pocket_sketch = native('SourcePlatePattern_r10', holes, pocket_placement,
                                       'PartDesign::Pocket', plate.Length)
        added = []
        thickness = joint['clevis_ear_thickness_mm']
        width = joint['clevis_ear_width_mm']
        end = frame['plate_inner_x_mm'][kind]
        # Terminate at the existing published outer plate datum; full plate
        # depth overlap avoids a narrow coincident boundary in native union.
        stem_end = end+sign*frame['plate_thickness_mm']
        x0, x1 = sorted((0, stem_end))
        face = section(rect(x0, -width/2, x1-x0, width)
                       .fuse(disk(0, 0, width/2))
                       .cut(disk(0, 0, joint['clevis_pin_bore_mm']/2)))
        for j, y in enumerate(joint['clevis_ear_y_centers_mm']):
            previous = body.Tip
            label = body.Name+'_CentralClevisEar'+str(j)+'_r10'
            sk = sketch_face(doc, body, label+'Profile', face)
            sk.Placement = App.Placement(xyz((0, y+thickness/2, 0)),
                App.Rotation(vec((1, 0, 0)), vec((0, 0, 1)), vec((0, -1, 0)), 'ZXY'))
            feature = body.newObject('PartDesign::Pad', label)
            feature.Profile = sk
            feature.Length = thickness
            doc.recompute()
            sk.Visibility = False
            previous.Visibility = False
            if not sk.FullyConstrained:
                raise RuntimeError(sk.Name+': clevis profile must be fully constrained')
            valid(feature)
            added.append(feature.Name)
        body.Revision = 'r10'
        body.PartNumber = body.Name+'_r10'
        valid(body)
        result[kind] = {'body': body.Name, 'plate': plate.Name,
            'plate_sketch': sketch.Name, 'plate_sketch_fully_constrained': sketch.FullyConstrained,
            'plate_web_pad': fill.Name, 'pattern_pocket': pocket.Name,
            'plate_web_fully_constrained': fill_sketch.FullyConstrained,
            'pattern_fully_constrained': pocket_sketch.FullyConstrained,
            'preserved_existing_objects': preserved, 'existing_feature_checks': existing_feature_checks, 'added_pads': added,
            'valid': body.Shape.isValid(), 'solid_count': len(body.Shape.Solids),
            'volume_mm3': body.Shape.Volume, 'E_torso_xyz': (0, 0, 0),
            'axis_torso_xyz': (0, 1, 0), 'clevis_centers_y_mm': joint['clevis_ear_y_centers_mm']}
    doc.recompute()
    return {'bodies': result, 'revision': 'r10',
        'pattern_interpretation': 'Arc center Y=0, given Z; angles from +Y; neighboring hole at Y=-2.5, same Z; sketch X=sign*Y',
        'scope': 'Appended native plate web/pocket and clevis only; legacy features unchanged; no save, motion, instance, or hardware changes',
        'clearance_status': 'NOT_RUN; lead integration must verify central pin stack and motion clearance'}
