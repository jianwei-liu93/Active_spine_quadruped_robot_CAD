"""Round-wire extension spring proxy, mm; eye centres (0,0,0)/(0,0,L).

The actual helical coil is OD 4 / wire diameter 0.5. Closed eyes lie in XZ
planes with ID 2, suitable for a nominal diameter-1.9 transverse pin.
Outward hook bends reach x=3 mm; this envelope must be checked in assembly.
This is an installed-geometry CAD proxy, not a spring manufacturing definition.
"""
import math


def shape(length, free_length):
    """Return a BRep-valid single solid at a separated-coil installed length.

    Qualified installed lengths: 21.85579/free18 and 16.15549/free13 mm.
    Free-length touching coils and compression are intentionally unsupported.
    """
    import FreeCAD as App
    import Part

    length, free_length = float(length), float(free_length)
    if not (math.isfinite(length) and math.isfinite(free_length)):
        raise ValueError('Spring lengths must be finite')
    turns = round((free_length - 4.0) / 0.5)
    if turns < 1 or length - 4.0 <= turns * 0.5:
        raise ValueError('Extension coil requires pitch greater than wire diameter')
    V = App.Vector
    radius, wire_radius = 1.75, 0.25
    pitch = (length - 4.0) / turns
    # Wrap the helix BEFORE translating: rewrapping translated edges can lose
    # the TopoShape location and silently misplace its end caps.
    path = Part.Wire(Part.makeHelix(pitch, length - 4.0, radius).Edges)
    profile = Part.Wire([Part.makeCircle(
        wire_radius, V(radius, 0, 0), V(0, radius, pitch / (2 * math.pi)))])
    result = path.makePipeShell([profile], True, True)
    result.translate(V(0, 0, 2))
    for z, sign in ((2, -1), (length - 2, 1)):
        points = (V(radius, 0, z), V(2.75, 0, z + sign * 0.5),
                  V(1.25, 0, z + sign * 2))
        # Positive-volume overlaps avoid fragile cap/tangent-only unions.
        # The outward route avoids grazing the adjacent helical turn.
        pieces = [Part.makeSphere(wire_radius, point) for point in points]
        for start, end in zip(points, points[1:]):
            delta = end - start
            unit = delta / delta.Length
            pieces.append(Part.makeCylinder(
                wire_radius, delta.Length + 0.1, start - unit * 0.05, unit))
        pieces.append(Part.makeTorus(1.25, wire_radius,
                                    V(0, 0, z + sign * 2), V(0, 1, 0)))
        for piece in pieces:
            result = result.fuse(piece)
    if not result.isValid() or len(result.Solids) != 1:
        raise RuntimeError('Extension spring union is not a valid single solid')
    return result
