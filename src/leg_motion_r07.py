"""Read-only prescribed leg/wheel motion on copied r06 native sources.

No document mutation, save, or passive equilibrium solve. The r03 installed
fixed-state guard remains intact. This adapter removes ONLY explicitly handled
tendon descriptors from a private controller facade, delegates all remaining
placements to r03, then supplies regenerated sources/placements for every
removed member. All lengths are mm, angles radians, sagittal positive CCW.
"""
import json
import math
from pathlib import Path
from types import SimpleNamespace

from leg_geometry_r02 import leg_geometry
from tendon_r03 import tendon_route, bilateral_states
import robot_pose_r03 as pose

ROOT = Path(__file__).resolve().parents[1]
# Candidate demonstrations, not paper-reported or collision-qualified limits.
CANDIDATE_LIMITS_DEG = {'fore': {'qh': (-65., -35.), 'qk': (-105., -75.)},
                        'hind': {'qh': (-55., -25.), 'qk': (-115., -85.)}}
COUPLING_COMPONENTS = frozenset(('D_shaft', 'outer_clip', 'outer_washer', 'root_shim'))
ORBITING_WHEEL_COMPONENTS = frozenset(('wheel_clamp','wheel_anchor_bolt','wheel_clamp_grub'))


def _assembly(config=None):
    if config is None:
        config = json.loads((ROOT / 'parameters/assembly_r06.json').read_text())
    # Source generators are frozen to r06 geometry; reject schema drift rather
    # than silently using mismatched lengths or cable/contact dimensions.
    p=config['parameters']; geometry=config['leg_geometry']
    expected={'wheel_pitch_radius_mm':5.5,'cable_diameter_mm':.3,
              'shell_guide_radius_mm':2.5,'wheel_axle_z_local_mm':0.}
    if any(abs(float(p[key])-value)>1e-9 for key,value in expected.items()):
        raise ValueError('Assembly parameters require unsupported generator geometry')
    for kind in ('fore','hind'):
        g=leg_geometry(kind)
        lengths=[g['lengths_mm']['a'+str(i)] for i in (1,2,3)]
        if any(abs(a-b)>1e-9 for a,b in zip(lengths,geometry[kind+'_lengths_mm'])):
            raise ValueError('Leg source lengths differ from authoritative assembly')
        neutral=[math.degrees(g['thigh_angle_rad']),math.degrees(g['passive_knee_rad'])]
        if any(abs(a-b)>1e-9 for a,b in zip(neutral,geometry[kind+'_neutral_angles_deg'])):
            raise ValueError('Neutral source state differs from authoritative assembly')
    return config


def _route_options(config):
    p = config['parameters']
    return dict(cable_plane_mm=p['cable_plane_y_abs_mm'],
                wheel_x_mm=p['wheel_axle_x_local_mm'],
                ankle_eye_radius_mm=p['ankle_eye_radius_mm'])


def pose_states(leg_angles=None, wheel_angle=0., config=None, enforce_candidates=True, positive_terminals=False):
    """Pure descriptor: full FK, closure, spring lengths, two cable states.

    leg_angles maps tags to (qh,qk). Standard tags are foreL/foreR/hindL/hindR.
    Missing tags use frozen neutral angles. Both chains share the same forward
    thigh/toe and rearward shank convention; no left/right sagittal reflection.
    Wheel is an independent prescribed coordinate in [0,pi/2]. Cable tensions
    use the existing provisional 2 N/mm law and DO NOT predict loaded knees.
    """
    config = _assembly(config)
    identities = {'foreL': ('fore', 1), 'foreR': ('fore', -1),
                  'hindL': ('hind', 1), 'hindR': ('hind', -1)}
    requested = {} if leg_angles is None else leg_angles
    if not isinstance(requested, dict) or set(requested) - set(identities):
        raise ValueError('Unknown leg tags; expected foreL/foreR/hindL/hindR')
    if not math.isfinite(wheel_angle) or not 0 <= wheel_angle <= math.pi/2:
        raise ValueError('Fixed-guide assembled wheel interval is [0,pi/2]')
    states = {}
    for tag, (kind, side) in identities.items():
        neutral = leg_geometry(kind)
        pair = requested.get(tag, (neutral['thigh_angle_rad'], neutral['passive_knee_rad']))
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(tag + ': expected (qh,qk) radians')
        qh, qk = map(float, pair)
        if not all(math.isfinite(q) for q in (qh, qk)):
            raise ValueError('Nonfinite leg angle')
        if enforce_candidates:
            for coordinate, q in (('qh', qh), ('qk', qk)):
                lo, hi = CANDIDATE_LIMITS_DEG[kind][coordinate]
                if not lo-1e-9 <= math.degrees(q) <= hi+1e-9:
                    raise ValueError(tag + ': outside candidate ' + coordinate + ' interval')
        g = leg_geometry(kind, qh, qk)
        states[tag] = {'kind': kind, 'side': side, 'angles_rad': (qh,qk), 'geometry': g}
    left, right = states['hindL']['angles_rad'], states['hindR']['angles_rad']
    cables = bilateral_states(wheel_angle, left[1], right[1], left[0], right[0],
                              **_route_options(config))
    if positive_terminals:
        from cable_clamps_r07 import terminated_route
        from leg_mechanics import cable_state
        for side,branch in cables['branches'].items():
            branch['route']=terminated_route(branch['route'])
            neutral=terminated_route(tendon_route(side,0,**_route_options(config)))
            branch['path_mm']=branch['route']['length_mm']
            branch['available_mm']=neutral['length_mm']+.5
            branch['state']=cable_state(branch['path_mm'],branch['available_mm'],
                                        {'cable_stiffness_N_per_mm':cables['stiffness_N_per_mm']})
        cables['available_policy']='Positive-terminal neutral path +0.5mm; winding and terminal geometry counted once'
    return {'legs': states, 'tendons': cables, 'wheel_angle_rad': wheel_angle,
            'provenance': 'DESIGN_ASSUMPTION prescribed demonstration',
            'loaded_equilibrium': False, 'ankle_closure': 'qa=-qk'}


def cable_moment_arms(route):
    """Analytic -d(path)/d(qh,qk) in mm/rad on the retained CW branch.

    A is the ankle pivot. The 1.5mm constant radial eye offset subtracts a
    constant from the final straight span, so it does not change derivatives.
    Tangency makes intermediate contact derivatives cancel (virtual work).
    """
    g=route['geometry']; A=g['A']; H=g['H']; K=g['K']
    final=route['primitives'][-1]
    span=tuple(b-a for a,b in zip(final['start'],final['end']))
    length=math.sqrt(sum(v*v for v in span))
    if length<=0:raise ValueError('Degenerate final cable span')
    ux,uz=span[0]/length,span[2]/length
    return {'qh':-(ux*-(A[1]-H[1])+uz*(A[0]-H[0])),
            'qk':-(ux*-(A[1]-K[1])+uz*(A[0]-K[0])),
            'wheel_dpath_du_mm_per_rad':route['wheel']['pitch_radius_mm']}


def _handled(name, m):
    if m['kind'].startswith('tendon_r03_'):
        return True
    return m['kind']=='torso_r04_rigid' and ('wheel_angle_rad' in m or
            m.get('component') in COUPLING_COMPONENTS | ORBITING_WHEEL_COMPONENTS or
            name.endswith(('_AnkleEye','_AnkleSpacer','_AnkleGrub')))


class _ReadOnlyFacade:
    def __init__(self, doc, motion):
        self._doc = doc
        original = doc.getObject('PoseController')
        values = {key: getattr(original,key) for key in original.PropertiesList}
        values['MotionMap'] = json.dumps(motion)
        values['PropertiesList'] = list(original.PropertiesList)
        self._controller = SimpleNamespace(**values)
        self.Objects = doc.Objects
    def getObject(self, name):
        return self._controller if name=='PoseController' else self._doc.getObject(name)


def _canonical_angles(tags, angles):
    result = {}
    for tag, (kind, side) in tags.items():
        standard = ('hind' if kind=='hind' else 'fore') + ('L' if side==1 else 'R')
        if standard in result:
            raise ValueError('Duplicate leg identity: '+standard)
        result[standard] = angles[tag]
    if len(result)!=4:
        raise ValueError('Expected exactly four standard leg identities')
    return result


def descriptor(doc, theta=0., leg_angles=None, wheel_angle=None, config=None):
    """Return all source-local placements and length-dependent shape requests.

    Does not generate shapes or change the document. leg_angles uses actual
    MotionMap tags (the current assembly uses foreL/foreR/hindL/hindR).
    Every removed rigid tendon member must be identified by supported component
    or AnkleEye/AnkleSpacer suffix, otherwise this fails closed.
    """
    import FreeCAD as App
    controller=doc.getObject('PoseController')
    if controller is None:raise ValueError('PoseController missing')
    if config is None and 'PrescribedMotionConfigR07' in controller.PropertiesList:
        config=json.loads(controller.PrescribedMotionConfigR07)
    config = _assembly(config)
    if wheel_angle is None:
        wheel_angle=float(getattr(controller,'WheelAngleR07',0.))
    original = json.loads(controller.MotionMap)
    tags, angles, changed = pose._angles(original, doc.getObject('PoseController'), leg_angles)
    terminal_flags=[bool(m.get('route_local',{}).get('r07_positive_terminals'))
                    for m in original.values() if m['kind']=='tendon_r03_cable']
    if len(terminal_flags)!=2 or len(set(terminal_flags))!=1:
        raise ValueError('Expected two branches with consistent termination topology')
    state = pose_states(_canonical_angles(tags, angles), wheel_angle, config,
                        positive_terminals=terminal_flags[0])
    removed = {n:m for n,m in original.items() if _handled(n,m)}
    facade = _ReadOnlyFacade(doc, {n:m for n,m in original.items() if n not in removed})
    placements, _, _, springs, guides, _ = pose._plan(facade, theta, leg_angles)
    rows = pose._spring_lengths(doc, springs)
    requests = {}
    warnings = []
    for name, m, src, length, free, mismatch in rows:
        # spring_wire_r03 rejects closed/touching extension turns explicitly.
        if m['spring']=='extension' and length <= free:
            raise ValueError(name+': extension spring requires open coils above free length')
        if m['spring']=='compression' and length < 8:
            raise ValueError(name+': below assumed solid+margin of 8mm')
        if mismatch:
            requests[name] = {'generator':'spring', 'length_mm':length,
                              'kind':m['spring'], 'free_length_mm':free}
    for name,m,gap in guides:
        partners = [d for n,d,v in guides if d['tag']==m['tag'] and n!=name]
        if len(partners)!=1:
            raise ValueError('Compression guide pair incomplete: '+name)
        overlap = m['length']+partners[0]['length']-gap
        if gap<m['length'] or overlap<=0:
            warnings.append({'instance':name,'gap_mm':gap,'overlap_mm':overlap})
    p = pose._parameters(doc)
    E = __import__('kinematics').spine(theta,p)['E1']
    a = pose.torso_angle(theta, 'hind', p)
    parent = App.Rotation(App.Vector(0,-1,0), math.degrees(a))
    V = lambda xyz: App.Vector(*xyz)
    routes = {s:state['tendons']['branches'][s]['route'] for s in (-1,1)}
    expected_wheel = config['parameters']['wheel_axle_x_local_mm']
    for name, source in removed.items():
        m = dict(source)
        kind = m['kind']
        if kind=='tendon_r03_wheel':
            if abs(m['center'][0]-expected_wheel)>1e-9:
                raise ValueError('Wheel descriptor differs from authoritative assembly parameters')
            m['angle_rad'] = wheel_angle
            placements[name] = pose._tendon_placement(App,m,E,a)
        elif kind=='tendon_r03_guide':
            frame = routes[m['side']][m['guide']]
            # Positive winding preserves the fixed physical guide frames.
            axis_error = min(math.dist(frame['axis'],m['axis']), math.dist(tuple(-x for x in frame['axis']),m['axis']))
            # Guide circle axes may be antiparallel; retain captured journal direction.
            if math.dist(frame['center'],m['center'])>1e-7 or axis_error>1e-7:
                raise ValueError(name+': route requires moving fixed guide; unsupported hardware state')
            placements[name] = pose._tendon_placement(App,m,E,a)
        elif kind=='tendon_r03_cable':
            if not m.get('rebuild_from_route'):
                raise ValueError('Cable lacks route regeneration contract: '+name)
            requests[name] = {'generator':'cable','route':routes[m['side']]}
            placements[name] = pose._tendon_placement(App,m,E,a)
        elif m.get('component') in ORBITING_WHEEL_COMPONENTS:
            data=json.loads(m['local_placement_json']);W=m['wheel_center']
            if math.dist(W,(expected_wheel,0.,0.))>1e-9:
                raise ValueError('Orbiting clamp wheel datum differs from assembly')
            rotation=App.Rotation(V((1,0,0)),math.degrees(wheel_angle-m.get('wheel_angle_rad',0.)))
            base=V(W)+rotation.multVec(V(data['base_xyz_mm'])-V(W))
            local_rotation=rotation.multiply(App.Rotation(*data['rotation_xyzw']))
            placements[name]=App.Placement(V(pose._world_tendon_point(E,a,tuple(base))),
                                            parent.multiply(local_rotation))
        elif m.get('component') in COUPLING_COMPONENTS:
            data = json.loads(m['local_placement_json'])
            rotation = App.Rotation(V((1,0,0)),math.degrees(wheel_angle-m.get('wheel_angle_rad',0.)))
            local = App.Rotation(*data['rotation_xyzw'])
            placements[name] = App.Placement(V(pose._world_tendon_point(E,a,data['base_xyz_mm'])),
                                              parent.multiply(rotation.multiply(local)))
        elif name.endswith(('_AnkleEye','_AnkleSpacer','_AnkleGrub')):
            side = 1 if '_L_' in name else -1 if '_R_' in name else None
            if side is None:
                raise ValueError('Unrecognized ankle attachment side: '+name)
            route = routes[side]
            captured_routes=[d['route_local'] for d in original.values()
                             if d['kind']=='tendon_r03_cable' and d['side']==side]
            if len(captured_routes)!=1:
                raise ValueError('Expected one captured route for ankle attachment')
            reference=captured_routes[0]
            oldA=reference['geometry']['A']; newA=route['geometry']['A']
            def incoming(r):
                start=r['primitives'][-1]['start']; A=r['geometry']['A']
                return math.atan2(start[2]-A[1],start[0]-A[0])
            delta=incoming(route)-incoming(reference)
            data=json.loads(m['local_placement_json'])
            captured=data['base_xyz_mm']
            x,z=pose._transform(newA,delta,(captured[0]-oldA[0],captured[2]-oldA[1]))
            rotation=App.Rotation(App.Vector(0,-1,0),math.degrees(delta))
            local=App.Placement(V((x,captured[1],z)),rotation.multiply(App.Rotation(*data['rotation_xyzw'])))
            placements[name] = App.Placement(V(pose._world_tendon_point(E,a,tuple(local.Base))),
                                              parent.multiply(local.Rotation))
        else:
            raise ValueError('Unhandled dynamic tendon attachment: '+name)
    return {'placements':placements, 'shape_requests':requests, 'state':state,
            'leg_angles_rad':angles, 'changed_leg_tags':sorted(changed),
            'guide_warnings':warnings, 'theta_rad':float(theta),'configuration':config,
            'limits':'Prescribed geometry only; candidate ranges require native collision checks; no load/equilibrium/fabrication claim.'}


def _spring_source(request):
    """Exact requested native wire; immutable qualified compression cache only."""
    if request['kind'] == 'extension':
        from spring_wire_r03 import shape
        return shape(request['length_mm'], request['free_length_mm'])
    if request['kind'] != 'compression':
        raise ValueError('Unsupported spring kind')
    import hashlib
    import Part
    from compression_spring_r07 import shape, validate, source_hash
    length = float(request['length_mm'])
    folder = ROOT / 'reports/tmp/spring_kernel_escalation/qualified_shapes'
    fingerprint = source_hash()
    key = length.hex() + '_' + fingerprint
    path = folder / (key + '.brep')
    sidecar = folder / (key + '.json')
    if path.exists() and sidecar.exists():
        record = json.loads(sidecar.read_text())
        if (record['generator_source_sha256'] != fingerprint or
                record['length_hex'] != length.hex() or
                record['brep_sha256'] != hashlib.sha256(path.read_bytes()).hexdigest()):
            raise RuntimeError('Qualified compression cache hash mismatch')
        native = Part.Shape()
        native.read(str(path))
        return validate(native, length, False)
    return shape(length, request['free_length_mm'])


def regenerate_sources(plan, cache=None):
    """Build private LOCAL shapes for shape_requests, without document writes.

    Lead may attach each returned shape to a private per-instance source and
    use plan['placements'][name] for its link. Shared library definitions must
    not be overwritten. Optional caller-owned cache stores exact request keys;
    every returned shape is copied, so callers cannot change cached geometry.
    """
    from build_tendon_r03 import cable_shape
    result = {}
    for name,request in plan['shape_requests'].items():
        key = json.dumps(request,sort_keys=True,allow_nan=False)
        if cache is not None and key in cache:
            shape = cache[key].copy()
        else:
            if request['generator']=='spring':
                shape = _spring_source(request)
            elif request['generator']=='cable':
                shape = cable_shape(request['route'])
            else:
                raise ValueError('Unknown shape generator: '+str(request['generator']))
            if not shape.isValid() or len(shape.Solids)!=1:
                raise ValueError('Regenerated source is not valid single solid: '+name)
            if cache is not None:cache[key]=shape.copy()
        result[name]=shape
    return result


def copied_shapes(doc, theta=0., leg_angles=None, wheel_angle=None, config=None, cache=None):
    """Return private WORLD TopoShape copies, safely regenerating coils/cables.

    Safe lead adapter: assign regenerated LOCAL shape to private source only,
    and its matching descriptor placement to instance. Never assign world shape
    to an App::Link source and then also apply the placement (double transform).
    This function returns world shapes exclusively for read-only validation.
    """
    plan = descriptor(doc,theta,leg_angles,wheel_angle,config)
    regenerated = regenerate_sources(plan,cache)
    shapes = {}
    for name, placement in plan['placements'].items():
        obj = doc.getObject(name)
        request = plan['shape_requests'].get(name)
        if request:
            shape = regenerated[name]
            shape.Placement = placement.multiply(shape.Placement)
        else:
            # Native linked source may have its own nonidentity Placement.
            shape = obj.Shape.copy()
            shape.Placement = placement.multiply(obj.LinkPlacement.inverse()).multiply(shape.Placement)
        if not shape.isValid() or len(shape.Solids)!=1:
            raise ValueError('Invalid source/placed shape: '+name)
        shapes[name] = shape
    return shapes, plan


def _inclusive(lo,hi,step):
    if not math.isfinite(step) or step<=0:
        raise ValueError('step_deg must be positive finite')
    return [lo+i*step for i in range(int(math.ceil((hi-lo)/step)))]+[hi]


def sample_states(step_deg=1., excursion_deg=15.):
    """One-coordinate ranges plus both directions of coordinated/asymmetric legs.

    Endpoints always included. This covers each coordinate over its interval,
    NOT every point in the full 10D spine/leg/wheel product. Theta is supplied
    separately to validate_native. Pure math_grid validates per-leg 2D grids.
    """
    excursion_deg=float(excursion_deg)
    if not math.isfinite(excursion_deg) or not 0<excursion_deg<=15:
        raise ValueError('excursion_deg must be in (0,15]')
    neutral = {tag:(leg_geometry(kind)['thigh_angle_rad'],leg_geometry(kind)['passive_knee_rad'])
               for tag,kind in (('foreL','fore'),('foreR','fore'),('hindL','hind'),('hindR','hind'))}
    yield {'label':'neutral','leg_angles':dict(neutral),'wheel_angle':0.}
    for tag, pair in neutral.items():
        kind = 'hind' if tag.startswith('hind') else 'fore'
        for coordinate,index in (('qh',0),('qk',1)):
            for degree in _inclusive(math.degrees(pair[index])-excursion_deg,math.degrees(pair[index])+excursion_deg,step_deg):
                angles = dict(neutral); q=list(pair);q[index]=math.radians(degree);angles[tag]=tuple(q)
                yield {'label':tag+'_'+coordinate+'_'+str(degree),'leg_angles':angles,'wheel_angle':0.}
    for degrees in _inclusive(0.,90.,step_deg):
        yield {'label':'wheel_'+str(degrees),'leg_angles':dict(neutral),'wheel_angle':math.radians(degrees)}
    for direction in (-1,1):
        for degrees in _inclusive(-excursion_deg,excursion_deg,step_deg):
            angles = {tag:(pair[0]+math.radians(degrees), pair[1]+math.radians(direction*degrees))
                      for tag,pair in neutral.items()}
            yield {'label':'coordinated_'+str(direction)+'_'+str(degrees),
                   'leg_angles':angles,'wheel_angle':math.radians(90*(degrees+excursion_deg)/(2*excursion_deg))}
            asymmetric = dict(angles)
            asymmetric['hindR'] = (neutral['hindR'][0]-math.radians(degrees),
                                    neutral['hindR'][1]-math.radians(direction*degrees))
            yield {'label':'asymmetric_'+str(direction)+'_'+str(degrees),
                   'leg_angles':asymmetric,'wheel_angle':math.radians(90*(degrees+excursion_deg)/(2*excursion_deg))}


def math_grid(step_deg=1., config=None):
    """Exhaust all independent 2D leg grids; wheel 0/45/90 on both routes.

    Closure, full FK, spring geometry, tangent continuity and derivatives are
    mathematical checks. Does not claim finite wire/solid or assembly clearance.
    """
    report = {'status':'PASS','step_deg':step_deg,'provenance':'DESIGN_ASSUMPTION candidate intervals',
              'limits_deg':CANDIDATE_LIMITS_DEG,'samples':0,'max_closure_mm':0.,
              'max_fk_mm':0.,'max_tangency_error':0.,'max_route_join_mm':0.,
              'max_route_derivative_mm_per_rad_error':0.,'max_joint_moment_arm_fd_error_mm':0.,'spring_lengths_mm':{},
              'cable_path_mm':{},'loaded_equilibrium':False,'native_collision':'NOT_RUN'}
    for kind in ('fore','hind'):
        spans = {s:[math.inf,-math.inf] for s in ('extension','compression')}
        cable_span = [math.inf,-math.inf]
        for hd in _inclusive(*CANDIDATE_LIMITS_DEG[kind]['qh'],step_deg):
            for kd in _inclusive(*CANDIDATE_LIMITS_DEG[kind]['qk'],step_deg):
                h,k = math.radians(hd),math.radians(kd)
                g = leg_geometry(kind,h,k);report['samples']+=1
                report['max_closure_mm']=max(report['max_closure_mm'],*g['loop_residuals_mm'].values())
                a1,a2,a3=(g['lengths_mm'][a] for a in ('a1','a2','a3'))
                F=(g['H'][0]+(a1+a3)*math.cos(h)+a2*math.cos(h+k),
                   g['H'][1]+(a1+a3)*math.sin(h)+a2*math.sin(h+k))
                report['max_fk_mm']=max(report['max_fk_mm'],math.dist(F,g['F']))
                if abs(g['qa_rad']+k)>1e-12:raise AssertionError('Ankle closure')
                for s,L in g['spring_lengths_mm'].items():
                    spans[s][0]=min(spans[s][0],L);spans[s][1]=max(spans[s][1],L)
                if kind=='hind':
                    for side in (-1,1):
                        opts = _route_options(_assembly(config))
                        routes = [tendon_route(side,u,h,k,**opts) for u in (0,math.pi/4,math.pi/2)]
                        for r in routes:
                            cable_span[0]=min(cable_span[0],r['length_mm']);cable_span[1]=max(cable_span[1],r['length_mm'])
                            report['max_tangency_error']=max(report['max_tangency_error'],*r['tangency_errors'].values())
                            for A,B in zip(r['primitives'],r['primitives'][1:]):
                                report['max_route_join_mm']=max(report['max_route_join_mm'],math.dist(A['end'],B['start']))
                        analytic=cable_moment_arms(routes[0])
                        epsilon=1e-6
                        for coordinate in ('qh','qk'):
                            dh=epsilon if coordinate=='qh' else 0
                            dk=epsilon if coordinate=='qk' else 0
                            plus=tendon_route(side,0,h+dh,k+dk,**opts)['length_mm']
                            minus=tendon_route(side,0,h-dh,k-dk,**opts)['length_mm']
                            error=abs(analytic[coordinate]+(plus-minus)/(2*epsilon))
                            report['max_joint_moment_arm_fd_error_mm']=max(report['max_joint_moment_arm_fd_error_mm'],error)
                        # Wheel derivative must be +R; no double take-up counting.
                        numerical=(routes[2]['length_mm']-routes[0]['length_mm'])/(math.pi/2)
                        report['max_route_derivative_mm_per_rad_error']=max(report['max_route_derivative_mm_per_rad_error'],abs(numerical-5.5))
        report['spring_lengths_mm'][kind]=spans
        if kind=='hind':report['cable_path_mm'][kind]=cable_span
    if max(report['max_closure_mm'],report['max_fk_mm'],report['max_route_join_mm'])>1e-8 or report['max_tangency_error']>1e-7 or report['max_route_derivative_mm_per_rad_error']>1e-8 or report['max_joint_moment_arm_fd_error_mm']>1e-6:
        report['status']='FAIL'
    return report


def validate_native(doc, samples=None, phases=(0.,), step_deg=1., output=None):
    """OCC broadphase/common on cloned actual native shapes; no fit exceptions.

    Checks all pairs whose relative motion may change, including same-torso
    pairs. At first sample checks every pair to establish raw baseline. Later
    samples skip a pair ONLY when both world shape bounds and placements are
    exactly unchanged from baseline; cable/spring regenerated pairs never skip.
    Outputs raw baseline and new/worsened intersections, not a clearance pass
    obtained by hiding designed bearing fits. Surface contact has zero volume.
    phases are radians; caller must declare intended spine/leg combined scope.
    """
    from sweep_robot_r03 import _bounds, _overlap
    import time
    start=time.monotonic()
    samples_generated=samples is None
    samples=list(sample_states(step_deg) if samples_generated else samples)
    phases=tuple(float(p) for p in phases)
    if not phases or not all(math.isfinite(p) for p in phases):
        raise ValueError('Finite nonempty phases required')
    report={'status':'RUNNING','step_deg':step_deg if samples_generated else None,'phase_values_rad':phases,
            'samples_total':len(samples)*len(phases),'samples_completed':0,'sample_definitions':samples,
            'instances':0,'bbox_candidates':0,'occ_checks':0,'baseline_overlaps':[],
            'new_or_worsened_overlaps':[],'errors':[],'guide_warnings':[],
            'scope':'Cloned native sources; prescribed sampled ranges; raw volume >1e-5mm3',
            'continuous_clearance':False,'loaded_equilibrium':False,'fabrication_release':False}
    original_map=doc.PoseController.MotionMap
    original_links={o.Name:tuple(o.LinkPlacement.toMatrix().A) for o in doc.Objects if o.TypeId=='App::Link'}
    baseline={};worst={};initial_bounds={};initial_places={};shape_cache={}
    try:
        for phase in phases:
            for sample in samples:
                shapes,plan=copied_shapes(doc,phase,sample['leg_angles'],sample['wheel_angle'],cache=shape_cache)
                names=sorted(shapes);bounds={n:_bounds(shapes[n]) for n in names}
                places={n:tuple(plan['placements'][n].toMatrix().A) for n in names}
                first=report['samples_completed']==0
                dynamic=set(plan['shape_requests'])
                report['instances']=len(names)
                for i,A in enumerate(names):
                    for B in names[i+1:]:
                        if not _overlap(bounds[A],bounds[B]):continue
                        if not first and A not in dynamic and B not in dynamic and all(bounds[n]==initial_bounds[n] and places[n]==initial_places[n] for n in (A,B)):
                            continue
                        report['bbox_candidates']+=1;report['occ_checks']+=1
                        volume=shapes[A].common(shapes[B]).Volume
                        if volume<=1e-5:continue
                        pair=(A,B)
                        row={'a':A,'b':B,'intersection_mm3':float(volume),'sample':sample['label'],
                             'spine_phase_rad':phase,'wheel_angle_rad':sample['wheel_angle'],
                             'leg_angles_rad':sample['leg_angles']}
                        if first:baseline[pair]=row
                        elif volume>baseline.get(pair,{}).get('intersection_mm3',0)+1e-5:
                            if volume>worst.get(pair,{}).get('intersection_mm3',0):worst[pair]=row
                if first:initial_bounds=bounds;initial_places=places
                report['samples_completed']+=1
                report['guide_warnings'].extend(dict(w,sample=sample['label']) for w in plan['guide_warnings'])
                if output:
                    report['baseline_overlaps']=list(baseline.values())
                    report['new_or_worsened_overlaps']=sorted(worst.values(),key=lambda r:-r['intersection_mm3'])
                    Path(output).write_text(json.dumps(dict(report,elapsed_seconds=time.monotonic()-start),indent=2)+'\n')
        report['status']='COLLISIONS_FOUND' if worst else 'SAMPLED_NO_NEW_RAW_OVERLAPS'
    except Exception as error:
        report['status']='ERROR';report['errors'].append({'error':repr(error),'sample':sample,'phase_rad':phase})
    report['baseline_overlaps']=list(baseline.values())
    report['new_or_worsened_overlaps']=sorted(worst.values(),key=lambda r:-r['intersection_mm3'])
    report['elapsed_seconds']=time.monotonic()-start
    report['document_unchanged']=(doc.PoseController.MotionMap==original_map and original_links=={o.Name:tuple(o.LinkPlacement.toMatrix().A) for o in doc.Objects if o.TypeId=='App::Link'})
    if not report['document_unchanged']:raise AssertionError('Read-only motion adapter changed document')
    if output:Path(output).write_text(json.dumps(report,indent=2)+'\n')
    return report


def apply_prescribed_pose(doc, theta=0., leg_angles=None, wheel_angle=None, config=None):
    """Lead-only live adapter: transactional private-source pose, NEVER saves.

    All geometry is prepared/validated before opening the transaction. Shared
    source definitions remain unchanged. Original neutral MotionMap attachment
    datums remain the reference; LegAnglesR03 and WheelAngleR07 store the pose.
    This is commanded geometry, not spring/cable equilibrium or safe operation.
    Caller must pass the reviewed assembly config for revised eye geometry.
    """
    import cad_common as cc
    plan=descriptor(doc,theta,leg_angles,wheel_angle,config)
    sources=regenerate_sources(plan)
    before_sources={name:doc.getObject(name).LinkedObject for name in sources}
    doc.openTransaction('r07 prescribed leg and tendon pose')
    try:
        library=doc.getObject('PartsLibrary')
        for name,shape in sources.items():
            old=before_sources[name];request=plan['shape_requests'][name]
            users=[o for o in doc.Objects if o.TypeId=='App::Link' and o.LinkedObject==old]
            private=(getattr(old,'PoseGeneratedInstanceR07',None)==name and len(users)==1)
            if private:
                source=old
            else:
                root=getattr(old,'PoseGeneratedRootR07',old.Name)
                source=doc.addObject('PartDesign::Feature',root+'_PoseR07')
                cc.metadata(source,old.PartNumber,old.MaterialName,old.Process,
                            role=getattr(old,'Role','SPRING' if request['generator']=='spring' else 'CABLE'))
                source.Revision='r07'
                for key in ('FreeLength_mm','AnchorFreeLength_mm','SeatInset_mm','WireDiameter_mm','OuterDiameter_mm'):
                    if key in old.PropertiesList:
                        source.addProperty('App::PropertyLength',key,'MotionR07')
                        setattr(source,key,pose._number(getattr(old,key)))
                for key,value in (('PoseGeneratedInstanceR07',name),('PoseGeneratedRootR07',root),
                                  ('Provenance','DESIGN_ASSUMPTION prescribed geometry')):
                    source.addProperty('App::PropertyString',key,'MotionR07');setattr(source,key,value)
                if library is not None:library.addObject(source)
                doc.getObject(name).setLink(source)
            source.Shape=shape
            if request['generator']=='spring':
                if 'InstalledCoilLength_mm' not in source.PropertiesList:
                    source.addProperty('App::PropertyLength','InstalledCoilLength_mm','MotionR07')
                source.InstalledCoilLength_mm=request['length_mm']
            source.Visibility=False
        for name,placement in plan['placements'].items():
            doc.getObject(name).LinkPlacement=placement
        controller=doc.getObject('PoseController')
        for key,typ in (('LegAnglesR03','App::PropertyString'),('WheelAngleR07','App::PropertyFloat'),
                        ('PrescribedMotionConfigR07','App::PropertyString')):
            if key not in controller.PropertiesList:controller.addProperty(typ,key,'MotionR07')
        controller.LegAnglesR03=json.dumps(plan['leg_angles_rad'])
        controller.WheelAngleR07=float(plan['state']['wheel_angle_rad'])
        controller.PrescribedMotionConfigR07=json.dumps(plan['configuration'])
        controller.SpinePhaseRad=float(theta)
        doc.recompute()
        if any(not doc.getObject(n).Shape.isValid() or len(doc.getObject(n).Shape.Solids)!=1
               for n in plan['placements']):
            raise RuntimeError('Recomputed prescribed pose contains invalid/multisolid source')
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction();raise
    return {'placements':len(plan['placements']),'regenerated_sources':sorted(sources),
            'leg_angles_rad':plan['leg_angles_rad'],'wheel_angle_rad':float(plan['state']['wheel_angle_rad']),
            'spine_phase_rad':float(theta),'guide_warnings':plan['guide_warnings'],
            'loaded_equilibrium':False,'saved':False,'fabrication_release':False}
