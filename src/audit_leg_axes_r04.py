"""Read-only actual-native neutral H/K/A/F and coaxial leg-bore audit.

Use audit(doc, output=None) inside isolated FreeCADCmd. Geometry is read from
world cylindrical faces, independently of MotionMap point placements. No
recompute, document mutation, save, GUI import or collision approval occurs.
"""
import hashlib
import json
import math
from pathlib import Path
import time

from leg_geometry_r02 import leg_geometry

ROOT = Path(__file__).resolve().parents[1]
LINEAR_TOL = 1e-6
AXIS_TOL = 1e-9
RADIUS_TOL = 1e-7


def _xyz(v):
    return [float(v.x), float(v.y), float(v.z)]


def _xz(v):
    return (v[0], v[2])


def _cylinders(shape):
    import Part
    rows = []
    for i, face in enumerate(shape.Faces):
        s = face.Surface
        if not isinstance(s, Part.Cylinder):
            continue
        axis = _xyz(s.Axis)
        norm = math.sqrt(sum(q*q for q in axis))
        if norm <= 0:
            raise ValueError('Zero cylinder axis')
        axis = [q / norm for q in axis]
        rows.append({'face_index': i+1, 'radius_mm': float(s.Radius),
                     'axis_point_xyz_mm': _xyz(s.Center), 'axis_direction_xyz': axis,
                     'axis_transverse_component': math.hypot(axis[0], axis[2])})
    return rows


def audit(doc, output=None):
    """Measure actual saved neutral axes, write JSON evidence and return it.

    Cylinder axis points may have arbitrary Y along the line. X/Z identify
    these nominal Y axes. F is the native FootPad origin/contact-cup center,
    additionally corroborated by its actual circular cylindrical surfaces.
    """
    start = time.monotonic()
    output = Path(output or ROOT/'reports/verification/r04_leg_native_axes.json')
    result = {'revision': str(getattr(doc.DesignParameters,'Revision','r04')), 'status': 'RUNNING',
              'scope': 'Actual saved neutral leg shaft/cylindrical bore axes and orientation; read-only native geometry',
              'document': {'name': doc.Name, 'file': doc.FileName},
              'tolerances': {'axis_position_mm': LINEAR_TOL,
                             'axis_transverse_unit_component': AXIS_TOL,
                             'surface_radius_match_mm': RADIUS_TOL},
              'checks': [], 'legs': [], 'errors': [],
              'limits': [
                  'Neutral saved pose only; no full gait or dynamic closure certification.',
                  'Cylindrical axis coincidence is checked, not keyed-flat angular engagement, bearing preload, fits, retention strength or motor spline.',
                  'F denotes the contact cup reference center, not a solved ground-contact point under load.',
                  'Candidate dimensions/neutral angles remain reconstruction assumptions; no source/supplier dimension certification.',
                  'No assembly-wide collision, equilibrium or fabrication approval.']}
    cache = {}

    def check(label, passed, **evidence):
        result['checks'].append(dict(check=label, passed=bool(passed), **evidence))

    def object_geometry(name):
        if name not in cache:
            o = doc.getObject(name)
            if o is None or o.TypeId != 'App::Link':
                raise ValueError('Missing actual App::Link: '+name)
            shape = o.Shape
            valid = shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 0
            check(name+':valid_single_solid', valid)
            cache[name] = (o, _cylinders(shape))
        return cache[name]

    def axis(name, radius, nearest=None):
        o, cylinders = object_geometry(name)
        faces = [c for c in cylinders if abs(c['radius_mm']-radius) <= RADIUS_TOL]
        if not faces:
            raise ValueError(name+': no native cylinder radius '+str(radius))
        if nearest is not None:
            distance = min(math.dist(_xz(c['axis_point_xyz_mm']), nearest) for c in faces)
            # Keep all faces on the selected bore/journal line, including split
            # surfaces after grooves. Other joints of the same radius remain
            # in the extraction evidence but are not mistaken for this bore.
            faces = [c for c in faces if math.dist(_xz(c['axis_point_xyz_mm']), nearest) <= distance+LINEAR_TOL]
        first = _xz(faces[0]['axis_point_xyz_mm'])
        spread = max(math.dist(first, _xz(c['axis_point_xyz_mm'])) for c in faces)
        direction = max(c['axis_transverse_component'] for c in faces)
        check(name+':selected_axis_parallel_Y', direction <= AXIS_TOL,
              transverse_component=direction, radius_mm=radius)
        check(name+':split_faces_coaxial', spread <= LINEAR_TOL,
              max_xz_spread_mm=spread, radius_mm=radius)
        return {'instance': name, 'source_object': o.LinkedObject.Name,
                'point_xz_mm': list(first), 'radius_mm': radius,
                'max_xz_spread_mm': spread,
                'max_axis_transverse_component': direction,
                'native_cylindrical_faces': faces}

    try:
        import FreeCAD as App
        result['runtime_freecad_version'] = App.Version()
        path = Path(doc.FileName) if doc.FileName else None
        if path and path.is_file():
            result['document'].update(bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        controller = doc.getObject('PoseController')
        if controller is None:
            raise ValueError('PoseController missing')
        phase = float(controller.SpinePhaseRad)
        check('saved_neutral_spine_phase', abs(math.atan2(math.sin(phase),math.cos(phase))) <= AXIS_TOL,
              phase_rad=phase)
        recorded = (json.loads(controller.LegAnglesR03)
                    if 'LegAnglesR03' in controller.PropertiesList else {})
        result['recorded_leg_angles_rad'] = recorded
        result['assembly_link_instances'] = sum(o.TypeId=='App::Link' for o in doc.Objects)
        # Independent contract: lumbar E axes are -33/+33, then add pure
        # leg_geometry points. Measure the saved E journals as well.
        E = {'hind': (-33.0,0.0), 'fore': (33.0,0.0)}
        result['expected_neutral_E_xz_mm'] = E
        result['output_ground_axes'] = []
        for kind, index in (('hind',1),('fore',2)):
            names = [o.Name for o in doc.Objects if o.TypeId=='App::Link'
                     and o.Name.startswith('E'+str(index)+'_') and o.Name.endswith('_Pin')]
            check(kind+':bilateral_E_journals_found', len(names)==2, instances=names)
            for name in names:
                measured = axis(name,.95)
                error = math.dist(measured['point_xz_mm'],E[kind])
                check(name+':E_contract', error <= LINEAR_TOL, error_mm=error)
                result['output_ground_axes'].append(measured)

        for tag in ('hindR','hindL','foreR','foreL'):
            kind = 'hind' if tag.startswith('hind') else 'fore'
            g = leg_geometry(kind)
            expected = {key: (E[kind][0]+g[key][0], E[kind][1]+g[key][1])
                        for key in ('H','K','A','F')}
            row = {'tag': tag, 'leg_type': kind, 'expected_points_xz_mm': expected,
                   'shaft_axes': {}, 'bore_axes': [], 'bearing_axes': []}
            result['legs'].append(row)
            if tag in recorded:
                pair = recorded[tag]
                check(tag+':recorded_neutral_angles', len(pair)==2 and
                      abs(pair[0]-g['thigh_angle_rad'])<=AXIS_TOL and
                      abs(pair[1]-g['passive_knee_rad'])<=AXIS_TOL,
                      recorded_rad=pair,
                      expected_rad=[g['thigh_angle_rad'],g['passive_knee_rad']])
            measured_points = {}
            for joint in ('H','K','A'):
                measured = axis(tag+'_'+joint+'_Journal',.95)
                measured_points[joint] = tuple(measured['point_xz_mm'])
                row['shaft_axes'][joint] = measured
                error = math.dist(measured_points[joint],expected[joint])
                check(tag+':'+joint+'_shaft_expected_position', error<=LINEAR_TOL,
                      error_mm=error, measured_xz_mm=measured_points[joint])

            pad_name = tag+'_FootPad'
            pad, faces = object_geometry(pad_name)
            point = pad.LinkPlacement.Base
            F = (float(point.x),float(point.z))
            measured_points['F'] = F
            row['foot_reference'] = {'instance': pad_name,
                                    'origin_xyz_mm': _xyz(point), 'point_xz_mm': F}
            error = math.dist(F,expected['F'])
            check(tag+':F_pad_origin_expected_position',error<=LINEAR_TOL,error_mm=error)
            native_pad = axis(pad_name,3.0)
            row['foot_reference']['native_cup_axis'] = native_pad
            error = math.dist(native_pad['point_xz_mm'],F)
            check(tag+':F_native_cup_matches_pad_origin',error<=LINEAR_TOL,error_mm=error)

            for joint,suffix,radius in (('H','thigh',1.025),('H','InputHorn',1.025),
                    ('K','thigh',2.025),('K','shank',2.025),
                    ('A','shank',2.025),('A','Foot',2.025)):
                measured = axis(tag+'_'+suffix,radius,measured_points[joint])
                measured['joint'] = joint
                error = math.dist(measured['point_xz_mm'],measured_points[joint])
                measured['shaft_axis_offset_mm'] = error
                check(measured['instance']+':'+joint+'_bore_shaft_coaxial',error<=LINEAR_TOL,error_mm=error)
                row['bore_axes'].append(measured)
            measured = axis('Torso_'+kind,2.025,measured_points['H'])
            measured['joint'] = 'H'
            error = math.dist(measured['point_xz_mm'],measured_points['H'])
            check(tag+':torso_H_support_coaxial',error<=LINEAR_TOL,error_mm=error)
            row['bore_axes'].append(measured)
            for joint in ('H','K','A'):
                prefix = tag+'_'+joint+'_Bearing'
                bearing_names = [o.Name for o in doc.Objects if o.TypeId=='App::Link' and o.Name.startswith(prefix)]
                check(prefix+':found',bool(bearing_names),instances=bearing_names)
                for name in bearing_names:
                    measured = axis(name,1.0)
                    measured['joint'] = joint
                    error = math.dist(measured['point_xz_mm'],measured_points[joint])
                    check(name+':shaft_coaxial',error<=LINEAR_TOL,error_mm=error)
                    row['bearing_axes'].append(measured)
            vectors = {}
            for a,b,sign in (('H','K',1),('K','A',-1),('A','F',1)):
                vector = [measured_points[b][i]-measured_points[a][i] for i in (0,1)]
                vectors[a+'_'+b] = vector
                check(tag+':'+a+'->'+b+'_direction',sign*vector[0]>LINEAR_TOL and vector[1]<-LINEAR_TOL,
                      measured_dx_dz_mm=vector, expected_x_sign=sign,expected_z_sign=-1)
            row['measured_points_xz_mm'] = measured_points
            row['measured_segment_vectors_dx_dz_mm'] = vectors
            row['measured_lengths_mm'] = {a+'_'+b:math.dist(measured_points[a],measured_points[b])
                                          for a,b in (('H','K'),('K','A'),('A','F'))}
        for kind in ('hind','fore'):
            rows = [row for row in result['legs'] if row['leg_type']==kind]
            error = max(math.dist(rows[0]['measured_points_xz_mm'][key],
                                  rows[1]['measured_points_xz_mm'][key])
                        for key in ('H','K','A','F'))
            check(kind+':left_right_same_sagittal_points',error<=LINEAR_TOL,error_mm=error)
        result['geometry_instances_inspected'] = len(cache)
        result['maximum_position_or_coaxial_error_mm'] = max(c.get('error_mm',0.0) for c in result['checks'])
        result['maximum_axis_transverse_component'] = max(c.get('transverse_component',0.0) for c in result['checks'])
        result['status'] = 'PASS' if all(c['passed'] for c in result['checks']) else 'FAIL'
    except Exception as exc:
        result['status'] = 'ERROR'
        result['errors'].append(type(exc).__name__+': '+str(exc))
    result['elapsed_seconds'] = time.monotonic()-start
    result['check_count'] = len(result['checks'])
    result['failed_checks'] = [c for c in result['checks'] if not c['passed']]
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','check_count','geometry_instances_inspected','failed_checks','errors') if k in result}),flush=True)
    return result


def main():
    import FreeCAD as App
    doc = App.openDocument(str(ROOT/'cad/flexor_r04_robot.FCStd'))
    try:
        return audit(doc)
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
