"""Additive native lumbar root blends; installed-MCP execution by lead only.

Never rebuild or edit accepted r14 factories. Geometric edge selectors refer
to preserved source-local datums, not stored topological edge numbers. All
radii are explicit reconstruction assumptions, not measurements from film.
"""
import json
import math

SOURCE = 'FRM_LUMBAR_COMPACT_CAGE_r12'
INSTANCE = 'LumbarIntegrated1'
TOL = 1e-6


def select_roots(shape, family):
    import Part
    result = []
    stations = (0., 56.8) if family == 'short_ear' else (-9.4, 66.2)
    for index, edge in enumerate(shape.Edges, 1):
        box = edge.BoundBox
        c = edge.CenterOfMass
        if not (isinstance(edge.Curve, Part.Line) and box.XLength > 8.
                and box.YLength < TOL and box.ZLength < TOL
                and abs(abs(c.y)-2.5) < TOL and 25. < abs(c.x) < 34.
                and min(abs(c.z-z) for z in stations) < TOL):
            continue
        if family == 'short_ear' and c.x*c.y < 0:
            continue
        result.append({'edge': 'Edge'+str(index), 'length_mm': edge.Length,
                       'center_local_mm': list(c)})
    expected = 4 if family == 'short_ear' else 8
    if len(result) != expected:
        raise RuntimeError(f'{family}: expected {expected} unique datum-selected roots, got {len(result)}')
    return result


def _valid(feature):
    shape = feature.Shape
    if (shape.isNull() or not shape.isValid() or len(shape.Solids) != 1
            or 'Error' in feature.State or feature.getStatusString() != 'Valid'):
        raise RuntimeError(feature.Name+': invalid or failed native feature')


def apply(body, config, families=('short_ear', 'guide')):
    """Append native parametric fillets to a private r14 source Body.

    No save, exports, pose assignment or live connection. Only the lead may
    call this against the new r15 assembly or an isolated prototype.
    """
    cfg = config['sculpted_geometry_r15']
    doc = body.Document
    if body.Name != SOURCE or body.getObject('RootBlendShortEarR15'):
        raise ValueError('Expected the retained r14 lumbar source, not an already refined body')
    if body.Tip is None:
        raise ValueError('A valid existing native Body.Tip is required')
    _valid(body.Tip)
    before = body.Shape.copy(copyGeom=True, copyMesh=False)
    group_before = tuple(o.Name for o in body.Group)
    placement = list(body.Placement.toMatrix().A)
    rows = []
    doc.openTransaction('r15 additive sculpted lumbar roots')
    try:
        for family in families:
            radius = float(cfg['short_ear_root_radius_mm' if family == 'short_ear' else 'guide_root_radius_mm'])
            if not math.isfinite(radius) or not 0 < radius <= 1.2:
                raise ValueError('Root radius outside reviewed local prototype interval')
            previous = body.Tip
            selected = select_roots(previous.Shape, family)
            feature = body.newObject('PartDesign::Fillet',
                                     'RootBlendShortEarR15' if family == 'short_ear' else 'RootBlendGuidesR15')
            feature.Base = (previous, [row['edge'] for row in selected])
            feature.Radius = radius
            doc.recompute()
            _valid(feature)
            previous.Visibility = False
            rows.append({'family': family, 'feature': feature.Name, 'radius_mm': radius,
                         'selector': 'source-local root planes and straight X-oriented lines',
                         'selected': selected, 'state': list(feature.State), 'status': feature.getStatusString()})
        _valid(body.Tip)
        after = body.Shape.copy(copyGeom=True, copyMesh=False)
        removed = float(before.cut(after).Volume)
        added = float(after.cut(before).Volume)
        if removed > 1e-5 or added <= 1e-5:
            raise RuntimeError(f'Expected strictly additive refinement: removed={removed}, added={added}')
        if list(body.Placement.toMatrix().A) != placement:
            raise RuntimeError('Source-local frame changed')
        if tuple(o.Name for o in body.Group)[:len(group_before)] != group_before:
            raise RuntimeError('Accepted r14 feature history changed')
        body.Revision = 'r15'
        body.PartNumber = 'FRM_LUMBAR_COMPACT_CAGE_r15'
        body.addProperty('App::PropertyString', 'RefinementR15', 'r15 refinement')
        body.RefinementR15 = 'Additive native concave roots; source-informed silhouette; radius, capacity, fits provisional'
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise
    return {'status': 'PASS_LOCAL_GEOMETRY_ONLY', 'source_object': body.Name,
            'physical_instance': INSTANCE, 'features': rows,
            'baseline_material_removed_mm3': removed, 'material_added_mm3': added,
            'volume_before_mm3': before.Volume, 'volume_after_mm3': after.Volume,
            'single_valid_solid': True, 'source_frame_preserved': True,
            'accepted_history_preserved': True,
            'scope': 'Local additive geometry; section, pose, clearance and interface checks required separately'}
