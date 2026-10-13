"""Pure-Python meshes for animated spring and cable proxies.

Coordinates are built in millimetres and converted to metres once at return.
The cable mesh is intentionally a dashed routing guide in every state; it is
not a solid cable whose changing route could imply that the tendon is taut.
"""
import math


_TAU = 2.0 * math.pi
_WIRE = 0.25
_RADIUS = 1.75
_SIDES = 8


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _unit(v, fallback=(0.0, 0.0, 1.0)):
    length = math.sqrt(_dot(v, v))
    return _mul(v, 1.0 / length) if length > 1e-12 else fallback


def _rotate(v, axis, angle):
    """Rodrigues rotation."""
    axis = _unit(axis)
    c, s = math.cos(angle), math.sin(angle)
    return _add(_add(_mul(v, c), _mul(_cross(axis, v), s)),
                _mul(axis, _dot(axis, v) * (1.0 - c)))


def _mesh_append(dst_v, dst_f, vertices, faces):
    offset = len(dst_v)
    dst_v.extend(vertices)
    dst_f.extend(tuple(offset + i for i in face) for face in faces)


def _tube(points, radius, sides=_SIDES):
    """Sweep a circular section along a sampled centreline, with fixed sides."""
    if len(points) < 2:
        points = [points[0], _add(points[0], (1e-6, 0.0, 0.0))]
    tangents = []
    for i in range(len(points)):
        if i == 0:
            d = _sub(points[1], points[0])
        elif i == len(points) - 1:
            d = _sub(points[-1], points[-2])
        else:
            d = _sub(points[i + 1], points[i - 1])
        tangents.append(_unit(d))
    # Pick a stable initial normal perpendicular to the first tangent, then
    # parallel-transport it between samples to avoid frame flips.
    ref = (0.0, 0.0, 1.0) if abs(tangents[0][2]) < 0.9 else (0.0, 1.0, 0.0)
    n = _unit(_cross(tangents[0], ref), (1.0, 0.0, 0.0))
    normals = [n]
    for old, new in zip(tangents, tangents[1:]):
        axis = _cross(old, new)
        axis_len = math.sqrt(_dot(axis, axis))
        if axis_len > 1e-12:
            n = _rotate(n, _mul(axis, 1.0 / axis_len), math.atan2(axis_len, max(-1.0, min(1.0, _dot(old, new)))))
        # Reproject to absorb floating point drift.
        n = _unit(_sub(n, _mul(new, _dot(n, new))), (1.0, 0.0, 0.0))
        normals.append(n)
    vertices = []
    for p, tangent, normal in zip(points, tangents, normals):
        binormal = _unit(_cross(tangent, normal), (0.0, 1.0, 0.0))
        for j in range(sides):
            angle = _TAU * j / sides
            offset = _add(_mul(normal, radius * math.cos(angle)),
                          _mul(binormal, radius * math.sin(angle)))
            vertices.append(_add(p, offset))
    faces = []
    for i in range(len(points) - 1):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    # Closed ends give each proxy robust renderable surfaces. Their cap fans
    # have fixed topology for every supported length/route.
    start_center, end_center = len(vertices), len(vertices) + 1
    vertices.extend((points[0], points[-1]))
    for j in range(sides):
        nxt = (j + 1) % sides
        faces.append((start_center, nxt, j))
        base = (len(points) - 1) * sides
        faces.append((end_center, base + j, base + nxt))
    return vertices, faces


def _torus(center, major, minor, axis=(0.0, 0.0, 1.0), major_steps=64, minor_steps=8):
    axis = _unit(axis)
    ref = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (0.0, 1.0, 0.0)
    u = _unit(_cross(axis, ref))
    v = _unit(_cross(axis, u))
    vertices = []
    for i in range(major_steps):
        t = _TAU * i / major_steps
        radial = _add(_mul(u, math.cos(t)), _mul(v, math.sin(t)))
        ring_center = _add(center, _mul(radial, major))
        for j in range(minor_steps):
            q = _TAU * j / minor_steps
            offset = _add(_mul(radial, minor * math.cos(q)),
                          _mul(axis, minor * math.sin(q)))
            vertices.append(_add(ring_center, offset))
    faces = []
    for i in range(major_steps):
        for j in range(minor_steps):
            a = i * minor_steps + j
            b = i * minor_steps + (j + 1) % minor_steps
            c = ((i + 1) % major_steps) * minor_steps + (j + 1) % minor_steps
            d = ((i + 1) % major_steps) * minor_steps + j
            faces.append((a, b, c, d))
    return vertices, faces


def _sphere(center, radius, rings=8, segments=12):
    vertices = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        for j in range(segments):
            theta = _TAU * j / segments
            vertices.append((center[0] + radius * math.sin(phi) * math.cos(theta),
                             center[1] + radius * math.sin(phi) * math.sin(theta),
                             center[2] + radius * math.cos(phi)))
    faces = []
    for i in range(rings):
        for j in range(segments):
            a, b = i * segments + j, i * segments + (j + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    return vertices, faces


def _finish(vertices, faces):
    return ([(x * 0.001, y * 0.001, z * 0.001) for x, y, z in vertices], faces)


def spring_mesh(record):
    """Return (vertices_m, faces) for an authoritative local-axis spring.

    The FreeCAD spring generators use a 1.75 mm coil centreline radius and a
    0.25 mm round wire. Sampling density depends only on the prescribed turn
    count, never on installed coil length, so a baked animation keeps topology.
    The CAD extension shape's outer hook/ring envelope reaches x=3 mm.
    """
    length = float(record["coil_length_mm"])
    free_length = float(record["free_length_mm"])
    kind = str(record["kind"]).lower()
    if not (math.isfinite(length) and math.isfinite(free_length) and length > 0):
        raise ValueError("spring lengths must be finite and coil length positive")
    vertices, faces = [], []
    if kind == "extension":
        turns = round((free_length - 4.0) / 0.5)
        if turns < 1:
            raise ValueError("extension free length does not define an active coil")
        samples = turns * 32
        points = []
        for i in range(samples + 1):
            t = _TAU * turns * i / samples
            points.append((_RADIUS * math.cos(t), _RADIUS * math.sin(t),
                           2.0 + (length - 4.0) * i / samples))
        _mesh_append(vertices, faces, *_tube(points, _WIRE))
        # Two outward hooks: source CAD joins short cylindrical pieces and
        # spheres at these exact points to eyes centred on z=0 and z=L.
        hooks = (((_RADIUS, 0.0, 2.0), (2.75, 0.0, 1.5), (1.25, 0.0, 0.0)),
                 ((_RADIUS, 0.0, length - 2.0), (2.75, 0.0, length - 1.5),
                  (1.25, 0.0, length)))
        for hook, eye_z in zip(hooks, (0.0, length)):
            for a, b in zip(hook, hook[1:]):
                _mesh_append(vertices, faces, *_tube([a, b], _WIRE))
            for point in hook:
                _mesh_append(vertices, faces, *_sphere(point, _WIRE))
            _mesh_append(vertices, faces,
                         *_torus((0.0, 0.0, eye_z), 1.25, _WIRE,
                                 axis=(0.0, 1.0, 0.0)))
    elif kind == "compression":
        turns = 12
        samples = turns * 32
        pitch_span = length - 0.5
        points = []
        for i in range(samples + 1):
            t = _TAU * turns * i / samples
            points.append((_RADIUS * math.cos(t), _RADIUS * math.sin(t),
                           0.25 + pitch_span * i / samples))
        _mesh_append(vertices, faces, *_tube(points, _WIRE))
        for z in (0.25, length - 0.25):
            _mesh_append(vertices, faces,
                         *_torus((0.0, 0.0, z), _RADIUS, _WIRE))
    else:
        raise ValueError("spring kind must be 'extension' or 'compression'")
    return _finish(vertices, faces)


def _arc_point(primitive, t):
    start = tuple(map(float, primitive["start"]))
    end = tuple(map(float, primitive["end"]))
    center = tuple(map(float, primitive["center"]))
    axis = _unit(tuple(map(float, primitive["axis"])))
    mid = tuple(map(float, primitive.get("mid", start)))
    radial = _sub(start, center)
    raw_sweep = float(primitive.get("sweep_rad", 0.0))
    # Pick the signed sweep whose half-way point follows the recorded midpoint.
    # This preserves the intended major/minor branch when axis conventions vary.
    candidates = (raw_sweep, -raw_sweep)
    sweep = min(candidates, key=lambda angle:
                sum((a - b) ** 2 for a, b in zip(
                    _add(center, _rotate(radial, axis, angle * 0.5)), mid)))
    if abs(sweep) < 1e-12:
        # Keep a harmless finite route if a neutral frame records a zero sweep;
        # the dash count/topology remains unchanged across the bake.
        return _add(start, _mul(_sub(end, start), t))
    return _add(center, _rotate(radial, axis, sweep * t))


def cable_mesh(record):
    """Return a dashed 0.15 mm-radius route guide as (vertices_m, faces).

    This guide is deliberately dashed for every cable state, including slack
    states, so the visualization never asserts that the route is a taut cable.
    Each line is sampled at 32 intervals and each arc at 64. A fixed 64 dashes
    across the whole route keep topology stable even when a neutral wheel arc
    becomes two arc primitives in a later frame.
    """
    route = record.get("route_local_mm", record)
    primitives = route.get("primitives", record.get("primitives", ()))
    vertices, faces = [], []
    sampled = []
    for primitive in primitives:
        kind = primitive.get("type", "line").lower()
        if kind == "line":
            start = tuple(map(float, primitive["start"]))
            end = tuple(map(float, primitive["end"]))
            intervals = 32
            points = [_add(start, _mul(_sub(end, start), i / intervals))
                      for i in range(intervals + 1)]
        elif kind == "arc":
            intervals = 64
            points = [_arc_point(primitive, i / intervals)
                      for i in range(intervals + 1)]
        else:
            continue
        if sampled:
            # Route primitives are contiguous by construction; keep one copy
            # of their shared endpoint when assembling the sampled centreline.
            sampled.extend(points[1:])
        else:
            sampled.extend(points)
    if not sampled:
        return ([], [])

    # Parameterize the concatenated sampled route by length, so fixed dash
    # positions remain spread along the complete route as its shape changes.
    cumulative = [0.0]
    for a, b in zip(sampled, sampled[1:]):
        cumulative.append(cumulative[-1] + math.sqrt(_dot(_sub(b, a), _sub(b, a))))
    total = cumulative[-1]

    def at_distance(distance):
        if total <= 1e-12:
            return sampled[0]
        distance = min(total, max(0.0, distance))
        lo, hi = 0, len(cumulative) - 1
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if cumulative[mid] < distance:
                lo = mid
            else:
                hi = mid
        span = cumulative[hi] - cumulative[lo]
        t = (distance - cumulative[lo]) / span if span > 1e-12 else 0.0
        return _add(sampled[lo], _mul(_sub(sampled[hi], sampled[lo]), t))

    for dash in range(64):
        lo = dash / 64.0
        hi = (dash + 0.5) / 64.0
        pts = [at_distance(total * (lo + (hi - lo) * j / 4.0))
               for j in range(5)]
        _mesh_append(vertices, faces, *_tube(pts, 0.15))
    return _finish(vertices, faces)

