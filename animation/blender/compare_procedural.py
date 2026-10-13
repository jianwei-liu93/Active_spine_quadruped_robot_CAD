"""Bounded native-export versus pure procedural render mesh comparison.

This is a numerical surface-sampling check, not a BRep/Boolean equivalence
test. It requires only Python's standard library and reads exported native
triangle JSON without opening FreeCAD or Blender.
"""
import hashlib
import gzip
import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "animation/geometry/r10/procedural_examples/manifest.json"
TIMELINE = ROOT / "animation/motion/coordinated_spine_legs_r10.jsonl.gz"
GEOMETRY = Path(__file__).with_name("procedural_geometry.py")
REPORT = ROOT / "reports/animation/procedural_surface_comparison.json"
SAMPLE_INDICES = (0, 75, 150)
SPRING_TOLERANCE_MM = 0.05
PROBE_COUNT = 500
VERTEX_PROBES = PROBE_COUNT // 2
CENTROID_PROBES = PROBE_COUNT - VERTEX_PROBES


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def point_triangle_distance_sq(p, a, b, c):
    """Squared Euclidean distance from p to a triangle, Ericson region tests."""
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    normal = (ab[1] * ac[2] - ab[2] * ac[1],
              ab[2] * ac[0] - ab[0] * ac[2],
              ab[0] * ac[1] - ab[1] * ac[0])
    if dot(normal, normal) <= 1e-30:
        # Pole fans and collapsed neutral-route samples can create zero-area
        # candidate triangles. Their closure is the union of their 3 edges.
        best = math.inf
        for u, v in ((a, b), (b, c), (c, a)):
            edge = sub(v, u)
            den = dot(edge, edge)
            t = max(0.0, min(1.0, dot(sub(p, u), edge) / den)) if den > 1e-30 else 0.0
            q = tuple(u[i] + t * edge[i] for i in range(3))
            d = sub(p, q)
            best = min(best, dot(d, d))
        return best
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return dot(ap, ap)
    bp = sub(p, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return dot(bp, bp)
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        q = tuple(a[i] + v * ab[i] for i in range(3))
        d = sub(p, q)
        return dot(d, d)
    cp = sub(p, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return dot(cp, cp)
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        q = tuple(a[i] + w * ac[i] for i in range(3))
        d = sub(p, q)
        return dot(d, d)
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        q = tuple(b[i] + w * sub(c, b)[i] for i in range(3))
        d = sub(p, q)
        return dot(d, d)
    denom = 1.0 / (va + vb + vc)
    v, w = vb * denom, vc * denom
    q = tuple(a[i] + ab[i] * v + ac[i] * w for i in range(3))
    d = sub(p, q)
    return dot(d, d)


class CentroidTree:
    """Small deterministic 3-D KD tree for nearest triangle-centroid queries."""
    def __init__(self, triangles, leaf_size=12):
        self.triangles = triangles
        self.centroids = [tuple((t[0][j] + t[1][j] + t[2][j]) / 3.0
                                for j in range(3)) for t in triangles]
        self.leaf_size = leaf_size
        self.root = self._build(list(range(len(triangles))))

    def _build(self, ids):
        if len(ids) <= self.leaf_size:
            return (None, None, None, ids)
        spreads = [max(self.centroids[i][axis] for i in ids) -
                   min(self.centroids[i][axis] for i in ids) for axis in range(3)]
        axis = max(range(3), key=spreads.__getitem__)
        ids.sort(key=lambda i: self.centroids[i][axis])
        mid = len(ids) // 2
        split = self.centroids[ids[mid]][axis]
        return (axis, split, self._build(ids[:mid]), self._build(ids[mid:]))

    def nearest_triangles(self, point, count=32):
        # Max heap encoded as negative squared distances; stores exact nearest
        # centroid candidates, then triangle distances refine the local set.
        import heapq
        heap = []

        def visit(node):
            axis, split, left, right = node
            if axis is None:
                for idx in right:
                    c = self.centroids[idx]
                    d2 = sum((point[j] - c[j]) ** 2 for j in range(3))
                    item = (-d2, idx)
                    if len(heap) < count:
                        heapq.heappush(heap, item)
                    elif item > heap[0]:
                        heapq.heapreplace(heap, item)
                return
            delta = point[axis] - split
            near, far = (left, right) if delta <= 0.0 else (right, left)
            visit(near)
            worst = -heap[0][0] if len(heap) == count else math.inf
            if delta * delta <= worst:
                visit(far)

        visit(self.root)
        return [idx for _, idx in heap]

    def distance(self, point, count=32):
        return math.sqrt(min(point_triangle_distance_sq(point, *self.triangles[i])
                             for i in self.nearest_triangles(point, count)))


def triangles_from_mesh(vertices, faces):
    triangles = []
    for face in faces:
        if len(face) == 3:
            triangles.append(tuple(vertices[i] for i in face))
        elif len(face) >= 4:
            for i in range(1, len(face) - 1):
                triangles.append((vertices[face[0]], vertices[face[i]], vertices[face[i + 1]]))
    return triangles


def deterministic_probes(vertices, triangles):
    probes = []
    for i in range(VERTEX_PROBES):
        idx = min(len(vertices) - 1, int((i + 0.5) * len(vertices) / VERTEX_PROBES))
        probes.append(("native_vertex", tuple(vertices[idx])))
    for i in range(CENTROID_PROBES):
        idx = min(len(triangles) - 1, int((i + 0.5) * len(triangles) / CENTROID_PROBES))
        tri = triangles[idx]
        probes.append(("native_triangle_centroid",
                       tuple(sum(p[j] for p in tri) / 3.0 for j in range(3))))
    return probes


def stats(values):
    ordered = sorted(values)
    return {
        "mean_mm": sum(values) / len(values),
        "median_mm": ordered[len(ordered) // 2],
        "p95_mm": ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)],
        "max_mm": ordered[-1],
    }


def route_points(record):
    route = record.get("route_local_mm", record)
    points = []
    primitives = route.get("primitives", record.get("primitives", ()))
    for primitive in primitives:
        kind = primitive.get("type", "line").lower()
        intervals = 32 if kind == "line" else 64
        if kind == "line":
            a, b = tuple(primitive["start"]), tuple(primitive["end"])
            samples = [tuple(a[j] + (b[j] - a[j]) * i / intervals for j in range(3))
                       for i in range(intervals + 1)]
        elif kind == "arc":
            samples = [pure._arc_point(primitive, i / intervals)
                       for i in range(intervals + 1)]
        else:
            continue
        points.extend(samples if not points else samples[1:])
    return points, primitives


def point_polyline_distance(point, points):
    best = math.inf
    for a, b in zip(points, points[1:]):
        ab = sub(b, a)
        den = dot(ab, ab)
        t = max(0.0, min(1.0, dot(sub(point, a), ab) / den)) if den > 1e-24 else 0.0
        q = tuple(a[j] + t * ab[j] for j in range(3))
        best = min(best, distance(point, q))
    return best


def main():
    global pure
    spec = importlib.util.spec_from_file_location("procedural_geometry", GEOMETRY)
    pure = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pure)
    manifest_bytes = MANIFEST.read_bytes()
    timeline_bytes = TIMELINE.read_bytes()
    manifest = json.loads(manifest_bytes)
    with gzip.open(TIMELINE, "rt", encoding="utf-8") as stream:
        timeline = [json.loads(line) for line in stream if line.strip()]
    if max(SAMPLE_INDICES) >= len(timeline):
        raise RuntimeError("coordinated timeline is shorter than native example sample indices")
    results = []
    probe_method = {
        "count": PROBE_COUNT,
        "native_vertices": VERTEX_PROBES,
        "native_triangle_centroids": CENTROID_PROBES,
        "selection": "deterministic evenly spaced index samples from source-local native mesh",
    }

    for entry in manifest["examples"]:
        sample = int(entry["sample_index"])
        frame = timeline[sample]
        record = next(x for x in frame["procedural_shapes"]
                      if x["instance_id"] == entry["instance_id"])
        native_path = ROOT / entry["path"]
        native_bytes = native_path.read_bytes()
        native_hash = hashlib.sha256(native_bytes).hexdigest()
        if native_hash != entry["sha256"]:
            raise RuntimeError("native example hash mismatch: " + str(entry["path"]))
        native = json.loads(native_bytes)
        native_vertices = [tuple(map(float, p)) for p in native["vertices_m"]]
        native_faces = native["triangles"]
        native_triangles = triangles_from_mesh(native_vertices, native_faces)
        probes = deterministic_probes(native_vertices, native_triangles)
        is_spring = record.get("generator") == "spring"
        if is_spring:
            candidate_vertices, candidate_faces = pure.spring_mesh(record)
            candidate_triangles = triangles_from_mesh(candidate_vertices, candidate_faces)
            tree = CentroidTree(candidate_triangles)
            distances_m = [tree.distance(p) for _, p in probes]
            distances_mm = [d * 1000.0 for d in distances_m]
            result = {
                "instance_id": entry["instance_id"],
                "sample_index": sample,
                "kind": record["kind"],
                "comparison": "native boundary vertex/triangle-centroid samples to candidate render triangles",
                "direction": "native_to_render_only",
                "native_sha256": native_hash,
                "native_vertex_count": len(native_vertices),
                "native_triangle_count": len(native_faces),
                "render_vertex_count": len(candidate_vertices),
                "render_face_count": len(candidate_faces),
                "render_triangle_count": len(candidate_triangles),
                "probe_method": probe_method,
                "distance": stats(distances_mm),
                "tolerance_mm": SPRING_TOLERANCE_MM,
                "status": "PASS_FINITE_PROBES" if max(distances_mm) <= SPRING_TOLERANCE_MM else "EXCEEDS_FINITE_PROBE_TOLERANCE",
            }
        elif record.get("generator") == "cable":
            candidate_vertices, candidate_faces = pure.cable_mesh(record)
            centerline, primitives = route_points(record)
            # Exported source-local mesh vertices are metres; route records are
            # millimetres. Compare native boundary points to the source route.
            radius_residuals = [abs(point_polyline_distance(tuple(c * 1000.0 for c in p),
                                                            centerline) - 0.15)
                                for _, p in probes]
            arc_endpoint_errors, arc_midpoint_errors, continuity_errors = [], [], []
            previous_end = None
            for primitive in primitives:
                start = tuple(primitive["start"])
                end = tuple(primitive["end"])
                if previous_end is not None:
                    continuity_errors.append(distance(previous_end, start))
                if primitive.get("type") == "arc":
                    arc_endpoint_errors.append(distance(pure._arc_point(primitive, 1.0), end))
                    arc_midpoint_errors.append(distance(pure._arc_point(primitive, 0.5),
                                                        tuple(primitive.get("mid", start))))
                previous_end = end
            result = {
                "instance_id": entry["instance_id"],
                "sample_index": sample,
                "comparison": "dashed route-guide centerline reconstruction and native cable surface radius samples",
                "direction": "native_surface_samples_to_source_route_centerline",
                "native_sha256": native_hash,
                "native_vertex_count": len(native_vertices),
                "native_triangle_count": len(native_faces),
                "render_vertex_count": len(candidate_vertices),
                "render_face_count": len(candidate_faces),
                "route_primitive_count": len(primitives),
                "route_centerline_sample_count": len(centerline),
                "probe_method": probe_method,
                "native_surface_radius_residual_from_0p15mm": stats(radius_residuals),
                "arc_endpoint_error_max_mm": max(arc_endpoint_errors, default=0.0) * 1000.0,
                "arc_midpoint_error_max_mm": max(arc_midpoint_errors, default=0.0) * 1000.0,
                "primitive_join_gap_max_mm": max(continuity_errors, default=0.0) * 1000.0,
                "solid_coverage_compared": False,
                "status": "MEASURED_DASHED_GUIDE_ONLY",
            }
        else:
            continue
        results.append(result)

    springs = [r for r in results if "tolerance_mm" in r]
    cables = [r for r in results if "solid_coverage_compared" in r]
    report = {
        "schema_version": 1,
        "status": "FINITE_NUMERICAL_COMPARISON",
        "scope": "source-local exported native tessellation compared to pure procedural render mesh",
        "limitations": [
            "One-direction finite sampling supports approximate rendered silhouette agreement; it does not establish Boolean or BRep equivalence.",
            "Spring distances sample native surface points against render triangles; buried render surfaces are intentionally not tested in reverse.",
            "Cable render geometry is a dashed routing guide, so cable comparison measures sampled native radius and route reconstruction only, not solid coverage.",
            "Centroid KD-tree searches the 32 nearest candidate triangle centroids before exact point-to-triangle distance; this is a bounded numerical approximation.",
        ],
        "source_hashes": {
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "production_timeline_sha256": hashlib.sha256(timeline_bytes).hexdigest(),
            "procedural_geometry_sha256": sha256_file(GEOMETRY),
            "comparison_script_sha256": sha256_file(Path(__file__).resolve()),
        },
        "sample_mapping": {str(i): timeline[i]["frame_id"] for i in SAMPLE_INDICES},
        "spring_tolerance_mm": SPRING_TOLERANCE_MM,
        "spring_record_count": len(springs),
        "spring_finite_probe_pass_count": sum(r["status"] == "PASS_FINITE_PROBES" for r in springs),
        "cable_record_count": len(cables),
        "records": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"report": str(REPORT), "spring_records": len(springs),
                      "spring_passes": report["spring_finite_probe_pass_count"],
                      "cable_records": len(cables),
                      "spring_max_mm": max((r["distance"]["max_mm"] for r in springs), default=None),
                      "cable_radius_residual_max_mm": max((r["native_surface_radius_residual_from_0p15mm"]["max_mm"] for r in cables), default=None)}, indent=2))


if __name__ == "__main__":
    main()
