"""Read-only section-property comparison for the r15 lumbar root prototype.

Call ``compare(old_shape, new_shape, bore_centers=...)`` with detached native
source-local BReps and explicit source-local A1/A2 centres.  FreeCAD imports
are lazy, so the module's input validation and JSON-safe helpers are usable in
ordinary Python.  The report measures actual clipped OCCT planar sections; it
does not infer section properties from bounding rectangles.

No native document, feature, parameter, or file is modified.  Empty/invalid
sections fail closed instead of contributing zero to a minimum ratio.
"""

from __future__ import annotations

import math


TOL = 1e-8
MIN_SECTION_AREA_MM2 = 1e-7
DEFAULT_Y_STATIONS_MM = (2.5, 2.75, 3.0, 3.25, 3.5, 4.125, 5.75, 7.375, 9.0)
DEFAULT_BORE_Z_STATIONS_MM = (0.8, 56.0)


def _root_regions():
    """Return the twelve specified root ROIs, mirrored in source X/Y."""
    regions = []
    # Short-ear roots follow the sagittal cheek orientation. Guide roots cover
    # all four X/Y sign combinations at both source-stack levels.
    for y_sign in (-1, 1):
        x_bounds = (-37.0, -22.0) if y_sign < 0 else (22.0, 37.0)
        for z_center in (0.0, 56.8):
            regions.append({
                'id': 'short_ear_y{:+d}_z{:g}'.format(y_sign, z_center),
                'family': 'short_ear', 'x_bounds_mm': x_bounds,
                'z_bounds_mm': (-2.0, 3.0) if z_center == 0.0 else (53.8, 58.8),
                'y_sign': y_sign, 'y_range_abs_mm': (2.5, 9.0),
            })
    for x_sign in (-1, 1):
        for y_sign in (-1, 1):
            for z_center in (-9.4, 66.2):
                regions.append({
                    'id': 'outer_guide_x{:+d}_y{:+d}_z{:g}'.format(x_sign, y_sign, z_center),
                    'family': 'outer_guide',
                    'x_bounds_mm': (-37.0, -22.0) if x_sign < 0 else (22.0, 37.0),
                    'z_bounds_mm': (z_center - 3.0, z_center + 3.0),
                    'x_sign': x_sign, 'y_sign': y_sign,
                    'y_range_abs_mm': (2.5, 9.0),
                })
    return tuple(regions)


DEFAULT_ROOT_REGIONS = _root_regions()


def _finite(value, label):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(label + ' must be finite')
    return value


def _bounds(shape):
    box = shape.BoundBox
    values = [float(getattr(box, key)) for key in
              ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax')]
    if not all(math.isfinite(value) for value in values):
        raise ValueError('B-rep has a nonfinite bounding box')
    return values


def _check_solid(shape, label):
    if shape is None or shape.isNull() or not shape.isValid():
        raise ValueError(label + ' must be a non-null valid B-rep')
    solids = list(shape.Solids)
    if len(solids) != 1:
        raise ValueError('{} must contain exactly one solid (got {})'.format(label, len(solids)))
    volume = _finite(shape.Volume, label + '.Volume')
    if volume <= 0:
        raise ValueError(label + ' must have positive volume')
    return volume


def _roi_face(Part, App, x_bounds, y, z_bounds):
    """Build an exact planar X-Z clipping face at source-local Y=y."""
    x0, x1 = map(float, x_bounds)
    z0, z1 = map(float, z_bounds)
    if not (x1 > x0 and z1 > z0):
        raise ValueError('ROI bounds must have positive width and height')
    points = [App.Vector(x0, y, z0), App.Vector(x1, y, z0),
              App.Vector(x1, y, z1), App.Vector(x0, y, z1),
              App.Vector(x0, y, z0)]
    face = Part.Face(Part.Wire(Part.makePolygon(points).Edges))
    if face.isNull() or not face.isValid() or float(face.Area) <= 0:
        raise ValueError('Could not construct a valid X-Z ROI plane')
    return face


def _faces(shape):
    """Flatten a planar common result into actual faces, preserving holes."""
    out = []
    if getattr(shape, 'ShapeType', '') == 'Face':
        out.append(shape)
    else:
        out.extend(list(getattr(shape, 'Faces', ())))
    return out


def _matrix_rows(matrix):
    raw = list(matrix.A)
    if len(raw) != 16:
        raise ValueError('OCCT MatrixOfInertia did not expose a 4x4 matrix')
    return [[float(raw[4 * r + c]) for c in range(4)] for r in range(4)]


def _section_properties(section_shape, plane_offset, label, plane='xz'):
    """Aggregate actual planar faces and central moments in their 2-D axes."""
    faces = _faces(section_shape)
    if not faces:
        raise ValueError(label + ': clipping produced no face; section coverage is incomplete')
    records = []
    area = cx_sum = cz_sum = 0.0
    raw_moments = [0.0, 0.0, 0.0]  # integral x^2, z^2, x*z about source origin
    for index, face in enumerate(faces):
        if face.isNull() or not face.isValid():
            raise ValueError('{}: invalid clipped section face {}'.format(label, index))
        a = _finite(face.Area, label + '.face_area')
        if a <= MIN_SECTION_AREA_MM2:
            raise ValueError('{}: section face area is empty/negligible'.format(label))
        c = face.CenterOfMass
        second_coord = c.z if plane == 'xz' else c.y
        second_axis = 'z' if plane == 'xz' else 'y'
        x = _finite(c.x, label + '.centroid_x')
        z = _finite(second_coord, label + '.centroid_' + second_axis)
        normal_coord = c.y if plane == 'xz' else c.z
        if abs(float(normal_coord) - plane_offset) > 1e-7:
            raise ValueError(label + ': clipped face is off its requested plane')
        inertia = _matrix_rows(face.MatrixOfInertia)
        # FreeCAD's Face.MatrixOfInertia is centroidal. Recover each face's
        # second products about the source origin, then aggregate and shift
        # once to the combined section centroid below.
        if plane == 'xz':
            int_x2 = inertia[2][2] + a * x * x
            int_z2 = inertia[0][0] + a * z * z
            int_xz = -inertia[0][2] + a * x * z
        elif plane == 'xy':
            int_x2 = inertia[1][1] + a * x * x
            int_z2 = inertia[0][0] + a * z * z
            int_xz = -inertia[0][1] + a * x * z
        else:
            raise ValueError('Unsupported section plane: ' + str(plane))
        values = (int_x2, int_z2, int_xz)
        if not all(math.isfinite(value) for value in values):
            raise ValueError(label + ': nonfinite section inertia')
        center_record = {'centroid_x_mm': x}
        center_record['centroid_z_mm' if plane == 'xz' else 'centroid_y_mm'] = z
        records.append({'area_mm2': a, **center_record,
                        'origin_moments_x2_second2_xsecond_mm4': list(values)})
        area += a
        cx_sum += a * x
        cz_sum += a * z
        raw_moments = [old + new for old, new in zip(raw_moments, values)]
    if not math.isfinite(area) or area <= MIN_SECTION_AREA_MM2:
        raise ValueError(label + ': total section area is empty/negligible')
    cx, cz = cx_sum / area, cz_sum / area
    ixx = raw_moments[0] - area * cx * cx
    izz = raw_moments[1] - area * cz * cz
    ixz = raw_moments[2] - area * cx * cz
    # In-plane central second-moment tensor, symmetric in X/Z coordinates.
    mean = 0.5 * (ixx + izz)
    radius = math.hypot(0.5 * (ixx - izz), ixz)
    eigenvalues = (mean - radius, mean + radius)
    if not all(math.isfinite(value) for value in (ixx, izz, ixz, *eigenvalues)):
        raise ValueError(label + ': nonfinite central area-moment tensor')
    if eigenvalues[0] < -max(1e-7, abs(eigenvalues[1]) * 1e-10):
        raise ValueError(label + ': materially negative principal area moment')
    centroid_key = 'centroid_xz_mm' if plane == 'xz' else 'centroid_xy_mm'
    tensor_key = 'central_area_moment_tensor_xz_mm4' if plane == 'xz' else 'central_area_moment_tensor_xy_mm4'
    return {'area_mm2': area, centroid_key: [cx, cz],
            tensor_key: [[ixx, ixz], [ixz, izz]],
            'principal_area_moments_mm4': [max(0.0, eigenvalues[0]), eigenvalues[1]],
            'face_count': len(faces), 'faces': records}


def _verify_matrix_of_inertia_probe(App, Part):
    """Runtime-check FreeCAD's centroidal planar inertia convention.

    The X-Z rectangle is 2 by 3 mm, at y=2.5 mm. Its centroidal 3-D inertia
    tensor is diag(4.5, 6.5, 2.0) mm^4; the nonzero normal coordinate must not
    be subtracted from the returned centroidal tensor.
    """
    points = [App.Vector(10, 2.5, 20), App.Vector(12, 2.5, 20),
              App.Vector(12, 2.5, 23), App.Vector(10, 2.5, 23),
              App.Vector(10, 2.5, 20)]
    face = Part.Face(Part.Wire(Part.makePolygon(points).Edges))
    if not face.isValid() or abs(float(face.Area) - 6.0) > 1e-9:
        raise RuntimeError('Known rectangle MatrixOfInertia probe could not be built')
    c = face.CenterOfMass
    if max(abs(float(a)-b) for a, b in ((c.x, 11.0), (c.y, 2.5), (c.z, 21.5))) > 1e-9:
        raise RuntimeError('Known rectangle centroid probe differs')
    matrix = _matrix_rows(face.MatrixOfInertia)
    expected = (4.5, 6.5, 2.0)
    actual = (matrix[0][0], matrix[1][1], matrix[2][2])
    if max(abs(a-b) for a, b in zip(actual, expected)) > 1e-8:
        raise RuntimeError('FreeCAD MatrixOfInertia convention differs: ' + repr(actual))
    return {'status': 'PASS', 'area_mm2': float(face.Area),
            'centroid_xyz_mm': [float(c.x), float(c.y), float(c.z)],
            'matrix_diagonal_mm4': list(actual), 'expected_matrix_diagonal_mm4': list(expected),
            'interpretation': 'Face.MatrixOfInertia is centroidal; use parallel-axis aggregation'}


def _section(old_shape, new_shape, Part, App, *, x_bounds, z_bounds, y, label):
    plane = _roi_face(Part, App, x_bounds, y, z_bounds)
    old_result = old_shape.common(plane)
    new_result = new_shape.common(plane)
    old_props = _section_properties(old_result, y, label + ' old')
    new_props = _section_properties(new_result, y, label + ' new')
    area_ratio = new_props['area_mm2'] / old_props['area_mm2']
    old_p = old_props['principal_area_moments_mm4']
    new_p = new_props['principal_area_moments_mm4']
    if min(old_p) <= 0:
        raise ValueError(label + ': old principal moment is zero; ratio undefined')
    moment_ratios = [b / a for a, b in zip(old_p, new_p)]
    return {'label': label, 'source_y_mm': y, 'x_bounds_mm': list(x_bounds),
            'z_bounds_mm': list(z_bounds), 'old': old_props, 'new': new_props,
            'area_ratio_new_over_old': area_ratio,
            'principal_moment_ratios_new_over_old': moment_ratios,
            'minimum_ratio': min([area_ratio] + moment_ratios)}


def _validate_regions(regions, y_stations_mm):
    regions = tuple(regions)
    if not regions:
        raise ValueError('At least one root ROI is required')
    ids = [str(row.get('id', '')) for row in regions]
    if any(not name for name in ids) or len(set(ids)) != len(ids):
        raise ValueError('Root ROI IDs must be nonempty and unique')
    stations = tuple(_finite(v, 'y station') for v in y_stations_mm)
    if not stations or len(set(stations)) != len(stations):
        raise ValueError('Y stations must be nonempty and unique')
    return stations


def _bore_section(Part, App, shape, *, center, radius_mm, z, label):
    """Actual XY source section in a fixed window around a pivot bore."""
    x, y = map(float, center)
    radius = float(radius_mm)
    # A compact, fixed 12 mm square around the datum contains the bore and
    # its neighboring material. The hole is retained as an inner wire by OCC.
    half = 6.0
    points = [App.Vector(x-half, y-half, z), App.Vector(x+half, y-half, z),
              App.Vector(x+half, y+half, z), App.Vector(x-half, y+half, z),
              App.Vector(x-half, y-half, z)]
    window = Part.Face(Part.Wire(Part.makePolygon(points).Edges))
    result = shape.common(window)
    props = _section_properties(result, z, label, plane='xy')
    # Verify that the local section contains the complete specified bore disk:
    # subtracting the nominal disk from the section would otherwise hide a
    # missing/capped bore. For a true circular opening, the disk common is null.
    nominal_bore = Part.makeCircle(radius, App.Vector(x, y, z), App.Vector(0, 0, 1))
    bore_edge = Part.Wire(nominal_bore.Edges)
    hole_test = result.common(Part.Face(bore_edge))
    hole_area = float(getattr(hole_test, 'Area', 0.0))
    if not math.isfinite(hole_area) or hole_area > max(1e-6, math.pi * radius * radius * 1e-8):
        raise ValueError(label + ': nominal pivot bore is filled or sectioned inconsistently')
    return props


def _bore_compare(old_shape, new_shape, Part, App, bore_centers,
                  radius_mm, z_stations_mm, area_tolerance_mm2):
    if not isinstance(bore_centers, dict) or not {'A1', 'A2'} <= set(bore_centers):
        raise ValueError('bore_centers must supply source-local (x,y) for both A1 and A2')
    results = []
    for key in ('A1', 'A2'):
        center = bore_centers[key]
        if len(center) != 2 or not all(math.isfinite(float(q)) for q in center):
            raise ValueError(key + ' center must be a finite source-local (x,y) pair')
        for z in z_stations_mm:
            label = '{} bore at source Z={:g} mm'.format(key, z)
            old_props = _bore_section(Part, App, old_shape, center=center,
                                      radius_mm=radius_mm, z=z, label=label + ' old')
            new_props = _bore_section(Part, App, new_shape, center=center,
                                      radius_mm=radius_mm, z=z, label=label + ' new')
            # Also compare exact 2D material regions in the local datum window.
            half = 6.0
            x, y = map(float, center)
            points = [App.Vector(x-half, y-half, z), App.Vector(x+half, y-half, z),
                      App.Vector(x+half, y+half, z), App.Vector(x-half, y+half, z),
                      App.Vector(x-half, y-half, z)]
            window = Part.Face(Part.Wire(Part.makePolygon(points).Edges))
            old_face = old_shape.common(window)
            new_face = new_shape.common(window)
            lost = float(old_face.cut(new_face).Area)
            added = float(new_face.cut(old_face).Area)
            if not all(math.isfinite(v) and v >= 0 for v in (lost, added)):
                raise ValueError(label + ': invalid 2D material difference')
            diff = max(lost, added)
            results.append({'bore': key, 'source_z_mm': z, 'center_xy_mm': list(center),
                            'nominal_radius_mm': radius_mm, 'old': old_props,
                            'new': new_props, 'material_difference_mm2': [lost, added],
                            'unchanged_within_tolerance': diff <= area_tolerance_mm2,
                            'area_tolerance_mm2': area_tolerance_mm2})
    return results


def compare(old_shape, new_shape, *, bore_centers, bore_radius_mm=2.025,
            regions=DEFAULT_ROOT_REGIONS, y_stations_mm=DEFAULT_Y_STATIONS_MM,
            bore_z_stations_mm=DEFAULT_BORE_Z_STATIONS_MM,
            bore_area_tolerance_mm2=1e-7, pa12_density_kg_m3=1000.0):
    """Compare actual source-local sections and global geometry metrics.

    Args:
        old_shape, new_shape: detached FreeCAD single-solid source-local BReps.
        bore_centers: required mapping ``{'A1': (x_mm,y_mm), 'A2': (...)}``.
          Supply actual native kinematic/datums; this helper does not guess them.
        regions: optional iterable of root ROI mappings. The defaults cover four
          short-ear and eight outer-guide roots, mirrored across X/Y.
        y_stations_mm: positive magnitudes sampled across each ROI's 2.5..9 mm
          source-Y band; the region's ``y_sign`` mirrors them.
        bore_z_stations_mm: source-stack stations used to compare A1/A2 support.
        pa12_density_kg_m3: explicit assumed density only; default 1000 is a
          screening assumption and is not material certification.

    Returns a JSON-serializable report. Any invalid/empty root or bore section
    raises ``ValueError``; it is never silently dropped from the result.
    """
    import FreeCAD as App
    import Part

    inertia_probe = _verify_matrix_of_inertia_probe(App, Part)
    old_volume = _check_solid(old_shape, 'old_shape')
    new_volume = _check_solid(new_shape, 'new_shape')
    density = _finite(pa12_density_kg_m3, 'PA12 density assumption')
    if density <= 0:
        raise ValueError('PA12 density assumption must be positive')
    regions = tuple(regions)
    stations = _validate_regions(regions, y_stations_mm)
    bore_radius = _finite(bore_radius_mm, 'bore radius')
    if bore_radius <= 0:
        raise ValueError('bore radius must be positive')
    bore_zs = tuple(_finite(v, 'bore Z station') for v in bore_z_stations_mm)
    if not bore_zs:
        raise ValueError('At least one A1/A2 bore station is required')
    area_tol = _finite(bore_area_tolerance_mm2, 'bore area tolerance')
    if area_tol < 0:
        raise ValueError('bore area tolerance cannot be negative')

    root_rows = []
    ratios = []
    for region in regions:
        name = str(region['id'])
        x_bounds = tuple(map(float, region['x_bounds_mm']))
        z_bounds = tuple(map(float, region['z_bounds_mm']))
        y_sign = int(region['y_sign'])
        if y_sign not in (-1, 1):
            raise ValueError(name + ': y_sign must be -1 or +1')
        lo, hi = map(float, region['y_range_abs_mm'])
        if not (lo > 0 and hi > lo):
            raise ValueError(name + ': invalid source-Y sampling range')
        if any(v < lo - TOL or v > hi + TOL for v in stations):
            raise ValueError(name + ': y station lies outside its ROI band')
        row_sections = []
        for station in stations:
            y = y_sign * station
            section = _section(old_shape, new_shape, Part, App,
                               x_bounds=x_bounds, z_bounds=z_bounds, y=y,
                               label=name + ' at y={:g} mm'.format(y))
            row_sections.append(section)
            ratios.append(section['minimum_ratio'])
        root_rows.append({'id': name, 'family': region.get('family', 'unspecified'),
                          'x_bounds_mm': list(x_bounds), 'z_bounds_mm': list(z_bounds),
                          'y_sign': y_sign, 'sections': row_sections,
                          'minimum_section_ratio': min(s['minimum_ratio'] for s in row_sections)})

    bore_rows = _bore_compare(old_shape, new_shape, Part, App, bore_centers,
                              bore_radius, bore_zs, area_tol)
    delta_volume = new_volume - old_volume
    density_g_mm3 = density * 1e-6
    old_bounds, new_bounds = _bounds(old_shape), _bounds(new_shape)
    bbox_delta = [new - old for old, new in zip(old_bounds, new_bounds)]
    bbox_lengths_old = [old_bounds[1]-old_bounds[0], old_bounds[3]-old_bounds[2], old_bounds[5]-old_bounds[4]]
    bbox_lengths_new = [new_bounds[1]-new_bounds[0], new_bounds[3]-new_bounds[2], new_bounds[5]-new_bounds[4]]
    if any(length <= 0 for length in bbox_lengths_old + bbox_lengths_new):
        raise ValueError('Old/new B-rep has a degenerate bounding-box extent')
    return {
        'status': 'SECTION_COMPARISON_COMPLETE',
        'scope': 'Actual OCCT clipped source-local sections and A1/A2 datum windows; geometry screening only',
        'matrix_of_inertia_probe': inertia_probe,
        'old': {'volume_mm3': old_volume, 'bbox_xyz_minmax_mm': old_bounds,
                'bbox_lengths_xyz_mm': bbox_lengths_old},
        'new': {'volume_mm3': new_volume, 'bbox_xyz_minmax_mm': new_bounds,
                'bbox_lengths_xyz_mm': bbox_lengths_new},
        'volume_delta_mm3': delta_volume,
        'pa12_density_assumption_kg_m3': density,
        'mass_delta_g_assumption_only': delta_volume * density_g_mm3,
        'bbox_delta_minmax_mm': bbox_delta,
        'bbox_length_delta_xyz_mm': [b-a for a, b in zip(bbox_lengths_old, bbox_lengths_new)],
        'root_region_count': len(root_rows), 'root_section_count': sum(len(r['sections']) for r in root_rows),
        'minimum_root_area_or_principal_moment_ratio': min(ratios),
        'root_sections': root_rows,
        'a1_a2_bore_support': {'status': 'PASS_UNCHANGED_LOCAL_SECTIONS'
                               if all(r['unchanged_within_tolerance'] for r in bore_rows)
                               else 'FAIL_LOCAL_SECTION_CHANGED',
                               'records': bore_rows,
                               'area_tolerance_mm2': area_tol},
        'limitations': ['No stress, strength, fatigue, buckling, fit, or fabrication qualification.',
                        'Density is an explicit PA12 screening assumption, not manufacturer verification.',
                        'Section ratios apply only to the listed finite ROIs and stations.'],
    }
