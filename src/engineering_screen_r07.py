"""Read-only r07 mass / quasi-static demand screen on an open FreeCAD document.

Run inside FreeCAD's Python with ``analyze_document(App.openDocument(...))``.
The native B-reps are read only. Mass-derived geometry values follow the r07
mass report conventions; controller/harness values are a separate sensitivity
case. This module deliberately does not judge material allowables or release.
"""
from __future__ import print_function
import json
import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENSITY = {'aluminum': 2700., 'cable': 970., 'copper': 8960., 'pa12': 1010.,
           'rubber': 1100., 'spring': 7850., 'steel': 7850.}


def _prop(obj, key, default=None):
    return getattr(obj, key) if key in getattr(obj, 'PropertiesList', []) else default


def _xyz(v):
    return [float(v.x), float(v.y), float(v.z)]


def _shape_com(shape):
    # Some FreeCAD builds expose Volume / CenterOfMass only on contained
    # solids, not on a Part.Compound App::Link.Shape wrapper.
    try:
        return shape.CenterOfMass
    except AttributeError:
        solids = list(shape.Solids)
        volume = sum(float(s.Volume) for s in solids)
        if not solids or volume <= 0:
            raise ValueError('Shape has no solid volume for center of mass')
        import FreeCAD as App
        return App.Vector(sum(s.Volume*s.CenterOfMass.x for s in solids)/volume,
                          sum(s.Volume*s.CenterOfMass.y for s in solids)/volume,
                          sum(s.Volume*s.CenterOfMass.z for s in solids)/volume)


def _mass_and_center(link):
    src = _prop(link, 'LinkedObject', None)
    if src is None:
        return None
    purchased = _prop(src, 'PurchasedMass_g', None)
    shape = link.Shape
    if purchased is not None:
        mass = float(purchased)
        method = 'PurchasedMass_g'
    else:
        material = str(_prop(src, 'MaterialName', '')).lower()
        if material not in DENSITY or shape.isNull() or shape.Volume <= 0:
            return None
        mass = float(shape.Volume) * DENSITY[material] * 1e-6
        method = 'B-rep volume × r07 material density estimate'
    return {'name': link.Name, 'pn': str(_prop(src, 'PartNumber', '')),
            'material': str(_prop(src, 'MaterialName', '')),
            'mass_g': mass, 'method': method,
            'center_mm': _xyz(_shape_com(shape))}


def _weighted(items):
    total = sum(x['mass_g'] for x in items)
    c = [sum(x['mass_g'] * x['center_mm'][i] for x in items) / total for i in range(3)]
    I = [[0.0] * 3 for _ in range(3)]
    for x in items:
        r = [x['center_mm'][i] - c[i] for i in range(3)]
        m = x['mass_g']
        for i in range(3):
            for j in range(3):
                I[i][j] += m * ((sum(t*t for t in r) if i == j else 0.0) - r[i]*r[j])
    return {'mass_g': total, 'center_mm': c, 'point_mass_inertia_g_mm2': I}


def _lowest_contact(shape):
    zmin = shape.BoundBox.ZMin
    verts = [v.Point for v in shape.Vertexes if abs(v.Point.z-zmin) < 1e-5]
    if not verts:
        return [shape.BoundBox.Center.x, shape.BoundBox.Center.y, zmin]
    return [sum(v.x for v in verts)/len(verts), sum(v.y for v in verts)/len(verts), zmin]


def _screens(total_mass_g, instances):
    g = 9.81
    rows = []
    # Native neutral-state H journal and O3 foot contact points; force direction
    # is a stated 0.3 horizontal / 1.0 vertical envelope in the sagittal plane.
    legs = {}
    for tag in ('foreL', 'foreR', 'hindL', 'hindR'):
        hip = instances.get(tag + '_H_Journal')
        foot = instances.get(tag + '_Foot')
        pin = instances.get(tag + '_O3_Journal')
        bearing = instances.get(tag + '_O3_Bearing0')
        if bearing is None:
            bearing = instances.get(tag + '_O3_Bearing1')
        if not hip or not foot or not pin or not bearing:
            continue
        hc = hip['center_mm']; fc = foot['contact_mm']
        pc = pin['center_mm']; bc = bearing['center_mm']
        ex = fc[0]-hc[0]; ez = fc[2]-hc[2]
        arm = math.hypot(ex, ez)
        pin_overhang = abs(pc[1]-bc[1])
        legs[tag] = {'kind': 'fore' if tag.startswith('fore') else 'hind',
                     'hip_mm': hc, 'foot_contact_estimate_mm': fc,
                     'hip_to_contact_xz_mm': [ex, ez], 'hip_arm_mm': arm,
                     'ankle_pin_center_mm': pc, 'ankle_bearing_center_mm': bc,
                     'native_bearing_to_joint_plane_mm': pin_overhang}
    for alpha in (1, 3, 6):
        whole_weight = total_mass_g / 1000.0 * g * alpha
        for support_mode, share in (('two_legs_equal_share', .5), ('one_leg_worst_case', 1.0)):
            fz = whole_weight * share
            fx = .3 * fz
            resultant = math.hypot(fz, fx)
            for tag, geo in legs.items():
                moment = abs(geo['hip_to_contact_xz_mm'][0] * fz - geo['hip_to_contact_xz_mm'][1] * fx) / 1000.0
                # Pin demand uses conservative single shear; equivalent two
                # plane shear is included as a non-allowable comparison only.
                d = 1.9
                area = math.pi*d*d/4
                tau1 = resultant/area
                tau2 = resultant/(2*area)
                e = geo['native_bearing_to_joint_plane_mm']
                bend_nmm = resultant * e
                sigma = 32*bend_nmm/(math.pi*d**3)
                rows.append({'alpha': alpha, 'support': support_mode, 'leg': tag,
                    'whole_robot_vertical_N': whole_weight, 'leg_vertical_N': fz,
                    'leg_horizontal_N': fx, 'leg_resultant_N': resultant,
                    'hip_static_moment_Nm': moment,
                    'hip_moment_fraction_of_XC330_M181_T_stall_at_5V': moment/0.60,
                    'pin_single_shear_MPa': tau1, 'pin_double_shear_MPa': tau2,
                    'pin_overhang_bending_moment_Nmm': bend_nmm,
                    'pin_nominal_bending_stress_MPa': sigma,
                    'PA12_bearing_seat_projected_pressure_MPa': resultant/(4.0*1.2)})
    return {'leg_geometry_native_mm': legs, 'cases': rows,
            'spine_B_shaft': {'diameter_mm': 3.6, 'max_span_assumption_mm': 60.0,
                'model': 'simply supported, central point load; M=F L/4',
                'cases': [{'alpha': a, 'support': mode, 'F_N': total_mass_g/1000*g*a*share,
                    'M_Nmm': total_mass_g/1000*g*a*share*60/4,
                    'nominal_bending_stress_MPa': 32*(total_mass_g/1000*g*a*share*60/4)/(math.pi*3.6**3)}
                    for a in (1,3,6) for mode,share in (('two_legs_equal_share',.5),('one_leg_worst_case',1.0))]}}


def analyze_document(doc):
    """Return JSON-serializable actual-native mass, CoM and demand data."""
    objects = [o for o in doc.Objects if getattr(o, 'TypeId', '') == 'App::Link']
    rows = {}
    physical = []
    unknown = []
    for obj in objects:
        src = _prop(obj, 'LinkedObject', None)
        if src is None:
            continue
        # AppLinks physically placed in the assembly have source metadata.
        role = str(_prop(src, 'Role', ''))
        if role == 'REFERENCE_CLEARANCE' or role == 'NONPHYSICAL_CLEARANCE':
            continue
        item = _mass_and_center(obj)
        if item is None:
            unknown.append({'name': obj.Name, 'pn': str(_prop(src, 'PartNumber', '')),
                            'reason': 'no PurchasedMass_g and no applicable material density; excluded from known sum'})
            continue
        physical.append(item)
        rows[obj.Name] = {'center_mm': item['center_mm'], 'mass_g': item['mass_g']}
        if obj.Name.endswith('_Foot'):
            rows[obj.Name]['contact_mm'] = _lowest_contact(obj.Shape)
    known = _weighted(physical)
    board = next((o for o in objects if 'OPENRB150_PCB_ENVELOPE_r07' == str(_prop(_prop(o,'LinkedObject',None),'PartNumber',''))), None)
    if board is None:
        raise ValueError('OpenRB150 PCB envelope link not found')
    board_center = _xyz(_shape_com(board.Shape))
    assumptions = json.loads((ROOT/'parameters/candidate_r02.json').read_text())['parameters']
    ctl_mass = float(assumptions['controller_mass_g']['value'])
    wire_mass = float(assumptions['wiring_mass_g']['value'])
    estimate_items = list(physical) + [
        {'mass_g': ctl_mass, 'center_mm': board_center, 'name': 'controller_mass_assumption'},
        {'mass_g': wire_mass, 'center_mm': board_center, 'name': 'wiring_mass_lumped_at_board_center'}]
    loaded = _weighted(estimate_items)
    return {'source': 'actual native B-rep link placements and source metadata',
        'native_document': doc.FileName, 'physical_link_count': len(objects),
        'mass_item_count': len(physical), 'unknown_mass': unknown,
        'known_mass': known, 'controller_board_center_mm': board_center,
        'separate_assumptions': {'controller_mass_g': ctl_mass, 'wiring_mass_g': wire_mass,
            'placement': 'both lumped at actual OpenRB150 envelope B-rep center',
            'source': 'parameters/candidate_r02.json r01 DESIGN_ASSUMPTION; not BOM mass'},
        'assumed_loaded_sensitivity': loaded,
        'load_screens': _screens(loaded['mass_g'], rows),
        'limitations': ['Point-mass inertia omits each solid’s own centroidal inertia.',
            'Known geometry masses are density estimates; purchased masses are nominal metadata.',
            'Controller and harness assumptions do not modify BOM or the unknown-mass PCB record.',
            'Loads are static screening cases, not dynamic gait, impact, cable-tension, fatigue or strength qualification.',
            'The hip-torque ratio compares static hip moment with 0.60 N m XC330-M181-T stall torque at 5 V; it is not a continuous-duty or thermal margin.']}


def write_report(doc, path):
    data = analyze_document(doc)
    native = Path(getattr(doc, "FileName", ""))
    if native.is_file():data["native_sha256"] = hashlib.sha256(native.read_bytes()).hexdigest()
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    return data
