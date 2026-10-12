"""Conservative exact-BRep separation prefilter; no FreeCAD/GUI imports.

Only ZERO_INTERSECTION permits skipping Boolean common. Every uncertain case
returns BOOLEAN_REQUIRED. This is a finite-tolerance kernel check, not an
approximate bbox test, minimum-clearance certificate or collision exception.

prepare(shape) may be frozen once and reused ONLY for rigidly placed copies of
that same validated topology. Any geometry/topology change requires prepare
again. In particular, merely having one connected solid is insufficient: a
sealed cavity supplies additional disconnected boundary shells. Such solids
are deliberately ineligible for this first-boundary-vertex method.
"""
from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class Qualification:
    eligible: bool
    reason: str
    shape_type: str = ''
    solids: int = 0
    shells: int = 0
    vertices: int = 0
    wrapper_depth: int = 0


def _solid(shape):
    """Unwrap only single-child Compounds; never discard stray geometry."""
    depth = 0
    while shape.ShapeType == 'Compound':
        children = shape.childShapes()
        if len(children) != 1 or depth >= 32:
            raise ValueError('not_a_single_child_solid_wrapper')
        # FreeCAD childShapes() returns cumulative locations by default.
        shape = children[0]
        depth += 1
    if shape.ShapeType != 'Solid':
        raise ValueError('not_a_solid_or_single_child_solid_wrapper')
    return shape, depth


def prepare(shape):
    """Qualify a positive-volume valid solid with ONE closed boundary shell.

    Only single-child Compound wrappers are unwrapped, retaining cumulative
    placement and every child. Other compounds, open shells, invalid shapes
    and missing vertices fall back. Through-bores can qualify: they do not
    create a second closed shell. No geometry conversion/repair is attempted.
    """
    data = {}
    try:
        data['shape_type'] = str(shape.ShapeType)
        data['solids'] = len(shape.Solids)
        data['shells'] = len(shape.Shells)
        data['vertices'] = len(shape.Vertexes)
        if data['solids'] != 1:
            return Qualification(False, 'not_exactly_one_solid_shape', **data)
        solid, depth = _solid(shape)
        data['wrapper_depth'] = depth
        if not shape.isValid() or not solid.isValid() or not solid.isClosed():
            return Qualification(False, 'invalid_or_open_solid', **data)
        volume = float(shape.Volume)
        if not math.isfinite(volume) or volume <= 0:
            return Qualification(False, 'nonpositive_or_nonfinite_volume', **data)
        if data['shells'] != 1:
            return Qualification(False, 'multiple_or_missing_boundary_shells', **data)
        shell = solid.Shells[0]
        if not shell.isClosed() or not shell.isValid():
            return Qualification(False, 'invalid_or_open_boundary_shell', **data)
        if data['vertices'] < 1:
            return Qualification(False, 'no_boundary_vertex', **data)
        return Qualification(True, 'valid_single_solid_single_closed_shell', **data)
    except Exception as exc:
        return Qualification(False, 'qualification_error:' + type(exc).__name__ + ':' + str(exc), **data)


def separation(a, b, *, a_check=None, b_check=None, tolerance=1e-6):
    """Return decision and kernel evidence without mutating either shape.

    Qualify once with prepare() for speed; certificates apply only to rigid
    copies of their original topology. Without certificates, validate here.
    Use the current WORLD shapes/vertices, never stale local vertex positions.

    If distance > tolerance and both current first boundary vertices are
    outside the other solid, connected boundaries are disjoint and neither
    volume contains the other. Otherwise common must still run. A contained
    solid, a bore-enclosed solid, intersection and touching are handled
    distinctly by distance plus strict point-in-solid classification.
    """
    result = {'decision': 'BOOLEAN_REQUIRED', 'skip_boolean': False,
              'reason': 'unclassified', 'distance_mm': None,
              'a_vertex_strictly_inside_b': None,
              'b_vertex_strictly_inside_a': None,
              'tolerance_mm': None}
    try:
        tolerance = float(tolerance)
        if not math.isfinite(tolerance) or tolerance <= 0:
            result['reason'] = 'invalid_tolerance'
            return result
        result['tolerance_mm'] = tolerance
        ca = prepare(a) if a_check is None else a_check
        cb = prepare(b) if b_check is None else b_check
        if not isinstance(ca, Qualification) or not isinstance(cb, Qualification):
            result['reason'] = 'invalid_qualification_certificate'
            return result
        result['a_qualification'] = asdict(ca)
        result['b_qualification'] = asdict(cb)
        if not ca.eligible or not cb.eligible:
            result['reason'] = 'ineligible_topology'
            return result
        # Even a valid frozen certificate must not hide a missing current
        # vertex. Coordinates come from the posed copies, not the certificate.
        a, da = _solid(a)
        b, db = _solid(b)
        if da != ca.wrapper_depth or db != cb.wrapper_depth:
            result['reason'] = 'qualification_wrapper_mismatch'
            return result
        va, vb = a.Vertexes, b.Vertexes
        if not va or not vb:
            result['reason'] = 'no_current_boundary_vertex'
            return result
        distance = float(a.distToShape(b)[0])
        result['distance_mm'] = distance if math.isfinite(distance) else None
        if not math.isfinite(distance) or distance < 0:
            result['reason'] = 'invalid_distance'
            return result
        if distance <= tolerance:
            result['reason'] = 'near_touching_intersecting_or_contained'
            return result
        # isInside(..., False) means strictly inside; ON is not IN. Since
        # boundaries must already be separated by > tolerance, ON cannot be
        # used to discard a near-contact or uncertain pair.
        ainb = b.isInside(va[0].Point, tolerance, False)
        bina = a.isInside(vb[0].Point, tolerance, False)
        if not isinstance(ainb, bool) or not isinstance(bina, bool):
            result['reason'] = 'unexpected_point_classification'
            return result
        result['a_vertex_strictly_inside_b'] = ainb
        result['b_vertex_strictly_inside_a'] = bina
        if ainb or bina:
            result['reason'] = 'containment_or_classified_overlap'
            return result
        result.update(decision='ZERO_INTERSECTION', skip_boolean=True,
                      reason='separated_connected_boundaries_and_no_containment')
        return result
    except Exception as exc:
        result['reason'] = 'kernel_or_input_error'
        result['error'] = type(exc).__name__ + ': ' + str(exc)
        return result
