"""Read-only AX0/AX1 numeric handoff from the authoritative CAD motion APIs.

No mesh/Blender export, document mutation, save, clearance campaign or loaded
motion prediction. App::Link names are stable IDs; label/order changes do not
change identity. Unknown motion, non-unit scaling or unresolved grounding fails.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TAGS = ('foreL', 'foreR', 'hindL', 'hindR')
COMMANDS = ('spine_phase', 'foreL_hip', 'foreR_hip', 'hindL_hip', 'hindR_hip', 'hind_wheel')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def serial(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':')).encode()


def shape_hash(shape):
    value = shape.exportBrepToString()
    return digest(value.encode() if isinstance(value, str) else value)


def matrix(placement):
    values = list(placement.toMatrix().A)
    return [values[i:i+4] for i in range(0, 16, 4)]


def apply(matrix_value, point):
    return [sum(matrix_value[i][j]*point[j] for j in range(3))+matrix_value[i][3] for i in range(3)]


def snapshot(doc):
    return {'objects': [o.Name for o in doc.Objects],
            'controller': {p: str(getattr(doc.PoseController, p)) for p in
                           ('MotionMap', 'SpinePhaseRad', 'LegAnglesR03', 'WheelAngleR07')},
            'links': {o.Name: {'source': o.LinkedObject.Name, 'matrix': matrix(o.LinkPlacement),
                              'source_hash': shape_hash(o.LinkedObject.Shape)}
                      for o in doc.Objects if o.TypeId == 'App::Link'}}


def _group(name, motion, role):
    if motion.get('tag'):
        return motion['tag']
    if motion.get('torso'):
        return 'torso:' + motion['torso']
    if motion['kind'].startswith('tendon'):
        return 'hind_tendon'
    if 'CONTROLLER' in role or 'OpenRB' in name or 'Controller' in name:
        return 'controller'
    return 'spine'


def _spring_record(doc, name, m, plan, frame_id):
    import FreeCAD as App
    import robot_pose_r03 as pose
    from kinematics import spine
    g = plan['state']['legs'][m['tag']]['geometry']
    torso = m['leg_type']; k = 1 if torso == 'hind' else 2
    E = spine(plan['theta_rad'], pose._parameters(doc))['E'+str(k)]
    angle = pose.torso_angle(plan['theta_rad'], torso, pose._parameters(doc))
    anchors = []
    owners = {'thigh': '_thigh', 'shank': '_shank', 'foot': '_Foot', 'motor_horn': '_InputHorn'}
    for joint in (m['a'], m['b']):
        x, z = pose._transform(E, angle, g[joint])
        world = App.Vector(x, m['y'], z)
        owner = m['tag'] + owners[g['owning_body'][joint]]
        assert doc.getObject(owner) is not None, 'Unresolved spring owner: '+owner
        local = plan['placements'][owner].inverse().multVec(world)
        anchors.append({'name': joint, 'owner_instance_id': 'instance:'+owner,
                        'owner_local_mm': list(local), 'world_mm': list(world)})
    a, b = [q['world_mm'] for q in anchors]
    span = math.dist(a, b); axis = [(y-x)/span for x, y in zip(a, b)]
    inset = float(m['seat_offset_mm']); length = span-2*inset
    seats = [[a[i]+inset*axis[i] for i in range(3)], [b[i]-inset*axis[i] for i in range(3)]]
    src = doc.getObject(name).LinkedObject
    free = pose._number(getattr(src, 'FreeLength_mm', m['free_length_mm']))
    return {'instance_id': 'instance:'+name, 'frame_id': frame_id, 'generator': 'spring',
            'kind': m['spring'], 'anchors': anchors, 'coil_seats_world_mm': seats,
            'axis_world': axis, 'coil_length_mm': length, 'free_length_mm': free,
            'generator_module': 'spring_wire_r03' if m['spring']=='extension' else 'compression_spring_r07',
            'turn_policy': 'authoritative generator; no affine mesh stretch',
            'force_state': 'NOT_SOLVED', 'regeneration_required': name in plan['shape_requests']}


def _cable_record(name, m, plan, frame_id):
    import FreeCAD as App
    route = plan['state']['tendons']['branches'][m['side']]['route']
    parent = plan['placements'][name]
    primitives = []
    for item in route['primitives']:
        row = dict(item)
        for field in ('start', 'end', 'mid', 'center'):
            if field in item:
                row[field+'_world_mm'] = list(parent.multVec(App.Vector(*item[field])))
        if 'axis' in item:
            row['axis_world'] = list(parent.Rotation.multVec(App.Vector(*item['axis'])))
        primitives.append(row)
    tag = 'hindL' if m['side']==1 else 'hindR'
    owner = 'HindTendon_'+('L' if m['side']==1 else 'R')+'_AnkleEye'
    end = parent.multVec(App.Vector(*route['primitives'][-1]['end']))
    local = plan['placements'][owner].inverse().multVec(end)
    prefix = 'HindTendon_'+('L' if m['side']==1 else 'R')
    owner_anchors = []
    endpoints = [('wheel_terminal',prefix+'_WheelClamp',route['primitives'][0]['start']),
                 ('shell_entry',prefix+'_shell_guide_Shaft',route['shell_guide']['entry']),
                 ('shell_exit',prefix+'_shell_guide_Shaft',route['shell_guide']['exit']),
                 ('hip_entry',prefix+'_hip_guide_Shaft',route['hip_guide']['entry']),
                 ('hip_exit',prefix+'_hip_guide_Shaft',route['hip_guide']['exit']),
                 ('ankle_terminal',owner,route['primitives'][-1]['end'])]
    for label, body, point in endpoints:
        world = parent.multVec(App.Vector(*point))
        body_local = plan['placements'][body].inverse().multVec(world)
        owner_anchors.append({'name':label,'owner_instance_id':'instance:'+body,
                              'owner_local_mm':list(body_local),'world_mm':list(world)})
    return {'instance_id':'instance:'+name, 'frame_id':frame_id, 'generator':'cable',
            'generator_module':'build_tendon_r03.cable_shape', 'parent_frame':'torso:hind',
            'route_local_mm':route, 'primitives':primitives, 'route_length_mm':route['length_mm'],
            'ankle_anchor':{'owner_instance_id':'instance:'+owner,'owner_local_mm':list(local),'world_mm':list(end)},
            'owner_anchors':owner_anchors,
            'state':plan['state']['tendons']['branches'][m['side']]['state'],
            'state_provenance':'PROVISIONAL_2_N_PER_MM_LAW_AT_PRESCRIBED_KNEE; NOT_LOADED_EQUILIBRIUM',
            'leg_tag':tag, 'regeneration_required':True}


def run(doc, output=None):
    import FreeCAD as App
    import Part
    import leg_motion_r07 as motion_api
    import robot_pose_r03 as pose
    from animation_manifest_validate import validate_manifest
    from kinematics import spine, residuals

    native = Path(doc.FileName).resolve()
    assert native.is_file() and native.is_relative_to(ROOT)
    revision = native.stem.removeprefix('flexor_').removesuffix('_robot')
    native_sha = digest(native.read_bytes())
    controller = doc.PoseController
    original_motion = json.loads(controller.MotionMap)
    links = sorted([o for o in doc.Objects if o.TypeId=='App::Link'], key=lambda o:o.Name)
    assert links and set(original_motion) <= {o.Name for o in links}
    assert not ({d['kind'] for d in original_motion.values()} - pose.KINDS)
    # Grounding is a reviewed explicit supplement to the historical sparse map.
    grounding_path = ROOT/'animation/schema'/('grounded_instances_'+revision+'.json')
    grounding = json.loads(grounding_path.read_text())
    absent = sorted(o.Name for o in links if o.Name not in original_motion)
    assert grounding['cad_sha256']==native_sha and grounding['grounded_names']==absent, 'Grounding audit stale'
    effective = dict(original_motion)
    effective.update({n:{'kind':'fixed','grounding':'reviewed lumbar datum'} for n in absent})
    before = snapshot(doc)
    meshes = {}; instances = []
    for obj in links:
        src = obj.LinkedObject; m = effective[obj.Name]
        assert not obj.LinkTransform and src.Placement.isIdentity(), 'Unhandled source/link transform composition'
        assert all(abs(float(getattr(obj,key,1.))-1.)<1e-12 for key in ('Scale',)), 'Unhandled instance scale'
        assert src.Shape.Placement.isIdentity(), 'Unhandled shape-local placement'
        mesh_id = 'mesh:'+src.Name
        meshes[mesh_id] = {'mesh_id':mesh_id,'local_units':'mm','geometry_hash':shape_hash(src.Shape),
                           'asset_status':'NOT_EXPORTED_AX01','local_geometry_status':'native source-local BREP; no tessellation'}
        procedural = m['kind'] in ('leg_r02_spring','tendon_r03_cable')
        directly_driven = m['kind'] in ('axialrot','tendon_r03_wheel','leg_r02_body_axial') or obj.Name.endswith('_InputHorn')
        classification = 'fixed' if m['kind']=='fixed' else 'active' if directly_driven else 'passive'
        instances.append({'instance_id':'instance:'+obj.Name,'freecad_object_name':obj.Name,
                          'source_object_name':src.Name,'part_number':str(src.PartNumber), 'mesh_id':mesh_id,
                          'group':_group(obj.Name,m,str(getattr(src,'Role',''))), 'motion_kind':m['kind'],
                          'geometry_kind':'length_route_dependent' if procedural else 'rigid',
                          'classification':classification,'local_frame':'source:'+src.Name})
    p = pose._parameters(doc)
    neutral = json.loads(controller.LegAnglesR03)
    samples = [('neutral_v1',0.,neutral,0.), ('smoke_1',math.pi/3,
                {t:[q[0]+math.radians(2),q[1]-math.radians(2)] for t,q in neutral.items()},math.radians(5)),
               ('smoke_2',4*math.pi/3,
                {t:[q[0]+math.radians(-2 if t.endswith('L') else 2),
                    q[1]+math.radians(2 if t.endswith('L') else -2)] for t,q in neutral.items()},math.radians(10))]
    frames = []; checks = []; previous = None; cache = {}
    for index, (frame_id, theta, angles, wheel) in enumerate(samples):
        shapes, plan = motion_api.copied_shapes(doc,theta,angles,wheel,cache=cache)
        regenerated = motion_api.regenerate_sources(plan,cache)
        assert set(shapes)==set(plan['placements'])=={o.Name for o in links}
        mm = []; metres = []; quats = []; procedural = []
        max_error = 0.; neutral_error = 0.; points = 0; axis_error = 0.; axis_angle_error = 0.; state = spine(theta,p)
        for i,obj in enumerate(links):
            placement = plan['placements'][obj.Name]
            M = matrix(placement); B = [row[:] for row in M]
            for k in range(3): B[k][3] *= .001
            mm.append(M); metres.append(B)
            qx,qy,qz,qw = placement.Rotation.Q
            quat = [qw,qx,qy,qz]; norm=math.sqrt(sum(q*q for q in quat));quat=[q/norm for q in quat]
            if previous is not None and sum(a*b for a,b in zip(quat,previous[i]))<0:quat=[-q for q in quat]
            quats.append(quat)
            local = regenerated.get(obj.Name,obj.LinkedObject.Shape)
            assert local.isValid() and len(local.Solids)==1
            expected = shapes[obj.Name]
            assert len(local.Vertexes)==len(expected.Vertexes)
            for v,w in zip(local.Vertexes,expected.Vertexes):
                world = apply(M,list(v.Point)); metres_back=[x*1000 for x in apply(B,[x*.001 for x in v.Point])]
                max_error=max(max_error,math.dist(world,tuple(w.Point)),math.dist(metres_back,tuple(w.Point)));points+=1
            if index==0:
                assert len(expected.Vertexes)==len(obj.Shape.Vertexes)
                neutral_error=max(neutral_error,*(math.dist(tuple(a.Point),tuple(b.Point)) for a,b in zip(expected.Vertexes,obj.Shape.Vertexes)))
            m=effective[obj.Name]
            if m['kind']=='segment' and obj.Name.startswith(('Link','DirectCrank')):
                bores=[]
                for sk in getattr(obj.LinkedObject,'Group',[]):
                    if sk.TypeId=='Sketcher::SketchObject':
                        bores.extend(placement.multVec(sk.Placement.multVec(g.Center)) for g in sk.Geometry if isinstance(g,Part.Circle))
                        if any(isinstance(g,Part.Circle) for g in sk.Geometry):
                            axis = placement.Rotation.multVec(sk.Placement.Rotation.multVec(App.Vector(0,0,1)))
                            axis_angle_error=max(axis_angle_error,math.acos(min(1.,abs(axis.y)/axis.Length)))
                for key in (m['a'],m['b']):
                    axis_error=max(axis_error,min(math.dist((v.x,v.z),state[key]) for v in bores))
            if m['kind']=='leg_r02_spring':procedural.append(_spring_record(doc,obj.Name,m,plan,frame_id))
            elif m['kind']=='tendon_r03_cable':procedural.append(_cable_record(obj.Name,m,plan,frame_id))
            if m['kind'] in ('leg_r02_spring','tendon_r03_cable'):
                procedural[-1]['local_shape_sha256']=shape_hash(local)
                procedural[-1]['shape_parameters_sha256']=digest(serial(plan['shape_requests'].get(obj.Name,procedural[-1])))
                modules = ('build_tendon_r03.py','tendon_r03.py','cable_clamps_r07.py') if m['kind']=='tendon_r03_cable' else (
                    ('spring_wire_r03.py',) if m['spring']=='extension' else ('compression_spring_r07.py',))
                procedural[-1]['generator_source_sha256']={n:digest((ROOT/'src'/n).read_bytes()) for n in modules}
        assert max_error<=.02 and neutral_error<=.02 and axis_error<=.02 and axis_angle_error<=1e-4
        assert not plan['guide_warnings']
        spine_residual=max(abs(r) for r in residuals(state,p))
        leg_residual=max(abs(r) for leg in plan['state']['legs'].values() for r in leg['geometry']['loop_residuals_mm'].values())
        assert spine_residual<=1e-6 and leg_residual<=1e-6 and min(state['margins_mm'])>0
        anchor_error=0.
        for row in procedural:
            for anchor in row.get('anchors',row.get('owner_anchors',[])):
                body=anchor['owner_instance_id'].removeprefix('instance:')
                world=plan['placements'][body].multVec(App.Vector(*anchor['owner_local_mm']))
                anchor_error=max(anchor_error,math.dist(tuple(world),anchor['world_mm']))
        assert anchor_error<=.02
        frames.append({'frame_id':frame_id,'time_s':float(index),'commanded_order':list(COMMANDS),
                       'commanded_rad':[theta]+[float(plan['leg_angles_rad'][t][0]) for t in TAGS]+[wheel],
                       'prescribed_knees_rad':{t:float(plan['leg_angles_rad'][t][1]) for t in TAGS},
                       'leg_angles_rad':{t:list(plan['leg_angles_rad'][t]) for t in TAGS},
                       'passive_provenance':'PRESCRIBED_KINEMATIC','transforms_mm':mm,'transforms_m':metres,
                       'quaternions_wxyz':quats,'procedural_shapes':procedural})
        checks.append({'frame_id':frame_id,'instances':len(shapes),'source_vertex_tests':points,
                       'local_to_world_max_error_mm':max_error,'neutral_native_vertex_max_error_mm':neutral_error,
                       'native_link_bore_center_max_error_mm':axis_error,'guide_warnings':plan['guide_warnings'],
                       'native_link_axis_angle_max_error_rad':axis_angle_error,
                       'spine_closure_max_residual_mm':spine_residual,'leg_loop_max_residual_mm':leg_residual,
                       'spine_min_branch_margin_mm':min(state['margins_mm']),
                       'procedural_owner_anchor_max_reprojection_mm':anchor_error,
                       'regenerated_instances':sorted(regenerated)})
        previous=quats
    config_files = ['parameters/assembly_'+revision+'.json','parameters/candidate_r02.json']
    payload = {'schema_version':'1.0','source':{'cad_path':str(native.relative_to(ROOT)),'cad_sha256':native_sha,
               'cad_revision':revision,'parameter_files_sha256':{s:digest((ROOT/s).read_bytes()) for s in config_files},
               'motion_map_sha256':digest(controller.MotionMap.encode()),
               'exporter_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},
               'conventions':{'world_axes':{'x':'forward','y':'left','z':'up'},'axis_mapping':'identity',
               'handedness':'right','cad_length_unit':'mm','blender_length_unit':'m','angle_unit':'rad',
               'matrix_layout':'row_major_nested_rows','vectors':'column','quaternion_order':'wxyz','reference_pose_id':'neutral_v1'},
               'instances':instances,'meshes':[meshes[k] for k in sorted(meshes)],
               'instance_order':['instance:'+o.Name for o in links],'frames':frames}
    validate_manifest(payload)
    assert before==snapshot(doc), 'Read-only adapter mutated document'
    assert native_sha==digest(native.read_bytes()), 'Canonical file changed'
    out=Path(output) if output else ROOT/'animation/motion'/('ax01_'+revision+'.json')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    report={'AX0':'PASS','AX1':'PASS','native_sha256':native_sha,'cad_revision':revision,
            'physical_instances':len(links),'source_definitions':len(meshes),'native_motion_entries':len(original_motion),
            'reviewed_explicit_grounded_instances':absent,'effective_motion_coverage':len(effective),
            'motion_kinds':dict(Counter(m['kind'] for m in effective.values())),
            'frame_checks':checks,'source_to_world_convention':'VERIFIED; LinkTransform=false; identity source/shape placements; one source-local placement',
            'document_unchanged':True,'native_file_unchanged':True,'output':str(out.relative_to(ROOT)),
            'output_sha256':digest(out.read_bytes()),'exporter_source_sha256':digest(Path(__file__).read_bytes()),
            'grounding_sha256':digest(grounding_path.read_bytes()),
            'limits':['Three prescribed poses only; no new clearance campaign or loaded gait prediction.',
                      'No meshes/Blender importer/video produced; AX2-AX4 NOT_RUN.',
                      'All ten deforming instances have procedural state; frozen mesh IDs are neutral source references only.',
                      'Joint parents/axes remain in the unmodified authoritative MotionMap; multi-parent closed loops are not flattened to a tree.',
                      'Unmapped grounded instances are explicit in an SHA-pinned reviewed supplement; future inventory changes fail closed.']}
    report['authoritative_motion_map']=original_motion
    report['generator_source_sha256']={n:digest((ROOT/'src'/n).read_bytes()) for n in
            ('robot_pose_r03.py','leg_motion_r07.py','spring_wire_r03.py','compression_spring_r07.py',
             'build_tendon_r03.py','cable_clamps_r07.py','animation_manifest_validate.py')}
    report['command_coupling']={'physical_motors':7,'commanded_coordinates':6,
            'spine_motor_inputs':'Two redundant XL330 motors share the one unwrapped spine_phase coordinate.',
            'prescribed_knees':4,'loaded_passive_motion':'NOT_SOLVED'}
    report['component_metadata']={o.Name:{'label':o.Label,'material':str(getattr(o.LinkedObject,'MaterialName','')),
                                    'release_status':str(getattr(o.LinkedObject,'ReleaseStatus','PROVISIONAL')),
                                    'source_local_origin_mm':[0,0,0], 'source_local_axes':'native right-handed XYZ',
                                    'parent_frame':'central_world for ground; authoritative closed-loop MotionMap for articulated parts',
                                    'motion':effective[o.Name]} for o in links}
    dest=ROOT/'reports/animation'/('ax01_'+revision+'.json');dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print('AX0_AX1_PASS',len(links),len(frames),max(r['local_to_world_max_error_mm'] for r in checks),flush=True)
    return report
